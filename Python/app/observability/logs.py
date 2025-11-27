import os
import sys
from typing import Optional
from opentelemetry.sdk.resources import Resource
from .config import (
    _LOGS_AVAILABLE,
    LoggerProvider,
    OTLPLogExporter,
    BatchLogRecordProcessor,
    set_otel_logger_provider
)


def init_logs(service_name: Optional[str] = None, otlp_endpoint: Optional[str] = None):
    """Initialize OpenTelemetry logs."""
    if not _LOGS_AVAILABLE:
        print("Warning: OpenTelemetry Logs SDK not available. Logs will only go to stdout.", file=sys.stderr)
        return None

    try:
        service_name = service_name or os.getenv("OTEL_SERVICE_NAME", "SampleServicePython")
        otlp_endpoint = otlp_endpoint or os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", os.getenv("OpenTelemetry__OtlpEndpoint", "http://localhost:4317"))
        
        resource = Resource.create({
            "service.name": service_name,
            "service.version": "1.0.0",
            "deployment.environment": os.getenv("ENVIRONMENT", "development"),
        })
        
        print(f"Initializing OTEL Logs: service={service_name}, endpoint={otlp_endpoint}", file=sys.stderr)
        
        provider = LoggerProvider(resource=resource)
        exporter = OTLPLogExporter(endpoint=otlp_endpoint)
        processor = BatchLogRecordProcessor(exporter)
        provider.add_log_record_processor(processor)
        
        set_otel_logger_provider(provider)
        
        from opentelemetry import _logs as logs_api
        logs_api.set_logger_provider(provider)
        
        print("✓ OTEL Logs initialized successfully", file=sys.stderr)
        return provider
    except Exception as e:
        import traceback
        print(f"✗ Failed to initialize OTEL Logs: {e}", file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
        return None