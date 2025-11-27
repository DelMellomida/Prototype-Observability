import os
from fastapi import FastAPI, HTTPException
import structlog

os.environ.setdefault("OTEL_SERVICE_NAME", "SampleServicePython")
os.environ.setdefault("ENVIRONMENT", "Production")
os.environ.setdefault("SERVICE_VERSION", "1.0.0")
os.environ.setdefault("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")

from app.observability import init_observability, instrument_app, TelemetryHelper
from app.middleware.observability_middleware import ObservabilityMiddleware

init_observability()

app = FastAPI(title="SampleServicePython", version="1.0.0")

app.add_middleware(ObservabilityMiddleware)

telemetry = TelemetryHelper()

try:
    instrument_app(app)
except Exception as e:
    print(f"Warning: Could not instrument app: {e}")


@app.get("/")
def read_root():
    """Root endpoint"""
    return {"message": "Hello World", "service": "SampleServicePython"}


@app.get("/health")
def health():
    """Health check endpoint"""
    return {"status": "healthy", "service": "SampleServicePython"}


@app.get("/weatherforecast/days/{days}")
def get_weather_forecast(days: int):
    """Get weather forecast for specified number of days (max 5)"""
    import random
    from datetime import datetime, timedelta
    from opentelemetry import trace
    
    if days > 5:
        log = structlog.get_logger("main.controllers.WeatherForecastController")
        
        span = trace.get_current_span()
        ctx = span.get_span_context() if span else None
        trace_id = format(ctx.trace_id, "032x") if ctx and ctx.trace_id != 0 else None
        span_id = format(ctx.span_id, "016x") if ctx and ctx.span_id != 0 else None
        
        log.error(
            f"Validation failed in WeatherForecastController.GetByDays: days={days}",
            traceId=trace_id,
            spanId=span_id,
            Days=days,
            Action="GetByDays",
            Controller="WeatherForecastController",
            RequestPath=f"/weatherforecast/days/{days}",
            error={
                "type": "ValidationException",
                "message": f"Days must be 5 or less. Requested: {days}",
                "code": "WEATHER_001"
            },
            context={
                "days": days,
                "maxAllowed": 5
            },
            message_template_text="Validation failed in {Controller}.{Action}: days={Days}"
        )
        raise HTTPException(status_code=400, detail=f"Days must be 5 or less. Requested: {days}")
    
    with telemetry.start_business_span("GenerateWeatherForecast", {"days": days}):
        forecasts = []
        summaries = ["Freezing", "Bracing", "Chilly", "Cool", "Mild", "Warm", "Balmy", "Hot", "Sweltering", "Scorching"]
        
        for i in range(days):
            date = datetime.now() + timedelta(days=i)
            temp_c = random.randint(-20, 55)
            forecasts.append({
                "date": date.isoformat(),
                "temperatureC": temp_c,
                "temperatureF": 32 + int(temp_c * 1.8),
                "summary": random.choice(summaries)
            })
        
        return forecasts


@app.get("/business")
def business():
    """Example business operation endpoint"""
    import time
    
    with telemetry.start_business_span("ExampleOperation", {"operation": "business.example"}):
        time.sleep(0.01)
        return {
            "result": "ok",
            "operation": "business.example",
            "service": "SampleServicePython"
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)