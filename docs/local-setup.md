# Local development

This application is designed to run entirely on your machine. It does not use InsForge, OpenRouter, or any other cloud control plane.

## Architecture

- Next.js dashboard on port 3000
- FastAPI orchestrator on port 8000
- kubectl investigation against contexts in your local kubeconfig
- Local SQLite for login and investigation history
- Heuristic Senior SRE engine (optional local Ollama)

## Run without Docker

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cd backend && PYTHONPATH=. uvicorn app.main:app --reload --port 8000
```

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000

Default login: `admin` / `admin`

## Run with Docker Compose (still local)

The backend container reads kubeconfig from `/kube/config`, which Compose bind-mounts from:

```text
$KUBECONFIG_HOST_PATH   or   $HOME/.kube/config
```

On WSL, Docker does **not** automatically use `C:\Users\...\ .kube\config`. Create or copy the file into Linux first:

```bash
ls -la ~/.kube/config
# if missing:
mkdir -p ~/.kube
cp /mnt/c/Users/<YourWindowsUser>/.kube/config ~/.kube/config
```

Then start (or recreate) the stack:

```bash
docker compose up --build
```

If the file lives somewhere else, create a `.env` next to `docker-compose.yml`:

```bash
KUBECONFIG_HOST_PATH=/mnt/c/Users/<YourWindowsUser>/.kube/config
```

Click a listed cluster, then **Investigate Cluster**.

## Demo mode (no live cluster)

```bash
DEMO_MODE=true PYTHONPATH=backend uvicorn app.main:app --app-dir backend --port 8000
```

## Failure scenarios

```bash
kubectl apply -f k8s/scenarios/namespace.yaml
kubectl apply -f k8s/scenarios/crashloop-missing-env.yaml
kubectl apply -f k8s/scenarios/imagepull-bad-tag.yaml
kubectl apply -f k8s/scenarios/oomkilled-low-memory.yaml
kubectl apply -f k8s/scenarios/service-selector-mismatch.yaml
```

Optional Ollama: set `LLM_PROVIDER=ollama` and run a local model. If Ollama is down, the heuristic engine still returns a diagnosis.
