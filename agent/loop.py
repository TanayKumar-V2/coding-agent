import os
import json
from datetime import datetime
import uuid
import cohere
from agent.tools import list_files, read_file, search_code, write_file, run_tests, patch_file, run_linter
from agent.tool_schemas import TOOLS
import re

TOOL_FUNCTIONS = {
    "list_files": list_files,
    "read_file": read_file,
    "search_code": search_code,
    "write_file": write_file,
    "patch_file": patch_file,
    "run_tests": run_tests,
    "run_linter": run_linter
}

def _serialize_tool_call(tc):
    if hasattr(tc, 'model_dump'): return tc.model_dump()
    if hasattr(tc, 'dict'): return tc.dict()
    return dict(tc)

def run_agent_loop(task: str, max_steps: int = 20):
    api_key = os.environ.get("COHERE_API_KEY")
    if not api_key:
        raise ValueError("COHERE_API_KEY environment variable is not set.")
    
    co = cohere.Client(api_key=api_key)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs', f'run_{timestamp}')
    os.makedirs(log_dir, exist_ok=True)
    transcript_file = os.path.join(log_dir, 'transcript.json')
    transcript = []
    
    def log_event(event_type, content):
        event = {"timestamp": datetime.now().isoformat(), "type": event_type, "content": content}
        transcript.append(event)
        with open(transcript_file, 'w', encoding='utf-8') as f:
            json.dump(transcript, f, indent=2)

    log_event("task", task)
    print(f"Starting Multi-Agent loop. Logs in {log_dir}")
    
    # ------------------ PLANNER AGENT ------------------
    print("\n=== STARTING PLANNER AGENT ===")
    planner_preamble = """You are an expert AI software architect. Your job is to plan how to solve the user's issue.
You only have read access to the repository (list_files, read_file, search_code).
1. Explore the codebase to find where the bug or feature should be implemented.
2. Find the relevant tests.
3. Formulate a detailed, step-by-step markdown plan of what files need to be changed and what code needs to be modified.
Do NOT write code directly. End your response with a clear, numbered plan.
DO NOT output tool calls as markdown JSON blocks. You MUST use the provided function calling API to execute tools."""
    
    PLANNER_TOOLS = [t for t in TOOLS if t["name"] in ["list_files", "read_file", "search_code"]]
    
    planner_conversation_id = str(uuid.uuid4())
    planner_msg = task
    tool_results = None
    planner_recent_calls = []
    
    for step in range(5):
        print(f"Planner Step {step+1}")
        kwargs = {"preamble": planner_preamble, "tools": PLANNER_TOOLS, "model": "command-a-03-2025", "conversation_id": planner_conversation_id}
        if tool_results:
            kwargs["message"] = ""
            kwargs["tool_results"] = tool_results
        else:
            kwargs["message"] = planner_msg
            
        for retry in range(3):
            try:
                response = co.chat(**kwargs)
                break
            except Exception as e:
                import time
                if "NO_TOOL_CALL_OR_RESPONSE_GENERATED" in str(e) and retry < 2:
                    time.sleep(2)
                    continue
                if retry < 2:
                    wait = 2 ** retry
                    print(f"Planner API error, retrying in {wait}s: {e}")
                    time.sleep(wait)
                    continue
                raise e
        
        log_event("planner_response", {"text": response.text, "tool_calls": [_serialize_tool_call(tc) for tc in (response.tool_calls or [])]})
        if response.text: print(f"Planner: {response.text}")
        
        if not response.tool_calls:
            # Check for JSON blocks
            json_blocks = re.findall(r'```json\n(.*?)\n```', response.text, re.DOTALL)
            parsed_tools = []
            for block in json_blocks:
                try:
                    data = json.loads(block)
                    if isinstance(data, dict) and 'tool_name' in data:
                        parsed_tools.append({
                            "name": data["tool_name"],
                            "parameters": data.get("parameters", {})
                        })
                except Exception:
                    pass
            if parsed_tools:
                print("==> PARSED JSON TOOL CALLS FROM TEXT")
                class DummyCall:
                    def __init__(self, n, p):
                        self.name = n
                        self.parameters = p
                response.tool_calls = [DummyCall(pt["name"], pt["parameters"]) for pt in parsed_tools]
                
        if not response.tool_calls:
            plan = response.text
            break
            
        current_calls = [{"name": tc.name, "parameters": tc.parameters if isinstance(tc.parameters, dict) else dict(tc.parameters)} for tc in response.tool_calls]
        if current_calls in planner_recent_calls:
            print("==> NUDGE: Repetitive loop detected in Planner.")
            tool_results = []
            for tc in response.tool_calls:
                args = tc.parameters if isinstance(tc.parameters, dict) else dict(tc.parameters)
                res = "ERROR: Loop detected. You recently executed this exact tool call with these exact parameters. Please analyze your previous results and try a different approach, search query, or file path. Do not repeat yourself."
                tool_results.append({"call": {"name": tc.name, "parameters": args}, "outputs": [{"result": res}]})
            log_event("planner_tool_results", tool_results)
            continue
            
        planner_recent_calls.append(current_calls)
        if len(planner_recent_calls) > 3:
            planner_recent_calls.pop(0)

        tool_results = []
        for tc in response.tool_calls:
            print(f"Planner Tool: {tc.name}")
            func = TOOL_FUNCTIONS[tc.name]
            args = tc.parameters if isinstance(tc.parameters, dict) else dict(tc.parameters)
            res = str(func(**args))
            tool_results.append({"call": {"name": tc.name, "parameters": args}, "outputs": [{"result": res}]})
        log_event("planner_tool_results", tool_results)
    else:
        plan = response.text
    
    print("\n=== PLAN COMPILED ===")
    print(plan)
    
    # ------------------ CODER AGENT ------------------
    print("\n=== STARTING CODER AGENT ===")
    coder_preamble = """You are an expert AI software engineer. You have been given a plan to solve an issue.
You must implement the plan using your tools (patch_file, write_file, run_tests, run_linter).
IMPORTANT RULES:
1. Always use `patch_file` for modifying existing files. Use `write_file` ONLY for creating new files.
2. After patching, you MUST run `run_linter`.
3. If the linter passes, you MUST run `run_tests`.
4. REFLECTION LOOP: If `run_linter` or `run_tests` fails, you must output a text response analyzing WHY it failed before you use `patch_file` again to fix it. Do not just blindly try the same patch again.
5. Do not stop until tests pass.
DO NOT output tool calls as markdown JSON blocks. You MUST use the provided function calling API to execute tools."""
    
    CODER_TOOLS = TOOLS # All tools including read, write, patch, test, linter
    coder_conversation_id = str(uuid.uuid4())
    
    coder_msg = f"Task: {task}\n\nPlan:\n{plan}\n\nPlease implement the plan. Start by applying patches."
    tool_results = None
    tests_passed = False
    coder_recent_calls = []
    no_tool_response_count = 0
    
    for step in range(max_steps):
        print(f"\nCoder Step {step+1}")
        kwargs = {"preamble": coder_preamble, "tools": CODER_TOOLS, "model": "command-a-03-2025", "conversation_id": coder_conversation_id}
        if tool_results:
            kwargs["message"] = ""
            kwargs["tool_results"] = tool_results
        else:
            kwargs["message"] = coder_msg
            
        for retry in range(3):
            try:
                response = co.chat(**kwargs)
                break
            except Exception as e:
                import time
                if "NO_TOOL_CALL_OR_RESPONSE_GENERATED" in str(e) and retry < 2:
                    time.sleep(2)
                    continue
                if retry < 2:
                    wait = 2 ** retry
                    print(f"Coder API error, retrying in {wait}s: {e}")
                    time.sleep(wait)
                    continue
                raise e
        
        log_event("coder_response", {"text": response.text, "tool_calls": [_serialize_tool_call(tc) for tc in (response.tool_calls or [])]})
        if response.text: print(f"Coder: {response.text}")
        
        if not response.tool_calls:
            # Check for JSON blocks
            json_blocks = re.findall(r'```json\n(.*?)\n```', response.text, re.DOTALL)
            parsed_tools = []
            for block in json_blocks:
                try:
                    data = json.loads(block)
                    if isinstance(data, dict) and 'tool_name' in data:
                        parsed_tools.append({
                            "name": data["tool_name"],
                            "parameters": data.get("parameters", {})
                        })
                except Exception:
                    pass
            if parsed_tools:
                print("==> PARSED JSON TOOL CALLS FROM TEXT")
                class DummyCall:
                    def __init__(self, n, p):
                        self.name = n
                        self.parameters = p
                response.tool_calls = [DummyCall(pt["name"], pt["parameters"]) for pt in parsed_tools]

        if not response.tool_calls:
            if not tests_passed:
                no_tool_response_count += 1
                if no_tool_response_count >= 2:
                    print("Coder finished (no tools needed).")
                    return response.text
                print("==> NUDGE: Model stopped without tools, but tests haven't passed.")
                coder_msg = "You provided a text response but did not execute any tool calls. If you haven't fixed the bug and verified it with tests yet, you must use `patch_file` to modify the code and `run_tests` to verify your fix. Please execute the required tool calls now."
                tool_results = None
                continue
            else:
                print("Coder finished successfully.")
                return response.text
        current_calls = [{"name": tc.name, "parameters": tc.parameters if isinstance(tc.parameters, dict) else dict(tc.parameters)} for tc in response.tool_calls]
        if current_calls in coder_recent_calls:
            print("==> NUDGE: Repetitive loop detected in Coder.")
            tool_results = []
            for tc in response.tool_calls:
                args = tc.parameters if isinstance(tc.parameters, dict) else dict(tc.parameters)
                res = "ERROR: Loop detected. You recently executed this exact tool call with these exact parameters. Please analyze your previous results and try a different approach. Do not repeat yourself."
                tool_results.append({"call": {"name": tc.name, "parameters": args}, "outputs": [{"result": res}]})
            log_event("coder_tool_results", tool_results)
            continue
            
        coder_recent_calls.append(current_calls)
        if len(coder_recent_calls) > 3:
            coder_recent_calls.pop(0)

        tool_results = []
        for tc in response.tool_calls:
            print(f"Coder executing: {tc.name} with args {tc.parameters}")
            func = TOOL_FUNCTIONS.get(tc.name)
            args = tc.parameters if isinstance(tc.parameters, dict) else dict(tc.parameters)
            if tc.name in ["run_tests", "run_linter"] and "path" not in args and "test_path" not in args:
                if tc.name == "run_tests": args["test_path"] = "tests/"
                else: args["path"] = "."
                
            try:
                res = str(func(**args))
            except Exception as e:
                res = f"Error: {e}"
                
            tool_results.append({"call": {"name": tc.name, "parameters": args}, "outputs": [{"result": res}]})
            print(f"Result: {res[:200]}...")
            
            # Auto-reflection injection if tests or linter fail
            if tc.name in ["run_tests", "run_linter"]:
                if "failed" in res.lower() or "error" in res.lower() or "failure" in res.lower():
                    print("==> REFLECTION LOOP TRIGGERED: Failure detected.")
                elif tc.name == "run_tests":
                    tests_passed = True
                
        log_event("coder_tool_results", tool_results)

    return "Max steps reached without convergence."
