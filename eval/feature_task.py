import os
import sys
import subprocess

def run_feature_task():
    task = "Add a new function `ordinal_suffix_only(value: int) -> str` to `src/humanize/number.py` that takes an integer and returns only its ordinal suffix (e.g. 1 -> 'st', 2 -> 'nd', 11 -> 'th'). Add unit tests for it in `tests/test_number.py` and ensure they pass."
    
    print(f"Starting feature task: {task}")
    try:
        subprocess.run(
            [sys.executable, 'main.py', '--task', task],
            check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"Agent failed to implement the feature: {e}")
        sys.exit(1)
        
    print("Feature successfully implemented by the agent!")

if __name__ == "__main__":
    if "COHERE_API_KEY" not in os.environ:
        print("Error: COHERE_API_KEY environment variable not set.")
        sys.exit(1)
    run_feature_task()
