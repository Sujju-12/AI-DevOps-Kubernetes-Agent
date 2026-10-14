# AI Kubernetes Troubleshooting Agent - High Level Design (HLD)

**Prompt 01–05:** `docker compose up --build` then open http://localhost:3000 (Supabase login + cluster picker). Click a kubeconfig cluster to investigate. See [docs/01-project-setup.md](docs/01-project-setup.md), [docs/02-investigation.md](docs/02-investigation.md), [docs/03-ai-reasoning.md](docs/03-ai-reasoning.md), [docs/04-dashboard.md](docs/04-dashboard.md), and [docs/05-e2e.md](docs/05-e2e.md). Failure fixtures: [k8s/scenarios/README.md](k8s/scenarios/README.md).

## AgentOps foundation (new)

This repository now includes an opt-in AgentOps foundation: OpenTelemetry tracing, a local Jaeger/Prometheus/Grafana stack, deterministic offline evaluation cases, security guardrails, a production-readiness roadmap, and an opt-in Terraform EKS scaffold.

- [AgentOps overview and local workflow](agentops/README.md)
- [Offline evaluator](agentops/evaluation/README.md)
- [Security boundaries and threat model](agentops/security/README.md)
- [Production-readiness checklist](docs/agentops-production-readiness.md)
- [Terraform EKS scaffold](infra/terraform/eks/README.md)

Run the deterministic local-rule evaluation with `PYTHONPATH=backend python agentops/evaluation/run_eval.py`. To start the application and local observability stack, set `GRAFANA_ADMIN_PASSWORD` in your environment and run `docker compose -f docker-compose.yml -f agentops/observability/docker-compose.yml up --build`. Jaeger is at http://localhost:16686, Prometheus at http://localhost:9090, and Grafana at http://localhost:3001.

Telemetry export is disabled unless an OTLP endpoint is configured. The new Terraform files do not provision infrastructure automatically. These resources are a foundation and do not by themselves certify the project as production-ready.

## Goal

Build an AI-powered Kubernetes troubleshooting platform that can:

- Investigate Kubernetes failures
- Analyze logs, events, and cluster state
- Identify root causes
- Suggest fixes
- Store investigation history
- Be deployed publicly as a real application

---

# High Level Architecture

```text
┌────────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster                     │
│                                                            │
│  Pods | Deployments | Services | Events | Logs            │
│                                                            │
│  This is where failures happen and evidence exists         │
└────────────────────────────────────────────────────────────┘
                              │
                              │ kubectl / Kubernetes API
                              ▼
┌────────────────────────────────────────────────────────────┐
│                  Investigation Layer                      │
│                                                            │
│ Responsibility:                                            │
│ - Connect to Kubernetes cluster                            │
│ - Collect troubleshooting signals                          │
│ - Gather debugging evidence                                │
│                                                            │
│ Components:                                                │
│                                                            │
│  1. Pod Inspector                                          │
│     - Get pod health                                       │
│     - Detect CrashLoopBackOff                              │
│     - Detect Pending/Error states                          │
│                                                            │
│  2. Logs Collector                                         │
│     - Read pod logs                                        │
│     - Capture container errors                             
│
##}
