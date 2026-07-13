import os
import cohere
from agent.tool_schemas import TOOLS

co = cohere.Client(os.environ.get("COHERE_API_KEY"))

response = co.chat(
    message="list the files",
    tools=TOOLS,
    model="command-a-03-2025"
)
print("Turn 1:", response.text, response.tool_calls)

tool_results = [
    {
        "call": {
            "name": response.tool_calls[0].name,
            "parameters": dict(response.tool_calls[0].parameters)
        },
        "outputs": [{"result": "file1.txt\\nfile2.txt"}]
    }
]

print("Sending tool results:", tool_results)

response2 = co.chat(
    message="",
    tools=TOOLS,
    tool_results=tool_results,
    model="command-a-03-2025"
)
print("Turn 2:", response2.text)
