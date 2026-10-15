# Agent security and production guardrails

## Current capability boundary

The existing agent gathers evidence with `kubectl` and recommends fixes. Keep it read-only by default. Do not add model-controlled shell execution or unrestricted Kubernetes writes.

## Minimum controls before production

- Use a dedicated Kubernetes identity with namespace-scoped, read-only RBAC for investigation.
- Never mount a developer's personal kubeconfig into a shared or internet-facing service.
- Store provider credentials in a secret manager; do not commit `.env`, tokens, kubeconfigs, or service-role keys.
- Treat pod logs, events, annotations, issue descriptions, and retrieved documents as untrusted data. They may contain prompt-injection instructions.
- Do not send secrets or full raw logs to the model by default. Redact tokens, credentials, and personal data before model calls and trace export.
- Apply request authentication, authorization, rate limits, timeouts, and per-tenant data isolation.
- Use a tool allowlist and validate every tool argument on the server side.
- Require human approval for any action that changes a cluster, IAM, networking, secrets, or production workload.
- Prefer a proposed Git change / pull request plus CI policy checks over direct production mutation.
- Record actor, target cluster, namespace, action proposal, approval, outcome, and correlation ID in an audit trail.
- Add retention limits and access controls to traces, investigation history, and exported artifacts.

## Remediation policy stages

1. **Read-only:** collect evidence and recommend a fix.
2. **Propose-only:** create a patch or pull request, without applying it.
3. **Approved execution:** a trusted service executes a narrowly defined, reviewed action after an authenticated approval.
4. **Never:** allow the LLM to construct arbitrary shell commands and execute them with cluster-admin credentials.

## Threats to test

- Prompt injection inside pod logs or Kubernetes annotations.
- Cross-tenant access to investigation history.
- A forged or stale approval.
- Malicious cluster/context names passed to subprocess commands.
- Oversized logs, hung kubectl calls, repeated model retries, and cost exhaustion.
- Secrets appearing in logs, prompts, traces, error messages, or CI artifacts.
