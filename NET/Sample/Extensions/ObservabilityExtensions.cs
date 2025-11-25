using OpenTelemetry.Exporter;
using OpenTelemetry.Metrics;
using OpenTelemetry.Resources;
using OpenTelemetry.Trace;
using Serilog;
using Serilog.Formatting.Json;
using Serilog.Sinks.OpenTelemetry;
using System.Diagnostics;
using Sample.Enricher;
using Sample.Telemetry;

public static class ObservabilityExtensions
{
    public static void AddCompanyObservability(this WebApplicationBuilder builder)
    {
        // 1. Load Configuration
        var serviceName = builder.Configuration.GetValue<string>("OTEL_SERVICE_NAME", "SampleService");
        var otlpEndpoint = builder.Configuration.GetValue<string>("OpenTelemetry:OtlpEndpoint", "http://localhost:4317");
        var enableOtel = builder.Configuration.GetValue<bool>("OpenTelemetry:Enabled", true);

        var resourceAttributes = new Dictionary<string, object>
        {
            ["service.name"] = serviceName,
            ["deployment.environment"] = builder.Environment.EnvironmentName,
            ["service.instance.id"] = Environment.MachineName
        };

        // 2. Configure Serilog
        builder.Logging.ClearProviders();
        var loggerConfig = new LoggerConfiguration()
            .Enrich.FromLogContext()
            .Enrich.With<ActivityEnricher>()
            .Enrich.WithProperty("service.name", serviceName)
            .Enrich.WithProperty("environment", builder.Environment.EnvironmentName)
            .WriteTo.Console(new JsonFormatter(renderMessage: true));

        if (enableOtel)
        {
            loggerConfig.WriteTo.OpenTelemetry(options =>
            {
                options.Endpoint = otlpEndpoint;
                options.Protocol = OtlpProtocol.Grpc;
                options.ResourceAttributes = resourceAttributes;
            });
        }

        var logger = loggerConfig.CreateLogger();
        Log.Logger = logger;
        builder.Logging.AddSerilog(logger);
        builder.Services.AddSerilog(logger);

        // 3. Register ActivitySource & Helper
        var activitySource = new ActivitySource(serviceName);
        builder.Services.AddSingleton(activitySource);
        builder.Services.AddSingleton<ITelemetryHelper, TelemetryHelper>();

        // 4. Configure OpenTelemetry
        if (enableOtel)
        {
            // Sampling Logic
            var configuredSampling = builder.Configuration.GetValue<double?>("OpenTelemetry:SamplingRatio");
            double defaultSampling = builder.Environment.IsDevelopment() ? 1.0 : 0.1;
            var samplingRatio = configuredSampling ?? defaultSampling;
            
            var sampler = new ParentBasedSampler(new TraceIdRatioBasedSampler(samplingRatio));

            builder.Services.AddOpenTelemetry()
                .ConfigureResource(r => r.AddService(serviceName).AddAttributes(resourceAttributes))
                .WithMetrics(metrics =>
                {
                    metrics
                        .AddAspNetCoreInstrumentation()
                        .AddHttpClientInstrumentation()
                        .AddRuntimeInstrumentation()
                        .AddProcessInstrumentation()
                        .AddOtlpExporter(opts => opts.Endpoint = new Uri(otlpEndpoint));
                })
                .WithTracing(tracing =>
                {
                    tracing
                        .AddSource(serviceName) // Important!
                        .SetSampler(sampler)
                        .AddAspNetCoreInstrumentation(options =>
                        {
                            // We are using manual middleware for exceptions, so disable auto-record
                            options.RecordException = false; 
                            options.EnrichWithHttpRequest = (activity, req) =>
                            {
                                activity.SetTag("http.method", req.Method);
                                activity.SetTag("http.target", req.Path);
                            };
                            options.EnrichWithHttpResponse = (activity, resp) =>
                            {
                                activity.SetTag("http.response.status_code", resp.StatusCode);
                            };
                        })
                        .AddHttpClientInstrumentation(o => o.RecordException = true)
                        .AddSqlClientInstrumentation(o => o.RecordException = true)
                        .AddOtlpExporter(opts => opts.Endpoint = new Uri(otlpEndpoint));
                });
        }
    }
}