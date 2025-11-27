import sys
import inspect


def instrument_app(app):
    """Instrument FastAPI application with OpenTelemetry."""
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.requests import RequestsInstrumentor
        from opentelemetry.instrumentation.logging import LoggingInstrumentor
    except Exception:
        raise

    try:
        sig = inspect.signature(FastAPIInstrumentor().instrument_app)
        params = sig.parameters
        
        instrument_kwargs = {}
        
        if 'server_request_hook' in params:
            def server_request_hook(span, scope):
                try:
                    method = scope.get("method")
                    path = scope.get("path")
                    if method:
                        span.set_attribute("http.method", method)
                    if path:
                        span.set_attribute("http.target", path)
                except Exception:
                    pass
            instrument_kwargs['server_request_hook'] = server_request_hook
        
        if 'client_request_hook' in params:
            instrument_kwargs['client_request_hook'] = None
        
        if 'client_response_hook' in params:
            instrument_kwargs['client_response_hook'] = None
        
        print(f"Instrumenting FastAPI with params: {list(instrument_kwargs.keys())}", file=sys.stderr)
        
        FastAPIInstrumentor().instrument_app(app, **instrument_kwargs)
        print("✓ FastAPI instrumented successfully", file=sys.stderr)
    except Exception as e:
        print(f"Warning: FastAPI instrumentation failed: {e}", file=sys.stderr)
        print("Falling back to basic instrumentation", file=sys.stderr)
        try:
            FastAPIInstrumentor().instrument_app(app)
            print("✓ FastAPI instrumented (basic mode)", file=sys.stderr)
        except Exception as e2:
            print(f"✗ Failed to instrument FastAPI: {e2}", file=sys.stderr)

    try:
        RequestsInstrumentor().instrument()
        print("✓ Requests library instrumented", file=sys.stderr)
    except Exception as e:
        print(f"Warning: Requests instrumentation failed: {e}", file=sys.stderr)
    
    try:
        LoggingInstrumentor().instrument(set_logging_format=True)
        print("✓ Logging instrumented", file=sys.stderr)
    except Exception as e:
        print(f"Warning: Logging instrumentation failed: {e}", file=sys.stderr)