import argparse
from agent.loop import run_agent_loop

def main():
    parser = argparse.ArgumentParser(description="Run the coding agent.")
    parser.add_argument("--task", type=str, required=True, help="The task for the agent to perform.")
    parser.add_argument("--max-steps", type=int, default=15, help="Maximum number of tool-calling steps.")
    args = parser.parse_args()
    
    print(f"Task: {args.task}")
    result = run_agent_loop(task=args.task, max_steps=args.max_steps)
    print("\\n--- Final Result ---")
    print(result)

if __name__ == "__main__":
    main()
