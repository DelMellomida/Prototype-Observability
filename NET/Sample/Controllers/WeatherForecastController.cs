using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Logging;
using OpenTelemetry.Trace;
using Sample.Telemetry;
using System.Diagnostics;

namespace Sample.Controllers
{
    [ApiController]
    [Route("[controller]")]
    public class WeatherForecastController : ControllerBase
    {
        private readonly ILogger<WeatherForecastController> _logger;
        private readonly ITelemetryHelper _telemetryHelper;

        // Inject ILogger and ITelemetryHelper via constructor
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
            if (days < 1 || days > 5)
            {
                activity?.SetTag("validation.failed", true);
                activity?.SetTag("error.type", "ValidationError");

                // Log validation failure as Error
                _logger.LogError("Validation failed in {Controller}.{Action}: days={Days}",
                    nameof(WeatherForecastController), nameof(GetByDays), days);

                return BadRequest(new { error = "Days must be between 1 and 5" });
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
}
