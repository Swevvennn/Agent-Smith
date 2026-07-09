*This project has been created as part of the 42 curriculum by erifflar, jagharrad and mosmond.*

# Agent Smith

## Description
Agent Smith is an agentic coding framework designed to solve benchmark tasks from MBPP and SWE-bench by combining a large language model with a constrained sandbox and an MCP-based tool layer. The system is built around an iterative loop of reasoning, code generation, execution, and observation. Its goal is to let an LLM interact with a controlled execution environment, inspect and modify repository code, and produce either a working function solution or a patch for a real bug.

The project is organized around three main layers:
- a reasoning layer powered by an LLM,
- a sandbox layer that safely executes generated code,
- a tool layer exposed through the Model Context Protocol (MCP) for MBPP and SWE-bench tasks.

## System Architecture
The architecture is composed of the following components:

- CLI orchestration: the main entrypoint in [student/agent_cli.py](student/agent_cli.py) parses user arguments, loads benchmark tasks, builds prompts, and drives the agent loop.
- Agent core: the modules in [student/agent](student/agent) handle prompt construction, extraction of executable code from model responses, Docker management for SWE-bench tasks, and serialization of results.
- Sandbox runtime: [student/sandbox/sandbox.py](student/sandbox/sandbox.py) executes generated code in a subprocess with restricted imports, restricted file access, and execution limits.
- MCP bridge: [student/client_mcp](student/client_mcp) exposes tools to the agent via MCP. The client side makes these tools callable as Python functions inside the sandbox, while the server side implements the actual tool behavior.
- Benchmarks: the project targets two task families:
  - MBPP: function-level code generation and test-based validation.
  - SWE-bench: repository patching and validation inside a Docker environment.

## Agent Loop Explanation
The project uses a feedback-driven agent loop:

1. The task is loaded from a JSON file and converted into a structured input object.
2. A system prompt and a user prompt are built for the selected benchmark.
3. The LLM is called with the current message history.
4. The response is parsed to extract a single executable Python block or tool invocation.
5. The sandbox executes the code.
6. The execution result (stdout, stderr, or timeout) is fed back into the conversation as an observation.
7. The loop repeats until the task is solved, a final answer is emitted, or resource limits are reached.

For MBPP, the loop stops when the generated solution passes the provided tests. For SWE-bench, the loop stops when the patch is validated by the benchmark script and a patch can be returned.

## Sandbox Design
The sandbox is a critical safety boundary around the agent.

Features:
- Subprocess isolation so agent code does not run in the main interpreter.
- Restricted builtins such as `__import__`, `open`, and network access.
- Controlled file-system access limited to approved directories.
- Execution timeouts and optional memory limits.
- MCP tool injection so the agent can call tools while still running inside the sandbox.

The default sandbox configuration is defined in [student/sandbox/sandbox_config.py](student/sandbox/sandbox_config.py). The sandbox is used both for MBPP solution execution and for SWE-bench repository manipulation workflows.

## Tool Implementation Details
The MCP tool layer is implemented in two modules:

- [student/client_mcp/server/tools_MBPP.py](student/client_mcp/server/tools_MBPP.py): exposes `run_tests(...)` for MBPP tasks.
- [student/client_mcp/server/tools_SWE_bench.py](student/client_mcp/server/tools_SWE_bench.py): exposes repository inspection and editing tools such as `read_file`, `edit_file`, `list_files`, `search_code`, `search_function_or_class_definition_in_code`, `find_references`, `run_tests`, `run_command`, and `get_patch`.

The client-side bridge in [student/client_mcp/bridge.py](student/client_mcp/bridge.py) creates Python-callable wrappers that make tool calls appear as regular functions to the agent. This enables the agent to operate in a natural, code-driven way while still using a remote and controlled tool interface.

## Instructions
### Prerequisites
- Python 3.10
- Docker (required for SWE-bench runs)
- Network access to the chosen LLM provider endpoint

### Installation
1. Clone the repository.
2. Install dependencies:
   ```bash
   pip install -e .
   ```
3. Create a `.env` file with the required API key environment variables, for example:
   ```bash
   OPENROUTER_API_KEY=your_key_here
   ```

### Running the project
#### MBPP
```bash
python3 student/agent_mbpp.py --task-file path/to/task.json --output cache/mbpp_solution.json
```

#### SWE-bench
```bash
python3 student/agent_swebench.py --task-file path/to/task.json --output cache/swebench_solution.json
```

#### Sandbox REPL
```bash
python3 -m student.sandbox_entrypoint
```

### Notes
- The project exposes MCP servers through [mcp_tools_mbpp.py](mcp_tools_mbpp.py) and [mcp_tools_swebench.py](mcp_tools_swebench.py).
- The CLI also supports `--mcp-stdio` and `--mcp-server` overrides for custom MCP connection targets.

## Usage Examples
### Example MBPP flow
The agent receives an MBPP problem, generates a Python implementation, runs the available tests, and emits a final answer once the solution passes.

### Example SWE-bench flow
The agent inspects the buggy repository inside a Docker container, applies a minimal patch, validates it with the benchmark script, and returns the patch via the MCP tool layer.

## Benchmark Results and Analysis
The current project is a research-oriented prototype. It focuses on demonstrating a working agent loop with sandbox isolation and MCP-backed tool access rather than claiming production-grade benchmark results.

Observed strengths:
- Clear separation between planning, tool use, and execution.
- Sandbox constraints make it possible to safely run generated code.
- The MCP interface allows the agent to operate on both simple function tasks and repository-level debugging tasks.

Observed limitations:
- The SWE-bench loop depends heavily on Docker availability and container startup time.
- The system is sensitive to prompt quality and tool descriptions.
- The sandbox is intentionally restrictive, which may block some legitimate operations unless carefully configured.

This makes the framework a good foundation for future experimentation with stronger prompting, tool synthesis, and benchmark evaluation.

## Resources
### References
- MCP documentation: https://modelcontextprotocol.io/
- OpenAI Python SDK documentation: https://platform.openai.com/docs
- Docker documentation: https://docs.docker.com/
- SWE-bench project: https://www.swebench.com/
- MBPP benchmark: https://huggingface.co/datasets/google-research-datasets/mbpp

### AI usage
AI assistance was used during development for:
- understanding the project structure and drafting the software architecture,
- generating and refining the prompt and tool abstractions,
- helping to implement the sandbox safety layer and MCP bridging logic,
- writing and reviewing the project documentation.

## Project Structure
```text
.
├── mcp_tools_mbpp.py
├── mcp_tools_swebench.py
├── pyproject.toml
├── README.md
├── setup_env.sh
├── student/
│   ├── agent/
│   ├── client_mcp/
│   ├── sandbox/
│   ├── testbed/
│   └── agent_cli.py
```

