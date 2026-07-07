from datetime import datetime

from pydantic import BaseModel, Field
from typing import List, Optional


class MBPPTaskInput(BaseModel):
    """Input for MBPP task evaluation."""
    task_id: int
    task_definition: str
    function_definition: str
    test_imports: List[str] = Field(default_factory=list)
    test_list: List[str] = Field(default_factory=list)


class SWEBenchTaskInput(BaseModel):
    """Input for a SWE-bench task, provided by the moulinette.
    Your agent receives this and must produce a git patch that fixes
    the issue.
    """
    instance_id: str = Field(..., description="SWE-bench instance identifier (e.g., 'sympy__sympy-23534')")
    problem_statement: str = Field(..., description="The GitHub issue description, what needs to be fixed")
    docker_image: str = Field(..., description="Full Docker image name to pull (e.g., 'swebench/sweb.eval.x86_64. sympy_1776_sympy-23534:latest')")
    eval_script: str = Field(..., description="Bash script to run inside the container to evaluate the patch")
    hints_text: str = Field(default="", description="Optional hints about the issue (may be empty)")
    repo: str = Field(default="", description="Repository name (e.g., 'sympy/sympy')")


class StepMetrics(BaseModel):
    """Metrics for a single agent step."""
    step: int
    input_tokens: int
    output_tokens: int
    request_time_ms: float
    api_url: str
    model_name: str
    llm_output: str
    sandbox_input: str
    sandbox_output: str
    retries: int
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class SolutionOutput(BaseModel):
    """Output from student solution - this is what students must
    produce."""
    task_id: str
    benchmark: str
    success: bool
    solution: str
    system_prompt: str
    iterations: int
    total_requests: int
    total_input_tokens: int
    total_output_tokens: int
    total_time_seconds: float
    steps: List["StepMetrics"] = Field(default_factory=list)
    error: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())