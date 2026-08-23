# Prompt 02 — Kubernetes Investigation Layer

The FastAPI backend now collects cluster evidence **before** any AI reasoning.

## Endpoint

```http
POST /investigate
Content-Type: application/json
```

Optional body:

```json
{
  "context": "kind-kind",
  "namespace": "default"
}
```

Success:

```json
{
  "status": "success",
  "investigation": {
    "pods": {},
    "logs": {},
    "events": {},
    "deployments": {},
    "network": {}
  }
}
```

If `kubectl` is missing or the cluster cannot be reached, the API still returns HTTP 200 with `"status": "error"` and a friendly `message` — not a 500 crash.

## How it works

All Kubernetes access uses **`kubectl` via subprocess** (`backend/app/kubernetes/executor.py`). There is no Kubernetes Python SDK.

Inspectors:

| Module | Role |
|--------|------|
| `pods.py` | Unhealthy pods (CrashLoopBackOff, ImagePullBackOff, Pending, Error, OOMKilled, ContainerCreating) |
| `logs.py` | Short log excerpts for those pods (exceptions, connection/env/image/startup) |
| `events.py` | FailedScheduling, BackOff, FailedMount, FailedPull, ErrImagePull, Unhealthy |
| `deployments.py` | Replica and condition health |
| `network.py` | Services, selector vs pod labels, missing endpoints, DNS-related events |

`backend/app/services/investigation.py` runs them in that order and returns one payload.

## Local kubeconfig (WSL / Docker)

Set `KUBECONFIG_PATH` to a **file** that exists.

Typical WSL issue: `~/.kube/config` is empty because the real file is on Windows, for example:

```text
/mnt/c/Users/<WindowsUser>/.kube/config
```

Docker Compose mounts `${KUBECONFIG_HOST_DIR:-$HOME/.kube}` to `/kube` and sets `KUBECONFIG_PATH=/kube/config`.
