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

class HuggingFaceGemmaProvider(BaseAIProvider):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.together_api_key
        self.model_id = settings.gemma_model_id or "google/gemma-2-9b-it"
        self.timeout = settings.model_timeout or 120
        self.router_url = "https://router.huggingface.co/hf-inference/v1/chat/completions"
        self.direct_url = "https://api-inference.huggingface.co/v1/chat/completions"

    async def validate_token(self) -> Dict[str, Any]:
        """Validate token against Hugging Face API."""
        if not self.api_key:
            raise AIProviderAuthenticationError("Hugging Face API key is required.")
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://huggingface.co/api/whoami-v2",
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            if resp.status_code in (401, 403):
                raise AIProviderAuthenticationError("Invalid Hugging Face API token. Authentication failed.")
            resp.raise_for_status()
            return resp.json()

    async def analyze_defect(
        self, 
        repo_content: str, 
        defect_description: str
    ) -> AnalysisResult:
        if not self.api_key:
            raise AIProviderAuthenticationError("Hugging Face API key is required.")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        system_prompt = (
            "You are a strict, world-class automated software verification engine and patch synthesizer. "
            "Given code evidence and a defect description, diagnose the root cause, propose an isolated reproduction pytest test, "
            "and generate a unified git diff patch to fix it.\n"
            "You MUST respond ONLY with a valid JSON object matching this schema:\n"
            f"{json.dumps(AnalysisResult.model_json_schema())}\n"
            "Return raw JSON only, no explanatory markdown outside the JSON."
        )

        user_prompt = (
            f"=== DEFECT DESCRIPTION ===\n{defect_description}\n\n"
            f"=== SOURCE CODE EVIDENCE ===\n{repo_content}\n\n"
            "Return valid JSON containing:\n"
            "- defect_summary (string)\n"
            "- suspected_root_cause (string)\n"
            "- source_evidence (list of {file_path, line_range, snippet})\n"
            "- reproduction_test_proposal (executable pytest code that fails on baseline bug and passes with patch)\n"
            "- candidate_patch_diff (unified diff starting with --- a/... +++ b/...)\n"
            "- candidate_patch_rationale (string)\n"
            "- risks_and_uncertainties (string)"
        )

        payload = {
            "model": self.model_id,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 2048
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                # Try primary router URL
                try:
                    response = await client.post(self.router_url, headers=headers, json=payload)
                except Exception:
                    response = await client.post(self.direct_url, headers=headers, json=payload)

                if response.status_code in (401, 403):
                    raise AIProviderAuthenticationError("Invalid Hugging Face API key. Authentication failed.")
                if response.status_code == 429:
                    raise AIProviderRateLimit("Rate limited by Hugging Face API.")
                
                response.raise_for_status()
                data = response.json()
                raw_content = data["choices"][0]["message"]["content"]

                # Sanitize markdown wrapper ```json ... ``` if model enclosed it
                cleaned = raw_content.strip()
                if cleaned.startswith("```json"):
                    cleaned = cleaned[7:]
                elif cleaned.startswith("```"):
                    cleaned = cleaned[3:]
                if cleaned.endswith("```"):
                    cleaned = cleaned[:-3]
                cleaned = cleaned.strip()

                return AnalysisResult.model_validate_json(cleaned)

            except (AIProviderAuthenticationError, AIProviderRateLimit):
                raise
            except httpx.TimeoutException:
                raise AIProviderTimeout("Hugging Face API request timed out.")
            except Exception as e:
                logger.error(f"Hugging Face Inference error: {e}")
                raise AIProviderError(f"Hugging Face Gemma Inference failed: {str(e)}")

def get_ai_provider(provider_type: Optional[str] = None, api_key: Optional[str] = None) -> BaseAIProvider:
    # If explicit HF API key is provided or model type is huggingface
    if (api_key and api_key.startswith("hf_")) or provider_type == "huggingface":
        return HuggingFaceGemmaProvider(api_key=api_key)
    
    if provider_type == "together" or settings.gemma_provider == "together":
        return Gemma4TogetherProvider()
    
    # If no key is provided, fallback to Mock for local demo fixtures
    return MockAIProvider()

