# Prompt 03 — AI Kubernetes Agent

`POST /investigate` still collects kubectl evidence (Prompt 02), then asks a Senior Kubernetes SRE prompt to find a root cause.

## Response shape

```json
{
  "status": "success",
  "investigation": { "pods": {}, "logs": {}, "events": {}, "deployments": {}, "network": {}, "probes": {} },
  "diagnosis": {
    "root_cause": "DATABASE_URL missing",
    "explanation": "Application cannot connect to DB.",
    "fix": "Add missing environment variable.",
    "kubectl_command": "kubectl edit deployment payment-service",
    "prevention": "Fail fast when required env vars are unset.",
    "confidence": 92,
    "confidence_reason": "Pod CrashLoopBackOff and logs agree."
  }
}
```

If the cluster cannot be reached, `diagnosis` is omitted and `status` is `"error"` (same as Prompt 02).

## OpenRouter key

Do **not** hardcode secrets. The backend reads:

```env
OPENROUTER_API_KEY=
OPENROUTER_MODEL=openai/gpt-4o-mini
```

Store the key in a local `.env` or in Supabase project secrets, then export it. Docker Compose already forwards `OPENROUTER_API_KEY` / `OPENROUTER_MODEL`.

If the key is missing or OpenRouter fails, the analyzer correlates the same evidence locally so the API still returns a diagnosis.

## Modules

| File | Role |
|------|------|
| `app/ai/prompt.py` | Senior SRE system prompt + evidence sections |
| `app/ai/llm.py` | OpenRouter via HTTPX, timeout + retries |
| `app/ai/analyzer.py` | Root-cause reasoning (LLM, then local fallback) |
| `app/ai/fixes.py` | Practical kubectl commands |
| `app/ai/confidence.py` | 0–100 confidence from evidence signals |
