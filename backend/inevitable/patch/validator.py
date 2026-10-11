import hashlib
import re
from pathlib import Path
from inevitable.patch.schemas import PatchValidationResult

def validate_patch(unified_diff: str) -> PatchValidationResult:
    """
    Validate the unified diff to ensure it does not contain unsafe paths
    like absolute paths, parent traversals, or unexpected binary modifications.
    """
    if not unified_diff.strip():
        return PatchValidationResult(is_valid=False, error_message="Empty patch.")
        
    patch_hash = hashlib.sha256(unified_diff.encode('utf-8')).hexdigest()
    
    # Very basic validation of paths (simplified)
    # Check lines starting with --- or +++
    for line in unified_diff.splitlines():
        if line.startswith("--- ") or line.startswith("+++ "):
            # Strip the 'a/' or 'b/' prefix if present
            filepath = line[4:].strip()
            if filepath == "/dev/null":
                continue
            if filepath.startswith("a/"):
                filepath = filepath[2:]
            elif filepath.startswith("b/"):
                filepath = filepath[2:]
                
            # Prevent absolute paths
            if filepath.startswith("/"):
                return PatchValidationResult(is_valid=False, error_message="Absolute paths are not allowed.", hash=patch_hash)
            
            # Prevent path traversal
            if ".." in filepath:
                return PatchValidationResult(is_valid=False, error_message="Path traversal (..) is not allowed.", hash=patch_hash)
                
            # Prevent binaries
            if any(filepath.endswith(ext) for ext in [".exe", ".dll", ".so", ".bin", ".pyc"]):
                return PatchValidationResult(is_valid=False, error_message="Binary patches are not allowed.", hash=patch_hash)
                
    return PatchValidationResult(is_valid=True, hash=patch_hash)
