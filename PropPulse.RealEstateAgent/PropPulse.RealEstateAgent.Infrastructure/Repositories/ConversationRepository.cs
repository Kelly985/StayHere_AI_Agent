using Microsoft.Extensions.Logging;
using PropPulse.RealEstateAgent.Application.Interfaces;
using PropPulse.RealEstateAgent.Domain.Entities;
using System.Collections.Concurrent;

namespace PropPulse.RealEstateAgent.Infrastructure.Repositories;

/// <summary>
/// In-memory implementation of conversation repository
/// In production, this would use a database (Cosmos DB, SQL, etc.)
/// </summary>
public class ConversationRepository : IConversationRepository
{
    private readonly ConcurrentDictionary<string, Conversation> _conversations = new();
    private readonly ILogger<ConversationRepository> _logger;

    public ConversationRepository(ILogger<ConversationRepository> logger)
    {
        _logger = logger;
    }

    public Task<Conversation?> GetByIdAsync(string conversationId, CancellationToken cancellationToken = default)
    {
        _conversations.TryGetValue(conversationId, out var conversation);
        return Task.FromResult(conversation);
    }

    public Task<Conversation> CreateAsync(Conversation conversation, CancellationToken cancellationToken = default)
    {
        conversation.Id ??= Guid.NewGuid().ToString();
        conversation.CreatedAt = DateTime.UtcNow;
        conversation.UpdatedAt = DateTime.UtcNow;
        _conversations[conversation.Id] = conversation;
        _logger.LogInformation("Created conversation {ConversationId}", conversation.Id);
        return Task.FromResult(conversation);
    }

    public Task<Conversation> UpdateAsync(Conversation conversation, CancellationToken cancellationToken = default)
    {
        conversation.UpdatedAt = DateTime.UtcNow;
        _conversations[conversation.Id] = conversation;
        _logger.LogInformation("Updated conversation {ConversationId}", conversation.Id);
        return Task.FromResult(conversation);
    }

    public Task DeleteAsync(string conversationId, CancellationToken cancellationToken = default)
    {
        _conversations.TryRemove(conversationId, out _);
        _logger.LogInformation("Deleted conversation {ConversationId}", conversationId);
        return Task.CompletedTask;
    }

    public Task<List<ConversationMessage>> GetHistoryAsync(string conversationId, CancellationToken cancellationToken = default)
    {
        if (_conversations.TryGetValue(conversationId, out var conversation))
        {
            return Task.FromResult(conversation.Messages);
        }
        return Task.FromResult(new List<ConversationMessage>());
    }
}
