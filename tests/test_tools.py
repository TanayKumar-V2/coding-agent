import os
import subprocess
import pytest
from agent.tools import list_files, read_file, search_code, write_file, run_tests, BASE_DIR
from eval.seed_bug import seed_bug

def test_list_files():
    # Happy path
    res = list_files("src")
    assert "humanize" in res
    assert "Error" not in res or "Access denied" not in res
    
    # Path traversal rejection
    res = list_files("../../../etc/passwd")
    assert "Error" in res or "Access denied" in res or "outside the sandbox" in res

def test_read_file():
    # Happy path
    res = read_file("src/humanize/__init__.py")
    assert "import" in res
    assert "Error" not in res
    
    # Absolute path outside sandbox
    res = read_file("/etc/passwd")
    assert "outside the sandbox" in res or "Access denied" in res

def test_search_code():
    # Happy path
    res = search_code("def ordinal")
    assert "number.py" in res
    assert "Error" not in res

def test_write_file():
    # Happy path
    test_file = "test_write.txt"
    res = write_file(test_file, "hello world")
    assert "Successfully wrote" in res
    
    read_res = read_file(test_file)
    assert "hello world" in read_res
    
    # Cleanup
    os.remove(os.path.join(BASE_DIR, test_file))
    
    # Path traversal
    res = write_file("../../../tmp/test.txt", "evil")
    assert "outside the sandbox" in res or "Access denied" in res

def test_run_tests():
    # Ensure fresh clone
    subprocess.run(['git', 'checkout', '--', '.'], cwd=BASE_DIR, check=True)
    
    # Passing test suite
    res = run_tests("tests/")
    assert "failed" not in res.lower() or "0 failed" in res.lower()
    assert "Error" not in res
    
    # Seed bug and test failing test suite
    seed_bug()
    res_failing = run_tests("tests/")
    assert "failed" in res_failing.lower()
    
    # Reset back to clean state
    subprocess.run(['git', 'checkout', '--', '.'], cwd=BASE_DIR, check=True)

def test_run_tests_timeout(monkeypatch):
    # Simulate timeout by patching subprocess.run
    def mock_run(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd="pytest", timeout=60)
    
    import subprocess as sub
    monkeypatch.setattr(sub, "run", mock_run)
    res = run_tests("tests/")
    assert "timed out after 60 seconds" in res
