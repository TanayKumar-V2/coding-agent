import os
import subprocess

def seed_bug():
    repo_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'target_repos', 'humanize'))
    target_file = os.path.join(repo_dir, 'src', 'humanize', 'number.py')
    
    # Ensure clean state first to make it idempotent
    subprocess.run(['git', 'checkout', '--', 'src/humanize/number.py'], cwd=repo_dir, check=True)
    
    with open(target_file, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Apply the bug
    buggy_content = content.replace(
        "digit = 0 if value % 100 in (11, 12, 13) else value % 10",
        "digit = 0 if value % 100 in (11, 12) else value % 10"
    )
    
    with open(target_file, 'w', encoding='utf-8') as f:
        f.write(buggy_content)
        
    print("Bug successfully seeded.")

if __name__ == '__main__':
    seed_bug()
