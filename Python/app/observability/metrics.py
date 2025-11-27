import os
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from .config import _PROM_AVAILABLE


def init_metrics(service_name: str = "SampleServicePython", otlp_endpoint: str = "http://localhost:4317"):
    """Initialize OpenTelemetry metrics."""
    service_name = service_name or os.getenv("OTEL_SERVICE_NAME", "SampleServicePython")
    otlp_endpoint = otlp_endpoint or os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", os.getenv("OpenTelemetry__OtlpEndpoint", "http://localhost:4317"))
    
    resource = Resource.create({
        "service.name": service_name,
    })

    try:
        if _PROM_AVAILABLE:
            from opentelemetry.exporter.prometheus import PrometheusMetricReader
            reader = PrometheusMetricReader()
            meter_provider = MeterProvider(resource=resource, metric_readers=[reader])
        else:
            exporter = OTLPMetricExporter(endpoint=otlp_endpoint)
            reader = PeriodicExportingMetricReader(exporter)
            meter_provider = MeterProvider(resource=resource, metric_readers=[reader])
        
        from opentelemetry import metrics
        metrics.set_meter_provider(meter_provider)
        return meter_provider
    except Exception:
        return None