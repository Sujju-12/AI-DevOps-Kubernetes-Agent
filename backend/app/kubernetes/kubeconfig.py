from pathlib import Path

from app.core.config import get_settings


def is_kubeconfig_file(path: Path) -> bool:
    try:
        return path.is_file() and not path.is_dir()
    except OSError:
        return False


def kubeconfig_candidates() -> list[Path]:
    settings = get_settings()
    raw: list[str] = []
    kubeconfig_env = __import__("os").environ.get("KUBECONFIG", "")
    if kubeconfig_env:
        raw.extend(part for part in kubeconfig_env.split(":") if part)
    raw.append(settings.kubeconfig_path)
    raw.extend(
        [
            "/kube/config",
            str(Path.home() / ".kube" / "config"),
            "/root/.kube/config",
        ]
    )
    seen: set[str] = set()
    paths: list[Path] = []
    for item in raw:
        path = str(Path(item).expanduser())
        if path in seen:
            continue
        seen.add(path)
        paths.append(Path(path))
    return paths


def resolve_kubeconfig() -> Path | None:
    for path in kubeconfig_candidates():
        if is_kubeconfig_file(path):
            return path
    return None
