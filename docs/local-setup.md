# Local setup (from prompts 01–05)

This app follows the in-repo prompts. InsForge is replaced with local SQLite login/history so you can run without a cloud backend. OpenRouter is optional (`OPENROUTER_API_KEY`); otherwise a local SRE engine diagnoses failures.

## Run with Docker Compose

```bash
docker compose up --build
```

- UI: http://localhost:3000
- API health: http://localhost:8000/health
- Login: `admin` / `admin`

If `~/.kube/config` is missing, the UI lists **demo clusters**. On WSL, copy Windows kubeconfig first:

```bash
mkdir -p ~/.kube
cp /mnt/c/Users/<You>/.kube/config ~/.kube/config
docker compose up -d --force-recreate --build backend
```

Or set `KUBECONFIG_HOST_DIR` in a `.env` file next to `docker-compose.yml`.

## Run without Docker

```bash
pip install -r backend/requirements.txt
cd backend && PYTHONPATH=. uvicorn app.main:app --reload --port 8000
```

```bash
cd frontend && npm install && npm run dev
```

## Failure scenarios

```bash
kubectl apply -f k8s/scenarios/namespace.yaml
kubectl apply -f k8s/scenarios/crashloop-missing-env.yaml
kubectl apply -f k8s/scenarios/imagepull-bad-tag.yaml
kubectl apply -f k8s/scenarios/oomkilled-low-memory.yaml
kubectl apply -f k8s/scenarios/service-selector-mismatch.yaml
```
