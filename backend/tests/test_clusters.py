from pathlib import Path

from app.core.config import get_settings
from app.kubernetes.clusters import list_clusters


def test_list_clusters(tmp_path: Path, monkeypatch) -> None:
    kubeconfig = tmp_path / "config"
    kubeconfig.write_text(
        """
apiVersion: v1
kind: Config
current-context: kind-dev
clusters:
  - name: kind-dev
    cluster: {server: https://127.0.0.1:6443}
contexts:
  - name: kind-dev
    context: {cluster: kind-dev, user: kind-dev}
  - name: k3d-local
    context: {cluster: k3d-local, user: k3d-local}
users:
  - name: kind-dev
"""
    )
    monkeypatch.delenv("KUBECONFIG", raising=False)
    monkeypatch.setenv("KUBECONFIG_PATH", str(kubeconfig))
    monkeypatch.setenv("HOME", str(tmp_path / "empty"))
    get_settings.cache_clear()
    result = list_clusters()
    assert {item.name for item in result.contexts} == {"kind-dev", "k3d-local"}
    get_settings.cache_clear()


def test_missing_kubeconfig_demo_clusters(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("KUBECONFIG", raising=False)
    monkeypatch.setenv("KUBECONFIG_PATH", str(tmp_path / "missing"))
    monkeypatch.setenv("HOME", str(tmp_path / "empty"))
    get_settings.cache_clear()
    result = list_clusters()
    assert any(item.name.startswith("demo-") for item in result.contexts)
    get_settings.cache_clear()
