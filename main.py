import argparse
import os
from agent.loop import run_agent_loop

def main():
    parser = argparse.ArgumentParser(description="Run the coding agent.")
    parser.add_argument("--task", type=str, required=True, help="The task for the agent to perform.")
    parser.add_argument("--max-steps", type=int, default=15, help="Maximum number of tool-calling steps.")
    parser.add_argument("--repo-dir", type=str, help="Path to the custom target repository.", default=None)
    parser.add_argument("--test-cmd", type=str, help="Custom command to run tests (e.g. 'npm test').", default=None)
    parser.add_argument("--lint-cmd", type=str, help="Custom command to run linter (e.g. 'npm run lint').", default=None)
    args = parser.parse_args()
    
    if args.repo_dir:
        os.environ["TARGET_REPO_DIR"] = os.path.abspath(args.repo_dir)
        print(f"Target Repo: {os.environ['TARGET_REPO_DIR']}")
    if args.test_cmd:
        os.environ["TEST_CMD"] = args.test_cmd
        print(f"Test Command: {args.test_cmd}")
    if args.lint_cmd:
        os.environ["LINT_CMD"] = args.lint_cmd
        print(f"Lint Command: {args.lint_cmd}")
        
    print(f"Task: {args.task}")
    result = run_agent_loop(task=args.task, max_steps=args.max_steps)
    print("\n--- Final Result ---")
    print(result)

if __name__ == "__main__":
    main()
