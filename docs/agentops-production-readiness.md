# AgentOps production-readiness roadmap

## Definition

Production readiness means more than deploying the UI and API to EKS. The agent needs reliable execution, observable runs, measurable quality, least-privilege access, controlled changes, recovery procedures, and clear operating ownership.

## Phase 1 — reliable diagnosis

- [ ] Validate the four scenario manifests in an isolated local cluster.
- [ ] Keep an offline regression dataset with known causes and expected signals.
- [ ] Add unit/integration tests for collection failures, timeouts, malformed model output, and fallback behavior.
- [ ] Bound log size, command duration, model retries, request size, and investigation duration.
- [ ] Ensure every run has a correlation ID and structured outcome.

## Phase 2 — AgentOps

- [ ] Enable OpenTelemetry OTLP export only in environments with a configured collector.
- [ ] Trace API requests and investigation spans; add model and tool spans without capturing sensitive payloads by default.
- [ ] Track success/error rate, latency, fallback rate, model cost/tokens when provider usage data is available, and evaluation quality.
- [ ] Run deterministic evaluation in CI.
- [ ] Add reviewed LLM evaluation sets and regression thresholds before changing prompts or models.
- [ ] Set trace retention and access controls.

## Phase 3 — security and controlled operations

- [ ] Use a dedicated read-only Kubernetes service identity, scoped to required namespaces/resources.
- [ ] Never use a human kubeconfig or cluster-admin credential for a shared agent.
- [ ] Add authentication and authorization to every investigation API and enforce tenant ownership in history operations.
- [ ] Redact secrets before model calls and telemetry export.
- [ ] Threat-model prompt injection from logs, events, annotations, and user input.
- [ ] Add a tool allowlist and server-side validation.
- [ ] Keep remediation recommendation-only initially; require human approval and audit logs for changes.
- [ ] Add rate limits, egress controls, secret management, and abuse/cost limits.

## Phase 4 — deployment and operations

- [ ] Provision infrastructure through reviewed Terraform plans.
- [ ] Use immutable image tags, image scanning, dependency scanning, SBOMs, and signed artifacts where practical.
- [ ] Deploy with Helm/Argo CD and environment promotion; no automatic Terraform apply from pull requests.
- [ ] Add readiness/liveness probes, resource requests/limits, disruption budgets, network policy, and pod security controls.
- [ ] Configure backup/restore, database migrations, disaster recovery objectives, and rollback procedures.
- [ ] Define alerts, on-call ownership, incident runbooks, and a monthly cost review.
- [ ] Load-test expected concurrency and test partial failures of the LLM provider, collector, database, and Kubernetes API.

## Success criteria

A release is not production-ready until its critical workflows are tested, evaluation quality meets an agreed threshold, sensitive data handling is reviewed, permissions are least-privilege, recovery has been exercised, and operators can detect and respond to failures. This checklist is intentionally not marked complete by adding configuration files alone.
