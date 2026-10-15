"""Optional OpenTelemetry tracing and metrics for the API and agent workflow.

Telemetry is disabled unless OTEL_EXPORTER_OTLP_ENDPOINT is configured.
Do not attach raw prompts, Kubernetes logs, kubeconfig contents, or secrets to spans.
"""
import os

from fastapi import FastAPI
from loguru import logger
from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

_resource_attributes = {
    "service.name": os.getenv("OTEL_SERVICE_NAME", "ai-kubernetes-agent"),
    "deployment.environment": os.getenv("APP_ENV", "development"),
}


def configure_telemetry(app: FastAPI) -> None:
    """Instrument FastAPI and export traces/metrics when an OTLP endpoint is configured."""
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "").strip()
    if not endpoint:
        logger.info("OpenTelemetry export disabled; set OTEL_EXPORTER_OTLP_ENDPOINT to enable it")
        return

    resource = Resource.create(_resource_attributes)
    trace_provider = TracerProvider(resource=resource)
    trace_provider.add_span_processor(
        BatchSpanProcessor(
            OTLPSpanExporter(endpoint=endpoint, insecure=endpoint.startswith("http://"))
        )
    )
    trace.set_tracer_provider(trace_provider)

    metric_reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(endpoint=endpoint, insecure=endpoint.startswith("http://")),
        export_interval_millis=15000,
    )
    metrics.set_meter_provider(MeterProvider(resource=resource, metric_readers=[metric_reader]))
    FastAPIInstrumentor.instrument_app(app, tracer_provider=trace_provider)
    logger.info("OpenTelemetry tracing and metrics enabled")
