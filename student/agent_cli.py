import argparse
import json
import os

from typing import Any, Optional
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
from pydantic import ValidationError

from agent.extract_code import extract_code
from sandbox.sandbox import run_code
from sandbox.sandbox_config import SandboxConfig
from client_mcp.bridge import SyncMCPClient
from agent.build_manual import build_sandbox_manual
from agent.model import MBPPTaskInput, SWEBenchTaskInput, SolutionOutput

REPO_ROOT = Path(__file__).resolve().parent.parent
MCP_COMMAND_MBPP = f"python3 {REPO_ROOT / 'mcp_tools_mbpp.py'}"


class CLI:
    """Command-line entry point for the agentic framework."""

    def __init__(self, mode: str) -> None:
        self.mode = mode
        self.task_file: Optional[str] = None
        self.output: Optional[str] = None
        self.model_name: Optional[str] = None
        self.provider_url: Optional[str] = None
        self.benchmark: Optional[str] = None
        self.max_iterations: int = 10
        self.sandbox_config: Optional[str] = None
        self.mcp_stdio: Optional[str] = None
        self.mcp_server: Optional[str] = None

    @staticmethod
    def build_parser() -> argparse.ArgumentParser:
        """Build the argument parser used by the student CLI."""
        parser = argparse.ArgumentParser(description="Agent Smith CLI")
        parser.add_argument("--task-file")
        parser.add_argument("--output")
        parser.add_argument("--model-name")
        parser.add_argument("--provider-url")
        parser.add_argument("--max-iterations", type=int, default=10)
        parser.add_argument("--mcp-stdio")
        parser.add_argument("--mcp-server")
        return parser

    def parse_args(self, argv: Optional[list[str]] = None) -> argparse.Namespace:
        """Parse command-line arguments and store them on the CLI instance."""
        parser = self.build_parser()
        args = parser.parse_args(argv)
        self.task_file = args.task_file
        self.output = args.output
        self.model_name = args.model_name
        self.provider_url = args.provider_url
        self.max_iterations = args.max_iterations
        self.mcp_stdio = args.mcp_stdio
        self.mcp_server = args.mcp_server
        return args

    def _resolve_mcp_connection(
        self,
        default_stdio_target: Optional[str] = None,
    ) -> tuple[str, Optional[str]]:
        if self.mcp_server:
            return "http", self.mcp_server
        if self.mcp_stdio:
            return "stdio", self.mcp_stdio
        return "stdio", default_stdio_target

    def run(self, argv: Optional[list[str]] = None) -> int:
        """Dispatch to the requested benchmark or sandbox mode."""
        args = self.parse_args(argv)
        if self.mode == "sandbox":
            return self.run_sandbox()
        elif self.mode == "mbpp":
            return self.run_mbpp_agent(args)
        elif self.mode == "swebench":
            return self.run_swebench_agent(args)
        else:
            raise ValueError(f"Unknown mode: {self.mode}")

    def run_sandbox(self, sandbox_config: Optional[str] = None) -> int:
        """Launch the interactive sandbox REPL."""
        config = SandboxConfig()
        mcp_transport, mcp_target = self._resolve_mcp_connection()
        print("Sandbox loaded!")
        while True:
            try:
                user = input(">>> ")

                if user.strip().lower() in ["exit", "quit"]:
                    print("Exiting sandbox...")
                    break
                result = run_code(
                    user,
                    config,
                    mcp_transport=mcp_transport,
                    mcp_target=mcp_target,
                )

                if result.get("timed_out"):
                    print(f"Timeout: {result['output']}")
                    continue

                if result.get("final_answer") is not None:
                    print(f"Final answer: {result['final_answer']}")

                print(f"Ouput: {result.get('output')}")
            except KeyboardInterrupt:
                print("Exit (CTRL+C)")
                break
            except EOFError:
                print("Exit (CTRL+D)")
                break
            except Exception as e:
                print(f"An error occured: {e}")
                break
        return 0

    def run_mbpp_agent(self, args: Any) -> int:
        """Run the MBPP agent loop and write the solution output."""
        task = self.load_task(args.task_file)
        load_dotenv()
        client = OpenAI(
            base_url=args.provider_url,
            api_key=os.getenv("OPEN_ROUTER_API_KEY")
        )
        mcp_transport, mcp_target = self._resolve_mcp_connection(MCP_COMMAND_MBPP)
        if mcp_transport == "http":
            mcp_client = SyncMCPClient(mcp_type="http", url=mcp_target or "")
        else:
            mcp_client = SyncMCPClient(command=mcp_target or MCP_COMMAND_MBPP, mcp_type="stdio")
        manual = build_sandbox_manual(mcp_client.list_tools())
        mcp_client.close()
        system_prompt = f"""You are a coding agent for MBPP.

    Your job is to solve the task by iterating through a strict loop:
    Thought -> Code -> Observation.

    You must reply in this format:
    Thought: brief reasoning in plain text.
    Code:
    ```python
    # one executable Python block only
    ```

    Only the Python block will be executed. Do not write multiple code blocks.
    Do not answer with prose only.

    {manual}

    Rules:
    - Prefer small, testable changes.
    - Use the available MCP tools as normal Python functions.
    - First build the solution, then test it with run_tests.
    - Call final_answer only when the tests pass.
    - If execution fails, inspect the observation and adapt the next code block.
    - If no valid code block is produced, rewrite with exactly one ```python block.
    - If a block is malformed, fix it in the next turn.
    - If the sandbox reports a timeout, partial output, or an error, use that
      observation directly and do not guess what happened.

    Example:
    Thought: I will write the function and verify it with the provided tests.
    Code:
    ```python
    solution = "def add(a, b):\\n    return a + b"
    result = run_tests(solution_code=solution, test_list=["assert add(2, 3) == 5"])
    print(result)
    ```

    When tests pass:
    Thought: The solution is validated, so I can finish.
    Code:
    ```python
    final_answer("def add(a, b):\\n    return a + b")
    ```
    """
        config = SandboxConfig()
        test_imports = "\n".join(task["test_imports"]) or "None"
        test_list = "\n".join(task["test_list"]) or "None"
        user_prompt = f"""
    Solve the following MBPP task.

    ## Task
    {task["task_definition"]}

    ## Function signature
    {task["function_definition"]}

    ## test imports
    {test_imports}

    ## tests
    {test_list}

    Instructions:
    - Implement exactly the requested function.
    - Respect the function signature.
    - Only call `final_answer(...)` after `run_tests` reports success.
    """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        final_solution = None
        for step in range(args.max_iterations):
            print(f"\n===== ITERATION {step + 1} =====")

            # a. Ask the LLM
            try:
                response = client.chat.completions.create(
                    model=args.model_name or "mistral-small-latest",
                    messages=messages,
                )
            except Exception as e:
                print(f"LLM call failed: {e}")
                break
            llm_text = response.choices[0].message.content
            print("LLM said:\n", llm_text)

            code = extract_code(llm_text)
            if code is None:
                observation = (
                    "No valid code block found. "
                    "Write exactly one ```python block."
                )
                print("Observation:", observation)
                messages.append({"role": "assistant", "content": llm_text})
                messages.append({"role": "user", "content": observation})
                continue

            result = run_code(
                code,
                config,
                mcp_transport=mcp_transport,
                mcp_target=mcp_target,
            )
            observation = result["output"]
            print("Observation:", observation)

            if result["final_answer"] is not None:
                final_solution = result["final_answer"]
                print("\n>>> final_answer received! Solution:")
                print(final_solution)
                break

            messages.append({"role": "assistant", "content": llm_text})
            messages.append({"role": "user", "content": f"Execution result:\n{observation}"})

        solution = SolutionOutput(
            task_id=str(task["task_id"]),
            benchmark="mbpp",
            success=final_solution is not None,
            solution=final_solution or "",
            system_prompt=system_prompt,
            iterations=step,
            total_requests=0,
            total_input_tokens=0,
            total_output_tokens=0,
            total_time_seconds=0,
            step=[]
        )
        output_path = args.output or "../cache/mbpp_solution.json"
        self.save_output(output_path, solution)
        print(f"\nSolution saved to {output_path}")

        return 0 if solution.success else 1

    def run_swebench_agent(self, args: Any) -> int:
        """Run the SWE-bench agent loop and write the solution output."""
        task = self.load_task(args.task_file)
        load_dotenv()
        client = OpenAI(
            base_url=args.provider_url,
            api_key=os.getenv("OPEN_ROUTER_API_KEY")
        )
        mcp_transport, mcp_target = self._resolve_mcp_connection(MCP_COMMAND_MBPP)
        if mcp_transport == "http":
            mcp_client = SyncMCPClient(mcp_type="http", url=mcp_target or "")
        else:
            mcp_client = SyncMCPClient(command=mcp_target or MCP_COMMAND_MBPP, mcp_type="stdio")
        manual = build_sandbox_manual(mcp_client.list_tools())
        mcp_client.close()
        system_prompt = """"""
        final_solution = None
        for step in range(args.max_iterations):
            print(f"\n===== ITERATION {step + 1} =====")

            # a. Ask the LLM
            try:
                response = client.chat.completions.create(
                    model=args.model_name or "mistral-small-latest",
                    messages=messages,
                )
            except Exception as e:
                print(f"LLM call failed: {e}")
                break
            llm_text = response.choices[0].message.content
            print("LLM said:\n", llm_text)

            code = extract_code(llm_text)
            if code is None:
                observation = (
                    "No valid code block found. "
                    "Write exactly one ```python block."
                )
                print("Observation:", observation)
                messages.append({"role": "assistant", "content": llm_text})
                messages.append({"role": "user", "content": observation})
                continue

            result = run_code(
                code,
                config,
                mcp_transport=mcp_transport,
                mcp_target=mcp_target,
            )
            observation = result["output"]
            print("Observation:", observation)

            if result["final_answer"] is not None:
                final_solution = result["final_answer"]
                print("\n>>> final_answer received! Solution:")
                print(final_solution)
                break

            messages.append({"role": "assistant", "content": llm_text})
            messages.append({"role": "user", "content": f"Execution result:\n{observation}"})

        solution = SolutionOutput(
            task_id=str(task["task_id"]),
            benchmark="mbpp",
            success=final_solution is not None,
            solution=final_solution or "",
            system_prompt=system_prompt,
            iterations=step,
            total_requests=0,
            total_input_tokens=0,
            total_output_tokens=0,
            total_time_seconds=0,
            step=[]
        )
        output_path = args.output or "../cache/mbpp_solution.json"
        self.save_output(output_path, solution)
        print(f"\nSolution saved to {output_path}")
        

    def load_task(self, task_file: str) -> dict[str, Any]:
        """Load a benchmark task description from disk."""
        if not task_file:
            print("Error: --task-file is required")
            raise SystemExit(1)
        model_class = (MBPPTaskInput
                       if self.mode == "mbpp"
                       else SWEBenchTaskInput)

        try:
            with open(task_file) as f:
                raw = f.read()
        except OSError as e:
            print(f"Error loading task from {task_file}: {e}")
            raise SystemExit(1)

        try:
            validated = model_class.model_validate_json(raw)
        except ValidationError as e:
            print(f"Invalid task file {task_file}: {e}")
            raise SystemExit(1)

        return validated.model_dump()

    def save_output(self, output_path: str, payload: SolutionOutput) -> None:
        """Serialize the final agent output to JSON."""
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            with open(output_path, "w") as f:
                json.dump(payload.model_dump(), f, indent=2)

        except Exception as e:
            print(f"Error saving output to {output_path}: {e}")


def main(mode: str, argv: Optional[list[str]] = None) -> int:
    """Module entry point for `python -m agent_cli` style execution."""
    cli = CLI(mode)
    return cli.run(argv)
