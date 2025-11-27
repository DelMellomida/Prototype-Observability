import time
import uuid
import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from opentelemetry import trace


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """Enhanced middleware for structured logging with OpenTelemetry integration."""
    
    def _extract_user_context(self, request: Request) -> dict:
        """Extract user context from request (customize based on your auth implementation)."""
        user_context = {}
        
        # Example: Extract from JWT token or session
        # This is a placeholder - implement based on your authentication method
        auth_header = request.headers.get("authorization", "")
        if auth_header:
            # TODO: Decode JWT and extract user information
            # user_context["id"] = decoded_token.get("sub")
            # user_context["tenantId"] = decoded_token.get("tenant_id")
            # user_context["role"] = decoded_token.get("role")
            pass
        
        # Example: Extract from custom headers
        user_id = request.headers.get("x-user-id")
        tenant_id = request.headers.get("x-tenant-id")
        
        if user_id:
            user_context["id"] = user_id
        if tenant_id:
            user_context["tenantId"] = tenant_id
            
        return user_context if user_context else None
    
    def _get_client_country(self, ip: str) -> str:
        """Get country from IP address (placeholder - requires GeoIP database)."""
        # TODO: Implement GeoIP lookup if needed
        # Example using geoip2:
        # try:
        #     import geoip2.database
        #     reader = geoip2.database.Reader('/path/to/GeoLite2-Country.mmdb')
        #     response = reader.country(ip)
        #     return response.country.iso_code
        # except:
        #     return None
        return None
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        log = structlog.get_logger("app.middleware.observability_middleware")
        
        # Extract trace context
        span = trace.get_current_span()
        ctx = span.get_span_context() if span else None
        
        trace_id = format(ctx.trace_id, "032x") if ctx and ctx.trace_id != 0 else "00000000000000000000000000000000"
        span_id = format(ctx.span_id, "016x") if ctx and ctx.span_id != 0 else "0000000000000000"
        
        # Extract client information
        client_host = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "")
        
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        
        # Extract user context (if authenticated)
        user_context = self._extract_user_context(request)
        
        # Build client object
        client_info = {"ip": client_host}
        country = self._get_client_country(client_host)
        if country:
            client_info["country"] = country
        
        # Build HTTP object
        http_info = {
            "method": request.method,
            "path": str(request.url.path),
            "scheme": request.url.scheme,
            "host": request.url.hostname,
            "userAgent": user_agent,
        }
        
        # Add query string if present
        if request.url.query:
            http_info["queryString"] = str(request.url.query)
        
        # Build base log context
        log_context = {
            "traceId": trace_id,
            "spanId": span_id,
            "http": http_info,
            "client": client_info,
            "requestId": request_id,
            "Protocol": f"HTTP/{request.scope.get('http_version', '1.1')}",
        }
        
        # Add user context if available
        if user_context:
            log_context["user"] = user_context
        
        # Log request started
        log.info("Request started", **log_context)
        
        try:
            response = await call_next(request)
            duration_ms = (time.time() - start_time) * 1000
            
            # Get response details
            status_code = response.status_code
            content_length = response.headers.get("content-length", "0")
            content_type = response.headers.get("content-type", "")
            
            # Determine log level based on status code
            if status_code >= 500:
                log_method = log.error
            elif status_code >= 400:
                log_method = log.warning
            else:
                log_method = log.info
            
            # Update HTTP info with response details
            http_info_complete = http_info.copy()
            http_info_complete.update({
                "statusCode": status_code,
                "duration": duration_ms,
            })
            
            # Build complete log context
            complete_context = {
                "traceId": trace_id,
                "spanId": span_id,
                "http": http_info_complete,
                "client": client_info,
                "requestId": request_id,
                "Protocol": f"HTTP/{request.scope.get('http_version', '1.1')}",
                "StatusCode": status_code,
                "ContentLength": content_length,
                "ContentType": content_type,
                "ElapsedMilliseconds": duration_ms,
                "RequestPath": str(request.url.path),
                "message_template_text": "Request finished {Protocol} {Method} {Scheme}://{Host}{Path} - {StatusCode} {ContentLength} {ContentType} {ElapsedMilliseconds}ms",
            }
            
            # Add user context if available
            if user_context:
                complete_context["user"] = user_context
            
            # Log request finished
            log_method(
                f"Request finished {request.scope.get('http_version', 'HTTP/1.1')} {request.method} "
                f"{request.url.scheme}://{request.url.hostname}{request.url.path} - "
                f"{status_code} {content_length} {content_type} {duration_ms:.3f}ms",
                **complete_context
            )
            
            return response
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            # Update HTTP info with duration
            http_info_error = http_info.copy()
            http_info_error["duration"] = duration_ms
            
            # Build error log context
            error_context = {
                "traceId": trace_id,
                "spanId": span_id,
                "http": http_info_error,
                "client": client_info,
                "error": {
                    "type": type(e).__name__,
                    "message": str(e),
                },
                "requestId": request_id,
                "ElapsedMilliseconds": duration_ms,
                "RequestPath": str(request.url.path),
            }
            
            # Add user context if available
            if user_context:
                error_context["user"] = user_context
            
            # Log exception
            log.error(
                f"Request failed: {str(e)}",
                **error_context
            )
            raise