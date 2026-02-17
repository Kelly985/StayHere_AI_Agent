using PropPulse.RealEstateAgent.Domain.ValueObjects;

namespace PropPulse.RealEstateAgent.Application.Interfaces;

/// <summary>
/// Interface for AI service integration (OpenRouter/Together AI)
/// </summary>
public interface IAiService
{
    Task<string> GenerateResponseAsync(
        string prompt,
        int maxTokens = 1000,
        double temperature = 0.7,
        CancellationToken cancellationToken = default);
}
