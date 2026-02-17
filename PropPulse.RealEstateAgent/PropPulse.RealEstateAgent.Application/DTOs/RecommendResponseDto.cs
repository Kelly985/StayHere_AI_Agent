namespace PropPulse.RealEstateAgent.Application.DTOs;

/// <summary>
/// Response DTO for property recommendation endpoint
/// </summary>
public class RecommendResponseDto
{
    public string Status { get; set; } = "000";
    public string Message { get; set; } = string.Empty;
    public RecommendDataDto Data { get; set; } = new();
}

/// <summary>
/// Data portion of recommendation response
/// </summary>
public class RecommendDataDto
{
    public List<PropertyDto> RecommendedListings { get; set; } = new();
    public string? ConversationId { get; set; }
    public double Confidence { get; set; }
    public DateTime Timestamp { get; set; } = DateTime.UtcNow;
}
