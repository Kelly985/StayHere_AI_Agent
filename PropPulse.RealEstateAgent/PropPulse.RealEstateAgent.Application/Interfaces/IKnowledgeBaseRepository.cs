using PropPulse.RealEstateAgent.Domain.Entities;
using PropPulse.RealEstateAgent.Domain.ValueObjects;

namespace PropPulse.RealEstateAgent.Application.Interfaces;

/// <summary>
/// Repository interface for knowledge base operations
/// </summary>
public interface IKnowledgeBaseRepository
{
    Task LoadDocumentsAsync(CancellationToken cancellationToken = default);
    Task<List<SearchResult>> SearchAsync(string query, int topK = 5, CancellationToken cancellationToken = default);
    Task<Dictionary<string, object>> GetStatusAsync(CancellationToken cancellationToken = default);
    bool IsLoaded { get; }
}
