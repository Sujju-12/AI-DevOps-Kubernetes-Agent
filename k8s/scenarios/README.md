# Intentional Kubernetes failures (Prompt 05)

These manifests create small, isolated problems so you can test the agent against a real cluster.

Apply **one scenario at a time**, wait for the pod/service to fail, then click that cluster in the dashboard (or pass the kubeconfig context to `POST /investigate`).

```bash
kubectl apply -f k8s/scenarios/01-crashloop-missing-env.yaml
kubectl apply -f k8s/scenarios/02-imagepull-bad-tag.yaml
kubectl apply -f k8s/scenarios/03-oomkilled-low-memory.yaml
kubectl apply -f k8s/scenarios/04-service-selector-mismatch.yaml
```

| File | Failure | What the agent should report |
| --- | --- | --- |
| `01-crashloop-missing-env.yaml` | CrashLoopBackOff | Missing env var (`DATABASE_URL`); add Secret/ConfigMap value |
| `02-imagepull-bad-tag.yaml` | ImagePullBackOff | Invalid image tag; update the Deployment image |
| `03-oomkilled-low-memory.yaml` | OOMKilled | Container exceeded memory limit; raise requests/limits |
| `04-service-selector-mismatch.yaml` | No endpoints | Service selector does not match pod labels; update the selector |

Cleanup:

```bash
kubectl delete ns demo-crashloop demo-imagepull demo-oom demo-selector
```

Optional namespace filter in the UI: `demo-crashloop`, `demo-imagepull`, `demo-oom`, or `demo-selector`.
