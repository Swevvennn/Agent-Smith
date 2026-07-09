import subprocess


class DockerManager:
    """Manage the lifecycle of a SWE-bench Docker container."""

    def __init__(self, image: str, container_name: str = "swebench_agent"):
        self.image = image
        self.container_name = container_name

    def start(self) -> None:
        """Pull the image and start the container (kept alive with sleep)."""
        self.cleanup()

        # Pull the image
        print(f"Pulling Docker image {self.image} ...")
        subprocess.run(
            ["docker", "pull", self.image],
            check=True,
            capture_output=True,
        )

        # Start the container in the background
        print(f"Starting container {self.container_name} ...")
        subprocess.run(
            [
                "docker", "run", "-d",
                "--name", self.container_name,
                self.image,
                "sleep", "infinity",
            ],
            check=True,
            capture_output=True,
        )

    def exec(self, command: str, workdir: str = "/testbed") -> tuple[str, str, int]:
        """Run a shell command inside the container.

        Returns (stdout, stderr, exit_code).
        """
        result = subprocess.run(
            [
                "docker", "exec", "-w", workdir,
                self.container_name,
                "bash", "-c", command,
            ],
            capture_output=True,
            text=True,
        )
        return result.stdout, result.stderr, result.returncode

    def cleanup(self) -> None:
        """Remove the container (force, ignore errors if it doesn't exist)."""
        subprocess.run(
            ["docker", "rm", "-f", self.container_name],
            capture_output=True,
        )
