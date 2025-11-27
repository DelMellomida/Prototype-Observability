using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Logging;
using Sample.Telemetry;
using Serilog.Context;
using System.Diagnostics;

namespace Sample.Controllers
{
    [ApiController]
    [Route("[controller]")]
    public class WeatherForecastController : ControllerBase
    {
        private readonly ILogger<WeatherForecastController> _logger;
        private readonly ITelemetryHelper _telemetryHelper;

        public WeatherForecastController(ILogger<WeatherForecastController> logger, ITelemetryHelper telemetryHelper)
        {
            _logger = logger;
            _telemetryHelper = telemetryHelper;
        }

        public static string[] Summaries =
        [
            "Freezing", "Bracing", "Chilly", "Cool", "Mild", "Warm", "Balmy", "Hot", "Sweltering", "Scorching"
        ];

        [HttpGet(Name = "GetWeatherForecast")]
        public IEnumerable<WeatherForecast> Get()
        {
            using var activity = _telemetryHelper.StartBusinessSpan("WeatherForecastGeneration",
                new Dictionary<string, object>
                {
                    ["controller"] = nameof(WeatherForecastController),
                    ["action"] = nameof(Get),
                    ["request.id"] = Guid.NewGuid().ToString()
                });

            var forecasts = Enumerable.Range(1, 5).Select(index => new WeatherForecast
            {
                Date = DateOnly.FromDateTime(DateTime.Now.AddDays(index)),
                TemperatureC = Random.Shared.Next(-20, 55),
                Summary = Summaries[Random.Shared.Next(Summaries.Length)]
            })
            .ToArray();

            activity?.SetTag("forecast.count", forecasts.Length);
            return forecasts;
        }

        [HttpGet("days/{days}", Name = "GetWeatherForecastByDays")]
        public ActionResult<IEnumerable<WeatherForecast>> GetByDays(int days)
        {
            using var activity = _telemetryHelper.StartBusinessSpan("WeatherForecastGenerationByDays",
                new Dictionary<string, object>
                {
                    ["controller"] = nameof(WeatherForecastController),
                    ["action"] = nameof(GetByDays),
                    ["request.id"] = Guid.NewGuid().ToString(),
                    ["days.requested"] = days
                });

            // Validation with structured error logging per documentation Section 4.3
            if (days < 1 || days > 5)
            {
                activity?.SetTag("validation.failed", true);
                activity?.SetTag("error.type", "ValidationError");

                var traceId = activity?.TraceId.ToString();
                var spanId = activity?.SpanId.ToString();

                // Structured error logging with all required fields
                using (LogContext.PushProperty("traceId", traceId))
                using (LogContext.PushProperty("spanId", spanId))
                using (LogContext.PushProperty("Days", days))
                using (LogContext.PushProperty("Action", nameof(GetByDays)))
                using (LogContext.PushProperty("Controller", nameof(WeatherForecastController)))
                using (LogContext.PushProperty("RequestPath", $"/weatherforecast/days/{days}"))
                using (LogContext.PushProperty("error", new
                {
                    type = "ValidationException",
                    message = $"Days must be between 1 and 5. Requested: {days}",
                    code = "WEATHER_001"
                }))
                using (LogContext.PushProperty("context", new
                {
                    days = days,
                    minAllowed = 1,
                    maxAllowed = 5
                }))
                using (LogContext.PushProperty("message_template_text",
                    "Validation failed in {Controller}.{Action}: days={Days}"))
                {
                    _logger.LogError(
                        "Validation failed in {Controller}.{Action}: days={Days}",
                        nameof(WeatherForecastController),
                        nameof(GetByDays),
                        days);
                }

                return BadRequest(new
                {
                    error = "ValidationException",
                    message = $"Days must be between 1 and 5. Requested: {days}",
                    code = "WEATHER_001"
                });
            }

            var forecasts = Enumerable.Range(1, days).Select(index => new WeatherForecast
            {
                Date = DateOnly.FromDateTime(DateTime.Now.AddDays(index)),
                TemperatureC = Random.Shared.Next(-20, 55),
                Summary = Summaries[Random.Shared.Next(Summaries.Length)]
            })
            .ToArray();

            activity?.SetTag("forecast.count", forecasts.Length);
            return Ok(forecasts);
        }
    }

    public class WeatherForecast
    {
        public DateOnly Date { get; set; }
        public int TemperatureC { get; set; }
        public int TemperatureF => 32 + (int)(TemperatureC / 0.5556);
        public string? Summary { get; set; }
    }
}