# AgentOps foundation

This directory adds an incremental AgentOps layer around the existing Kubernetes troubleshooting agent. It is a **foundation**, not a claim that the application is already production-certified.

## Included

- evaluation/: deterministic offline checks for known local diagnosis patterns.
- observability/: OpenTelemetry Collector, Jaeger, Prometheus, and Grafana local stack.
- security/: threat model, tool boundaries, and production guardrails.
- ../infra/terraform/eks/: opt-in EKS infrastructure scaffold.
- ../docs/agentops-production-readiness.md: operational readiness checklist.

## AgentOps measurements

Each completed POST /investigate request records aggregate OpenTelemetry metrics for request outcome, elapsed time, diagnosis source (llm, local_fallback, or not_run), and counts of evidence items by category. The diagnosis span includes the diagnosis source and a total evidence count.

Metrics intentionally exclude investigation IDs, cluster/context names, namespaces, raw logs, prompts, and secrets to avoid high-cardinality labels and accidental data disclosure. Evidence counts are counts of the known finding lists, not total Kubernetes objects in the cluster. Measurements export only when OTEL_EXPORTER_OTLP_ENDPOINT is configured; otherwise OpenTelemetry uses no-op instruments.

## Local workflow

1. Install backend dependencies: python -m pip install -r backend/requirements.txt.
2. Run backend tests: python -m pytest backend/tests -q.
3. Run deterministic evaluator: PYTHONPATH=backend python agentops/evaluation/run_eval.py.
4. Start the app and telemetry stack: docker compose -f docker-compose.yml -f agentops/observability/docker-compose.yml up --build.
5. Open Jaeger at http://localhost:16686 and Grafana at http://localhost:3001.

The telemetry override enables trace export through OTLP. Do not expose these local observability ports to the public internet.

## Current boundaries

- The agent remains recommendation-only; this change does not add autonomous cluster writes.
- The evaluator checks known local-rule cases, not general LLM quality or real-cluster recovery.
- Metrics are aggregate telemetry, not a durable per-investigation audit ledger or cost accounting.
- Terraform is opt-in infrastructure code. It does not create resources until you run Terraform yourself.
- Before a real production rollout, configure authentication/authorization, secret management, network controls, backups, alert routing, retention, and a tested rollback process.
