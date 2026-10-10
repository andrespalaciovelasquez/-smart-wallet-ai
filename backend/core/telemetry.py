"""Configuración centralizada de Observabilidad con OpenTelemetry puro (Tracing + Metrics)"""

from fastapi import FastAPI, Response
from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
import prometheus_client

from backend.core.config import settings


def setup_telemetry(app: FastAPI) -> None:
    """Configura OpenTelemetry para Tracing (Tempo vía OTLP gRPC) y Metrics (Prometheus)"""
    resource = Resource.create(
        {
            "service.name": settings.PROJECT_NAME,
            "deployment.environment": settings.APP_ENV,
        }
    )

    # Tracing Distribuido: TracerProvider exportando a Tempo en puerto 4317
    tracer_provider = TracerProvider(resource=resource)
    otlp_exporter = OTLPSpanExporter(
        endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT,
        insecure=True,
    )
    tracer_provider.add_span_processor(
        BatchSpanProcessor(otlp_exporter, schedule_delay_millis=1000)
    )
    trace.set_tracer_provider(tracer_provider)

    # Métricas: MeterProvider exportando en formato de Prometheus
    prometheus_reader = PrometheusMetricReader()
    meter_provider = MeterProvider(resource=resource, metric_readers=[prometheus_reader])
    metrics.set_meter_provider(meter_provider)

    # Instrumentar FastAPI automáticamente (mide cada request, ruta y latencia)
    FastAPIInstrumentor.instrument_app(
        app,
        tracer_provider=tracer_provider,
        meter_provider=meter_provider,
        excluded_urls="health,metrics,docs,openapi.json,redoc",
    )

    from backend.core.database import engine
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
    from openinference.instrumentation.openai import OpenAIInstrumentor

    # Instrumentar OpenAI (LLM calls) de forma limpia
    OpenAIInstrumentor().instrument(tracer_provider=tracer_provider)
    
    # Instrumentar SQLAlchemy (DB calls) que sí respeta contextvars
    SQLAlchemyInstrumentor().instrument(
        engine=engine.sync_engine,
        tracer_provider=tracer_provider
    )

    # Exponer endpoint estándar /metrics para que Prometheus lo scrapee
    @app.get("/metrics", tags=["Observability"], include_in_schema=False)
    def metrics_endpoint() -> Response:
        return Response(
            content=prometheus_client.generate_latest(),
            media_type=prometheus_client.CONTENT_TYPE_LATEST,
        )