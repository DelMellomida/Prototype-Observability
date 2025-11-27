import os
import sys

try:
    from opentelemetry.sdk._logs import LoggerProvider, LogRecord
    from opentelemetry._logs import SeverityNumber
    from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
    from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
    _LOGS_AVAILABLE = True
    print("✓ OpenTelemetry Logs SDK loaded successfully", file=sys.stderr)
except Exception as e:
    print(f"✗ Failed to import logs SDK: {e}", file=sys.stderr)
    _LOGS_AVAILABLE = False
    BatchLogRecordProcessor = None
    OTLPLogExporter = None
    LoggerProvider = None
    LogRecord = None
    SeverityNumber = None

try:
    from opentelemetry.exporter.prometheus import PrometheusMetricReader
    _PROM_AVAILABLE = True
except Exception:
    _PROM_AVAILABLE = False

_otel_logger_provider = None


def get_otel_logger_provider():
    """Get the global OTEL logger provider."""
    return _otel_logger_provider


def set_otel_logger_provider(provider):
    """Set the global OTEL logger provider."""
    global _otel_logger_provider
    _otel_logger_provider = provider


def get_service_config():
    """Get service configuration from environment variables."""
    return {
        "service_name": os.getenv("OTEL_SERVICE_NAME", "SampleServicePython"),
        "otlp_endpoint": os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", os.getenv("OpenTelemetry__OtlpEndpoint", "http://localhost:4317")),
        "environment": os.getenv("ENVIRONMENT", "development"),
        "sampling_ratio_env": os.getenv("OPEN_TELEMETRY_SAMPLING_RATIO", os.getenv("OpenTelemetry__SamplingRatio")),
    }


def get_sampling_ratio(environment: str, sampling_ratio_env: str = None) -> float:
    """Calculate sampling ratio based on environment."""
    try:
        if sampling_ratio_env is not None:
            return float(sampling_ratio_env)
        elif environment.lower() in ["development", "dev", "local"]:
            return 1.0
        else:
            return 0.1
    except Exception:
        return 1.0