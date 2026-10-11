from inevitable.patch.schemas import EvaluationResult
from inevitable.proof.schemas import VerificationStatus

def determine_verification_status(eval_result: EvaluationResult) -> tuple[VerificationStatus, str]:
    """
    Deterministic verification state machine.
    Never relies on LLM heuristics.
    Returns a tuple of (status, reason).
    """
    # 1. BLOCKED
    if eval_result.patch_apply_error and "SecurityPolicyError" in eval_result.patch_apply_error:
        return VerificationStatus.BLOCKED, "Execution blocked by security policy constraints."
        
    if eval_result.baseline_test_result and eval_result.baseline_test_result.execution_error:
        return VerificationStatus.BLOCKED, "Baseline test execution failed at the infrastructure level."
        
    if eval_result.patched_test_result and eval_result.patched_test_result.execution_error:
        return VerificationStatus.BLOCKED, "Patched test execution failed at the infrastructure level."

    # 2. INCONCLUSIVE
    if not eval_result.baseline_test_result:
        return VerificationStatus.INCONCLUSIVE, "Baseline test results are missing."
        
    if eval_result.baseline_test_result.timed_out:
        return VerificationStatus.INCONCLUSIVE, "Baseline test timed out."
        
    if eval_result.baseline_test_result.passed:
        return VerificationStatus.INCONCLUSIVE, "The proposed regression test PASSED on the baseline, meaning it failed to reproduce the defect."

    if not eval_result.patch_applied:
        # Patch failed to apply. Not explicitly rejected as a bad fix, just inconclusive structure
        return VerificationStatus.INCONCLUSIVE, f"Patch failed to apply cleanly to the repository: {eval_result.patch_apply_error}"
        
    if not eval_result.patched_test_result:
        return VerificationStatus.INCONCLUSIVE, "Patched test results are missing despite successful patch application."
        
    if eval_result.patched_test_result.timed_out:
        return VerificationStatus.INCONCLUSIVE, "Patched test timed out."

    # 3. REJECTED
    # Baseline failed correctly, patch applied cleanly, but the patched test still fails.
    if not eval_result.patched_test_result.passed:
        return VerificationStatus.REJECTED, "The patch applied cleanly, but the regression test still FAILED on the patched repository."
        
    # 4. VERIFIED
    if not eval_result.baseline_test_result.passed and eval_result.patched_test_result.passed:
        return VerificationStatus.VERIFIED, "Required baseline and patched checks completed successfully. The expected regression behavior was observed and subsequently resolved."
        
    # Fallback
    return VerificationStatus.INCONCLUSIVE, "Unforeseen execution state."
