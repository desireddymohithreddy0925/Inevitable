import pytest
from inevitable.ai.schemas import AnalysisResult
from inevitable.ai.provider import MockAIProvider, Gemma4TogetherProvider, get_ai_provider
from inevitable.ai.exceptions import AIProviderAuthenticationError

import asyncio

def test_mock_provider_returns_valid_schema():
    """MOCKED TEST: Verify that the mock provider returns a valid AnalysisResult schema."""
    provider = MockAIProvider()
    result = asyncio.run(provider.analyze_defect("repo data", "bug description"))
    
    assert isinstance(result, AnalysisResult)
    assert "intentionally subtracts" in result.defect_summary
    assert "subtraction operator" in result.suspected_root_cause

def test_together_provider_without_key_raises_error(monkeypatch):
    """Test that the real integration correctly blocks if API key is not present."""
    from inevitable.config import settings
    monkeypatch.setattr(settings, "together_api_key", None)
    
    provider = Gemma4TogetherProvider()
    with pytest.raises(AIProviderAuthenticationError):
        import asyncio
        asyncio.run(provider.analyze_defect("repo data", "bug"))

def test_get_ai_provider_mock(monkeypatch):
    from inevitable.config import settings
    monkeypatch.setattr(settings, "gemma_provider", "mock")
    provider = get_ai_provider()
    assert isinstance(provider, MockAIProvider)
