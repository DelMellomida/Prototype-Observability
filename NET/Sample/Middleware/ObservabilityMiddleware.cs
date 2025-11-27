using System.Diagnostics;
using Microsoft.AspNetCore.Http;
using Microsoft.Extensions.Logging;
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
        // Invoke next middleware and capture response status or exceptions
        try
        {
            await _next(context);

            // Ensure http.status_code is present on current activity
            var activity = Activity.Current;
            activity?.SetTag("http.response.status_code", context.Response.StatusCode);

            if (context.Response.StatusCode >= 400)
            {
                if (context.Response.StatusCode >= 500)
                {
                    _logger.LogError("Request {Path} returned {StatusCode}", context.Request.Path, context.Response.StatusCode);
                    activity?.SetStatus(ActivityStatusCode.Error, $"HTTP {context.Response.StatusCode}");
                }
                else
                {
                    _logger.LogWarning("Request {Path} returned {StatusCode}", context.Request.Path, context.Response.StatusCode);
                }
            }
        }
        catch (Exception ex)
        {
            RecordException(ex, context);
            throw; // Re-throw to allow the framework to handle it
        }
    }

    // Record exception details to current activity and structured logs
    private void RecordException(Exception ex, HttpContext context)
    {
        var activity = Activity.Current;
        if (activity != null)
        {
            activity.SetStatus(ActivityStatusCode.Error, ex.Message);
            activity.SetTag("exception.type", ex.GetType().FullName);
            activity.SetTag("exception.message", ex.Message);
            activity.SetTag("http.request.path", context.Request.Path);
            activity.AddEvent(new ActivityEvent("exception", default, new ActivityTagsCollection
            {
                ["exception.type"] = ex.GetType().FullName,
                ["exception.message"] = ex.Message
            }));
        }

        _logger.LogError(ex, "Unhandled exception processing request {Path}", context.Request.Path);
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
