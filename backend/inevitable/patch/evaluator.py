import os
import shutil
import tempfile
import logging
from pathlib import Path
from git import Repo, GitCommandError

from inevitable.test_runner.runner import PytestRunner, SecurityPolicyError
from inevitable.test_runner.schemas import ExecutionLimits
from inevitable.patch.schemas import EvaluationResult
from inevitable.patch.validator import validate_patch

logger = logging.getLogger("inevitable.patch")

class PatchEvaluator:
    def __init__(self, limits: ExecutionLimits = None):
        self.runner = PytestRunner(limits=limits)
        
    async def evaluate(
        self, 
        repo_path: Path, 
        commit_sha: str, 
        reproduction_test_code: str, 
        candidate_patch_diff: str,
        is_safe_fixture: bool = False
    ) -> EvaluationResult:
        """
        Evaluate a patch against a reproducible baseline.
        repo_path must be a clean checkout of the repository at commit_sha.
        """
        # 1. Validate Patch
        validation = validate_patch(candidate_patch_diff)
        
        result = EvaluationResult(
            commit_sha=commit_sha,
            patch_hash=validation.hash,
            patch_applied=False
        )
        
        if not validation.is_valid:
            result.patch_apply_error = f"Patch rejected by validator: {validation.error_message}"
            return result
            
        # Write reproduction test to the repo
        tests_dir = repo_path / "tests"
        if not tests_dir.exists():
            tests_dir = repo_path
        repro_test_path = tests_dir / "test_inevitable_repro.py"
        
        # Write test code
        repro_test_path.write_text(reproduction_test_code)
        relative_test_path = str(repro_test_path.relative_to(repo_path))
        
        # 2. Run Baseline Test
        logger.info(f"Running baseline test on {commit_sha}")
        try:
            baseline_result = await self.runner.run_tests(repo_path, [relative_test_path], is_safe_fixture=is_safe_fixture)
            result.baseline_test_result = baseline_result
        except SecurityPolicyError as e:
            result.patch_apply_error = str(e)
            return result
            
        # 3. Apply Patch in a disposable worktree
        with tempfile.TemporaryDirectory() as temp_dir:
            patched_repo_path = Path(temp_dir) / "patched_repo"
            shutil.copytree(repo_path, patched_repo_path)
            
            # Write patch to a file to use git apply
            patch_file = patched_repo_path / "candidate.patch"
            patch_file.write_text(candidate_patch_diff)
            
            patched_repo = Repo(patched_repo_path)
            
            try:
                logger.info(f"Applying patch {validation.hash}")
                # Use standard git apply. We want it to fail if it doesn't apply cleanly.
                patched_repo.git.apply(str(patch_file))
                result.patch_applied = True
            except GitCommandError as e:
                logger.warning(f"Patch failed to apply: {e}")
                result.patch_apply_error = f"Git apply failed: {e.stderr}"
                return result
                
            # 4. Run Patched Test
            logger.info("Running tests on patched repository")
            try:
                patched_result = await self.runner.run_tests(patched_repo_path, [relative_test_path], is_safe_fixture=is_safe_fixture)
                result.patched_test_result = patched_result
            except SecurityPolicyError as e:
                result.patch_apply_error = str(e)
                return result
                
        return result
