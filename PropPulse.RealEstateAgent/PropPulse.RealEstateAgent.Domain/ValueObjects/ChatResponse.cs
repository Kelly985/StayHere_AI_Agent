namespace PropPulse.RealEstateAgent.Domain.ValueObjects;

/// <summary>
/// Represents a chat response from the AI agent
/// </summary>
public class ChatResponse
{
    public string Response { get; set; } = string.Empty;
    public string ConversationId { get; set; } = string.Empty;
    public List<string> Sources { get; set; } = new();
    public double Confidence { get; set; }
    public DateTime Timestamp { get; set; } = DateTime.UtcNow;
}
