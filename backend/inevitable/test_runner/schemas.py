from pydantic import BaseModel, Field, computed_field
from typing import Optional

class ExecutionLimits(BaseModel):
    timeout_seconds: int = Field(default=30)
    max_output_bytes: int = Field(default=1024 * 1024)  # 1MB limit

class ExecutionResult(BaseModel):
    command: str
    working_dir: str
    exit_code: Optional[int] = None
    stdout: str = ""
    stderr: str = ""
    start_time: float
    end_time: float
    duration_seconds: float
    timed_out: bool = False
    execution_error: Optional[str] = None
    
    @computed_field
    @property
    def passed(self) -> bool:
        """Returns True if the process completed successfully with exit code 0."""
        return self.exit_code == 0 and not self.timed_out and not self.execution_error
