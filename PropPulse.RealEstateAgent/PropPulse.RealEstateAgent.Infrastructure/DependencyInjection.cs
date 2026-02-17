using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using PropPulse.RealEstateAgent.Application.Interfaces;
using PropPulse.RealEstateAgent.Infrastructure.Repositories;
using PropPulse.RealEstateAgent.Infrastructure.Services;

namespace PropPulse.RealEstateAgent.Infrastructure;

/// <summary>
/// Extension methods for dependency injection
/// </summary>
public static class DependencyInjection
{
    public static IServiceCollection AddInfrastructure(this IServiceCollection services, IConfiguration configuration)
    {
        // Repositories
        services.AddSingleton<IConversationRepository, ConversationRepository>();
        services.AddSingleton<IPropertyRepository, PropertyRepository>();
        services.AddSingleton<IKnowledgeBaseRepository, KnowledgeBaseRepository>();

        // Services
        services.AddHttpClient<IAiService, OpenRouterAiService>(client =>
        {
            client.Timeout = TimeSpan.FromSeconds(60);
        });

        return services;
    }
}
