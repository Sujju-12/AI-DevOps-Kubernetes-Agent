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


def resolve_kubeconfig() -> Path | None:
    settings = get_settings()
    candidates = []
    env = os.environ.get("KUBECONFIG", "")
    if env:
        candidates.extend(env.split(":"))
    candidates.extend(
        [
            settings.kubeconfig_path,
            "/kube/config",
            str(Path.home() / ".kube" / "config"),
        ]
    )
    seen: set[str] = set()
    for raw in candidates:
        path = Path(raw).expanduser()
        key = str(path)
        if key in seen:
            continue
        seen.add(key)
        try:
            if path.is_file():
                return path
        except OSError:
            continue
    return None


def run_kubectl(args: list[str], context: str | None = None, timeout: int | None = None) -> KubectlResult:
    settings = get_settings()
    kubeconfig = resolve_kubeconfig()
    env = os.environ.copy()
    if not kubeconfig:
        env.pop("KUBECONFIG", None)
        return KubectlResult(
            success=False,
            stdout="",
            stderr="kubeconfig file not found",
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
            logger.warning("kubectl failed: {}", result.stderr.strip())
        return result
    except FileNotFoundError:
        return KubectlResult(False, "", "kubectl is not installed on this machine.", " ".join(command), 127)
    except subprocess.TimeoutExpired:
        return KubectlResult(False, "", "kubectl timed out while talking to the cluster.", " ".join(command), 124)
