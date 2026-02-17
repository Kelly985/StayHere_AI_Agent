namespace PropPulse.RealEstateAgent.Domain.Entities;

/// <summary>
/// Represents a conversation between a user and the AI agent
/// </summary>
public class Conversation
{
    public string Id { get; set; } = string.Empty;
    public List<ConversationMessage> Messages { get; set; } = new();
    public DateTime CreatedAt { get; set; }
    public DateTime UpdatedAt { get; set; }
    public string? UserId { get; set; }
}

/// <summary>
/// Represents a single message in a conversation
/// </summary>
public class ConversationMessage
{
    public string Role { get; set; } = string.Empty; // "user" or "assistant"
    public string Content { get; set; } = string.Empty;
    public DateTime Timestamp { get; set; }
}
