import sys
import logging
import structlog
from typing import Optional
from opentelemetry import trace
from .config import (
    _LOGS_AVAILABLE, 
    SeverityNumber, 
    LogRecord,
    get_otel_logger_provider
)


def _add_trace_fields(logger, method_name, event_dict):
    """Add trace_id and span_id to log events."""
    span = trace.get_current_span()
    ctx = getattr(span, "get_span_context", lambda: None)()
    if ctx is not None:
        try:
            trace_id = ctx.trace_id
            span_id = ctx.span_id
            if trace_id and trace_id != 0:
                event_dict["trace_id"] = format(trace_id, "032x")
                event_dict["TraceId"] = format(trace_id, "032x")
            if span_id and span_id != 0:
                event_dict["span_id"] = format(span_id, "016x")
                event_dict["SpanId"] = format(span_id, "016x")
        except Exception:
            pass
    return event_dict


def _otel_log_forwarder(logger, method_name, event_dict):
    """Forward structlog events to OpenTelemetry."""
    otel_logger_provider = get_otel_logger_provider()
    
    if not _LOGS_AVAILABLE or otel_logger_provider is None:
        return event_dict
    
    try:
        logger_name = event_dict.get("logger", "app.middleware.observability_middleware")
        otel_logger = otel_logger_provider.get_logger(logger_name)
        
        level = event_dict.get("level", "info").lower()
        severity_map = {
            "debug": SeverityNumber.DEBUG,
            "info": SeverityNumber.INFO,
            "warning": SeverityNumber.WARN,
            "error": SeverityNumber.ERROR,
            "critical": SeverityNumber.FATAL,
        }
        severity = severity_map.get(level, SeverityNumber.INFO)
        
        event = event_dict.get("event", "")
        
        span = trace.get_current_span()
        trace_id = None
        span_id = None
        trace_flags = None
        
        if span:
            ctx = span.get_span_context()
            if ctx and ctx.trace_id != 0:
                trace_id = ctx.trace_id
                span_id = ctx.span_id
                trace_flags = ctx.trace_flags
        
        if not trace_id and "TraceId" in event_dict:
            try:
                trace_id_str = event_dict["TraceId"]
                if trace_id_str and trace_id_str != "":
                    trace_id = int(trace_id_str, 16)
            except Exception:
                pass
        
        if not span_id and "SpanId" in event_dict:
            try:
                span_id_str = event_dict["SpanId"]
                if span_id_str and span_id_str != "":
                    span_id = int(span_id_str, 16)
            except Exception:
                pass
        
        excluded_keys = {"event", "level", "timestamp", "logger"}
        attributes = {}
        
        for k, v in event_dict.items():
            if k not in excluded_keys:
                if k in ["TraceId", "trace_id"] and trace_id:
                    attributes[k] = format(trace_id, "032x")
                elif k in ["SpanId", "span_id"] and span_id:
                    attributes[k] = format(span_id, "016x")
                else:
                    attributes[k] = str(v) if not isinstance(v, (str, int, float, bool, type(None))) else v
        
        if trace_id and "trace_id" not in attributes:
            attributes["trace_id"] = format(trace_id, "032x")
        if span_id and "span_id" not in attributes:
            attributes["span_id"] = format(span_id, "016x")
        
        otel_logger.emit(
            LogRecord(
                timestamp=None,
                trace_id=trace_id,
                span_id=span_id,
                trace_flags=trace_flags,
                severity_text=level.upper(),
                severity_number=severity,
                body=event,
                attributes=attributes,
            )
        )
    except Exception as e:
        print(f"Error forwarding log to OTEL: {e}", file=sys.stderr)
    
    return event_dict


def init_logging(service_name: Optional[str] = None, environment: str = "development"):
    """Initialize structured logging with OpenTelemetry integration."""
    logging.basicConfig(stream=sys.stdout, format="%(message)s", level=logging.INFO)

    processors = [
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        _add_trace_fields,
        _otel_log_forwarder,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(sort_keys=True),
    ]

    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    log = structlog.get_logger()
    
    if service_name:
        log = log.bind(service_name=service_name, environment=environment)
    else:
        log = log.bind(environment=environment)
    
    return log