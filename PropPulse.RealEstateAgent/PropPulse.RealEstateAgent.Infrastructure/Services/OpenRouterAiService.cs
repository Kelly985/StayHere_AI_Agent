using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using PropPulse.RealEstateAgent.Application.Interfaces;
using System.Net.Http.Json;
using System.Text.Json;

namespace PropPulse.RealEstateAgent.Infrastructure.Services;

/// <summary>
/// OpenRouter AI service implementation
/// </summary>
public class OpenRouterAiService : IAiService
{
    private readonly HttpClient _httpClient;
    private readonly IConfiguration _configuration;
    private readonly ILogger<OpenRouterAiService> _logger;

    public OpenRouterAiService(
        HttpClient httpClient,
        IConfiguration configuration,
        ILogger<OpenRouterAiService> logger)
    {
        _httpClient = httpClient;
        _configuration = configuration;
        _logger = logger;
    }

    public async Task<string> GenerateResponseAsync(
        string prompt,
        int maxTokens = 1000,
        double temperature = 0.7,
        CancellationToken cancellationToken = default)
    {
        var apiKey = _configuration["OpenRouter:ApiKey"];
        var model = _configuration["OpenRouter:Model"] ?? "deepseek/deepseek-chat-v3.1:free";

        if (string.IsNullOrEmpty(apiKey))
        {
            _logger.LogError("OpenRouter API key is not configured");
            throw new InvalidOperationException("OpenRouter API key is not configured");
        }

        var url = "https://openrouter.ai/api/v1/chat/completions";
        var request = new
        {
            model = model,
            messages = new[]
            {
                new { role = "system", content = GetSystemPrompt() },
                new { role = "user", content = prompt }
            },
            max_tokens = maxTokens,
            temperature = temperature,
            top_p = 0.9,
            stream = false
        };

        _httpClient.DefaultRequestHeaders.Clear();
        _httpClient.DefaultRequestHeaders.Add("Authorization", $"Bearer {apiKey}");
        _httpClient.DefaultRequestHeaders.Add("Content-Type", "application/json");
        _httpClient.DefaultRequestHeaders.Add("HTTP-Referer", _configuration["BaseUrl"] ?? "http://localhost:7071");
        _httpClient.DefaultRequestHeaders.Add("X-Title", "PropPulse Real Estate AI Agent");

        try
        {
            _logger.LogDebug("Sending request to OpenRouter with model {Model}", model);
            var response = await _httpClient.PostAsJsonAsync(url, request, cancellationToken);
            response.EnsureSuccessStatusCode();

            var responseContent = await response.Content.ReadFromJsonAsync<OpenRouterResponse>(cancellationToken: cancellationToken);

            if (responseContent?.Choices != null && responseContent.Choices.Length > 0)
            {
                var generatedText = responseContent.Choices[0].Message?.Content?.Trim() ?? string.Empty;
                _logger.LogDebug("Received response from OpenRouter: {Length} characters", generatedText.Length);
                return generatedText;
            }

            _logger.LogWarning("OpenRouter returned empty response");
            return "I apologize, but I couldn't generate a response at this time.";
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error calling OpenRouter API");
            throw;
        }
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

    private class OpenRouterResponse
    {
        public OpenRouterChoice[]? Choices { get; set; }
    }

    private class OpenRouterChoice
    {
        public OpenRouterMessage? Message { get; set; }
    }

    private class OpenRouterMessage
    {
        public string? Content { get; set; }
    }
}
