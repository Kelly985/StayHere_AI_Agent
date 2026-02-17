namespace PropPulse.RealEstateAgent.Application.DTOs;

/// <summary>
/// Request DTO for property recommendation endpoint
/// </summary>
public class RecommendRequestDto
{
    public string Query { get; set; } = string.Empty;
    public string? ConversationId { get; set; }
    public int MaxResults { get; set; } = 10;
    public Dictionary<string, object>? Filters { get; set; }
    public double Temperature { get; set; } = 0.7;
}
