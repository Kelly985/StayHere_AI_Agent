namespace PropPulse.RealEstateAgent.Application.DTOs;

/// <summary>
/// Response DTO for chat endpoint
/// </summary>
public class ChatResponseDto
{
    public string Response { get; set; } = string.Empty;
    public string ConversationId { get; set; } = string.Empty;
    public List<string> Sources { get; set; } = new();
    public double Confidence { get; set; }
    public DateTime Timestamp { get; set; } = DateTime.UtcNow;
}
