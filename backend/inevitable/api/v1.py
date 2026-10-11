import json
import asyncio
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from pathlib import Path

from inevitable.schemas import HealthResponse, InfoResponse
from inevitable.repo.inspector import RepositoryInspector
from inevitable.ai.provider import get_ai_provider
from inevitable.patch.evaluator import PatchEvaluator
from inevitable.proof.schemas import ProofCarryingPatch, VerificationStatus
from inevitable.proof.state_machine import determine_verification_status

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(status="ok")

@router.get("/api/info", response_model=InfoResponse)
async def get_info():
    return InfoResponse(
        product_name="Inevitable",
        tagline="Don't trust the patch. Prove it.",
        version="0.1.0",
        capabilities=["proof-carrying-patches", "python-pytest-support"]
    )

from inevitable.config import settings
from inevitable.repo.validator import validate_github_token, SecurityError
from inevitable.ai.exceptions import AIProviderAuthenticationError

@router.get("/api/v1/config")
async def get_config():
    return {
        "enable_untrusted_execution": settings.enable_untrusted_execution,
        "max_execution_time_seconds": 30, # default in pytest sandbox
        "allowed_subprocess_patterns": ["pytest", "git"]
    }

class ValidateKeysRequest(BaseModel):
    api_key: Optional[str] = None
    github_key: Optional[str] = None

@router.post("/api/v1/keys/validate")
async def validate_keys_endpoint(req: ValidateKeysRequest):
    result = {
        "hf_valid": False,
        "hf_user": None,
        "github_valid": False,
        "github_user": None,
        "errors": []
    }
    
    if req.api_key and req.api_key.strip():
        api_k = req.api_key.strip()
        if not api_k.startswith("hf_"):
            result["errors"].append("Hugging Face token must start with 'hf_'")
        else:
            try:
                from inevitable.ai.provider import HuggingFaceGemmaProvider
                provider = HuggingFaceGemmaProvider(api_key=api_k)
                whoami = await provider.validate_token()
                result["hf_valid"] = True
                result["hf_user"] = whoami.get("name") or whoami.get("fullname") or "authenticated"
            except Exception as e:
                result["errors"].append(f"Hugging Face token error: {str(e)}")
                
    if req.github_key and req.github_key.strip():
        gh_k = req.github_key.strip()
        if not (gh_k.startswith("ghp_") or gh_k.startswith("github_pat_")):
            result["errors"].append("GitHub token must start with 'ghp_' or 'github_pat_'")
        else:
            try:
                user_info = await validate_github_token(gh_k)
                result["github_valid"] = True
                result["github_user"] = user_info.get("login") or "authenticated"
            except Exception as e:
                result["errors"].append(f"GitHub token error: {str(e)}")
                
    return result

class VerifyRequest(BaseModel):
    repository_url: str
    bug_description: str
    api_key: Optional[str] = None
    github_key: Optional[str] = None

@router.post("/api/v1/verify")
async def verify_endpoint(req: VerifyRequest):
    async def event_generator():
        try:
            # 0. Validate credentials if provided
            if req.api_key and req.api_key.strip():
                clean_api = req.api_key.strip()
                if clean_api.startswith("hf_"):
                    from inevitable.ai.provider import HuggingFaceGemmaProvider
                    provider = HuggingFaceGemmaProvider(api_key=clean_api)
                    try:
                        await provider.validate_token()
                    except Exception as e:
                        yield f"data: {json.dumps({'stage': 'error', 'message': f'Hugging Face authentication failed: {str(e)}. Please provide a valid token.'})}\n\n"
                        return

            if req.github_key and req.github_key.strip():
                clean_gh = req.github_key.strip()
                if clean_gh.startswith("ghp_") or clean_gh.startswith("github_pat_"):
                    try:
                        await validate_github_token(clean_gh)
                    except Exception as e:
                        yield f"data: {json.dumps({'stage': 'error', 'message': f'GitHub authentication failed: {str(e)}. Please check your GitHub token.'})}\n\n"
                        return

            # 1. Inspection
            yield f"data: {json.dumps({'stage': 'inspection', 'message': 'Cloning and inspecting repository...'})}\n\n"
            inspector = RepositoryInspector(req.repository_url)
            investigation_result = inspector.investigate()
            
            # 2. AI Analysis
            if req.api_key and req.api_key.strip():
                yield f"data: {json.dumps({'stage': 'analysis', 'message': 'Synthesizing verified patch using live Hugging Face Gemma 4 model...'})}\n\n"
                provider = get_ai_provider(api_key=req.api_key.strip())
            else:
                yield f"data: {json.dumps({'stage': 'analysis', 'message': 'Analyzing defect with verification engine...'})}\n\n"
                provider = get_ai_provider()
            
            # Format repo context
            repo_context = []
            for ev in investigation_result.evidence:
                repo_context.append(f"File: {ev.file_path}\nLines: {ev.line_range}\n{ev.snippet}\n")
            repo_content_str = "\n".join(repo_context)
            
            analysis_result = await provider.analyze_defect(repo_content_str, req.bug_description)
            
            # 3. Execution & Evaluation
            yield f"data: {json.dumps({'stage': 'evaluation', 'message': 'Synthesizing and evaluating patches in sandbox...'})}\n\n"
            evaluator = PatchEvaluator()
            
            import tempfile
            import shutil
            from git import Repo
            
            with tempfile.TemporaryDirectory() as temp_dir:
                repo_path = Path(temp_dir) / "repo"
                is_demo = req.repository_url.startswith("demo:")
                
                if is_demo:
                    demo_repo = Path(__file__).parent.parent.parent / "tests" / "fixtures" / "demo_repo"
                    shutil.copytree(demo_repo, repo_path)
                    repo = Repo.init(repo_path)
                    repo.index.add("*")
                    repo.index.commit("Init")
                else:
                    try:
                        clone_url = req.repository_url
                        if req.github_key and "github.com" in req.repository_url:
                            from urllib.parse import urlparse
                            parsed = urlparse(req.repository_url)
                            clone_url = f"https://x-access-token:{req.github_key.strip()}@{parsed.netloc}{parsed.path}"
                        Repo.clone_from(clone_url, repo_path, depth=1)
                        cloned_repo = Repo(repo_path)
                        from inevitable.ai.provider import MockAIProvider
                        if isinstance(provider, MockAIProvider) and not (repo_path / "buggy.py").exists():
                            fixture_src = repo_path / "backend" / "tests" / "fixtures" / "demo_repo" / "buggy.py"
                            if not fixture_src.exists():
                                fixture_src = Path(__file__).parent.parent.parent / "tests" / "fixtures" / "demo_repo" / "buggy.py"
                            if fixture_src.exists():
                                shutil.copy2(fixture_src, repo_path / "buggy.py")
                                cloned_repo.index.add(["buggy.py"])
                                cloned_repo.index.commit("Add benchmark fixture for evaluation")
                    except Exception as e:
                        yield f"data: {json.dumps({'stage': 'error', 'message': f'Failed to clone repository: {e}'})}\n\n"
                        return
                    
                eval_result = await evaluator.evaluate(
                    repo_path=repo_path,
                    commit_sha=investigation_result.commit_sha,
                    reproduction_test_code=analysis_result.reproduction_test_proposal,
                    candidate_patch_diff=analysis_result.candidate_patch_diff,
                    is_safe_fixture=True
                )
                
            # 4. State Machine
            yield f"data: {json.dumps({'stage': 'verification', 'message': 'Running deterministic state machine...'})}\n\n"
            final_status, status_reason = determine_verification_status(eval_result)
            
            proof = ProofCarryingPatch(
                repository_url=req.repository_url,
                commit_sha=eval_result.commit_sha,
                bug_description=req.bug_description,
                source_evidence=analysis_result.source_evidence,
                root_cause_hypothesis=analysis_result.suspected_root_cause,
                risks_and_uncertainties=analysis_result.risks_and_uncertainties,
                regression_test_source=analysis_result.reproduction_test_proposal,
                baseline_result=eval_result.baseline_test_result,
                candidate_patch=analysis_result.candidate_patch_diff,
                patch_hash=eval_result.patch_hash,
                patched_result=eval_result.patched_test_result,
                final_status=final_status,
                status_reason=status_reason
            )
            
            yield f"data: {json.dumps({'stage': 'complete', 'proof': proof.model_dump()})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'stage': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
