import os
import sys
import subprocess
import argparse

def seed_bug():
    print("Seeding bug...")
    subprocess.run([sys.executable, 'eval/seed_bug.py'], check=True)

def verify_fix() -> bool:
    print("Verifying fix by running pytest...")
    result = subprocess.run(
        [sys.executable, '-m', 'pytest', 'target_repos/humanize/tests', '--ignore=target_repos/humanize/tests/test_benchmarks.py', '-q'],
        capture_output=True,
        text=True
    )
    return result.returncode == 0

def run_evaluation(num_runs: int = 3):
    successes = 0
    task = "Tests are failing in this repo. Find the bug and fix it."
    
    print(f"Starting evaluation: {num_runs} runs.")
    
    for i in range(num_runs):
        print(f"\\n--- Run {i+1}/{num_runs} ---")
        try:
            # 1. Seed the bug
            seed_bug()
            
            # 2. Run the agent
            print("Running agent...")
            result = subprocess.run(
                [sys.executable, 'main.py', '--task', task],
                capture_output=True,
                text=True,
                timeout=600 # 10 minute timeout per run
            )
            
            if result.returncode != 0:
                print(f"Agent failed with error:\\n{result.stderr}")
            
            # 3. Verify if tests pass
            is_success = verify_fix()
            if is_success:
                print(f"Run {i+1}: SUCCESS")
                successes += 1
            else:
                print(f"Run {i+1}: FAILURE")
                
        except subprocess.TimeoutExpired:
            print(f"Run {i+1}: TIMEOUT")
        except Exception as e:
            print(f"Run {i+1}: ERROR - {str(e)}")
            
    success_rate = (successes / num_runs) * 100
    print(f"\\n=== Evaluation Complete ===")
    print(f"Success Rate: {successes}/{num_runs} ({success_rate:.1f}%)")
    return success_rate

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate the agent's ability to fix bugs")
    parser.add_argument("--runs", type=int, default=3, help="Number of runs to evaluate")
    args = parser.parse_args()
    
    # Ensure COHERE_API_KEY is set
    if "COHERE_API_KEY" not in os.environ:
        print("Error: COHERE_API_KEY environment variable not set.")
        sys.exit(1)
        
    run_evaluation(args.runs)
