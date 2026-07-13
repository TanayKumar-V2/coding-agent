import os
import subprocess

# Default base path if not configured
DEFAULT_BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'target_repos', 'humanize'))

def get_base_dir() -> str:
    """Get the target repository directory."""
    path = os.environ.get("TARGET_REPO_DIR", DEFAULT_BASE_DIR)
    return os.path.abspath(path)

def _resolve_and_check_path(path: str) -> str:
    """Resolve a path and ensure it is within the sandbox."""
    base_dir = get_base_dir()
    if os.path.isabs(path):
        resolved = os.path.abspath(path)
    else:
        resolved = os.path.abspath(os.path.join(base_dir, path))
        
    if not resolved.startswith(base_dir):
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
    """Read the contents of a file."""
    try:
        target_path = _resolve_and_check_path(path)
        if not os.path.exists(target_path):
            return f"Error: File {path} does not exist."
        if not os.path.isfile(target_path):
            return f"Error: {path} is not a file."
        with open(target_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if len(content) > 30000:
                lines = content.splitlines()
                truncated_content = "\n".join(lines[:300]) + f"\n\n... [TRUNCATED {len(lines) - 300} lines] ...\n"
                return truncated_content
            return content
    except Exception as e:
        return f"Error: {str(e)}"

def search_code(query: str) -> str:
    """Search across the repo for a string/pattern."""
    try:
        base_dir = get_base_dir()
        result = subprocess.run(
            ['grep', '-rn', query, '.'],
            cwd=base_dir,
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
        test_cmd = os.environ.get("TEST_CMD")
        if test_cmd:
            import shlex
            cmd = shlex.split(test_cmd)
        else:
            # We assume pytest is installed in the current environment
            import sys
            # Need to point to the python executable running the agent loop
            python_executable = sys.executable
            cmd = [python_executable, '-m', 'pytest', target_path, '--ignore=tests/test_benchmarks.py', '-q', '--tb=short', '--color=no']
        
        base_dir = get_base_dir()
        result = subprocess.run(
            cmd,
            cwd=base_dir,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        output = result.stdout + "\n" + result.stderr
        
        # Clean up output to remove long lines of dots
        cleaned_lines = []
        for line in output.splitlines():
            if line.startswith('.') and len(line) > 10 and line.strip('.FEs ') == '':
                continue
            cleaned_lines.append(line)
        output = "\n".join(cleaned_lines)

        if len(output) > 3000:
            lines = output.splitlines()
            if len(lines) > 100:
                output = "\n".join(lines[:40]) + "\n\n... [OUTPUT TRUNCATED] ...\n\n" + "\n".join(lines[-60:])
        return output
    except subprocess.TimeoutExpired:
        return "Error: Test suite execution timed out after 60 seconds."
    except Exception as e:
        return f"Error: {str(e)}"

def patch_file(path: str, target_string: str, replacement_string: str) -> str:
    """Patch a file by replacing a specific string."""
    try:
        target_path = _resolve_and_check_path(path)
        if not os.path.exists(target_path):
            return f"Error: File {path} does not exist."
            
        with open(target_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if target_string not in content:
            return "Error: target_string not found in file."
        if content.count(target_string) > 1:
            return "Error: target_string found multiple times. Please provide a more specific target_string."
            
        new_content = content.replace(target_string, replacement_string)
        with open(target_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return f"Successfully patched {path}."
    except Exception as e:
        return f"Error: {str(e)}"

def run_linter(path: str = ".") -> str:
    """Run flake8 on the given path to check for syntax and style errors."""
    try:
        target_path = _resolve_and_check_path(path)
        lint_cmd = os.environ.get("LINT_CMD")
        if lint_cmd:
            import shlex
            cmd = shlex.split(lint_cmd)
        else:
            import sys
            cmd = [sys.executable, '-m', 'flake8', target_path]
            
        base_dir = get_base_dir()
        result = subprocess.run(
            cmd,
            cwd=base_dir,
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            return "Linter passed: No issues found."
        else:
            return f"Linter issues found:\n{result.stdout}\n{result.stderr}"
    except Exception as e:
        return f"Error running linter: {str(e)}"
