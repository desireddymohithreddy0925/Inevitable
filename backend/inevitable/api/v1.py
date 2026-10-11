import json
import asyncio
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
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

@router.get("/api/v1/config")
async def get_config():
    return {
        "enable_untrusted_execution": settings.enable_untrusted_execution,
        "max_execution_time_seconds": 30, # default in pytest sandbox
        "allowed_subprocess_patterns": ["pytest", "git"]
    }

class VerifyRequest(BaseModel):
    repository_url: str
    bug_description: str

@router.post("/api/v1/verify")
async def verify_endpoint(req: VerifyRequest):
    async def event_generator():
        try:
            # 1. Inspection
            yield f"data: {json.dumps({'stage': 'inspection', 'message': 'Cloning and inspecting repository...'})}\n\n"
            inspector = RepositoryInspector(req.repository_url)
            investigation_result = inspector.investigate()
            
            # 2. AI Analysis
            yield f"data: {json.dumps({'stage': 'analysis', 'message': 'Analyzing defect with Gemma 4...'})}\n\n"
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
            
            # To evaluate, we need the local repo path from the inspector. 
            # Wait, inspector doesn't preserve the temporary directory across calls!
            # We need to adapt this. Since it's a demo, we can just use the fixture repo.
            from inevitable.config import settings
            import tempfile
            import shutil
            from git import Repo
            
            with tempfile.TemporaryDirectory() as temp_dir:
                repo_path = Path(temp_dir) / "repo"
                
                is_demo = req.repository_url.startswith("demo:")
                
                if is_demo:
                    # Safely load the controlled demo fixture and allow execution for it
                    demo_repo = Path(__file__).parent.parent.parent / "tests" / "fixtures" / "demo_repo"
                    shutil.copytree(demo_repo, repo_path)
                    repo = Repo.init(repo_path)
                    repo.index.add("*")
                    repo.index.commit("Init")
                else:
                    try:
                        Repo.clone_from(req.repository_url, repo_path, depth=1)
                    except Exception as e:
                        yield f"data: {json.dumps({'stage': 'error', 'message': f'Failed to clone repo: {e}'})}\n\n"
                        return
                    
                eval_result = await evaluator.evaluate(
                    repo_path=repo_path,
                    commit_sha=investigation_result.commit_sha,
                    reproduction_test_code=analysis_result.reproduction_test_proposal,
                    candidate_patch_diff=analysis_result.candidate_patch_diff,
                    is_safe_fixture=is_demo
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
