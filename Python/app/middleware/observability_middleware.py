from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from opentelemetry import trace
from opentelemetry.trace.status import Status, StatusCode
import structlog
import time
import uuid
import socket

log = structlog.get_logger()


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enrich spans with HTTP semantic attributes and log requests
    in a format similar to .NET's observability middleware.
    """

    def __init__(self, app):
        super().__init__(app)
        self.hostname = socket.gethostname()

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())
        start = time.time()

        # Extract request details
        method = request.method
        scheme = request.url.scheme
        host = request.url.hostname or ""
        port = request.url.port
        path = request.url.path
        query_string = str(request.url.query) if request.url.query else ""
        
        # Get client info
        client_host = ""
        if request.client:
            client_host = getattr(request.client, "host", "")
        
        connection_id = request.headers.get("Connection-Id", request_id[:16])
        
        # Get protocol version
        protocol = "HTTP/1.1"
        http_version = request.scope.get("http_version", "1.1")
        protocol = f"HTTP/{http_version}"

        # Build host string
        host_with_port = f"{host}:{port}" if port and port not in [80, 443] else host
        query_part = f"?{query_string}" if query_string else ""

        try:
            # Process request - this is where FastAPI instrumentation creates the span
            response = await call_next(request)

            # NOW get the span context AFTER the request is processed
            span = trace.get_current_span()
            trace_id = ""
            span_id = ""
            parent_span_id = "0000000000000000"
            
            if span is not None:
                try:
                    ctx = span.get_span_context()
                    if ctx and ctx.trace_id and ctx.trace_id != 0:
                        trace_id = format(ctx.trace_id, "032x")
                        span_id = format(ctx.span_id, "016x")
                        print(f"DEBUG: Captured trace context - TraceId: {trace_id}, SpanId: {span_id}", flush=True)
                    else:
                        print(f"DEBUG: Span context is invalid or zero", flush=True)
                except Exception as e:
                    print(f"DEBUG: Error getting span context: {e}", flush=True)
            else:
                print(f"DEBUG: No active span found", flush=True)

            # Calculate duration
            elapsed_ms = round((time.time() - start) * 1000, 4)

            # Get response details
            status_code = response.status_code
            content_type = response.headers.get("content-type", "")
            content_length = response.headers.get("content-length", "")

            # Update span with additional attributes
            if span is not None:
                try:
                    span.set_attribute("http.method", method)
                    span.set_attribute("http.status_code", status_code)
                    span.set_attribute("StatusCode", status_code)
                    span.set_attribute("ElapsedMilliseconds", elapsed_ms)
                    span.set_attribute("ContentType", content_type)
                    span.set_attribute("ContentLength", content_length)
                    span.set_attribute("RequestId", request_id)
                    span.set_attribute("ConnectionId", connection_id)
                    
                    if status_code >= 500:
                        span.set_status(Status(StatusCode.ERROR, f"HTTP {status_code}"))
                except Exception as e:
                    print(f"Error updating span: {e}", flush=True)

            # Build detailed finish message
            finish_message = f"Request finished {protocol} {method} {scheme}://{host_with_port}{path}{query_part} - {status_code} {content_length} {content_type} {elapsed_ms}ms"

            # Log completion
            log_method = log.info
            if status_code >= 500:
                log_method = log.error
            elif status_code >= 400:
                log_method = log.warning

            try:
                log_method(
                    finish_message,
                    ElapsedMilliseconds=elapsed_ms,
                    StatusCode=status_code,
                    ContentType=content_type,
                    ContentLength=content_length,
                    Protocol=protocol,
                    Method=method,
                    Scheme=scheme,
                    Host=host_with_port,
                    PathBase="",
                    Path=path,
                    QueryString=query_part,
                    RequestId=request_id,
                    ConnectionId=connection_id,
                    RequestPath=path,
                    TraceId=trace_id,
                    SpanId=span_id,
                    ParentId=parent_span_id,
                    message_template_text="Request finished {Protocol} {Method} {Scheme}://{Host}{PathBase}{Path}{QueryString} - {StatusCode} {ContentLength} {ContentType} {ElapsedMilliseconds}ms",
                )
            except Exception as e:
                print(f"Error logging request finish: {e}", flush=True)

            return response

        except Exception as exc:
            elapsed_ms = round((time.time() - start) * 1000, 4)
            
            # Record exception on span and get trace context
            span = trace.get_current_span()
            trace_id = ""
            span_id = ""
            parent_span_id = "0000000000000000"
            
            if span is not None:
                try:
                    span.record_exception(exc)
                    span.set_status(Status(StatusCode.ERROR, str(exc)))
                    span.set_attribute("exception.type", type(exc).__name__)
                    span.set_attribute("exception.message", str(exc))
                    
                    ctx = span.get_span_context()
                    if ctx and ctx.trace_id and ctx.trace_id != 0:
                        trace_id = format(ctx.trace_id, "032x")
                        span_id = format(ctx.span_id, "016x")
                except Exception:
                    pass

            error_message = f"Request failed {protocol} {method} {scheme}://{host_with_port}{path}{query_part} - {type(exc).__name__}: {str(exc)}"

            try:
                log.error(
                    error_message,
                    exception=str(exc),
                    exception_type=type(exc).__name__,
                    ElapsedMilliseconds=elapsed_ms,
                    Protocol=protocol,
                    Method=method,
                    Scheme=scheme,
                    Host=host_with_port,
                    Path=path,
                    PathBase="",
                    QueryString=query_part,
                    RequestId=request_id,
                    ConnectionId=connection_id,
                    RequestPath=path,
                    TraceId=trace_id,
                    SpanId=span_id,
                    ParentId=parent_span_id,
                    trace_id=trace_id,
                    span_id=span_id,
                    parent_span_id=parent_span_id,
                    message_template_text="Request failed {Protocol} {Method} {Scheme}://{Host}{PathBase}{Path}{QueryString} - {exception_type}: {exception}",
                )
            except Exception:
                pass

            raise