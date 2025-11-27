from contextlib import contextmanager
from typing import Optional
from opentelemetry import trace
from opentelemetry.trace.status import Status, StatusCode


class TelemetryHelper:
    """Helper to start business-level spans using the global tracer."""

    def __init__(self, service_name: str = "SampleServicePython"):
        self._tracer = trace.get_tracer(service_name)

    @contextmanager
    def start_business_span(self, span_name: str, attributes: Optional[dict] = None):
        """Start a business-level span with optional attributes."""
        with self._tracer.start_as_current_span(f"business.{span_name}") as span:
            if attributes:
                for k, v in attributes.items():
                    try:
                        span.set_attribute(k, str(v))
                    except Exception:
                        pass
            try:
                yield span
            except Exception as exc:
                try:
                    span.record_exception(exc)
                    span.set_status(Status(StatusCode.ERROR, str(exc)))
                except Exception:
                    pass
                raise