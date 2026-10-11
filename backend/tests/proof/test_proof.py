import pytest
import json
from pathlib import Path
from inevitable.proof.schemas import ProofCarryingPatch, VerificationStatus
from inevitable.proof.state_machine import determine_verification_status
from inevitable.patch.schemas import EvaluationResult
from inevitable.test_runner.schemas import ExecutionResult
from inevitable.proof.reporter import write_reports, generate_markdown_report

def create_mock_eval_result(
    baseline_passed: bool = False,
    baseline_error: str = None,
    baseline_timeout: bool = False,
    patch_applied: bool = True,
    patch_error: str = None,
    patched_passed: bool = True,
    patched_error: str = None,
    patched_timeout: bool = False,
) -> EvaluationResult:
    return EvaluationResult(
        commit_sha="dummy",
        patch_hash="hash",
        patch_applied=patch_applied,
        patch_apply_error=patch_error,
        baseline_test_result=ExecutionResult(
            command="pytest", working_dir="/", exit_code=0 if baseline_passed else 1, 
            start_time=0, end_time=1, duration_seconds=1, 
            timed_out=baseline_timeout, execution_error=baseline_error
        ),
        patched_test_result=ExecutionResult(
            command="pytest", working_dir="/", exit_code=0 if patched_passed else 1, 
            start_time=0, end_time=1, duration_seconds=1, 
            timed_out=patched_timeout, execution_error=patched_error
        ) if patch_applied else None
    )

def test_status_verified():
    eval_res = create_mock_eval_result(baseline_passed=False, patched_passed=True)
    status, reason = determine_verification_status(eval_res)
    assert status == VerificationStatus.VERIFIED

def test_status_rejected():
    eval_res = create_mock_eval_result(baseline_passed=False, patched_passed=False)
    status, reason = determine_verification_status(eval_res)
    assert status == VerificationStatus.REJECTED

def test_status_blocked_security():
    eval_res = create_mock_eval_result(patch_applied=False, patch_error="SecurityPolicyError: not allowed")
    status, reason = determine_verification_status(eval_res)
    assert status == VerificationStatus.BLOCKED

def test_status_inconclusive_baseline_passed():
    eval_res = create_mock_eval_result(baseline_passed=True, patched_passed=True)
    status, reason = determine_verification_status(eval_res)
    assert status == VerificationStatus.INCONCLUSIVE
    assert "PASSED on the baseline" in reason

def test_status_inconclusive_patch_failed_to_apply():
    eval_res = create_mock_eval_result(baseline_passed=False, patch_applied=False, patch_error="Git apply failed")
    status, reason = determine_verification_status(eval_res)
    assert status == VerificationStatus.INCONCLUSIVE
    assert "Patch failed to apply" in reason

def test_report_generation(tmp_path):
    proof = ProofCarryingPatch(
        repository_url="https://github.com/a/b.git",
        commit_sha="123",
        bug_description="Bug",
        source_evidence=[],
        root_cause_hypothesis="Root",
        risks_and_uncertainties="Risk",
        regression_test_source="test()",
        baseline_result=None,
        candidate_patch="diff",
        patch_hash="hash",
        patched_result=None,
        final_status=VerificationStatus.INCONCLUSIVE,
        status_reason="Reason"
    )
    
    write_reports(proof, tmp_path)
    
    assert (tmp_path / "proof_report.json").exists()
    assert (tmp_path / "proof_report.md").exists()
    
    data = json.loads((tmp_path / "proof_report.json").read_text())
    assert data["final_status"] == "INCONCLUSIVE"
