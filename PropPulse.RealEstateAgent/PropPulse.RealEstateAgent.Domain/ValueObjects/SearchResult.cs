namespace PropPulse.RealEstateAgent.Domain.ValueObjects;

/// <summary>
/// Represents a search result from the knowledge base
/// </summary>
public class SearchResult
{
    public string Content { get; set; } = string.Empty;
    public string Source { get; set; } = string.Empty;
    public double Score { get; set; }
    public Dictionary<string, object> Metadata { get; set; } = new();
}
