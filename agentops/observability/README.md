# Local observability stack

Run from the repository root after setting a non-default Grafana password:

```bash
export GRAFANA_ADMIN_PASSWORD='change-this-local-password'
docker compose -f docker-compose.yml -f agentops/observability/docker-compose.yml up --build
```

- Jaeger UI: http://localhost:16686
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001

The backend exports FastAPI request spans plus explicit evidence-collection and diagnosis spans over OTLP when `OTEL_EXPORTER_OTLP_ENDPOINT` is set. The Collector exports traces to Jaeger and exposes received OpenTelemetry metrics to Prometheus.

This is a local development stack. The Collector's debug exporter can print span metadata; do not send secrets, full prompts, raw Kubernetes logs, or other sensitive data as span attributes. For production, secure all endpoints, use persistent storage and a retention policy, configure TLS/authentication for telemetry transport, and add alert rules and dashboards appropriate to the service SLOs.
