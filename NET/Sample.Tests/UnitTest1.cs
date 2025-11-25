using System.Net;
using Microsoft.AspNetCore.Mvc.Testing;
using Xunit;
using Serilog;

using Sample.Controllers;

public class WeatherForecastControllerTests : IClassFixture<WebApplicationFactory<Program>>
{
    private readonly WebApplicationFactory<Program> _factory;

    public WeatherForecastControllerTests(WebApplicationFactory<Program> factory)
    {
        _factory = factory;
    }

    [Fact]
    public async Task Get_ReturnsForecasts_InfoLog()
    {
        var client = _factory.CreateClient();
        var response = await client.GetAsync("/WeatherForecast");

        Assert.Equal(HttpStatusCode.OK, response.StatusCode);

        // Here you'd assert logs captured by Serilog sink
        // Example: check that "forecast.count" attribute exists
    }

    [Fact]
    public async Task Get_ThrowsException_ErrorLog()
    {
        var client = _factory.CreateClient();

        // Force Summaries empty to trigger IndexOutOfRangeException
        WeatherForecastController.Summaries = Array.Empty<string>();

        var response = await client.GetAsync("/WeatherForecast");

        Assert.Equal(HttpStatusCode.InternalServerError, response.StatusCode);
    }

}
