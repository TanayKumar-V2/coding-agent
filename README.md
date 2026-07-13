# Automated Bug-Fixing Coding Agent

This repository contains a production-grade coding agent that uses Cohere's Command-R / Command-A model to autonomously fix bugs in a sandbox environment. The target repository used for demonstration is `humanize`.

## Features
- **ReAct-style Agent Loop**: The agent lists files, reads code, searches, writes fixes, and runs tests to verify them.
- **Robust Sandboxing**: Tools strictly enforce path traversal limits and execute tests inside an isolated environment.
- **Large Context Truncation**: Safeguards to gracefully truncate overly large outputs, preventing context window crashes and API failures.

## Quickstart

1. Set up the environment:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Export your API key:
```bash
export COHERE_API_KEY="your_api_key_here"
```

3. Seed a bug and run the agent to fix it:
```bash
# Injects a missing-case bug into humanize's ordinal function
python eval/seed_bug.py

# Run the agent autonomously
python main.py --task "Tests are failing in this repo. Find the bug and fix it."
```

## Evaluation Harness

You can automatically measure the agent's success rate over multiple runs using the evaluation harness:
```bash
python eval/evaluate.py --runs 3
```

## Feature Extension

To test the agent's ability to implement a new feature rather than fixing a bug, use the feature task script:
```bash
python eval/feature_task.py
```

## Architecture
- `agent/loop.py`: The core ReAct loop orchestrating Cohere's chat API.
- `agent/tools.py`: Python tools (list_files, read_file, search_code, write_file, run_tests).
- `agent/tool_schemas.py`: JSON schemas matching Cohere's ToolCall format.
- `eval/`: Scripts to seed bugs, evaluate success rates, and prompt feature addition.
- `target_repos/humanize/`: The cloned open-source repository where the agent works.
