"""LLM Provider Tests"""
from unittest.mock import AsyncMock, patch

import pytest

from app.core.exceptions import LLMException
from app.llm import GroqProvider, LLMConfig


@pytest.fixture
def llm_config():
    return LLMConfig(
        api_key="test-key",
        model="test-model",
        temperature=0.3,
        max_tokens=100,
        timeout=10,
    )


@pytest.mark.asyncio
async def test_groq_provider_initialization(llm_config):
    """Test Groq provider initialization"""
    provider = GroqProvider(llm_config)
    assert provider is not None
    assert provider.config.model == "test-model"


@pytest.mark.asyncio
async def test_groq_provider_failed_initialization():
    """Test Groq provider initialization with invalid config"""
    config = LLMConfig(
        api_key="",
        model="test-model",
        temperature=0.3,
        max_tokens=100,
        timeout=10,
    )
    
    with pytest.raises(LLMException):
        GroqProvider(config)


@pytest.mark.asyncio
async def test_groq_generation(llm_config):
    """Test Groq generation (mocked)"""
    with patch("app.llm.groq_provider.ChatGroq") as mock_groq:
        # Setup mock
        mock_instance = AsyncMock()
        mock_instance.agenerate.return_value = type(
            'Response',
            (),
            {
                'generations': [[type('Generation', (), {'text': 'Test response'})()]],
                'llm_output': {'token_usage': {'total_tokens': 10}},
            }
        )()
        mock_groq.return_value = mock_instance
        
        provider = GroqProvider(llm_config)
        response = await provider.generate("Test prompt")
        
        assert response.success is True
        assert response.content == "Test response"
        assert response.model == "test-model"