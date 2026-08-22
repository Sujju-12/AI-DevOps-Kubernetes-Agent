from dataclasses import dataclass
import os
import subprocess

from loguru import logger

from app.core.config import get_settings
from app.kubernetes.kubeconfig import resolve_kubeconfig

MISSING_KUBECONFIG = (
    "kubeconfig file not found. The backend will use local demo investigations "
    "until you mount a real ~/.kube/config."
)


@dataclass
class KubectlResult:
    success: bool
    stdout: str
    stderr: str
    command: str
    returncode: int

    def parsed_json(self) -> dict | list | None:
        if not self.success or not self.stdout.strip():
            return None
        import json

        try:
            return json.loads(self.stdout)
        except json.JSONDecodeError:
            return None


def run_kubectl(
    args: list[str],
    context: str | None = None,
    timeout: int | None = None,
) -> KubectlResult:
    """Safely execute kubectl and return structured output."""
    settings = get_settings()
    kubeconfig = resolve_kubeconfig()
    env = os.environ.copy()
    if not kubeconfig:
        env.pop("KUBECONFIG", None)
        return KubectlResult(
            success=False,
            stdout="",
            stderr=MISSING_KUBECONFIG,
            command="kubectl (skipped: no kubeconfig)",
            returncode=2,
        )

    command = ["kubectl", "--kubeconfig", str(kubeconfig)]
    env["KUBECONFIG"] = str(kubeconfig)
    if context:
        command += ["--context", context]
    command += args

    logger.info("Running kubectl: {}", " ".join(command))
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
            logger.warning("kubectl failed ({}) {}", result.returncode, result.stderr.strip())
        return result
    except FileNotFoundError:
        return KubectlResult(
            success=False,
            stdout="",
            stderr="kubectl is not installed on this machine.",
            command=" ".join(command),
            returncode=127,
        )
    except subprocess.TimeoutExpired:
        return KubectlResult(
            success=False,
            stdout="",
            stderr="kubectl timed out while talking to the cluster.",
            command=" ".join(command),
            returncode=124,
        )
