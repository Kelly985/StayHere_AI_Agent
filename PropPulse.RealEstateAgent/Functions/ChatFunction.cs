using MediatR;
using Microsoft.Azure.Functions.Worker;
using Microsoft.Azure.Functions.Worker.Http;
using Microsoft.Extensions.Logging;
using PropPulse.RealEstateAgent.Application.Commands;
using PropPulse.RealEstateAgent.Application.DTOs;
using System.Net;
using System.Text.Json;

namespace PropPulse.RealEstateAgent.Functions;

/// <summary>
/// Azure Function for chat endpoint
/// </summary>
public class ChatFunction
{
    private readonly IMediator _mediator;
    private readonly ILogger<ChatFunction> _logger;

    public ChatFunction(IMediator mediator, ILogger<ChatFunction> logger)
    {
        _mediator = mediator;
        _logger = logger;
    }

    [Function("Chat")]
    public async Task<HttpResponseData> Run(
        [HttpTrigger(AuthorizationLevel.Function, "post", Route = "chat")] HttpRequestData req)
    {
        _logger.LogInformation("Chat function triggered");

        try
        {
            var requestBody = await new StreamReader(req.Body).ReadToEndAsync();
            var chatRequest = JsonSerializer.Deserialize<ChatRequestDto>(requestBody, new JsonSerializerOptions
            {
                PropertyNameCaseInsensitive = true
            });

            if (chatRequest == null || string.IsNullOrEmpty(chatRequest.Query))
            {
                var badRequestResponse = req.CreateResponse(HttpStatusCode.BadRequest);
                await badRequestResponse.WriteStringAsync("{\"error\":\"Invalid request. Query is required.\"}");
                return badRequestResponse;
            }

            var command = new ProcessChatCommand { Request = chatRequest };
            var response = await _mediator.Send(command);

            var okResponse = req.CreateResponse(HttpStatusCode.OK);
            okResponse.Headers.Add("Content-Type", "application/json");
            await okResponse.WriteStringAsync(JsonSerializer.Serialize(response));

            return okResponse;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error processing chat request");
            var errorResponse = req.CreateResponse(HttpStatusCode.InternalServerError);
            await errorResponse.WriteStringAsync($"{{\"error\":\"Internal server error\",\"message\":\"{ex.Message}\"}}");
            return errorResponse;
        }
    }
}
