import os
import subprocess

# Base path for the sandboxed target repo
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'target_repos', 'humanize'))

def _resolve_and_check_path(path: str) -> str:
    """Resolve a path and ensure it is within the sandbox."""
    if os.path.isabs(path):
        resolved = os.path.abspath(path)
    else:
        resolved = os.path.abspath(os.path.join(BASE_DIR, path))
        
    if not resolved.startswith(BASE_DIR):
        raise ValueError(f"Access denied: path {path} is outside the sandbox.")
        
    return resolved

def list_files(directory: str) -> str:
    """List files and directories under the given path."""
    try:
        target_dir = _resolve_and_check_path(directory)
        if not os.path.exists(target_dir):
            return f"Error: Directory {directory} does not exist."
        if not os.path.isdir(target_dir):
            return f"Error: {directory} is not a directory."
            
        entries = os.listdir(target_dir)
        return "\\n".join(entries) if entries else "Directory is empty."
    except Exception as e:
        return f"Error: {str(e)}"

def read_file(path: str) -> str:
    """Read a file's contents."""
    try:
        target_path = _resolve_and_check_path(path)
        if not os.path.exists(target_path):
            return f"Error: File {path} does not exist."
        if not os.path.isfile(target_path):
            return f"Error: {path} is not a file."
            
        with open(target_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error: {str(e)}"

def search_code(query: str) -> str:
    """Search across the repo for a string/pattern."""
    try:
        result = subprocess.run(
            ['grep', '-rn', query, '.'],
            cwd=BASE_DIR,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return result.stdout
        elif result.returncode == 1:
            return "No matches found."
        else:
            return f"Error searching code: {result.stderr}"
    except Exception as e:
        return f"Error: {str(e)}"

def write_file(path: str, content: str) -> str:
    """Overwrite a file's full contents."""
    try:
        target_path = _resolve_and_check_path(path)
        # Ensure directory exists
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        with open(target_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully wrote to {path}."
    except Exception as e:
        return f"Error: {str(e)}"

def run_tests(test_path: str = "tests/") -> str:
    """Run pytest against the given path, with a timeout."""
    try:
        target_path = _resolve_and_check_path(test_path)
        if not os.path.exists(target_path):
            return f"Error: Test path {test_path} does not exist."
            
        # We assume pytest is installed in the current environment
        import sys
        # Need to point to the python executable running the agent loop
        python_executable = sys.executable
        
        result = subprocess.run(
            [python_executable, '-m', 'pytest', target_path, '--ignore=tests/test_benchmarks.py'],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            timeout=60
        )
        return result.stdout + "\\n" + result.stderr
    except subprocess.TimeoutExpired:
        return "Error: Test suite execution timed out after 60 seconds."
    except Exception as e:
        return f"Error: {str(e)}"
