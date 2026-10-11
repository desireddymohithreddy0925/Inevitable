import pytest
import asyncio
import shutil
from pathlib import Path
from inevitable.patch.evaluator import PatchEvaluator
from inevitable.patch.validator import validate_patch

@pytest.fixture
def demo_dir(tmp_path):
    source = Path(__file__).parent.parent / "fixtures" / "demo_repo"
    dest = tmp_path / "demo_repo"
    shutil.copytree(source, dest)
    return dest

def test_patch_validator_valid():
    diff = """--- a/buggy.py
+++ b/buggy.py
@@ -1,4 +1,4 @@
 def add_numbers(a, b):
-    return a - b
+    return a + b
"""
    result = validate_patch(diff)
    assert result.is_valid is True

def test_patch_validator_absolute_path():
    diff = """--- a/etc/passwd
+++ /etc/passwd
@@ -1,4 +1,4 @@
"""
    result = validate_patch(diff)
    assert result.is_valid is False
    assert "Absolute paths" in result.error_message

def test_patch_validator_traversal():
    diff = """--- a/buggy.py
+++ b/../../secret.txt
@@ -1,4 +1,4 @@
"""
    result = validate_patch(diff)
    assert result.is_valid is False
    assert "traversal" in result.error_message

def test_patch_evaluator_successful_fix(demo_dir, monkeypatch):
    from inevitable.config import settings
    monkeypatch.setattr(settings, "enable_untrusted_execution", True)
    
    from git import Repo
    repo = Repo.init(demo_dir)
    repo.index.add("*")
    repo.index.commit("Initial commit")
    
    evaluator = PatchEvaluator()
    
    test_code = """from buggy import add_numbers
def test_add_numbers_repro():
    assert add_numbers(5, 3) == 8
"""
    
    patch_diff = """--- a/buggy.py
+++ b/buggy.py
@@ -1,6 +1,6 @@
 def add_numbers(a, b):
     # Intentional bug: subtracts instead of adding
-    return a - b
+    return a + b
 
 class Calculator:
     def multiply(self, a, b):
"""

    result = asyncio.run(evaluator.evaluate(
        repo_path=demo_dir,
        commit_sha=repo.head.commit.hexsha,
        reproduction_test_code=test_code,
        candidate_patch_diff=patch_diff
    ))

    assert result.patch_applied is True
    assert result.patch_apply_error is None
    
    assert result.baseline_test_result is not None
    assert result.baseline_test_result.passed is False
    assert result.baseline_test_result.exit_code == 1
    
    assert result.patched_test_result is not None
    assert result.patched_test_result.passed is True
    assert result.patched_test_result.exit_code == 0
    
    assert result.verification_passed is True

def test_patch_evaluator_patch_reject(demo_dir):
    evaluator = PatchEvaluator()
    
    patch_diff = """--- /etc/passwd
+++ /etc/passwd
@@ -1,4 +1,4 @@
"""

    result = asyncio.run(evaluator.evaluate(
        repo_path=demo_dir,
        commit_sha="dummy",
        reproduction_test_code="",
        candidate_patch_diff=patch_diff
    ))

    assert result.patch_applied is False
    assert "Patch rejected by validator" in result.patch_apply_error
