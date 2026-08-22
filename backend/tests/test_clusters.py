from pathlib import Path

from app.kubernetes.clusters import list_clusters
from app.core.config import get_settings


def test_list_clusters_from_kubeconfig(tmp_path: Path, monkeypatch) -> None:
    kubeconfig = tmp_path / "config"
    kubeconfig.write_text(
        """
apiVersion: v1
kind: Config
current-context: kind-dev
clusters:
  - name: kind-dev
    cluster:
      server: https://127.0.0.1:6443
  - name: k3d-local
    cluster:
      server: https://127.0.0.1:6550
contexts:
  - name: kind-dev
    context:
      cluster: kind-dev
      user: kind-dev
      namespace: default
  - name: k3d-local
    context:
      cluster: k3d-local
      user: k3d-local
users:
  - name: kind-dev
  - name: k3d-local
"""
    )
    monkeypatch.setenv("KUBECONFIG_PATH", str(kubeconfig))
    get_settings.cache_clear()
    result = list_clusters()
    assert result.current_context == "kind-dev"
    names = {item.name for item in result.contexts}
    assert names == {"kind-dev", "k3d-local"}
    current = next(item for item in result.contexts if item.is_current)
    assert current.server == "https://127.0.0.1:6443"
    get_settings.cache_clear()


def test_missing_kubeconfig_includes_path(tmp_path: Path, monkeypatch) -> None:
    missing = tmp_path / "does-not-exist"
    monkeypatch.setenv("KUBECONFIG_PATH", str(missing))
    get_settings.cache_clear()
    result = list_clusters()
    assert result.contexts == []
    assert str(missing) in (result.warning or "")
    get_settings.cache_clear()
