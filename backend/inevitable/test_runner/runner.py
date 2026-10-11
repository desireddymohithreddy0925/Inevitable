import os
import sys
import time
import shlex
import asyncio
import logging
from typing import List
from pathlib import Path
from inevitable.test_runner.schemas import ExecutionResult, ExecutionLimits
from inevitable.config import settings

logger = logging.getLogger("inevitable.test_runner")

class SecurityPolicyError(Exception):
    pass

class PytestRunner:
    def __init__(self, limits: ExecutionLimits = None):
        self.limits = limits or ExecutionLimits()
        
    async def run_tests(
        self, 
        working_dir: Path, 
        test_files: List[str] = None,
        is_safe_fixture: bool = False
    ) -> ExecutionResult:
        """
        Run pytest in the specified working directory.
        """
        # Security Check: No arbitrary execution unless configured explicitly.
        if not settings.enable_untrusted_execution and not is_safe_fixture:
            # Hard boundary check
            if "fixtures/demo_repo" not in str(working_dir.resolve()):
                raise SecurityPolicyError(
                    "Untrusted execution is disabled. "
                    "Cannot execute tests outside of controlled demo repositories. "
                    "Set ENABLE_UNTRUSTED_EXECUTION=true to override (DANGEROUS)."
                )

        test_files = test_files or []
        
        # We explicitly run pytest via the current python executable
        cmd_args = [sys.executable, "-m", "pytest", "-q", "--tb=short"] + test_files
        command_str = shlex.join(cmd_args)
        
        logger.info(f"Executing: {command_str} in {working_dir}")
        
        start_time = time.time()
        
        result = ExecutionResult(
            command=command_str,
            working_dir=str(working_dir),
            start_time=start_time,
            end_time=0.0,
            duration_seconds=0.0
        )
        
        try:
            # Create subprocess
            # Prevent secret leakage via environment inheritance
            safe_env_vars = {"PATH", "LANG", "LC_ALL", "USER", "HOME"}
            safe_env = {k: v for k, v in os.environ.items() if k in safe_env_vars}
            safe_env["PYTHONPATH"] = str(working_dir)
            
            process = await asyncio.create_subprocess_exec(
                *cmd_args,
                cwd=str(working_dir),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=safe_env,
                preexec_fn=os.setsid
            )
            
            try:
                # Wait with timeout
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    process.communicate(), 
                    timeout=self.limits.timeout_seconds
                )
                
                result.exit_code = process.returncode
                # Enforce output-size limits
                result.stdout = stdout_bytes.decode('utf-8', errors='replace')[:self.limits.max_output_bytes]
                result.stderr = stderr_bytes.decode('utf-8', errors='replace')[:self.limits.max_output_bytes]
                
            except asyncio.TimeoutError:
                # Kill process group if it times out
                import signal
                try:
                    os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                    await process.wait()
                except OSError:
                    pass
                result.timed_out = True
                result.execution_error = f"Execution timed out after {self.limits.timeout_seconds} seconds."
                
        except Exception as e:
            result.execution_error = f"Process launch failed: {str(e)}"
            
        result.end_time = time.time()
        result.duration_seconds = result.end_time - result.start_time
        
        return result
