from pathlib import Path

from app.core.config import get_settings
from app.kubernetes.clusters import demo_scenario_for_context, list_clusters


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
    monkeypatch.delenv("KUBECONFIG", raising=False)
    monkeypatch.setenv("KUBECONFIG_PATH", str(kubeconfig))
    monkeypatch.setenv("HOME", str(tmp_path / "empty-home"))
    get_settings.cache_clear()
    result = list_clusters()
    assert result.current_context == "kind-dev"
    names = {item.name for item in result.contexts}
    assert names == {"kind-dev", "k3d-local"}
    current = next(item for item in result.contexts if item.is_current)
    assert current.server == "https://127.0.0.1:6443"
    get_settings.cache_clear()


def test_missing_kubeconfig_lists_demo_clusters(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("KUBECONFIG", raising=False)
    monkeypatch.setenv("KUBECONFIG_PATH", str(tmp_path / "does-not-exist"))
    monkeypatch.setenv("HOME", str(tmp_path / "empty-home"))
    get_settings.cache_clear()
    result = list_clusters()
    names = {item.name for item in result.contexts}
    assert "demo-crashloop" in names
    assert "demo-imagepull" in names
    assert result.current_context == "demo-crashloop"
    assert result.warning
    get_settings.cache_clear()


def test_directory_kubeconfig_lists_demo_clusters(tmp_path: Path, monkeypatch) -> None:
    directory = tmp_path / "config"
    directory.mkdir()
    monkeypatch.delenv("KUBECONFIG", raising=False)
    monkeypatch.setenv("KUBECONFIG_PATH", str(directory))
    monkeypatch.setenv("HOME", str(tmp_path / "empty-home"))
    get_settings.cache_clear()
    result = list_clusters()
    assert any(item.name.startswith("demo-") for item in result.contexts)
    get_settings.cache_clear()


def test_demo_scenario_for_context() -> None:
    assert demo_scenario_for_context("demo-oom") == "oom"
    assert demo_scenario_for_context("kind-dev") is None
