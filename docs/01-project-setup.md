# Prompt 01 — project foundation

Run the skeleton app (no Kubernetes or AI logic yet):

```bash
docker compose up --build
```

- Frontend: http://localhost:3000
- Health: http://localhost:8000/health

Without Docker:

```bash
pip install -r backend/requirements.txt
cd backend && PYTHONPATH=. uvicorn app.main:app --reload --port 8000
```

```bash
cd frontend && npm install && npm run dev
```
