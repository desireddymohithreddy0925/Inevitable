import json
from pathlib import Path
from inevitable.proof.schemas import ProofCarryingPatch

def generate_markdown_report(proof: ProofCarryingPatch) -> str:
    """Generates a human-readable Markdown report for a Proof-Carrying Patch."""
    md = [
        f"# Inevitable Proof-Carrying Patch Report",
        f"**Repository:** `{proof.repository_url}`",
        f"**Commit SHA:** `{proof.commit_sha}`",
        f"**Investigation Timestamp:** `{proof.investigation_timestamp}`",
        f"**Status:** `{proof.final_status.value}`",
        f"**Reason:** {proof.status_reason}",
        "",
        "## Bug Description",
        f"{proof.bug_description}",
        "",
        "## Root Cause Hypothesis",
        f"{proof.root_cause_hypothesis}",
        "",
        "## Risks and Uncertainties",
        f"{proof.risks_and_uncertainties}",
        "",
        "## Source Evidence"
    ]
    
    for ev in proof.source_evidence:
        md.append(f"### {ev.file_path} (Lines {ev.line_range})")
        md.append("```python")
        md.append(ev.snippet)
        md.append("```")
        
    md.extend([
        "",
        "## Regression Test Proposal",
        "```python",
        proof.regression_test_source,
        "```",
        ""
    ])
    
    md.append("## Baseline Execution Result")
    if proof.baseline_result:
        md.append(f"Exit Code: `{proof.baseline_result.exit_code}` | Passed: `{proof.baseline_result.passed}` | Timed Out: `{proof.baseline_result.timed_out}`")
        md.append(f"Duration: `{proof.baseline_result.duration_seconds:.2f}s`")
        if proof.baseline_result.stdout:
            md.append("### stdout")
            md.append("```")
            md.append(proof.baseline_result.stdout)
            md.append("```")
    else:
        md.append("No baseline execution data.")
        
    md.extend([
        "",
        "## Candidate Patch",
        f"**Hash:** `{proof.patch_hash}`",
        "```diff",
        proof.candidate_patch,
        "```",
        ""
    ])
    
    md.append("## Patched Execution Result")
    if proof.patched_result:
        md.append(f"Exit Code: `{proof.patched_result.exit_code}` | Passed: `{proof.patched_result.passed}` | Timed Out: `{proof.patched_result.timed_out}`")
        md.append(f"Duration: `{proof.patched_result.duration_seconds:.2f}s`")
        if proof.patched_result.stdout:
            md.append("### stdout")
            md.append("```")
            md.append(proof.patched_result.stdout)
            md.append("```")
    else:
        md.append("No patched execution data.")
        
    md.extend([
        "",
        "## Limitations",
        "\n".join(f"- {limit}" for limit in proof.limitations)
    ])
    
    return "\n".join(md)

def write_reports(proof: ProofCarryingPatch, output_dir: Path):
    """Writes both JSON and Markdown reports to the specified directory."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    json_path = output_dir / "proof_report.json"
    json_path.write_text(proof.model_dump_json(indent=2))
    
    md_path = output_dir / "proof_report.md"
    md_path.write_text(generate_markdown_report(proof))
