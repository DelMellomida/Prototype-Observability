# Observability (Logging, Tracing, Metrics) — Prototype-Observability

This README documents the observability approach used in this prototype, how logs/traces/metrics are produced and correlated, configuration keys you can change, and quick run/verification steps. It also includes example Signoz log entries captured while exercising the `WeatherForecast` endpoints.

**Overview**
- Structured logs: Serilog is configured to emit JSON logs to the console and to an OTLP sink. JSON ensures downstream systems (Signoz, ELK, etc.) can parse fields.
- Tracing: OpenTelemetry (.NET) is used for tracing. The app uses a DI-registered `ActivitySource` and an injectable `TelemetryHelper` to create business-level spans (prefixed with `business.`).
- Metrics: OpenTelemetry metrics are collected (ASP.NET, HTTP client, runtime/process) and exported via OTLP to your collector.
- Correlation: Logs include `trace_id` and `span_id` (snake_case) so logs and traces can be correlated in the backend.
- PII handling: The app avoids recording request bodies/headers at the instrumentation source. The OTEL Collector config also contains processors to remove known PII attributes before exporting to the backend.
- Health checks: The app registers standard .NET health checks and exposes endpoints for orchestration.

**Key components & files**
- `NET/Sample/Program.cs` — bootstraps Serilog, OpenTelemetry, sampling, health checks, DI registrations.
- `NET/Sample/Enricher/ActivityEnricher.cs` — Serilog enricher that injects `trace_id`, `span_id`, `parent_span_id` into every log record.
- `NET/Sample/Telemetry/TelemetryHelper.cs` — injectable helper (uses `ActivitySource`) to start business spans.
- `config/otel-collector-config.yaml` — example collector configuration used in this repo (resource detection, attribute processors to delete PII, OTLP exporters to Signoz).

**Important configuration keys**
- `OTEL_SERVICE_NAME` — service name used for `ActivitySource` and resource/service registration (default: `SampleService`).
- `OpenTelemetry:Enabled` — toggle OTEL on/off.
- `OpenTelemetry:OtlpEndpoint` — OTLP collector endpoint (default: `http://localhost:4317`).
- `OpenTelemetry:SamplingRatio` — sampling ratio for traces (double). Default: `1.0` in Development, `0.1` otherwise.

**Setup (Quick)**
- Prerequisites: install [.NET 10 SDK](https://dotnet.microsoft.com/), and Docker (optional for running the OpenTelemetry Collector or Signoz).
- Configure the collector/backend: open `config/otel-collector-config.yaml` and set your ingestion endpoint and any API/key values (e.g. replace the Signoz `signoz-ingestion-key` header with your workspace key) or set `OpenTelemetry:OtlpEndpoint` in `appsettings.json`.
- Configure service name and sampling (optional): set `OTEL_SERVICE_NAME` and `OpenTelemetry:SamplingRatio` via environment variables or in `NET/Sample/appsettings.json`.

	- PowerShell examples (temporary env vars for the session):
		```powershell
		$env:OTEL_SERVICE_NAME = "MyService"
		$env:OpenTelemetry__SamplingRatio = "0.1"
		$env:OpenTelemetry__OtlpEndpoint = "http://localhost:4317"
		```

	- To persist settings, update `NET/Sample/appsettings.json` (example):
		```json
		{
			"OpenTelemetry": {
				"Enabled": true,
				"OtlpEndpoint": "http://localhost:4317",
				"SamplingRatio": 0.1
			},
			"OTEL_SERVICE_NAME": "SampleService"
		}
		```

- (Optional) Start the OpenTelemetry Collector using the included config so your app can export to a local collector:

	```powershell
	docker run --rm -p 4317:4317 -p 4318:4318 -v "${PWD}\config\otel-collector-config.yaml":/etc/otel/config.yaml otel/opentelemetry-collector:latest --config /etc/otel/config.yaml
	```

- Run the app (from repo root):
	```powershell
	cd "G:\Documents\Testing\Prototype-Observability\NET\Sample"
	dotnet run --profile https
	https:\\localhost:7001
	```

- Health endpoints: the app registers health checks. If you need explicit mappings, add these lines to `Program.cs` (or confirm your Observability extension maps them):
	```csharp
	app.MapHealthChecks("/health");
	app.MapHealthChecks("/readiness");
	```


**Log schema & conventions**
- JSON log entries include (at minimum): `timestamp`, `severity`/`severity_text`, `message`/`body`, `service.name`, `environment`, and the correlation fields `trace_id` and `span_id` (snake_case).
- Business spans are named `business.<OperationName>` (e.g. `business.WeatherForecastGeneration`).
- Instrumentation tags follow OTEL semantic conventions where practical (e.g. `http.method`, `http.target`, `http.response.status_code`).

**PII handling**
- The app configures ASP.NET instrumentation to NOT record request bodies or sensitive headers.
- The OTEL Collector config further removes known PII attributes (e.g. `user.password`, `user.ssn`, `user.credit_card`, `user.email`) before exporting.

**Health endpoints**
- The app registers the default health checks service. Map endpoints are available (`/health`, `/readiness`) — confirm these in `Program.cs` or the Observability extension.

**How to run locally**
1. (Optional) Start the OTEL Collector using the included config if you want to forward telemetry to a running Signoz/collector:

```powershell
docker run --rm -p 4317:4317 -p 4318:4318 -v "${PWD}\config\otel-collector-config.yaml":/etc/otel/config.yaml otel/opentelemetry-collector:latest --config /etc/otel/config.yaml
```

2. Run the sample app:

```powershell
cd "G:\Documents\Testing\Prototype-Observability\NET\Sample"
dotnet run
```

3. Exercise the endpoints (example):

```powershell
Invoke-WebRequest -Uri "https://localhost:5001/WeatherForecast" -UseBasicParsing
Invoke-WebRequest -Uri "https://localhost:5001/WeatherForecast/days/3" -UseBasicParsing
```

4. Confirm console output contains JSON logs and fields `trace_id` and `span_id`.

**Verifying in Signoz / OTLP backend**
- Search traces by `service.name` and `trace_id`.
- Use the log viewer to filter by `trace_id` or `span_id` and verify log entries are attached to the correct traces.
- Confirm that validation or expected errors produce a single recorded exception event (middleware centralizes exception recording).

**Sample Signoz log entries**
Below are example log entries captured from the prototype (kept as-is so you can see what to expect). Fields of note: `trace_id`, `span_id`, `parent_span_id`, `service.name`, `environment`, `message_template.text`, and `attributes` that provide request and controller context.

```json
{ "body": "Executing endpoint 'Sample.Controllers.WeatherForecastController.GetByDays (Sample)'", "date": "2025-11-25T07:46:52.7450154Z", "id": "0ih4cI5hq7lj2firyZj73t0KA1E", "timestamp": "2025-11-25T07:46:52.7450154Z", "attributes": { "ConnectionId": "0HNHBUPCMRVH0", "EndpointName": "Sample.Controllers.WeatherForecastController.GetByDays (Sample)", "EventId": "{\"Name\":\"ExecutingEndpoint\"}", "RequestId": "0HNHBUPCMRVH0:00000001", "RequestPath": "/weatherforecast/days/8", "SpanId": "e4ed6a1c11e11156", "TraceId": "1f92ccf1737d9fe4ab924bbded8c8423", "environment": "Development", "message_template.text": "Executing endpoint '{EndpointName}'", "parent_span_id": "0000000000000000", "service.instance.id": "23cbcf1f1991", "service.name": "SampleService", "span_id": "e4ed6a1c11e11156", "trace_id": "1f92ccf1737d9fe4ab924bbded8c8423" }, "resources": { "deployment.environment": "Development", "host.name": "23cbcf1f1991", "os.type": "linux", "service.instance.id": "DESKTOP-DO1ESVO", "service.name": "SampleService", "service.namespace": "production", "service.version": "1.0.0", "signoz.workspace.key.id": "019aab6b-9bf9-7679-a895-7e77113d39ed", "telemetry.sdk.language": "dotnet", "telemetry.sdk.name": "serilog", "telemetry.sdk.version": "4.2.0-main-057a8c1+057a8c1712d1268a4d7f0952819c535e45c56647" }, "scope": {}, "severity_text": "Information", "severity_number": 9, "scope_name": "Microsoft.AspNetCore.Routing.EndpointMiddleware", "scope_version": "", "span_id": "e4ed6a1c11e11156", "trace_flags": 0, "trace_id": "1f92ccf1737d9fe4ab924bbded8c8423" }

{ "body": "Validation failed in WeatherForecastController.GetByDays: days=8", "date": "2025-11-25T07:46:52.7657829Z", "id": "0ih4cI82ep4mgm5PgFoPZFZPv74", "timestamp": "2025-11-25T07:46:52.7657829Z", "attributes": { "Days": 8, "Action": "GetByDays", "ActionId": "9a073cdf-4f0b-4607-a1a7-2f27167b3986", "ActionName": "Sample.Controllers.WeatherForecastController.GetByDays (Sample)", "ConnectionId": "0HNHBUPCMRVH0", "Controller": "WeatherForecastController", "RequestId": "0HNHBUPCMRVH0:00000001", "RequestPath": "/weatherforecast/days/8", "SpanId": "12c8f446e37275cb", "TraceId": "1f92ccf1737d9fe4ab924bbded8c8423", "environment": "Development", "message_template.text": "Validation failed in {Controller}.{Action}: days={Days}", "parent_span_id": "e4ed6a1c11e11156", "service.instance.id": "23cbcf1f1991", "service.name": "SampleService", "span_id": "12c8f446e37275cb", "trace_id": "1f92ccf1737d9fe4ab924bbded8c8423" }, "resources": { "deployment.environment": "Development", "host.name": "23cbcf1f1991", "os.type": "linux", "service.instance.id": "DESKTOP-DO1ESVO", "service.name": "SampleService", "service.namespace": "production", "service.version": "1.0.0", "signoz.workspace.key.id": "019aab6b-9bf9-7679-a895-7e77113d39ed", "telemetry.sdk.language": "dotnet", "telemetry.sdk.name": "serilog", "telemetry.sdk.version": "4.2.0-main-057a8c1+057a8c1712d1268a4d7f0952819c535e45c56647" }, "scope": {}, "severity_text": "Error", "severity_number": 17, "scope_name": "Sample.Controllers.WeatherForecastController", "scope_version": "", "span_id": "12c8f446e37275cb", "trace_flags": 0, "trace_id": "1f92ccf1737d9fe4ab924bbded8c8423" }

{ "body": "Request /weatherforecast/days/8 returned 400", "date": "2025-11-25T07:46:52.7911629Z", "id": "0ih4cIAtdhsqfS1XxfwmA5540KX", "timestamp": "2025-11-25T07:46:52.7911629Z", "attributes": { "StatusCode": 400, "ConnectionId": "0HNHBUPCMRVH0", "Path": "/weatherforecast/days/8", "RequestId": "0HNHBUPCMRVH0:00000001", "RequestPath": "/weatherforecast/days/8", "SpanId": "e4ed6a1c11e11156", "TraceId": "1f92ccf1737d9fe4ab924bbded8c8423", "environment": "Development", "message_template.text": "Request {Path} returned {StatusCode}", "parent_span_id": "0000000000000000", "service.instance.id": "23cbcf1f1991", "service.name": "SampleService", "span_id": "e4ed6a1c11e11156", "trace_id": "1f92ccf1737d9fe4ab924bbded8c8423" }

{ "body": "Validation failed in WeatherForecastController.GetByDays: days=10", "date": "2025-11-25T07:50:29.6705418Z", "id": "0ih4idbpb0LFfDvd0vkNOQPQppM", "timestamp": "2025-11-25T07:50:29.6705418Z", "attributes": { "Days": 10, "Action": "GetByDays", "ActionId": "1ec15210-07d8-4b0c-9a3f-dbb1db99797e", "ActionName": "Sample.Controllers.WeatherForecastController.GetByDays (Sample)", "ConnectionId": "0HNHBUT6RMKRR", "Controller": "WeatherForecastController", "RequestId": "0HNHBUT6RMKRR:00000001", "RequestPath": "/weatherforecast/days/10", "SpanId": "acdca94332011e82", "TraceId": "135b382dadf3bb31dad132b4a196fc73", "environment": "Development", "message_template.text": "Validation failed in {Controller}.{Action}: days={Days}", "parent_span_id": "5ea009d9ef65b1bd", "service.instance.id": "23cbcf1f1991", "service.name": "SampleService", "span_id": "acdca94332011e82", "trace_id": "135b382dadf3bb31dad132b4a196fc73" }

{ "body": "Executing action method Sample.Controllers.WeatherForecastController.Get (Sample) - Validation state: Valid", "date": "2025-11-25T07:54:22.2364016Z", "id": "0ih4pRV3s5LrIAzOfldmnSraqtQ", "timestamp": "2025-11-25T07:54:22.2364016Z", "attributes": { "ActionId": "a71ccf3e-2f70-48ec-8465-172a2985a0d8", "ActionName": "Sample.Controllers.WeatherForecastController.Get (Sample)", "ConnectionId": "0HNHBUT6RMKRV", "EventId": "{\"Id\":101,\"Name\":\"ActionMethodExecuting\"}", "RequestId": "0HNHBUT6RMKRV:00000001", "RequestPath": "/weatherforecast", "SpanId": "aa3e81295b9ae771", "TraceId": "24bf3472fed387639047cc6685e3e2fd", "ValidationState": "Valid", "environment": "Development", "message_template.text": "Executing action method {ActionName} - Validation state: {ValidationState}", "parent_span_id": "0000000000000000", "service.instance.id": "23cbcf1f1991", "service.name": "SampleService", "span_id": "aa3e81295b9ae771", "trace_id": "24bf3472fed387639047cc6685e3e2fd" }
```

**Interpreting the sample logs**
- Correlation: note `trace_id` is the same across the related entries (trace of a single request). Each log's `span_id` shows which span emitted the log, and `parent_span_id` shows parent relationships.
- Severity: `severity_text`/`severity_number` indicate log level. Example: `Validation failed ...` appears as `Error` / `Fatal` depending on the controller log level.
- Validation logs: Controller-level validation produces explicit Warning/Error logs and also sets `validation.failed` as a span tag for querying.

**Troubleshooting tips**
- If you see duplicate exception records, confirm you have `options.RecordException = false` in `.AddAspNetCoreInstrumentation(...)` and that your middleware records exceptions once.
- If business spans are not visible, ensure `ActivitySource` name matches `.AddSource(...)` in OpenTelemetry configuration (we register the `OTEL_SERVICE_NAME` value in DI and use it for `.AddSource(...)`).
- If logs do not include `trace_id`/`span_id`, verify `ActivityEnricher` is registered with Serilog (the Observability extension configures `.Enrich.With<ActivityEnricher>()`).

---

