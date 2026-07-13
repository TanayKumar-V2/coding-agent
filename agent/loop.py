import os
import json
from datetime import datetime
import uuid
import cohere
from agent.tools import list_files, read_file, search_code, write_file, run_tests
from agent.tool_schemas import TOOLS

# Map tool names to functions
TOOL_FUNCTIONS = {
    "list_files": list_files,
    "read_file": read_file,
    "search_code": search_code,
    "write_file": write_file,
    "run_tests": run_tests
}

def _serialize_tool_call(tc):
    if hasattr(tc, 'model_dump'):
        return tc.model_dump()
    if hasattr(tc, 'dict'):
        return tc.dict()
    return dict(tc)

def run_agent_loop(task: str, max_steps: int = 15):
    api_key = os.environ.get("COHERE_API_KEY")
    if not api_key:
        raise ValueError("COHERE_API_KEY environment variable is not set.")
    
    co = cohere.Client(api_key=api_key)
    
    # Setup logging
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs', f'run_{timestamp}')
    os.makedirs(log_dir, exist_ok=True)
    transcript_file = os.path.join(log_dir, 'transcript.json')
    
    transcript = []
    
    def log_event(event_type, content):
        event = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "content": content
        }
        transcript.append(event)
        with open(transcript_file, 'w', encoding='utf-8') as f:
            json.dump(transcript, f, indent=2)

    log_event("task", task)
    
    preamble = """You are an expert AI software engineer. Your task is to fix a bug in the provided repository.
You must use the available tools to explore the codebase, understand the bug, modify the code, and run tests.
Workflow:
1. Search the code or list files to understand the project.
2. Run tests to see what is failing.
3. Read the relevant files. IMPORTANT: Do NOT use read_file on large test files (like test_number.py) because they are too large and will crash the context limit. Use search_code to find specific failing test definitions or line numbers instead.
4. Write the fix using write_file.
5. Run tests again to verify.
Do not stop until the tests pass."""
    
    log_event("system_preamble", preamble)
    
    print(f"Starting agent loop. Logs in {log_dir}")
    
    conversation_id = str(uuid.uuid4())
    step_count = 0
    
    # First turn uses message=task
    current_message = task
    tool_results = None
    
    while step_count < max_steps:
        step_count += 1
        print(f"\\n--- Step {step_count} ---")
        
        try:
            kwargs = {
                "preamble": preamble,
                "tools": TOOLS,
                "model": "command-a-03-2025",
                "conversation_id": conversation_id
            }
            if tool_results:
                kwargs["message"] = ""
                kwargs["tool_results"] = tool_results
                print(f"DEBUG: sending tool_results with {len(tool_results)} items.")
            else:
                kwargs["message"] = current_message
                
            for retry_count in range(3):
                try:
                    response = co.chat(**kwargs)
                    break
                except Exception as e:
                    if "NO_TOOL_CALL_OR_RESPONSE_GENERATED" in str(e) and retry_count < 2:
                        print(f"Retrying after error: {e}")
                        import time; time.sleep(2)
                        continue
                    raise e
            
            # Log the response safely
            log_event("model_response", {
                "text": response.text,
                "tool_calls": [_serialize_tool_call(tc) for tc in (response.tool_calls or [])]
            })
            
            if response.text:
                print(f"Model: {response.text}")
                
            if not response.tool_calls:
                print("No more tool calls. Task finished.")
                log_event("finish", "Model completed without tool calls.")
                return response.text
                
            # Execute tool calls
            tool_results = []
            for tc in response.tool_calls:
                print(f"Executing tool: {tc.name} with args {tc.parameters}")
                func = TOOL_FUNCTIONS.get(tc.name)
                if not func:
                    result = f"Error: unknown tool {tc.name}"
                else:
                    try:
                        args = tc.parameters if isinstance(tc.parameters, dict) else dict(tc.parameters)
                        # ensure test_path has a default if omitted by model
                        if tc.name == "run_tests" and "test_path" not in args:
                            args["test_path"] = "tests/"
                        result = str(func(**args))
                    except Exception as e:
                        result = f"Error executing {tc.name}: {str(e)}"
                
                # Format for Cohere tool_results
                parameters_dict = tc.parameters if isinstance(tc.parameters, dict) else dict(tc.parameters)
                tool_results.append({
                    "call": {
                        "name": tc.name,
                        "parameters": parameters_dict
                    },
                    "outputs": [{"result": result}]
                })
                print(f"Result: {result[:200]}{'...' if len(result) > 200 else ''}")
                
            log_event("tool_results", tool_results)
            
        except Exception as e:
            print(f"Error calling Cohere API: {e}")
            log_event("error", str(e))
            return f"Failed due to API error: {e}"
            
    print("Max steps reached. Did not converge.")
    log_event("finish", "Max steps reached.")
    return "Did not converge in max steps."
