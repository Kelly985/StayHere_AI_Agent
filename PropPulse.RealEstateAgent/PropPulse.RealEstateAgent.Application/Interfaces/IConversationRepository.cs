using PropPulse.RealEstateAgent.Domain.Entities;

namespace PropPulse.RealEstateAgent.Application.Interfaces;

/// <summary>
/// Repository interface for conversation management
/// </summary>
public interface IConversationRepository
{
    Task<Conversation?> GetByIdAsync(string conversationId, CancellationToken cancellationToken = default);
    Task<Conversation> CreateAsync(Conversation conversation, CancellationToken cancellationToken = default);
    Task<Conversation> UpdateAsync(Conversation conversation, CancellationToken cancellationToken = default);
    Task DeleteAsync(string conversationId, CancellationToken cancellationToken = default);
    Task<List<ConversationMessage>> GetHistoryAsync(string conversationId, CancellationToken cancellationToken = default);
}
