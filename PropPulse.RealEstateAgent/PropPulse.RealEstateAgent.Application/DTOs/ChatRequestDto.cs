namespace PropPulse.RealEstateAgent.Application.DTOs;

/// <summary>
/// Request DTO for chat endpoint
/// </summary>
public class ChatRequestDto
{
    public string Query { get; set; } = string.Empty;
    public string? ConversationId { get; set; }
    public int MaxTokens { get; set; } = 1000;
    public double Temperature { get; set; } = 0.7;
}
