using System.Diagnostics;

var builder = WebApplication.CreateBuilder(args);

// Ensure W3C trace context and predictable Activity id format across libraries
Activity.DefaultIdFormat = ActivityIdFormat.W3C;
Activity.ForceDefaultIdFormat = true;

// Note: the OpenTelemetry .NET SDK already uses W3C TraceContext + Baggage by default;
// avoid replacing the default propagator here since the API to set it varies by SDK version.

// 1. The Paved Road: One line to configure everything
builder.AddCompanyObservability();

builder.Services.AddControllers();
builder.Services.AddHealthChecks();
builder.Services.AddOpenApi();

var app = builder.Build();

// 2. The Middleware: One line to handle exceptions and logging
app.UseCompanyObservability();

if (app.Environment.IsDevelopment())
{
    app.MapOpenApi();
}

app.UseHttpsRedirection();
app.UseAuthorization();
app.MapControllers();

app.Run();