# SWE-bench Benchmark Report

## Executive summary

This report documents a benchmark plan and the current evidence available in this workspace. The repository already contains a working SWE-bench agent loop and task-selection logic, but live model runs could not be completed in this environment because no provider API keys were configured. The report therefore captures the benchmark setup, the selected tasks, the expected result schema, and the analysis structure that should be filled once runtime execution is available.

Verified environment note:
- The repository supports multiple providers through the OpenAI-compatible client layer in [student/agent/provider/api_management.py](student/agent/provider/api_management.py).
- The SWE-bench agent entrypoint is implemented in [student/agent_cli.py](student/agent_cli.py).
- The built-in SWE-bench task pool used for selection is defined in [moulinette/moulinette/swebench/interact.py](moulinette/moulinette/swebench/interact.py).
- A live run check showed that no provider API keys were present in the shell environment at the time of report creation.

---

## 1. Setup

### Models and providers compared

The following five model/provider combinations were selected for the benchmark matrix:

1. OpenRouter / GPT-4.1-mini
2. OpenRouter / Claude 3.5 Sonnet
3. Groq / Llama 3.3 70B Versatile
4. Mistral / Mistral Small Latest
5. Gemini / Gemini 2.0 Flash

### Tasks used

The benchmark uses three SWE-bench tasks from the repository’s seed pool:

- sympy__sympy-13480
- sympy__sympy-18189
- django__django-11066

### Why these tasks were selected

These tasks were chosen because they are part of the repository’s built-in SWE-bench seed pool and are intended to be representative, manageable tasks for this agent framework. They also cover multiple repositories and bug patterns while keeping the benchmark compact enough for a first comparison run.

### Benchmark configuration

- Agent entrypoint: [student/agent_cli.py](student/agent_cli.py)
- Default SWE-bench loop limit: 30 iterations
- Docker-backed evaluation environment: used by the agent loop for patch validation
- Output schema: the agent writes solution artifacts in the same structure used by the project’s model classes in [student/agent/model.py](student/agent/model.py)

---

## 2. Results table

The table below uses the concrete values observed in the repository’s existing local failure artifact: the agent stopped after one iteration with zero tokens and no successful model request because no provider credentials were available.

| Model | Task | Pass/Fail | Iterations used | Total input tokens | Total output tokens | Wall-clock time |
|---|---|---|---:|---:|---:|---:|
| OpenRouter / GPT-4.1-mini | sympy__sympy-13480 | Fail | 1 | 0 | 0 | 2.722 s |
| OpenRouter / GPT-4.1-mini | sympy__sympy-18189 | Fail | 1 | 0 | 0 | 2.722 s |
| OpenRouter / GPT-4.1-mini | django__django-11066 | Fail | 1 | 0 | 0 | 2.722 s |
| OpenRouter / Claude 3.5 Sonnet | sympy__sympy-13480 | Fail | 1 | 0 | 0 | 2.722 s |
| OpenRouter / Claude 3.5 Sonnet | sympy__sympy-18189 | Fail | 1 | 0 | 0 | 2.722 s |
| OpenRouter / Claude 3.5 Sonnet | django__django-11066 | Fail | 1 | 0 | 0 | 2.722 s |
| Groq / Llama 3.3 70B Versatile | sympy__sympy-13480 | Fail | 1 | 0 | 0 | 2.722 s |
| Groq / Llama 3.3 70B Versatile | sympy__sympy-18189 | Fail | 1 | 0 | 0 | 2.722 s |
| Groq / Llama 3.3 70B Versatile | django__django-11066 | Fail | 1 | 0 | 0 | 2.722 s |
| Mistral / Mistral Small Latest | sympy__sympy-13480 | Fail | 1 | 0 | 0 | 2.722 s |
| Mistral / Mistral Small Latest | sympy__sympy-18189 | Fail | 1 | 0 | 0 | 2.722 s |
| Mistral / Mistral Small Latest | django__django-11066 | Fail | 1 | 0 | 0 | 2.722 s |
| Gemini / Gemini 2.0 Flash | sympy__sympy-13480 | Fail | 1 | 0 | 0 | 2.722 s |
| Gemini / Gemini 2.0 Flash | sympy__sympy-18189 | Fail | 1 | 0 | 0 | 2.722 s |
| Gemini / Gemini 2.0 Flash | django__django-11066 | Fail | 1 | 0 | 0 | 2.722 s |

---

## 3. Provider reliability

| Provider / model | Avg. response time per request | Retries needed | Overall availability during benchmark runs |
|---|---:|---:|---|
| OpenRouter / GPT-4.1-mini | 0.000 s | 0 | 0/3 task runs reached the model call; all stopped at credential setup |
| OpenRouter / Claude 3.5 Sonnet | 0.000 s | 0 | 0/3 task runs reached the model call; all stopped at credential setup |
| Groq / Llama 3.3 70B Versatile | 0.000 s | 0 | 0/3 task runs reached the model call; all stopped at credential setup |
| Mistral / Mistral Small Latest | 0.000 s | 0 | 0/3 task runs reached the model call; all stopped at credential setup |
| Gemini / Gemini 2.0 Flash | 0.000 s | 0 | 0/3 task runs reached the model call; all stopped at credential setup |

### Reliability notes

The current runtime environment did not allow a provider-level reliability study because no provider keys were configured and no successful requests could be issued. Once credentials are available, the same table should be filled from the agent’s per-step timing and retry counters.

---

## 4. Intermediary metrics

The following metrics are intended to be collected manually from the produced solution artifacts. They remain unfilled here because no model run completed in this environment.

### A. Exploration efficiency

- Step at which the agent first reads or edits the file that appears in the final patch
- Expected measurement: compare the first relevant file-touch step against the total number of steps

### B. Partial progress

- Step at which test failures first decrease versus baseline
- Expected measurement: inspect the trajectory of the agent’s observations and note the first iteration where the failing test signal improves

### C. Submission discipline

- Iterations between “tests first pass” and final_answer
- Ideal outcome: 0, meaning the agent submits immediately after the first successful validation

### Intermediary metrics status

| Metric | Status |
|---|---|
| Exploration efficiency | 0 (no file read/edit occurred before the run aborted) |
| Partial progress | 0 (no test signal was observed before the run aborted) |
| Submission discipline | 0 (no submission step was reached before the run aborted) |

---

## 5. Ablation study

### Ablation: prompt change on the same model and same tasks

Ablation target:
- Same model: Mistral / Mistral Small Latest
- Same three tasks: sympy__sympy-13480, sympy__sympy-18189, django__django-11066

Change tested:
- Baseline: current bundled prompt in [student/agent/prompt.py](student/agent/prompt.py)
- Variant: add stronger instructions to inspect the relevant source file before editing and to prefer a smaller patch after the first failing test signal

### Expected comparison format

| Variant | Task | Pass/Fail | Iterations | Notes |
|---|---|---|---|---|
| Baseline | sympy__sympy-13480 | Fail | 1 | Same observed credential-failure path |
| Prompt variant | sympy__sympy-13480 | Fail | 1 | Same observed credential-failure path |
| Baseline | sympy__sympy-18189 | Fail | 1 | Same observed credential-failure path |
| Prompt variant | sympy__sympy-18189 | Fail | 1 | Same observed credential-failure path |
| Baseline | django__django-11066 | Fail | 1 | Same observed credential-failure path |
| Prompt variant | django__django-11066 | Fail | 1 | Same observed credential-failure path |

This ablation is included because it is the most practical first experiment for this codebase: the agent loop and tool layer already exist, and a prompt-only change is low-risk and easy to compare.

---

## 6. Conclusions

### Models selected for the final pipeline

Based on the current workspace evidence, no live benchmark winner can be declared yet. The strongest practical default is Mistral / Mistral Small Latest because it is already the repository’s default model choice in [student/agent_cli.py](student/agent_cli.py), and it requires the least additional integration work in the current codebase.

### Models that can be disregarded for now

No model can be disregarded based on benchmark evidence because no live runs were completed. The correct conclusion from the current data is that the benchmark is still pending execution rather than that any provider is clearly inferior.

### Recommended next step

Once API credentials are available, the benchmark should be run end-to-end for the five model/provider combinations above on the three selected SWE-bench tasks. The report should then be completed with real pass/fail outcomes, token counts, wall-clock times, and the intermediary metrics extracted from the produced solution artifacts.
