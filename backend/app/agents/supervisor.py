"""Supervisor Agent - Understands the query and decides which agents to run.

This agent is the entry node of the LangGraph workflow (see app/graph/workflow.py).
It does NOT execute the other agents itself anymore - it only extracts tickers and
decides routing; the graph's conditional edges fan out to the selected agent nodes,
which the graph then runs (in parallel where possible).
"""
import logging
import re
from typing import Any, Dict, List

from app.agents.base import BaseAgent
from app.core.known_companies import find_tickers_in_text
from app.llm.provider import LLMProvider

logger = logging.getLogger(__name__)


class SupervisorAgent(BaseAgent):
    """Supervisor Agent - decides which specialized agents a query needs."""

    def __init__(
        self,
        llm_provider: LLMProvider,
        available_agents: List[BaseAgent] = None,
    ):
        super().__init__("Supervisor", llm_provider)
        self.available_agents = available_agents or []
        self.agent_map = {agent.name: agent for agent in self.available_agents}
        logger.info(f"Available agents: {list(self.agent_map.keys())}")

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Extract tickers and decide which agents are required for this query."""
        user_query = state.get("user_query", "")
        self.logger.info(f"Supervisor analyzing query: {user_query}")

        tickers = await self._extract_tickers(user_query)
        self.logger.info(f"Extracted tickers: {tickers}")

        required_agents = self._determine_agents(user_query, tickers)
        debate_mode = bool(state.get("debate_mode")) or self._wants_debate(user_query)

        warnings = []
        available_required = []
        for agent_name in required_agents:
            if agent_name in self.agent_map:
                available_required.append(agent_name)
            else:
                warnings.append(f"Agent {agent_name} not available in this deployment")

        self.logger.info(f"Required agents: {available_required}, debate mode: {debate_mode}")

        return {
            "tickers": tickers,
            "required_agents": available_required,
            "debate_mode": debate_mode,
            "warnings": warnings,
        }

    def _wants_debate(self, query: str) -> bool:
        """Auto-detect debate intent from the query text (in addition to the
        explicit `debate` request flag, which already seeds state["debate_mode"])."""
        query_lower = query.lower()
        return any(
            phrase in query_lower
            for phrase in ["bull and bear", "bull vs bear", "bull vs. bear", "bull case and bear case", "debate"]
        )

    async def _extract_tickers(self, query: str) -> List[str]:
        """Extract stock tickers from the query (cheap keyword pass, LLM fallback)."""
        tickers = find_tickers_in_text(query)

        if not tickers:
            try:
                prompt = f"""
                Extract all stock ticker symbols from this query.
                Query: {query}
                Return only the ticker symbols as a comma-separated list.
                If no tickers found, return "NONE".
                Examples:
                - "Analyze NVIDIA" -> "NVDA"
                - "Compare Apple and Microsoft" -> "AAPL, MSFT"
                - "What about Tesla?" -> "TSLA"
                """

                response = await self.call_llm(prompt)
                if response and response.strip().upper() != "NONE" and not response.startswith("Error"):
                    candidates = [t.strip().upper() for t in response.split(",") if t.strip()]
                    # Keep only plausible ticker symbols (1-5 letters, optional dot-class suffix)
                    tickers = [t for t in candidates if re.fullmatch(r"[A-Z]{1,5}(\.[A-Z])?", t)]
            except Exception as e:
                self.logger.warning(f"LLM ticker extraction failed: {e}")

        return tickers

    def _determine_agents(self, query: str, tickers: List[str]) -> List[str]:
        """Determine which agents are needed for the query."""
        query_lower = query.lower()
        agents: List[str] = []

        if tickers:
            # Technical analysis is computed as part of stock analysis (deterministic,
            # no separate LLM agent needed), so technical-sounding queries just confirm
            # StockAnalysis is included rather than routing to a nonexistent agent.
            agents.append("StockAnalysis")

        if tickers and any(
            word in query_lower for word in ["news", "sentiment", "current", "recent", "headline", "latest"]
        ):
            agents.append("NewsAnalysis")

        if tickers and any(
            word in query_lower for word in ["risk", "volatility", "var", "drawdown", "safe", "danger", "portfolio"]
        ):
            agents.append("RiskAnalysis")

        if tickers and any(
            word in query_lower for word in ["sec", "filing", "10-k", "10-q", "10k", "10q", "annual report"]
        ):
            agents.append("SECAnalysis")

        return agents
