import os
import ast
import tempfile
import logging
import time
from pathlib import Path
from git import Repo, GitCommandError
from pydantic import BaseModel, Field
from typing import List

from inevitable.repo.validator import validate_repository_url, SecurityError

logger = logging.getLogger("inevitable.repo")

MAX_FILE_SIZE = 500 * 1024 # 500 KB
MAX_FILES = 1000
MAX_EVIDENCE_SIZE = 500000 # ~500 KB of total text evidence
MAX_PROCESSING_TIME = 60 # seconds

class FileEvidence(BaseModel):
    file_path: str = Field(description="The relative path to the source file.")
    line_range: str = Field(description="The lines referenced.")
    snippet: str = Field(description="The source code snippet.")

class InvestigationResult(BaseModel):
    commit_sha: str = Field(description="The exact Git commit SHA that was investigated.")
    evidence: List[FileEvidence] = Field(description="Bounded source evidence.")

def is_safe_path(base: Path, target: Path) -> bool:
    try:
        target.resolve().relative_to(base.resolve())
        return True
    except ValueError:
        return False

def is_ignored_file(path: Path) -> bool:
    ignored_dirs = {".git", "__pycache__", "venv", "env", ".venv", "node_modules", "build", "dist"}
    ignored_exts = {".pyc", ".so", ".exe", ".dll", ".bin", ".zip", ".tar", ".gz"}
    
    if any(part in ignored_dirs for part in path.parts):
        return True
    if path.suffix in ignored_exts:
        return True
    if path.name == ".env" or "secret" in path.name.lower():
        return True
    return False

class RepositoryInspector:
    def __init__(self, url: str):
        self.url = validate_repository_url(url)
        self.total_evidence_size = 0
        self.start_time = time.time()
        
    def investigate(self) -> InvestigationResult:
        evidence = []
        commit_sha = ""
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            try:
                if self.url.startswith("demo:"):
                    logger.info("Loading safe demo fixture.")
                    import shutil
                    demo_repo = Path(__file__).parent.parent.parent / "tests" / "fixtures" / "demo_repo"
                    shutil.copytree(demo_repo, temp_dir, dirs_exist_ok=True)
                    repo = Repo.init(temp_dir)
                    repo.index.add("*")
                    repo.index.commit("Init")
                    commit_sha = repo.head.commit.hexsha
                else:
                    logger.info(f"Cloning {self.url} to a secure temporary directory.")
                    repo = Repo.clone_from(self.url, temp_dir, depth=1)
                    commit_sha = repo.head.commit.hexsha
            except GitCommandError as e:
                raise SecurityError(f"Git clone failed or was rejected: {e}")
                
            files_processed = 0
            
            for root, _, files in os.walk(temp_dir):
                for file in files:
                    if time.time() - self.start_time > MAX_PROCESSING_TIME:
                        logger.warning("Investigation time limit reached.")
                        return InvestigationResult(commit_sha=commit_sha, evidence=evidence)
                        
                    if files_processed > MAX_FILES:
                        logger.warning("Max file limit reached.")
                        return InvestigationResult(commit_sha=commit_sha, evidence=evidence)
                    
                    files_processed += 1
                    file_path = Path(root) / file
                    
                    if not is_safe_path(temp_path, file_path):
                        continue
                        
                    if is_ignored_file(file_path.relative_to(temp_path)):
                        continue
                        
                    if file_path.is_file() and file_path.stat().st_size <= MAX_FILE_SIZE:
                        if file_path.suffix == ".py":
                            file_ev = self._parse_python_file(file_path, temp_path)
                            for ev in file_ev:
                                if self.total_evidence_size + len(ev.snippet) > MAX_EVIDENCE_SIZE:
                                    logger.warning("Total evidence size limit reached.")
                                    return InvestigationResult(commit_sha=commit_sha, evidence=evidence)
                                evidence.append(ev)
                                self.total_evidence_size += len(ev.snippet)
                                
        return InvestigationResult(commit_sha=commit_sha, evidence=evidence)

    def _parse_python_file(self, file_path: Path, base_path: Path) -> List[FileEvidence]:
        evidence = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            lines = content.splitlines()
            
            try:
                tree = ast.parse(content)
                has_functions_or_classes = False
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                        has_functions_or_classes = True
                        start = node.lineno
                        end = getattr(node, "end_lineno", start)
                        snippet = "\n".join(lines[start-1:end])
                        if len(snippet) < 10000:
                            evidence.append(FileEvidence(
                                file_path=str(file_path.relative_to(base_path)),
                                line_range=f"{start}-{end}",
                                snippet=snippet
                            ))
                            
                if not has_functions_or_classes:
                    snippet = "\n".join(lines[:100])
                    evidence.append(FileEvidence(
                        file_path=str(file_path.relative_to(base_path)),
                        line_range=f"1-{min(100, len(lines))}",
                        snippet=snippet
                    ))
                    
            except SyntaxError:
                snippet = "\n".join(lines[:100])
                evidence.append(FileEvidence(
                    file_path=str(file_path.relative_to(base_path)),
                    line_range=f"1-{min(100, len(lines))}",
                    snippet=snippet
                ))

        except Exception as e:
            logger.debug(f"Failed to read {file_path}: {e}")
            
        return evidence
