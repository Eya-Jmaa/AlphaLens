"""LangGraph-based orchestration for the AlphaLens multi-agent workflow.

Supervisor runs once (ticker extraction + routing), fans out to the required
evidence-gathering agents in parallel (they write to disjoint state keys), then
joins at EvidenceJoin. From there, debate-mode queries branch into a parallel
Bull/Bear argument pair -> Judge before reaching the Final Analyst; everything
else goes straight to the Final Analyst.
"""
import logging
import time
from typing import Any, AsyncIterator, Dict, List, Optional

from langgraph.graph import END, StateGraph

from app.agents.base import BaseAgent
from app.agents.bear import BearAgent
from app.agents.bull import BullAgent
from app.agents.final import FinalAnalystAgent
from app.agents.judge import JudgeAgent
from app.agents.stock import StockAnalysisAgent
from app.agents.supervisor import SupervisorAgent
from app.graph.state import FinancialAnalysisState, create_initial_state
from app.llm.provider import LLMProvider
from app.services.company_service import CompanyService

logger = logging.getLogger(__name__)

ADDITIVE_KEYS = ("errors", "warnings", "completed_agents", "evidence")
MERGE_DICT_KEYS = ("agent_timings", "debate_results")

EVIDENCE_JOIN = "EvidenceJoin"


def _load_news_agent(llm_provider) -> Optional[BaseAgent]:
    try:
        import textblob  # noqa: F401

        from app.agents.news import NewsAgent
        return NewsAgent(llm_provider)
    except Exception as e:
        logger.warning(f"NewsAgent unavailable, continuing without it: {e}")
        return None


def _load_risk_agent(llm_provider) -> Optional[BaseAgent]:
    try:
        import pypfopt  # noqa: F401

        from app.agents.risk import RiskAgent
        return RiskAgent(llm_provider)
    except Exception as e:
        logger.warning(f"RiskAgent unavailable, continuing without it: {e}")
        return None


def _load_sec_agent(llm_provider) -> Optional[BaseAgent]:
    try:
        from app.agents.sec import SECAgent
        return SECAgent(llm_provider)
    except Exception as e:
        logger.warning(f"SECAgent unavailable, continuing without it: {e}")
        return None


def _wrap_agent_node(agent: BaseAgent):
    """Wrap an agent's process() with uniform timing + completed_agents bookkeeping."""

    async def node(state: FinancialAnalysisState) -> Dict[str, Any]:
        start = time.monotonic()
        try:
            update = await agent.process(state)
        except Exception as e:
            logger.error(f"{agent.name} node failed: {e}")
            update = {"errors": [f"{agent.name} failed: {str(e)}"]}

        update = dict(update or {})
        update["completed_agents"] = [agent.name]
        update["agent_timings"] = {agent.name: round(time.monotonic() - start, 3)}
        return update

    return node


async def _evidence_join_node(state: FinancialAnalysisState) -> Dict[str, Any]:
    """Pure structural join point - not a user-facing agent, so it doesn't
    appear in completed_agents/agent_timings."""
    return {}


def _merge_update(state: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
    """Mirror the graph's declared reducers so the manually-accumulated stream view
    (built from per-node deltas in `stream()`) matches what `ainvoke` would return."""
    merged = dict(state)
    for key, value in update.items():
        if key in ADDITIVE_KEYS:
            merged[key] = merged.get(key, []) + value
        elif key in MERGE_DICT_KEYS:
            merged[key] = {**merged.get(key, {}), **value}
        else:
            merged[key] = value
    return merged


class AlphaLensWorkflow:
    """Builds and runs the compiled LangGraph workflow for a given LLM provider."""

    def __init__(self, llm_provider: LLMProvider, company_service: Optional[CompanyService] = None):
        self.llm_provider = llm_provider
        self.company_service = company_service or CompanyService()

        self.stock_agent = StockAnalysisAgent(llm_provider, self.company_service)
        self.final_agent = FinalAnalystAgent(llm_provider)
        self.bull_agent = BullAgent(llm_provider)
        self.bear_agent = BearAgent(llm_provider)
        self.judge_agent = JudgeAgent(llm_provider)
        self.news_agent = _load_news_agent(llm_provider)
        self.risk_agent = _load_risk_agent(llm_provider)
        self.sec_agent = _load_sec_agent(llm_provider)

        self.available_agents: List[BaseAgent] = [self.stock_agent]
        for agent in (self.news_agent, self.risk_agent, self.sec_agent):
            if agent:
                self.available_agents.append(agent)

        self.supervisor = SupervisorAgent(llm_provider, self.available_agents)
        self.node_names = [a.name for a in self.available_agents]
        self.graph = self._build_graph()

    def _build_graph(self):
        graph = StateGraph(FinancialAnalysisState)

        graph.add_node("Supervisor", _wrap_agent_node(self.supervisor))
        graph.add_node(EVIDENCE_JOIN, _evidence_join_node)
        graph.add_node("FinalAnalyst", _wrap_agent_node(self.final_agent))
        graph.add_node("BullCase", _wrap_agent_node(self.bull_agent))
        graph.add_node("BearCase", _wrap_agent_node(self.bear_agent))
        graph.add_node("Judge", _wrap_agent_node(self.judge_agent))
        for agent in self.available_agents:
            graph.add_node(agent.name, _wrap_agent_node(agent))

        graph.set_entry_point("Supervisor")

        node_names = self.node_names

        def route_from_supervisor(state: FinancialAnalysisState) -> List[str]:
            required = [a for a in state.get("required_agents", []) if a in node_names]
            return required if required else [EVIDENCE_JOIN]

        supervisor_routing_map = {name: name for name in node_names}
        supervisor_routing_map[EVIDENCE_JOIN] = EVIDENCE_JOIN
        graph.add_conditional_edges("Supervisor", route_from_supervisor, supervisor_routing_map)

        for name in node_names:
            graph.add_edge(name, EVIDENCE_JOIN)

        def route_from_evidence_join(state: FinancialAnalysisState) -> List[str]:
            return ["BullCase", "BearCase"] if state.get("debate_mode") else ["FinalAnalyst"]

        graph.add_conditional_edges(
            EVIDENCE_JOIN,
            route_from_evidence_join,
            {"BullCase": "BullCase", "BearCase": "BearCase", "FinalAnalyst": "FinalAnalyst"},
        )

        graph.add_edge("BullCase", "Judge")
        graph.add_edge("BearCase", "Judge")
        graph.add_edge("Judge", "FinalAnalyst")
        graph.add_edge("FinalAnalyst", END)

        return graph.compile()

    async def run(self, query: str, debate: bool = False) -> FinancialAnalysisState:
        """Run the full workflow synchronously and return the final merged state."""
        initial_state = create_initial_state(query, debate_mode=debate)
        try:
            return await self.graph.ainvoke(initial_state)
        except Exception as e:
            logger.error(f"Workflow run failed: {e}")
            initial_state["errors"] = initial_state.get("errors", []) + [f"Workflow failed: {str(e)}"]
            return initial_state

    async def stream(self, query: str, debate: bool = False) -> AsyncIterator[Dict[str, Any]]:
        """Stream per-node progress events as they complete, then a final 'done' event."""
        initial_state = create_initial_state(query, debate_mode=debate)
        accumulated: Dict[str, Any] = dict(initial_state)

        try:
            async for step in self.graph.astream(initial_state, stream_mode="updates"):
                for node_name, update in step.items():
                    # LangGraph reports a no-op node's update as None (e.g. the
                    # structural EvidenceJoin node, which writes nothing).
                    update = update or {}
                    accumulated = _merge_update(accumulated, update)
                    if node_name == EVIDENCE_JOIN:
                        continue  # structural node, not user-facing
                    yield {
                        "type": "agent_completed",
                        "agent": node_name,
                        "errors": update.get("errors", []),
                        "warnings": update.get("warnings", []),
                    }
        except Exception as e:
            logger.error(f"Workflow stream failed: {e}")
            accumulated["errors"] = accumulated.get("errors", []) + [f"Workflow failed: {str(e)}"]
            yield {"type": "agent_completed", "agent": "Workflow", "errors": [str(e)], "warnings": []}

        yield {"type": "done", "state": accumulated}
