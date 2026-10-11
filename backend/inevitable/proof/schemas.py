from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum
import datetime

from inevitable.ai.schemas import SourceEvidence
from inevitable.test_runner.schemas import ExecutionResult
from inevitable.patch.schemas import EvaluationResult

class VerificationStatus(str, Enum):
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    INCONCLUSIVE = "INCONCLUSIVE"
    BLOCKED = "BLOCKED"

class ProofCarryingPatch(BaseModel):
    # 1. Repository identity and exact source commit.
    repository_url: str
    commit_sha: str
    
    # 2. Bug description and investigation timestamp.
    bug_description: str
    investigation_timestamp: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    
    # 3. Source file paths, line ranges and evidence snippets.
    source_evidence: List[SourceEvidence]
    
    # 4. Root-cause hypothesis with explicit uncertainty.
    root_cause_hypothesis: str
    risks_and_uncertainties: str
    
    # 5. Regression-test source and intended behavior.
    regression_test_source: str
    
    # 6. Baseline execution result.
    baseline_result: Optional[ExecutionResult]
    
    # 7. Candidate patch and cryptographic patch hash.
    candidate_patch: str
    patch_hash: str
    
    # 8. Patched execution result.
    patched_result: Optional[ExecutionResult]
    
    # 10. Final deterministic status and machine-readable reasons.
    final_status: VerificationStatus
    status_reason: str
    
    # 11. Known limitations and checks not performed.
    limitations: List[str] = Field(default_factory=lambda: [
        "A passing test suite is not a mathematical proof of complete correctness.",
        "Security execution boundaries may be limited depending on the host configuration.",
        "Side effects (database, network) are not fully intercepted or verified."
    ])
