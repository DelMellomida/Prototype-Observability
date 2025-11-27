import os
import sys
from typing import Optional
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.sampling import ParentBased, TraceIdRatioBased, ALWAYS_ON


def init_tracing(service_name: Optional[str] = None, otlp_endpoint: Optional[str] = None, sampling_ratio: Optional[float] = None):
    """Initialize OpenTelemetry tracing."""
    service_name = service_name or os.getenv("OTEL_SERVICE_NAME", "SampleServicePython")
    otlp_endpoint = otlp_endpoint or os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", os.getenv("OpenTelemetry__OtlpEndpoint", "http://localhost:4317"))
    
    resource = Resource.create({
        "service.name": service_name,
        "service.version": os.getenv("SERVICE_VERSION", "1.0.0"),
        "deployment.environment": os.getenv("ENVIRONMENT", "development"),
    })

    sampler = None
    try:
        if sampling_ratio is None:
            sampling_ratio = 1.0 if os.getenv("ENVIRONMENT") == "development" else 0.1

        if sampling_ratio >= 1.0:
            sampler = ALWAYS_ON
        else:
            sampler = ParentBased(TraceIdRatioBased(sampling_ratio))
    except Exception:
        sampler = ALWAYS_ON

    print(f"Initializing tracing: service={service_name}, endpoint={otlp_endpoint}, sampling={sampling_ratio}", file=sys.stderr)
    print(f"Using sampler: {sampler}", file=sys.stderr)
    
    provider = TracerProvider(resource=resource, sampler=sampler)
    exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
    span_processor = BatchSpanProcessor(exporter)
    provider.add_span_processor(span_processor)
    trace.set_tracer_provider(provider)
    
    print("✓ Tracing initialized successfully", file=sys.stderr)
    
    try:
        tracer = trace.get_tracer(__name__)
        with tracer.start_as_current_span("test_span") as test_span:
            ctx = test_span.get_span_context()
            if ctx and ctx.trace_id != 0:
                print(f"✓ Test span created successfully with TraceId: {format(ctx.trace_id, '032x')}", file=sys.stderr)
            else:
                print("⚠ Warning: Test span has invalid trace_id", file=sys.stderr)
    except Exception as e:
        print(f"⚠ Warning: Could not create test span: {e}", file=sys.stderr)
    
    return provider