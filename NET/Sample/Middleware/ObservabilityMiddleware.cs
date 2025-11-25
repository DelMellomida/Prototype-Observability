using System.Diagnostics;
using Serilog;

public class ObservabilityMiddleware
{
    private readonly RequestDelegate _next;
    private readonly ILogger<ObservabilityMiddleware> _logger;

    public ObservabilityMiddleware(RequestDelegate next, ILogger<ObservabilityMiddleware> logger)
    {
        _next = next;
        _logger = logger;
    }

    public async Task InvokeAsync(HttpContext context)
    {
        try
        {
            await _next(context);
            
            // Handle 4xx/5xx that aren't exceptions (like 404s)
            if (context.Response.StatusCode >= 400)
            {
                var level = context.Response.StatusCode >= 500 ? LogLevel.Error : LogLevel.Warning;
                _logger.Log(level, "Request {Path} returned {StatusCode}", context.Request.Path, context.Response.StatusCode);
            }
        }
        catch (Exception ex)
        {
            RecordException(ex);
            throw; // Re-throw so the framework knows it failed
        }
    }

    private void RecordException(Exception ex)
    {
        var activity = Activity.Current;
        if (activity != null)
        {
            activity.SetStatus(ActivityStatusCode.Error, ex.Message);
            activity.AddException(ex);
            activity.SetTag("exception.type", ex.GetType().FullName);
        }

        // Serilog will pick up TraceId/SpanId from the Activity automatically
        _logger.LogError(ex, "Unhandled exception occurred");
    }
}

// Extension method for clean usage
public static class MiddlewareExtensions
{
    public static IApplicationBuilder UseCompanyObservability(this IApplicationBuilder app)
    {
        return app.UseMiddleware<ObservabilityMiddleware>();
    }
}