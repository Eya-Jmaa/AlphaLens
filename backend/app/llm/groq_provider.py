"""Groq LLM Provider Implementation"""
import logging
from typing import Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.exceptions import LLMException
from app.llm.config import LLMConfig
from app.llm.provider import LLMProvider, LLMResponse

logger = logging.getLogger(__name__)


class GroqProvider(LLMProvider):
    """Groq API LLM Provider"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self._client = None
        self._init_client()
    
    def _init_client(self):
        """Initialize Groq client"""
        try:
            self._client = ChatGroq(
                groq_api_key=self.config.api_key,
                model_name=self.config.model,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                timeout=self.config.timeout,
            )
            logger.info(f"Initialized Groq provider with model: {self.config.model}")
        except Exception as e:
            logger.error(f"Failed to initialize Groq client: {e}")
            raise LLMException(f"Groq initialization failed: {e}")
    
    @retry(
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=1, min=1, max=20),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    async def _call_api(self, messages: list, params: dict):
        """The actual network call, retried on transient failures (rate limits,
        timeouts). Must raise on failure - `generate()` below is what catches
        and converts a final, retries-exhausted failure into a graceful
        LLMResponse(success=False, ...). Retrying `generate()` itself would be a
        no-op, since it never lets an exception escape."""
        return await self._client.agenerate([messages], **params)

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate response from Groq"""
        try:
            messages = []

            if system_prompt:
                messages.append(SystemMessage(content=system_prompt))

            messages.append(HumanMessage(content=prompt))

            # Prepare parameters
            params = {
                "temperature": temperature or self.config.temperature,
                "max_tokens": max_tokens or self.config.max_tokens,
            }

            response = await self._call_api(messages, params)

            # Extract response
            content = response.generations[0][0].text

            # Get token usage
            usage = {
                "prompt_tokens": response.llm_output.get("token_usage", {}).get("prompt_tokens", 0),
                "completion_tokens": response.llm_output.get("token_usage", {}).get("completion_tokens", 0),
                "total_tokens": response.llm_output.get("token_usage", {}).get("total_tokens", 0),
            }

            logger.debug(f"Groq response: {len(content)} chars, tokens: {usage}")

            return LLMResponse(
                content=content,
                model=self.config.model,
                usage=usage,
                metadata={"temperature": params["temperature"]},
                success=True,
            )

        except Exception as e:
            logger.error(f"Groq generation failed after retries: {e}")
            return LLMResponse(
                content="",
                model=self.config.model,
                usage={},
                metadata={},
                success=False,
                error=str(e),
            )