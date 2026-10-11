import pytest
import asyncio
import shutil
from pathlib import Path
from inevitable.test_runner.schemas import ExecutionLimits
from inevitable.test_runner.runner import PytestRunner, SecurityPolicyError

@pytest.fixture
def demo_dir():
    return Path(__file__).parent.parent / "fixtures" / "demo_repo"

def test_runner_blocks_untrusted_execution(tmp_path):
    """Test that runner blocks arbitrary directories when isolation is off."""
    untrusted_dir = tmp_path / "untrusted"
    untrusted_dir.mkdir()
    
    runner = PytestRunner()
    
    with pytest.raises(SecurityPolicyError, match="Untrusted execution is disabled"):
        asyncio.run(runner.run_tests(untrusted_dir))

def test_runner_passing_test(demo_dir):
    runner = PytestRunner()
    result = asyncio.run(runner.run_tests(demo_dir, ["test_buggy.py::test_calculator_pass"]))
    
    assert result.timed_out is False
    assert result.execution_error is None
    assert result.exit_code == 0
    assert result.passed is True
    assert "1 passed" in result.stdout

def test_runner_failing_test(demo_dir):
    runner = PytestRunner()
    result = asyncio.run(runner.run_tests(demo_dir, ["test_buggy.py::test_add_numbers_pass"]))
    
    assert result.timed_out is False
    assert result.execution_error is None
    assert result.exit_code == 1 # Pytest returns 1 for failed tests
    assert result.passed is False
    assert "1 failed" in result.stdout

def test_runner_timeout(demo_dir):
    runner = PytestRunner(limits=ExecutionLimits(timeout_seconds=1))
    result = asyncio.run(runner.run_tests(demo_dir, ["test_buggy.py::test_timeout"]))
    
    assert result.timed_out is True
    assert result.passed is False
    assert result.execution_error is not None
    assert "timed out" in result.execution_error

def test_runner_execution_error(demo_dir):
    runner = PytestRunner()
    result = asyncio.run(runner.run_tests(demo_dir, ["test_malformed.py"]))
    
    # Missing module means pytest will fail to collect
    assert result.exit_code != 0
    assert result.passed is False
    assert ("ModuleNotFoundError" in result.stdout or 
            "ImportError" in result.stdout or 
            "Error" in result.stdout or 
            "error" in result.stdout.lower() or
            "error" in result.stderr.lower())
