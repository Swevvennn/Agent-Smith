import argparse
import json
import os
import time
import sys

from typing import Any, Optional
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
from pydantic import ValidationError

from agent.extract_code import extract_code
from agent.build_manual import build_sandbox_manual
from agent.model import (MBPPTaskInput,
                         SWEBenchTaskInput, SolutionOutput, StepMetrics)
from agent.provider.api_management import call_with_key_rotation
from agent.docker_manager import DockerManager
from agent import prompt
from sandbox.sandbox import run_code
from sandbox.sandbox_config import SandboxConfig
from client_mcp.bridge import SyncMCPClient


REPO_ROOT = Path(__file__).resolve().parent.parent
MCP_COMMAND_MBPP = f"python3 {REPO_ROOT / 'mcp_tools_mbpp.py'}"
MCP_COMMAND_SWEBENCH = f"python3 {REPO_ROOT / 'mcp_tools_swebench.py'}"


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
        parser.add_argument("--model-name", default="mistral-small-latest",
                            help="Defaults to mistral-small-latest")
        parser.add_argument("--provider-url",
                            default="https://api.mistral.ai/v1",
                            help="Defaults to Mistral's endpoint")
        parser.add_argument("--max-iterations", type=int, default=10)
        parser.add_argument("--mcp-stdio")
        parser.add_argument("--mcp-server")
        parser.add_argument(
            "sandbox_config", nargs="?",
            default=None, help="Path to sandbox JSON config")
        return parser

    def parse_args(
            self, argv: Optional[list[str]] = None) -> argparse.Namespace:
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
        self.sandbox_config = args.sandbox_config
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
            return self.run_sandbox(args.sandbox_config)
        elif self.mode == "mbpp":
            if args.max_iterations == 10:
                args.max_iterations = 10
            return self.run_mbpp_agent(args)
        elif self.mode == "swebench":
            if args.max_iterations == 10:
                args.max_iterations = 30
            return self.run_swebench_agent(args)
        else:
            raise ValueError(f"Unknown mode: {self.mode}")

    def run_sandbox(self, sandbox_config: Optional[str] = None) -> int:
        """Launch the interactive sandbox REPL."""
        if sandbox_config:
            config_path = Path(sandbox_config)
            if not config_path.exists():
                print(
                    "Error: The configuration file "
                    f"'{sandbox_config}' does not exist.", file=sys.stderr)
                return 1
            try:
                with open(config_path, "r") as f:
                    config = SandboxConfig.model_validate_json(f.read())
            except ValidationError as e:
                print(
                    "Error: The configuration file is malformed or invalid.\n"
                    f"{e}",
                    file=sys.stderr)
                return 1
            except Exception as e:
                print(f"Error reading file: {e}", file=sys.stderr)
                return 1
        else:
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
        raw_keys = os.getenv("OPENROUTER_API_KEY", "")
        api_keys = [k.strip() for k in raw_keys.split(",") if k.strip()]
        provider_url = args.provider_url
        mcp_transport, mcp_target = (
            self._resolve_mcp_connection(MCP_COMMAND_MBPP)
            )
        if mcp_transport == "http":
            mcp_client = SyncMCPClient(mcp_type="http", url=mcp_target or "")
        else:
            mcp_client = (
                SyncMCPClient(
                    command=mcp_target or MCP_COMMAND_MBPP, mcp_type="stdio"))
        manual = build_sandbox_manual(mcp_client.list_tools())
        mcp_client.close()
        system_prompt = prompt.build_system_prompt_mbpp(manual)
        config = SandboxConfig()
        user_prompt = prompt.build_user_prompt_mbpp(task)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        final_solution = None
        total_input_tokens = 0
        total_output_tokens = 0
        total_requests = 0
        start_time = time.time()
        steps = []
        for step in range(args.max_iterations):
            print(f"\n===== ITERATION {step + 1} =====")

            if time.time() - start_time > 120:
                print("Global timeout (120s) reached, stopping.")
                break

            request_start = time.time()
            try:
                def make_call(key):
                    client = OpenAI(base_url=provider_url, api_key=key)
                    return client.chat.completions.create(
                        model=args.model_name or "mistral-small-latest",
                        messages=messages,
                    )
                response, retries = call_with_key_rotation(make_call, api_keys)
            except Exception as e:
                print(f"LLM call failed: {e}")
                break
            request_time_ms = (time.time() - request_start) * 1000
            llm_text = response.choices[0].message.content
            print("LLM said:\n", llm_text)

            # Count tokens and requests for this step
            total_requests += 1
            total_input_tokens += response.usage.prompt_tokens
            total_output_tokens += response.usage.completion_tokens

            # Stop if we exceed the MBPP hard limits (subject section VI.1.1)
            if total_input_tokens > 6000 or total_output_tokens > 1500:
                print("Token limit exceeded, stopping.")
                break

            code = extract_code(llm_text)
            if code is None:
                observation = (
                    "No valid code block found. "
                    "Write exactly one ```python block."
                )
                print("Observation:", observation)
                # Record this step (no sandbox execution happened)
                steps.append(StepMetrics(
                    step=step + 1,
                    input_tokens=response.usage.prompt_tokens,
                    output_tokens=response.usage.completion_tokens,
                    request_time_ms=request_time_ms,
                    api_url=args.provider_url or "",
                    model_name=args.model_name or "mistral-small-latest",
                    llm_output=llm_text,
                    sandbox_input="",
                    sandbox_output=observation,
                    retries=retries,
                ))
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

            # Record this step (with sandbox execution)
            steps.append(StepMetrics(
                step=step + 1,
                input_tokens=response.usage.prompt_tokens,
                output_tokens=response.usage.completion_tokens,
                request_time_ms=request_time_ms,
                api_url=args.provider_url or "",
                model_name=args.model_name or "mistral-small-latest",
                llm_output=llm_text,
                sandbox_input=code,
                sandbox_output=observation,
                retries=retries,
            ))

            if result["final_answer"] is not None:
                final_solution = result["final_answer"]
                print("\n>>> final_answer received! Solution:")
                print(final_solution)
                break

            messages.append({"role": "assistant", "content": llm_text})
            messages.append(
                {
                    "role": "user",
                    "content": f"Execution result:\n{observation}"})

        solution = SolutionOutput(
            task_id=str(task["task_id"]),
            benchmark="mbpp",
            success=final_solution is not None,
            solution=final_solution or "",
            system_prompt=system_prompt,
            iterations=step + 1,
            total_requests=total_requests,
            total_input_tokens=total_input_tokens,
            total_output_tokens=total_output_tokens,
            total_time_seconds=time.time() - start_time,
            steps=steps,
        )
        output_path = args.output or "cache/mbpp_solution.json"
        self.save_output(output_path, solution)
        print(f"\nSolution saved to {output_path}")

        return 0 if solution.success else 1

    def run_swebench_agent(self, args: Any) -> int:
        """Run the SWE-bench agent loop and write the solution output.

        The MCP connection / task loading setup is kept here. The main
        agent loop (with Docker handling) is still TODO.
        """
        task = self.load_task(args.task_file)
        load_dotenv()
        raw_keys = os.getenv("OPENROUTER_API_KEY", "")
        api_keys = [k.strip() for k in raw_keys.split(",") if k.strip()]
        provider_url = args.provider_url
        mcp_transport, mcp_target = (
            self._resolve_mcp_connection(MCP_COMMAND_SWEBENCH))
        if mcp_transport == "http":
            mcp_client = SyncMCPClient(mcp_type="http", url=mcp_target or "")
        else:
            mcp_client = SyncMCPClient(
                command=mcp_target or MCP_COMMAND_SWEBENCH, mcp_type="stdio")
        manual = build_sandbox_manual(mcp_client.list_tools())
        mcp_client.close()

        # Start the Docker container holding the buggy repo (at /testbed)
        docker = DockerManager(image=task["docker_image"])
        try:
            docker.start()
            # Tell the MCP tools which container to run commands in,
            # and give them the eval script (without changing run_tests()'s
            # signature, per the subject's Mandatory Tools spec).
            os.environ["SWEBENCH_CONTAINER"] = docker.container_name
            os.environ["SWEBENCH_EVAL_SCRIPT"] = task["eval_script"]
        except Exception as e:
            print(f"Failed to start Docker container: {e}")
            return 1

        system_prompt = prompt.build_system_prompt_swebench(manual)
        config = SandboxConfig(max_memory_mb=0)
        user_prompt = prompt.build_user_prompt_swebench(task)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        final_solution = None
        total_input_tokens = 0
        total_output_tokens = 0
        total_requests = 0
        start_time = time.time()
        steps = []
        for step in range(args.max_iterations):
            print(f"\n===== ITERATION {step + 1} =====")

            if time.time() - start_time > 900:
                print("Global timeout (900s) reached, stopping.")
                break

            request_start = time.time()
            try:
                def make_call(key):
                    client = OpenAI(base_url=provider_url, api_key=key)
                    return client.chat.completions.create(
                        model=args.model_name or "mistral-small-latest",
                        messages=messages,
                    )
                response, retries = call_with_key_rotation(make_call, api_keys)
            except Exception as e:
                print(f"LLM call failed: {e}")
                break
            request_time_ms = (time.time() - request_start) * 1000
            llm_text = response.choices[0].message.content
            print("LLM said:\n", llm_text)

            total_requests += 1
            total_input_tokens += response.usage.prompt_tokens
            total_output_tokens += response.usage.completion_tokens

            if total_input_tokens > 300000 or total_output_tokens > 10000:
                print("Token limit exceeded, stopping.")
                break

            code = extract_code(llm_text)
            if code is None:
                observation = (
                    "No valid code block found. "
                    "Write exactly one ```python block."
                )
                print("Observation:", observation)
                steps.append(StepMetrics(
                    step=step + 1,
                    input_tokens=response.usage.prompt_tokens,
                    output_tokens=response.usage.completion_tokens,
                    request_time_ms=request_time_ms,
                    api_url=args.provider_url or "",
                    model_name=args.model_name or "mistral-small-latest",
                    llm_output=llm_text,
                    sandbox_input="",
                    sandbox_output=observation,
                    retries=retries,
                ))
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

            steps.append(StepMetrics(
                step=step + 1,
                input_tokens=response.usage.prompt_tokens,
                output_tokens=response.usage.completion_tokens,
                request_time_ms=request_time_ms,
                api_url=args.provider_url or "",
                model_name=args.model_name or "mistral-small-latest",
                llm_output=llm_text,
                sandbox_input=code,
                sandbox_output=observation,
                retries=retries,
            ))

            if result["final_answer"] is not None:
                final_solution = result["final_answer"]
                print("\n>>> final_answer received! Solution:")
                print(final_solution)
                break

            messages.append({"role": "assistant", "content": llm_text})
            messages.append(
                {
                    "role": "user",
                    "content": f"Execution result:\n{observation}"})

        solution = SolutionOutput(
            task_id=str(task["instance_id"]),
            benchmark="swebench",
            success=final_solution is not None,
            solution=final_solution or "",
            system_prompt=system_prompt,
            iterations=step + 1,
            total_requests=total_requests,
            total_input_tokens=total_input_tokens,
            total_output_tokens=total_output_tokens,
            total_time_seconds=time.time() - start_time,
            steps=steps,
        )
        output_path = args.output or "cache/swebench_solution.json"
        self.save_output(output_path, solution)
        print(f"\nSolution saved to {output_path}")

        # Clean up the Docker container (required by the subject)
        docker.cleanup()

        return 0 if solution.success else 1

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
            directory = os.path.dirname(output_path)
            if directory:
                os.makedirs(directory, exist_ok=True)

            with open(output_path, "w") as f:
                json.dump(payload.model_dump(), f, indent=2)

        except Exception as e:
            print(f"Error saving output to {output_path}: {e}")


def main(mode: str, argv: Optional[list[str]] = None) -> int:
    """Module entry point for `python -m agent_cli` style execution."""
    cli = CLI(mode)
    return cli.run(argv)
