import json
import os
from dotenv import load_dotenv
from openai import OpenAI

from student.agent.extract_code import extract_code
from student.sandbox.sandbox import run_code
from student.sandbox.sandbox_config import SandboxConfig


MCP_COMMAND = "python3 mcp_tools_mbpp.py"


def load_task(path: str) -> dict:
    with open(path) as f:
        return json.load(f)


def load_test(task: dict) -> list[str]:
    return task.get("test_list") or task.get("public_test_list") or []


def load_api(env_key):
    load_dotenv()
    api_key = os.getenv(env_key)
    if not api_key:
        print("Something went wrong (api key loader)")
    return api_key


SYSTEM_PROMPT = """You are a coding agent that solves Python problems (MBPP).

You work in a loop: you write ONE Python code block, it runs in a sandbox,
and you see the result. Then you write the next block, and so on.

AVAILABLE TOOLS (call them like normal Python functions):
- run_tests(solution_code, test_list): runs the given tests against your
  solution. Returns {"passed": bool, "message": str}. Use it to CHECK your
  work before finishing.
- final_answer(solution_code): call this ONLY once your solution passes the
  tests. Pass the full function code as a string.

RULES:
- Always write your code between ```python and ```
- First write your solution, test it with run_tests, and only call
  final_answer when the tests pass.

EXAMPLE:
```python
solution = "def add(a, b):\\n    return a + b"
result = run_tests(solution_code=solution, test_list=["assert add(2, 3) == 5"])
print(result)
```
Then, once tests pass:
```python
final_answer("def add(a, b):\\n    return a + b")
```
"""

def main():

    task = load_task("cache/mbpp_task.json")
    tests = load_test(task)

    api_key = load_api("OPEN_ROUTER_API_KEY")
    client = OpenAI(base_url="https://api.mistral.ai/v1", api_key=api_key)

    config = SandboxConfig()

    task_text = task["task_definition"]
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Solve this task:\n{task_text}\n\nTests to pass:\n{tests}"},
    ]

    final_solution = None

    for step in range(10):
        print(f"\n===== ITERATION {step + 1} =====")

        # a. Ask the LLM
        response = client.chat.completions.create(
            model="mistral-small-latest",
            messages=messages,
        )
        llm_text = response.choices[0].message.content
        print("LLM said:\n", llm_text)

        code = extract_code(llm_text)
        if code is None:
            observation = "No code block found. Write your code between ```python and ```"
            print("Observation:", observation)
            messages.append({"role": "assistant", "content": llm_text})
            messages.append({"role": "user", "content": observation})
            continue

        result = run_code(code, config, mcp_command=MCP_COMMAND)
        observation = result["output"]
        print("Observation:", observation)

        if result["final_answer"] is not None:
            final_solution = result["final_answer"]
            print("\n>>> final_answer received! Solution:")
            print(final_solution)
            break

        messages.append({"role": "assistant", "content": llm_text})
        messages.append({"role": "user", "content": f"Execution result:\n{observation}"})

    solution = {
        "task_id": str(task["task_id"]),
        "benchmark": "mbpp",
        "success": final_solution is not None,
        "solution": final_solution or "",
    }
    with open("cache/mbpp_solution.json", "w") as f:
        json.dump(solution, f, indent=2)
    print("\nSolution saved to cache/mbpp_solution.json")


if __name__ == "__main__":
    main()