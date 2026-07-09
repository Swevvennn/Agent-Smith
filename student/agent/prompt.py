def build_system_prompt_mbpp(manual):
    systeme_prompt = f"""You are a coding agent for MBPP.

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
    - These are public test make sure you answer is strong, hidden test can
        occur
    - IMPORTANT: as soon as run_tests returns {{"passed": true}}, you MUST
      call final_answer in the VERY NEXT code block. Do not repeat the
      solution, do not re-test. Just call final_answer.
    - final_answer must be lowercase and inside a ```python block, like:
      ```python
      final_answer("def add(a, b):\\n    return a + b")
      ```
    - If execution fails, inspect the observation and
          adapt the next code block.
    - If no valid code block is produced,
          rewrite with exactly one ```python block.
    - If a block is malformed, fix it in the next turn.
    - If the sandbox reports a timeout, partial output, or an error, use that
      observation directly and do not guess what happened.

    Example:
    Thought: I will write the function and verify it with the provided tests.
    Code:
    ```python
    solution = "def add(a, b):\\n    return a + b"
    result = run_tests(
        solution_code=solution,
        test_list=["assert add(2, 3) == 5"],
    )
    print(result)
    ```

    When tests pass:
    Thought: The solution is validated, so I can finish.
    Code:
    ```python
    final_answer("def add(a, b):\\n    return a + b")
    ```
    """
    return systeme_prompt


def build_system_prompt_swebench(manual):
    systeme_prompt = f"""You are a coding agent that fixes real bugs
        in real repositories (SWE-bench).

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
    - Start by exploring the codebase: use search_code,
      search_function_or_class_definition_in_code,
      read_file to locate the code relevant to the issue described below.
    - Make the smallest change that fixes the issue, using edit_file.
    - Verify your fix by calling run_tests() before finishing.
    - IMPORTANT: once run_tests() passes,
      you must retrieve your patch by calling
    get_patch(), and pass its result directly to final_answer. Do not write the
    patch yourself, do not guess the diff format - always use get_patch().
    - final_answer must be inside a ```python block, like:
    ```python
    patch = get_patch()
    final_answer(patch)
    ```
    - If execution fails, inspect the observation and
        adapt the next code block.
    - If no valid code block is produced,
        rewrite with exactly one ```python block.
    - If the sandbox reports a timeout, partial output, or an error, use that
    observation directly and do not guess what happened.

    Example:
    Thought: I will locate the function mentioned in the issue.
    Code:
    ```python
    result = search_function_or_class_definition_in_code("some_function")
    print(result)
    ```

    When the fix is verified:
    Thought: run_tests() passed, so I can retrieve my patch and finish.
    Code:
    ```python
    patch = get_patch()
    final_answer(patch)
    ```

    IMPORTANT OUTPUT FORMAT:
    Your entire response must be a single plain text Python code block.

    Do not return JSON.
    Do not use message blocks.
    Do not provide explanations before or after the code.
    Do not include reasoning content.
    """
    return systeme_prompt


def build_user_prompt_mbpp(task):
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

    ## Public tests
    {test_list}

    Instructions:
    - Implement exactly the requested function.
    - Respect the function signature.
    - Only call `final_answer(...)` after `run_tests` reports success.
    """
    return user_prompt


def build_user_prompt_swebench(task):
    user_prompt = f"""
        Solve the following SWEBENCH task.

        ## Task
        {task["problem_statement"]}

        ## Docker image
        {task["docker_image"]}

        ## Bash script to run inside the container to evaluate the patch
        {task["eval_script"]}

        ## Optional hints about the issue
        {task["hints_text"]}

        ## Repository name (default="")
        {task["repo"]}

        Instructions:
        - Implement exactly the correct patch
        - Respect the problem statement task
        - Call (patch = get_patch(), final_answer(patch))
          only when the problem is solved
    """
    return user_prompt
