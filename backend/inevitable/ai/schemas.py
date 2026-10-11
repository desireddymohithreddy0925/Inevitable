from pydantic import BaseModel, Field
from typing import List

class SourceEvidence(BaseModel):
    file_path: str = Field(description="The path to the source file analyzed.")
    line_range: str = Field(description="The lines referenced, e.g., '10-25'.")
    snippet: str = Field(description="The actual code snippet referenced.")

class AnalysisResult(BaseModel):
    defect_summary: str = Field(description="A clear summary of the defect being investigated.")
    suspected_root_cause: str = Field(description="The model's hypothesis of the root cause.")
    source_evidence: List[SourceEvidence] = Field(description="Evidence from the provided source files.")
    reproduction_test_proposal: str = Field(description="Proposed pytest code to reproduce the defect.")
    candidate_patch_diff: str = Field(default="", description="The unified diff of the proposed candidate patch.")
    candidate_patch_rationale: str = Field(description="Reasoning behind the candidate patch.")
    risks_and_uncertainties: str = Field(description="Any risks, assumptions, and uncertainties regarding this patch.")
