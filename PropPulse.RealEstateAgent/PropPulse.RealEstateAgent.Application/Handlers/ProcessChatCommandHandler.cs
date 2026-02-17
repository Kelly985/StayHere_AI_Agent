using MediatR;
using Microsoft.Extensions.Logging;
using PropPulse.RealEstateAgent.Application.Commands;
using PropPulse.RealEstateAgent.Application.DTOs;
using PropPulse.RealEstateAgent.Application.Interfaces;
using PropPulse.RealEstateAgent.Domain.ValueObjects;

namespace PropPulse.RealEstateAgent.Application.Handlers;

/// <summary>
/// Handler for processing chat commands
/// </summary>
public class ProcessChatCommandHandler : IRequestHandler<ProcessChatCommand, ChatResponseDto>
{
    private readonly IKnowledgeBaseRepository _knowledgeBaseRepository;
    private readonly IAiService _aiService;
    private readonly IConversationRepository _conversationRepository;
    private readonly ILogger<ProcessChatCommandHandler> _logger;

    public ProcessChatCommandHandler(
        IKnowledgeBaseRepository knowledgeBaseRepository,
        IAiService aiService,
        IConversationRepository conversationRepository,
        ILogger<ProcessChatCommandHandler> logger)
    {
        _knowledgeBaseRepository = knowledgeBaseRepository;
        _aiService = aiService;
        _conversationRepository = conversationRepository;
        _logger = logger;
    }

    public async Task<ChatResponseDto> Handle(ProcessChatCommand request, CancellationToken cancellationToken)
    {
        var chatRequest = request.Request;
        var conversationId = chatRequest.ConversationId ?? Guid.NewGuid().ToString();

        _logger.LogInformation("Processing chat query for conversation {ConversationId}", conversationId);

        // Search knowledge base
        var searchResults = await _knowledgeBaseRepository.SearchAsync(
            chatRequest.Query,
            topK: 5,
            cancellationToken);

        // Prepare context
        var context = PrepareContext(searchResults);

        // Get conversation history
        var history = await _conversationRepository.GetHistoryAsync(conversationId, cancellationToken);

        // Build prompt
        var prompt = BuildPrompt(chatRequest.Query, context, history);

        // Generate response
        var response = await _aiService.GenerateResponseAsync(
            prompt,
            chatRequest.MaxTokens,
            chatRequest.Temperature,
            cancellationToken);

        // Calculate confidence
        var confidence = CalculateConfidence(searchResults, response);

        // Update conversation
        var conversation = await _conversationRepository.GetByIdAsync(conversationId, cancellationToken);
        if (conversation == null)
        {
            conversation = new Domain.Entities.Conversation
            {
                Id = conversationId,
                CreatedAt = DateTime.UtcNow,
                UpdatedAt = DateTime.UtcNow
            };
            await _conversationRepository.CreateAsync(conversation, cancellationToken);
        }

        conversation.Messages.Add(new Domain.Entities.ConversationMessage
        {
            Role = "user",
            Content = chatRequest.Query,
            Timestamp = DateTime.UtcNow
        });
        conversation.Messages.Add(new Domain.Entities.ConversationMessage
        {
            Role = "assistant",
            Content = response,
            Timestamp = DateTime.UtcNow
        });
        conversation.UpdatedAt = DateTime.UtcNow;
        await _conversationRepository.UpdateAsync(conversation, cancellationToken);

        return new ChatResponseDto
        {
            Response = response,
            ConversationId = conversationId,
            Sources = searchResults.Select(r => r.Source).ToList(),
            Confidence = confidence,
            Timestamp = DateTime.UtcNow
        };
    }

    private string PrepareContext(List<SearchResult> searchResults)
    {
        if (!searchResults.Any())
            return "No specific information found in knowledge base.";

        var contextParts = searchResults.Select(r => $"Source: {r.Source}\n{r.Content}\n");
        return string.Join("\n---\n", contextParts);
    }

    private string BuildPrompt(string query, string context, List<Domain.Entities.ConversationMessage> history)
    {
        var systemPrompt = GetSystemPrompt();
        var promptParts = new List<string> { systemPrompt };

        if (!string.IsNullOrEmpty(context))
        {
            promptParts.Add($"\n\nRelevant Information from Knowledge Base:\n{context}");
        }

        if (history.Any())
        {
            promptParts.Add("\n\nConversation History:");
            foreach (var exchange in history.TakeLast(4))
            {
                var role = exchange.Role == "assistant" ? "You" : "User";
                promptParts.Add($"{role}: {exchange.Content}");
            }
        }

        promptParts.Add($"\n\nCurrent User Question: {query}");
        promptParts.Add("\nYour Response:");

        return string.Join("\n", promptParts);
    }

    private string GetSystemPrompt()
    {
        return @"You are a knowledgeable Kenyan real estate assistant. Have natural conversations about property prices, locations, and market trends in Kenya.

CONVERSATION RULES:
- Keep responses conversational and concise (2-4 sentences max)
- Only use greetings like ""Hey"" or ""Hi"" for the FIRST message in a conversation
- For follow-up messages, jump straight to the answer
- Remember what you've discussed and build on it naturally
- Stay on topic and reference previous questions when relevant
- Don't repeat information you've already provided

RESPONSE STYLE:
- Give specific prices and examples when possible
- Use natural, friendly tone without being overly casual
- If unsure, give reasonable estimates and suggest checking current sources
- Focus directly on what they're asking

You know about property markets across Kenya, especially Nairobi areas like Westlands, Karen, Kilimani, etc.

Be helpful, context-aware, and conversational.";
    }

    private double CalculateConfidence(List<SearchResult> searchResults, string response)
    {
        if (!searchResults.Any())
            return 0.3;

        var avgScore = searchResults.Average(r => r.Score);
        var responseFactor = Math.Min(response.Length / 500.0, 1.0);
        var sourceFactor = Math.Min(searchResults.Count / 5.0, 1.0);

        return Math.Min((avgScore * 0.5 + responseFactor * 0.3 + sourceFactor * 0.2), 1.0);
    }
}
