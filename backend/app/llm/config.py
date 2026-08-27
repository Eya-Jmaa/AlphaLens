"""LLM Configuration"""
from dataclasses import dataclass


@dataclass
class LLMConfig:
    """Configuration for LLM provider"""
    
    api_key: str
    model: str
    temperature: float = 0.3
    max_tokens: int = 4096
    timeout: int = 60
    
    # Optional settings
    max_retries: int = 3
    retry_delay: int = 1
    streaming: bool = False