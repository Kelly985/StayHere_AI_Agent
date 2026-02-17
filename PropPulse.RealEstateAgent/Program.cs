using Microsoft.Azure.Functions.Worker;
using Microsoft.Azure.Functions.Worker.Builder;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using PropPulse.RealEstateAgent.Application.Handlers;
using PropPulse.RealEstateAgent.Infrastructure;
using Serilog;
using System.Reflection;

var builder = FunctionsApplication.CreateBuilder(args);

// Configure Serilog for structured logging
Log.Logger = new LoggerConfiguration()
    .WriteTo.Console()
    .WriteTo.File("logs/app-.log", rollingInterval: RollingInterval.Day)
    .CreateLogger();

builder.Services.AddLogging(loggingBuilder =>
{
    loggingBuilder.ClearProviders();
    loggingBuilder.AddSerilog();
});

// Configure Functions
builder.ConfigureFunctionsWebApplication();

// Add Application Insights
builder.Services
    .AddApplicationInsightsTelemetryWorkerService()
    .ConfigureFunctionsApplicationInsights();

// Add MediatR for CQRS
builder.Services.AddMediatR(cfg =>
{
    cfg.RegisterServicesFromAssembly(typeof(ProcessChatCommandHandler).Assembly);
});

// Add Infrastructure services
builder.Services.AddInfrastructure(builder.Configuration);

// Add JWT validation middleware
builder.Services.AddAuthentication();
builder.Services.AddAuthorization();

// Register custom middleware
builder.Services.ConfigureFunctionsWorkerDefaults(worker =>
{
    worker.UseMiddleware<Middleware.JwtValidationMiddleware>();
});

var app = builder.Build();

app.Run();
