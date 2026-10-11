import abc
import json
import logging
from typing import Optional, Dict, Any
import httpx

from inevitable.ai.schemas import AnalysisResult
from inevitable.ai.exceptions import (
    AIProviderError, AIProviderTimeout, 
    AIProviderRateLimit, AIProviderAuthenticationError
)
from inevitable.config import settings

logger = logging.getLogger("inevitable.ai")

class BaseAIProvider(abc.ABC):
    @abc.abstractmethod
    async def analyze_defect(
        self, 
        repo_content: str, 
        defect_description: str
    ) -> AnalysisResult:
        """Analyze a defect and return structured findings."""
        pass

class MockAIProvider(BaseAIProvider):
    async def analyze_defect(
        self, 
        repo_content: str, 
        defect_description: str
    ) -> AnalysisResult:
        logger.info("[Mock] Analyzing defect...")
        return AnalysisResult(
            defect_summary="The `add_numbers` function intentionally subtracts instead of adding.",
            suspected_root_cause="Line 3 uses the subtraction operator (-) instead of the addition operator (+).",
            source_evidence=[{
                "file_path": "buggy.py",
                "line_range": "1-3",
                "snippet": "def add_numbers(a, b):\n    # Intentional bug: subtracts instead of adding\n    return a - b"
            }],
            reproduction_test_proposal="from buggy import add_numbers\n\ndef test_add_numbers_repro():\n    assert add_numbers(5, 3) == 8\n",
            candidate_patch_diff="--- a/buggy.py\n+++ b/buggy.py\n@@ -1,6 +1,6 @@\n def add_numbers(a, b):\n     # Intentional bug: subtracts instead of adding\n-    return a - b\n+    return a + b\n \n class Calculator:\n     def multiply(self, a, b):\n",
            candidate_patch_rationale="Change the operator from - to +.",
            risks_and_uncertainties="None. This is a controlled fixture."
        )

class Gemma4TogetherProvider(BaseAIProvider):
    def __init__(self):
        self.api_key = settings.together_api_key
        self.model_id = settings.gemma_model_id or "google/gemma-4-preview"
        self.timeout = settings.model_timeout
        self.base_url = "https://api.together.xyz/v1/chat/completions"

    async def analyze_defect(
        self, 
        repo_content: str, 
        defect_description: str
    ) -> AnalysisResult:
        if not self.api_key:
            raise AIProviderAuthenticationError("TOGETHER_API_KEY is not configured.")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Defend against prompt injection by clearly separating data and instructions
        system_prompt = (
            "You are a strict software verification analyzer. "
            "Return ONLY valid JSON matching this schema: "
            f"{AnalysisResult.model_json_schema()}"
        )
        
        user_prompt = (
            f"Defect Description:\n{defect_description}\n\n"
            f"Repository Content:\n{repo_content}"
        )

        payload = {
            "model": self.model_id,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "response_format": {"type": "json_object"}
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(self.base_url, headers=headers, json=payload)
                if response.status_code == 401:
                    raise AIProviderAuthenticationError("Invalid API key.")
                if response.status_code == 429:
                    raise AIProviderRateLimit("Rate limited by provider.")
                response.raise_for_status()
                
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                return AnalysisResult.model_validate_json(content)
            
            except httpx.TimeoutException:
                raise AIProviderTimeout("Provider request timed out.")
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error from AI provider: {e.response.status_code}")
                raise AIProviderError(f"HTTP error: {e.response.status_code}")
            except Exception as e:
                logger.error(f"Unexpected provider error: {str(e)}")
                raise AIProviderError("Failed to parse or retrieve model response.")

def get_ai_provider() -> BaseAIProvider:
    if settings.gemma_provider == "mock":
        return MockAIProvider()
    elif settings.gemma_provider == "together":
        return Gemma4TogetherProvider()
    else:
        raise ValueError(f"Unknown GEMMA_PROVIDER: {settings.gemma_provider}")
