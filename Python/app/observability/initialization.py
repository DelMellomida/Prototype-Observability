import sys
from typing import Optional
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from opentelemetry.propagate import set_global_textmap
from .config import get_service_config, get_sampling_ratio
from .tracing import init_tracing
from .logs import init_logs
from .logging import init_logging
from .metrics import init_metrics
from .instrumentation import instrument_app


def init_observability(service_name: Optional[str] = None):
    """Initialize all observability components in correct order."""
    config = get_service_config()
    
    service_name = service_name or config["service_name"]
    otlp = config["otlp_endpoint"]
    environment = config["environment"]
    sampling_ratio = get_sampling_ratio(environment, config["sampling_ratio_env"])
    
    print(f"Environment: {environment}", file=sys.stderr)
    print(f"Sampling ratio: {sampling_ratio}", file=sys.stderr)

    try:
        set_global_textmap(TraceContextTextMapPropagator())
        print("✓ W3C trace context propagation set", file=sys.stderr)
    except Exception as e:
        print(f"Warning: Could not set trace propagation: {e}", file=sys.stderr)

    init_tracing(service_name=service_name, otlp_endpoint=otlp, sampling_ratio=sampling_ratio)
    init_logs(service_name=service_name, otlp_endpoint=otlp)
    log = init_logging(service_name=service_name, environment=environment)
    init_metrics(service_name=service_name, otlp_endpoint=otlp)

    try:
        log.info("Observability initialized", 
                service_name=service_name, 
                otlp_endpoint=otlp, 
                sampling_ratio=sampling_ratio,
                environment=environment)
    except Exception:
        pass