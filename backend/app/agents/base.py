"""Base Agent Class"""
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from app.llm.provider import LLMProvider

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Base class for all agents"""
    
    def __init__(
        self,
        name: str,
        llm_provider: Optional[LLMProvider] = None,
    ):
        self.name = name
        self.llm = llm_provider
        self.logger = logging.getLogger(f"{__name__}.{name}")
    
    @abstractmethod
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process the (read-only) state and return a PARTIAL state update.

        Only return the keys this agent owns (plus "errors"/"warnings" for
        anything that went wrong). Do not mutate the incoming `state` dict —
        this agent may run concurrently with sibling agents in the same
        LangGraph superstep, and the graph merges each node's returned dict
        via the reducers declared on FinancialAnalysisState.
        """
        pass
    
    async def call_llm(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """Call LLM with error handling"""
        if not self.llm:
            self.logger.warning(f"{self.name}: No LLM provider configured")
            return "LLM not available"
        
        try:
            response = await self.llm.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                **kwargs
            )
            if response.success:
                return response.content
            else:
                self.logger.error(f"LLM error: {response.error}")
                return f"Error: {response.error}"
        except Exception as e:
            self.logger.error(f"LLM call failed: {e}")
            return f"Error: {str(e)}"