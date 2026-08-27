"""Abstract LLM Provider Interface"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class LLMResponse:
    """Standardized LLM response"""
    
    content: str
    model: str
    usage: Dict[str, int]  # token usage
    metadata: Dict[str, Any]
    success: bool = True
    error: Optional[str] = None
    
    @property
    def text(self) -> str:
        """Get response content"""
        return self.content


class LLMProvider(ABC):
    """Abstract interface for LLM providers.

    Deliberately just one method: every agent calls the LLM for reasoning/
    synthesis over already-computed data (see BaseAgent.call_llm) - there's no
    native tool-calling or token-streaming anywhere in this codebase (the
    LangGraph workflow's own SSE progress stream is agent-completion events,
    not token streaming - see app/graph/workflow.py), so those aren't part of
    the interface every provider implementation would otherwise have to satisfy.
    """

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate response from LLM"""
        pass