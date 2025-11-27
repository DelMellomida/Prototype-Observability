# Unified Logging & Monitoring Standard - Prototype

## 📋 Overview

This prototype demonstrates a **unified observability implementation** across multiple technology stacks (.NET and Python) following our organization's Logging & Monitoring Standard. It provides:

- **Consistent audit trails** for compliance
- **End-to-end distributed tracing** with W3C Trace Context
- **Structured JSON logging** with OpenTelemetry integration
- **Centralized monitoring** via SigNoz
- **Rapid incident response** through correlated logs, traces, and metrics

### Key Features

✅ **Trace-Centric Architecture** - Every request generates a unique Trace ID that propagates across services  
✅ **Structured Logging** - All logs are in JSON format with consistent metadata  
✅ **OpenTelemetry Standard** - Industry-standard instrumentation across all stacks  
✅ **Automatic Correlation** - Logs, metrics, and traces linked via Trace ID + Span ID  
✅ **Privacy by Design** - Automatic redaction of sensitive data (PII, passwords, tokens)  
✅ **Performance Monitoring** - Golden Signals (Latency, Traffic, Errors, Saturation)

## 🏗️ Architecture

```
Application (.NET/Python)
    ↓
OpenTelemetry SDK (Auto-instrumentation + Manual Spans)
    ↓
OpenTelemetry Collector (receivers → processors → exporters)
    ↓
SigNoz Cloud (Unified Logs, Traces, Metrics)
    ↓
Dashboards & Alerts
```

## 🚀 How to Run

### Prerequisites

- Docker Desktop (for OpenTelemetry Collector)
- .NET 8.0 SDK (for .NET sample)
- Python 3.9+ (for Python sample)
- PowerShell (for running scripts)
- SigNoz Cloud account (or self-hosted instance)

### Step 0: Setup SigNoz Cloud (For Testing)

For your own testing, sign up for **SigNoz Cloud** (30 days free trial):

1. **Sign up for SigNoz Cloud:**
   - Visit [https://signoz.io/teams/](https://signoz.io/teams/)
   - Create a free account (no credit card required)
   - Select your preferred region (US, EU, or India)

2. **Get your ingestion key:**
   - Log in to your SigNoz Cloud account
   - Navigate to **Settings** → **Ingestion Settings**
   - Under **Data Sources**, select **OpenTelemetry Collector**
   - Copy your `SIGNOZ_INGESTION_KEY` (looks like: `signoz-xxxxx-xxxxx-xxxxx`)
   - Note your ingestion endpoint (e.g., `ingest.us.signoz.cloud:443`)

3. **Configure your collector:**
   ```bash
   # In the config/ directory
   cd config
   
   # Copy the example environment file
   cp collector.env.example collector.env
   
   # Edit collector.env and add your values
   ```

   **Example `collector.env` file:**
   ```bash
   SIGNOZ_INGESTION_KEY=your-signoz-ingestion-key-here
   OTEL_SERVICE_NAME=your-service-name
   HOSTNAME=your-hostname
   ```

   **Important:** 
   - Replace `your-signoz-ingestion-key-here` with the actual key from SigNoz Cloud
   - The ingestion endpoint is already configured in `otel-collector-config.yaml` as `ingest.us.signoz.cloud:443`
   - For EU region, change it to `ingest.eu.signoz.cloud:443`
   - For India region, change it to `ingest.in.signoz.cloud:443`

> **Note:** If you're using self-hosted SigNoz, update the exporter endpoints in `otel-collector-config.yaml` to point to your local instance (e.g., `localhost:4317`) and set `insecure: true`

### Step 1: Configure Environment Variables

Before running, set your SigNoz endpoint and credentials:

**For .NET:**
Edit `NET/Sample/appsettings.Development.json`:
```json
{
  "OpenTelemetry": {
    "OtlpEndpoint": "http://localhost:4317",
    "ServiceName": "SampleServiceNET"
  }
}
```

**For Python:**
Edit `main.py` or set environment variables:
```bash
export OTEL_SERVICE_NAME="SampleServicePython"
export OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4317"
export ENVIRONMENT="Development"
```

### Step 2: Start OpenTelemetry Collector

The collector receives telemetry data from your applications and forwards it to SigNoz.

```bash
cd config
./run-collector.ps1
```

**Verify the collector is running:**
```bash
docker ps
# You should see otel-collector container running on ports 4317 (gRPC) and 4318 (HTTP)
```

**Check collector health:**
```bash
curl http://localhost:13133
# Should return health check status
```

### Step 3: Run Your Application

#### Option A: .NET Service

```bash
cd NET/Sample
dotnet restore
dotnet run --launch-profile https
```

The service will start on `https://localhost:7001` and `http://localhost:5255`

**Test endpoints:**
```bash
# API check
curl http://localhost:5255/weatherforecast

# Get weather forecast (valid)
curl http://localhost:5255/weatherforecast/days/3

# Trigger validation error (for error log testing)
curl http://localhost:5255/weatherforecast/days/7
```

#### Option B: Python Service

```bash
cd Python

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate.ps1  # Windows PowerShell
# OR
source venv/bin/activate    # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run the application
uvicorn main:app --reload
```

The service will start on `http://localhost:8000`

**Test endpoints:**
```bash
# Health check
curl http://localhost:8000/health

# Get weather forecast (valid)
curl http://localhost:8000/weatherforecast/days/3

# Trigger validation error (for error log testing)
curl http://localhost:8000/weatherforecast/days/7

# Business operation (with custom span)
curl http://localhost:8000/business
```

## 📊 How to View Logs & Traces

### OpenTelemetry Collector (Local Debugging)

**View collector logs:**
```bash
docker logs -f otel-collector
```

**Monitor collector metrics:**
```bash
# Prometheus metrics endpoint
curl http://localhost:8888/metrics
```

### SigNoz Dashboard

1. **Login to SigNoz Cloud:**
   - Navigate to your SigNoz instance (e.g., `https://your-org.signoz.cloud`)
   - Or for self-hosted: `http://localhost:3301`

2. **View Traces:**
   - Go to **Services** → Select your service (`SampleServiceNET` or `SampleServicePython`)
   - Click on any trace to see the full request flow
   - Observe span duration, errors, and attributes

3. **View Logs:**
   - Go to **Logs** section
   - Filter by:
     - `service.name = "SampleServicePython"` or `"SampleServiceNET"`
     - `severity_text = "ERROR"` for errors only
     - `trace_id = "<specific-trace-id>"` to see all logs for a request
   - Logs are automatically correlated with traces

4. **View Metrics:**
   - Go to **Metrics** → **Dashboard**
   - View Golden Signals:
     - Request rate (`http.server.request.count`)
     - Latency (`http.server.request.duration`)
     - Error rate (`http.server.error.count`)

5. **Explore Service Maps:**
   - Go to **Service Map**
   - Visualize dependencies between services
   - Identify bottlenecks and failure points

## 🔍 Log Structure Examples

Both .NET and Python services produce consistent, structured logs following the unified standard. Here are real examples from SigNoz:

### INFO Log (Successful Request)

**Python:**
```json
{
  "body": "Request finished HTTP/1.1 GET http://localhost:8000/weatherforecast/days/5 - 200 462 application/json 1.996ms",
  "date": "2025-11-27T08:04:44.039716Z",
  "timestamp": "2025-11-27T08:04:44.039716Z",
  "severity_text": "INFO",
  "severity_number": 9,
  "trace_id": "88847db0b8983565f659b12c7cb75e00",
  "span_id": "64981d8150d2d729",
  "trace_flags": 1,
  "scope_name": "app.middleware.observability_middleware",
  "attributes": {
    "Method": "GET",
    "Path": "/weatherforecast/days/5",
    "StatusCode": 200,
    "ElapsedMilliseconds": 1.996,
    "Protocol": "HTTP/1.1",
    "ContentType": "application/json",
    "ContentLength": "462",
    "Host": "localhost:8000",
    "RequestId": "fae471c5-c92a-4844-9988-54b213637039",
    "message_template_text": "Request finished {Protocol} {Method} {Scheme}://{Host}{PathBase}{Path}{QueryString} - {StatusCode} {ContentLength} {ContentType} {ElapsedMilliseconds}ms"
  },
  "resources": {
    "service.name": "SampleServicePython",
    "service.namespace": "production",
    "host.name": "eb223a9b9dde",
    "os.type": "linux",
    "telemetry.sdk.language": "python",
    "telemetry.sdk.name": "opentelemetry",
    "telemetry.sdk.version": "1.38.0"
  }
}
```

**.NET:**
```json
{
  "body": "Executed endpoint 'Sample.Controllers.WeatherForecastController.GetByDays (Sample)'",
  "date": "2025-11-26T19:41:48.5458178Z",
  "timestamp": "2025-11-26T19:41:48.5458178Z",
  "severity_text": "Information",
  "severity_number": 9,
  "trace_id": "c6e9a8f2b48cd51dd557ea2ed7624c05",
  "span_id": "c81ac9c1b7b85a7b",
  "trace_flags": 0,
  "scope_name": "Microsoft.AspNetCore.Routing.EndpointMiddleware",
  "attributes": {
    "EndpointName": "Sample.Controllers.WeatherForecastController.GetByDays (Sample)",
    "RequestPath": "/weatherforecast/days/7",
    "ConnectionId": "0HNHD4F45S2DU",
    "RequestId": "0HNHD4F45S2DU:00000001",
    "ParentId": "0000000000000000",
    "environment": "Development",
    "message_template.text": "Executed endpoint '{EndpointName}'"
  },
  "resources": {
    "service.name": "SampleServiceNET",
    "service.namespace": "production",
    "service.version": "1.0.0",
    "deployment.environment": "Development",
    "host.name": "2bd0a45cedc3",
    "os.type": "linux",
    "telemetry.sdk.language": "dotnet",
    "telemetry.sdk.name": "serilog",
    "telemetry.sdk.version": "4.2.0-main-057a8c1+057a8c1712d1268a4d7f0952819c535e45c56647"
  }
}
```

### ERROR Log (Validation Failure)

**Python:**
```json
{
  "body": "Validation failed in WeatherForecastController.GetByDays: days=6",
  "date": "2025-11-27T08:08:47.3013227Z",
  "timestamp": "2025-11-27T08:08:47.3013227Z",
  "severity_text": "ERROR",
  "severity_number": 17,
  "trace_id": "159154b103d536e80a7b2e87e15964b3",
  "span_id": "1d4dd18374917aa9",
  "trace_flags": 1,
  "scope_name": "main.controllers.WeatherForecastController",
  "attributes": {
    "Controller": "WeatherForecastController",
    "Action": "GetByDays",
    "Days": 6,
    "RequestPath": "/weatherforecast/days/6",
    "message_template_text": "Validation failed in {Controller}.{Action}: days={Days}"
  },
  "resources": {
    "service.name": "SampleServicePython",
    "service.namespace": "production",
    "host.name": "eb223a9b9dde",
    "os.type": "linux",
    "telemetry.sdk.language": "python",
    "telemetry.sdk.name": "opentelemetry",
    "telemetry.sdk.version": "1.38.0"
  }
}
```

**.NET:**
```json
{
  "body": "Validation failed in WeatherForecastController.GetByDays: days=6",
  "date": "2025-11-27T08:07:32.7002267Z",
  "timestamp": "2025-11-27T08:07:32.7002267Z",
  "severity_text": "Error",
  "severity_number": 17,
  "trace_id": "24ed135b797b3f0c847275c4ca71728a",
  "span_id": "8c7f63b4354a3890",
  "trace_flags": 0,
  "scope_name": "Sample.Controllers.WeatherForecastController",
  "attributes": {
    "Controller": "WeatherForecastController",
    "Action": "GetByDays",
    "Days": 6,
    "ActionId": "77f439e4-0bba-4561-81f2-2865a5e83bf5",
    "ActionName": "Sample.Controllers.WeatherForecastController.GetByDays (Sample)",
    "RequestPath": "/weatherforecast/days/6",
    "ConnectionId": "0HNHDHFV9E87U",
    "RequestId": "0HNHDHFV9E87U:00000001",
    "ParentId": "47417675d5507eae",
    "environment": "Development",
    "message_template.text": "Validation failed in {Controller}.{Action}: days={Days}"
  },
  "resources": {
    "service.name": "SampleServiceNET",
    "service.namespace": "production",
    "service.version": "1.0.0",
    "deployment.environment": "Development",
    "host.name": "eb223a9b9dde",
    "os.type": "linux",
    "service.instance.id": "DESKTOP-DO1ESVO",
    "telemetry.sdk.language": "dotnet",
    "telemetry.sdk.name": "serilog",
    "telemetry.sdk.version": "4.2.0-main-057a8c1+057a8c1712d1268a4d7f0952819c535e45c56647"
  }
}
```

### Key Observations

**Consistent Fields Across Both Stacks:**
- ✅ `trace_id` and `span_id` - For distributed tracing correlation
- ✅ `timestamp` and `date` - ISO 8601 formatted timestamps
- ✅ `severity_text` and `severity_number` - Standardized log levels
- ✅ `body` - Human-readable log message
- ✅ `attributes` - Structured context (Controller, Action, RequestPath, etc.)
- ✅ `resources` - Service metadata (name, version, environment, SDK info)
- ✅ `message_template_text` - Template for structured logging

**Stack-Specific Differences:**
- .NET includes additional ASP.NET Core context (`ActionId`, `ConnectionId`, `ParentId`)
- Python uses simpler attribute names but maintains the same structure
- Both produce identical log patterns for the same business logic (validation errors)

This demonstrates the **unified standard in action** - different technology stacks producing consistent, queryable telemetry data!

## 🔒 Security Features

The OpenTelemetry Collector is configured with **automatic sensitive data redaction** to prevent accidental logging of:

### Automatically Filtered Attributes:
- **Authentication & Credentials:** passwords, tokens, API keys, JWT, session IDs
- **Personal Identifiable Information (PII):** SSN, email, phone, address, full name, date of birth
- **Financial Information:** credit card numbers, CVV, bank accounts, routing numbers, IBAN
- **Health Information:** medical records, patient IDs, diagnoses, prescriptions
- **Database Credentials:** connection strings, database passwords, private keys, encryption keys

These attributes are automatically **deleted** by the collector before data reaches SigNoz, ensuring compliance with GDPR, HIPAA, and other privacy regulations.

**Configuration:** See `config/otel-collector-config.yaml` → `processors.attributes.actions`

## 🧪 Testing Observability Features

### 1. Test Distributed Tracing

Make a request and copy the `trace_id` from the logs:

```bash
# .NET
curl http://localhost:5159/weatherforecast/days/3

# Python
curl http://localhost:8000/weatherforecast/days/3
```

Then search for that `trace_id` in SigNoz to see:
- All logs from that request
- All spans (HTTP handler, business logic, etc.)
- Request duration and status

### 2. Test Error Logging

Trigger a validation error:

```bash
curl http://localhost:8000/weatherforecast/days/7
# Returns 400 Bad Request: "Days must be 5 or less"
```

In SigNoz:
- Filter logs by `severity_text = "ERROR"`
- Verify structured error attributes are present
- Confirm trace context is preserved

### 3. Test Custom Business Spans

```bash
curl http://localhost:8000/business
```

In SigNoz Traces:
- Find spans named `business.ExampleOperation`
- Verify custom attributes are attached
- Check nested span hierarchy

### 4. Test Cross-Service Tracing (Future)

When both .NET and Python services are running and calling each other:
1. Make a request to .NET service that calls Python
2. Search for the trace in SigNoz
3. Verify the trace shows the full request flow across both services

## 📁 Project Structure

```
├── config/
│   ├── otel-collector-config.yaml   # OpenTelemetry Collector configuration
│   ├── collector.env.example        # Example environment variables
│   ├── collector.env                # Your SigNoz credentials (gitignored)
│   └── run-collector.ps1            # Script to start collector
├── NET/
│   └── Sample/                      # .NET sample application
│       ├── Controllers/
│       ├── Middleware/
│       └── Program.cs               # Observability initialization
├── Python/
│   ├── app/
│   │   ├── observability/           # Observability package
│   │   │   ├── __init__.py
│   │   │   ├── config.py           # Configuration and globals
│   │   │   ├── tracing.py          # Tracing setup
│   │   │   ├── logging.py          # Structured logging
│   │   │   ├── metrics.py          # Metrics initialization
│   │   │   ├── logs.py             # OTEL logs setup
│   │   │   ├── instrumentation.py  # Auto-instrumentation
│   │   │   ├── telemetry.py        # Helper classes
│   │   │   └── initialization.py   # Main init function
│   │   └── middleware/
│   │       └── observability_middleware.py
│   ├── main.py                      # FastAPI application
│   └── requirements.txt
└── README.md                        # This file
```

## 🛠️ Troubleshooting

### Collector not starting?

1. **Check environment variables:**
   ```bash
   # Verify collector.env exists and has correct values
   cat config/collector.env
   ```

2. **Verify Docker is running:**
   ```bash
   docker --version
   docker ps
   ```

3. **Check for port conflicts:**
   ```bash
   # On Windows
   netstat -ano | findstr :4317
   netstat -ano | findstr :4318
   
   # On Linux/Mac
   lsof -i :4317
   lsof -i :4318
   ```

4. **Review collector configuration:**
   ```bash
   # Validate YAML syntax
   docker run --rm -v ${PWD}/config:/config otel/opentelemetry-collector-contrib:0.93.0 \
     validate --config=/config/otel-collector-config.yaml
   ```

### Logs not appearing in SigNoz?

1. **Check collector is running:**
   ```bash
   docker ps
   docker logs otel-collector
   ```

2. **Verify SigNoz ingestion key:**
   - Ensure `SIGNOZ_INGESTION_KEY` in `collector.env` is correct
   - Check for typos or extra spaces
   - Verify the key hasn't expired

3. **Check endpoint configuration:**
   - US region: `ingest.us.signoz.cloud:443`
   - EU region: `ingest.eu.signoz.cloud:443`
   - India region: `ingest.in.signoz.cloud:443`
   - Self-hosted: `localhost:4317` (with `insecure: true`)

4. **Test network connectivity:**
   ```bash
   # Test SigNoz endpoint
   curl https://ingest.us.signoz.cloud:443
   
   # Should return a connection (even if refused, confirms endpoint is reachable)
   ```

5. **Review application logs:**
   - Check for OTEL initialization messages
   - Look for "✓ Tracing initialized successfully"
   - Verify no errors during startup

6. **Check collector debug output:**
   ```bash
   docker logs otel-collector | grep -i error
   docker logs otel-collector | grep -i "status code"
   ```

### Traces not correlated?

1. **Verify W3C Trace Context headers:**
   ```bash
   curl -v http://localhost:8000/weatherforecast/days/3
   # Look for traceparent header in response
   ```

2. **Check trace propagation:**
   - Ensure all services use OpenTelemetry SDK
   - Verify HTTP client instrumentation is enabled

3. **Validate trace IDs:**
   - Trace IDs should be consistent across logs and traces

### High memory/CPU usage?

1. **Adjust sampling rate:**
   ```bash
   # Environment variable
   export OPEN_TELEMETRY_SAMPLING_RATIO=0.1  # Sample 10%
   ```

2. **Reduce log level:**
   ```bash
   export ENVIRONMENT=production  # Disables DEBUG logs
   ```

3. **Check collector configuration:**
   - Review batch processor settings
   - Adjust `send_batch_size` and `timeout`

## 📚 Additional Resources

- [Unified Logging & Monitoring Standard (Full Document)](./Unified%20Logging%20%26%20Monitoring%20Standard.pdf)
- [OpenTelemetry .NET Documentation](https://opentelemetry.io/docs/languages/net/)
- [OpenTelemetry Python Documentation](https://opentelemetry.io/docs/languages/python/)
- [SigNoz Documentation](https://signoz.io/docs/)
- [W3C Trace Context Specification](https://www.w3.org/TR/trace-context/)

## 🤝 Contributing

When adding new services or modifying observability code:

1. Follow the standard logging fields (see Section 4 of the standard)
2. Use W3C Trace Context for propagation
3. Add custom spans for operations >100ms
4. Implement automatic sensitive data redaction
5. Test with both success and error scenarios
6. Document any new environment variables

## 📞 Support

- **On-Call Rotation:** [Your Team's On-Call Schedule]
- **SigNoz Support:** support@signoz.io
- **Internal Slack:** #observability-help

---

**Last Updated:** November 27, 2025  
**Version:** 1.0.0  
**Maintained by:** Observability Team