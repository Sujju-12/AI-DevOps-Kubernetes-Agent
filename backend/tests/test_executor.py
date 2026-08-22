from app.core.config import get_settings
from app.kubernetes.executor import run_kubectl


def test_run_kubectl_skips_when_kubeconfig_missing(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("KUBECONFIG", "/kube/config")
    monkeypatch.setenv("KUBECONFIG_PATH", str(tmp_path / "missing"))
    monkeypatch.setenv("HOME", str(tmp_path / "empty-home"))
    get_settings.cache_clear()
    result = run_kubectl(["get", "pods"])
    assert result.success is False
    assert "kubeconfig" in result.stderr.lower()
    assert "skipped" in result.command
    get_settings.cache_clear()
