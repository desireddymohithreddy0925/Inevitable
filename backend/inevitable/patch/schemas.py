from pydantic import BaseModel, Field
from typing import Optional
from inevitable.test_runner.schemas import ExecutionResult

class PatchValidationResult(BaseModel):
    is_valid: bool
    error_message: Optional[str] = None
    hash: str = ""

class EvaluationResult(BaseModel):
    commit_sha: str
    patch_hash: str
    patch_applied: bool
    patch_apply_error: Optional[str] = None
    baseline_test_result: Optional[ExecutionResult] = None
    patched_test_result: Optional[ExecutionResult] = None
    
    @property
    def verification_passed(self) -> bool:
        """
        True if the baseline test failed (proving it reproduces the bug)
        and the patched test passed (proving the patch fixes it).
        """
        if not self.patch_applied:
            return False
        if not self.baseline_test_result or not self.patched_test_result:
            return False
        # Baseline must fail (exit code 1 usually, meaning test failed)
        # Patched must pass (exit code 0)
        return not self.baseline_test_result.passed and self.patched_test_result.passed
