var builder = WebApplication.CreateBuilder(args);

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