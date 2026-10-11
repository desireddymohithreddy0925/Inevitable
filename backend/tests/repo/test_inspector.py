import pytest
from pathlib import Path
import shutil
from inevitable.repo.validator import validate_repository_url, SecurityError
from inevitable.repo.inspector import RepositoryInspector, is_ignored_file

def test_valid_https_url():
    url = "https://github.com/example/repo.git"
    assert validate_repository_url(url) == url

def test_invalid_scheme_raises_error():
    with pytest.raises(SecurityError, match="Only HTTPS and demo protocols are supported"):
        validate_repository_url("http://github.com/example/repo.git")
    with pytest.raises(SecurityError):
        validate_repository_url("file:///etc/passwd")

def test_embedded_credentials_raises_error():
    with pytest.raises(SecurityError, match="Embedded credentials"):
        validate_repository_url("https://user:pass@github.com/example")

def test_localhost_raises_error():
    with pytest.raises(SecurityError, match="loopback"):
        validate_repository_url("https://127.0.0.1/repo.git")

def test_ignored_files():
    assert is_ignored_file(Path(".git/config")) == True
    assert is_ignored_file(Path(".env")) == True
    assert is_ignored_file(Path("secret.txt")) == True
    assert is_ignored_file(Path("main.pyc")) == True
    assert is_ignored_file(Path("src/main.py")) == False

class MockRepo:
    class Head:
        class Commit:
            hexsha = "mocksha123"
        commit = Commit()
    head = Head()

def test_investigator_with_mocked_clone(monkeypatch, tmp_path):
    fixture_path = Path(__file__).parent.parent / "fixtures" / "demo_repo"
    
    def mock_clone_from(url, to_path, **kwargs):
        shutil.copytree(fixture_path, to_path, dirs_exist_ok=True)
        return MockRepo()
        
    import inevitable.repo.inspector
    monkeypatch.setattr(inevitable.repo.inspector.Repo, "clone_from", mock_clone_from)
    
    inspector = RepositoryInspector("https://github.com/mock/mock.git")
    result = inspector.investigate()
    
    assert result.commit_sha == "mocksha123"
    assert len(result.evidence) > 0
    
    # Check that .env wasn't parsed
    for ev in result.evidence:
        assert ev.file_path != ".env"
        
    # Check that buggy.py was parsed
    buggy_evidence = [ev for ev in result.evidence if ev.file_path == "buggy.py"]
    assert len(buggy_evidence) > 0
    assert "def add_numbers" in buggy_evidence[0].snippet
