from pydantic import BaseModel, Field
from typing import List


class SandboxConfig(BaseModel):

    authorized_imports: List[str] = Field(default_factory=lambda: [
        "math", "re", "json", "itertools", "collections",
        "typing", "functools", "string", "random", "datetime",
    ])

    allowed_directories: List[str] = Field(default_factory=lambda: [
        "/tmp/agent", "testbed"
    ])

    max_execution_time_seconds: int = 30
    max_memory_mb: int = 512


def load_config(path: str | None = None) -> SandboxConfig:
    """Charge la config depuis un fichier JSON, ou renvoie la config par défaut."""
    if path is None:
        return SandboxConfig()

    import json
    with open(path, "r") as f:
        data = json.load(f)
    return SandboxConfig(**data)


# if __name__ == "__main__":
#     config = load_config()
#     print(config)
#     print("authorized_imports:", config.authorized_imports)
#     print("max_execution_time_seconds:", config.max_execution_time_seconds)
