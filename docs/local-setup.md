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

```bash
docker compose up --build
```

The backend mounts `$HOME/.kube` (override with `KUBECONFIG_HOST_DIR`). If `config` is missing, the UI lists **demo clusters** so you can still click Investigate.

On WSL, Docker does not use `C:\Users\...\.kube\config` automatically. Copy it first:

```bash
mkdir -p ~/.kube
cp /mnt/c/Users/<YourWindowsUser>/.kube/config ~/.kube/config
docker compose up -d --force-recreate backend
```

Or point Compose at the Windows path in a `.env` file next to `docker-compose.yml`:

```bash
KUBECONFIG_HOST_DIR=/mnt/c/Users/<YourWindowsUser>/.kube
```

## Demo mode

If kubeconfig is missing, demo clusters are shown automatically:

- demo-crashloop
- demo-imagepull
- demo-oom
- demo-selector
- demo-healthy

You can also force this with `DEMO_MODE=true`.

## Failure scenarios (real cluster)

```bash
kubectl apply -f k8s/scenarios/namespace.yaml
kubectl apply -f k8s/scenarios/crashloop-missing-env.yaml
kubectl apply -f k8s/scenarios/imagepull-bad-tag.yaml
kubectl apply -f k8s/scenarios/oomkilled-low-memory.yaml
kubectl apply -f k8s/scenarios/service-selector-mismatch.yaml
```

Optional Ollama: set `LLM_PROVIDER=ollama` and run a local model. If Ollama is down, the heuristic engine still returns a diagnosis.
