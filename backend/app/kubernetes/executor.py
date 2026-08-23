"""Safely run kubectl via subprocess and return structured output."""

from dataclasses import dataclass
import os
import subprocess
from pathlib import Path

from loguru import logger

from app.core.config import get_settings


@dataclass
class KubectlResult:
    success: bool
    stdout: str
    stderr: str
    command: str
    returncode: int

    def parsed_json(self):
        if not self.success or not self.stdout.strip():
            return None
        import json

        try:
            return json.loads(self.stdout)
        except json.JSONDecodeError:
            return None


def run_kubectl(args: list[str], context: str | None = None, timeout: int | None = None) -> KubectlResult:
    settings = get_settings()
    command = ["kubectl"]
    kubeconfig = Path(settings.kubeconfig_path).expanduser()
    if kubeconfig.is_file():
        command += ["--kubeconfig", str(kubeconfig)]
    if context:
        command += ["--context", context]
    command += args

    logger.info("Running kubectl: {}", " ".join(command))
    env = os.environ.copy()
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout or settings.kubectl_timeout_seconds,
            check=False,
            env=env,
        )
        result = KubectlResult(
            success=completed.returncode == 0,
            stdout=completed.stdout or "",
            stderr=completed.stderr or "",
            command=" ".join(command),
            returncode=completed.returncode,
        )
        if not result.success:
            logger.warning("kubectl failed ({}): {}", result.returncode, result.stderr.strip())
        return result
    except FileNotFoundError:
        logger.error("kubectl is not installed")
        return KubectlResult(False, "", "kubectl is not installed.", " ".join(command), 127)
    except subprocess.TimeoutExpired:
        logger.error("kubectl timed out: {}", " ".join(command))
        return KubectlResult(False, "", "kubectl timed out.", " ".join(command), 124)
