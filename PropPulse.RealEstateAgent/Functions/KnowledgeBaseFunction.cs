using MediatR;
using Microsoft.Azure.Functions.Worker;
using Microsoft.Azure.Functions.Worker.Http;
using Microsoft.Extensions.Logging;
using PropPulse.RealEstateAgent.Application.Queries;
using System.Net;
using System.Text.Json;

namespace PropPulse.RealEstateAgent.Functions;

/// <summary>
/// Azure Function for knowledge base endpoints
/// </summary>
public class KnowledgeBaseFunction
{
    private readonly IMediator _mediator;
    private readonly ILogger<KnowledgeBaseFunction> _logger;

    public KnowledgeBaseFunction(IMediator mediator, ILogger<KnowledgeBaseFunction> logger)
    {
        _mediator = mediator;
        _logger = logger;
    }

    [Function("GetKnowledgeBaseStatus")]
    public async Task<HttpResponseData> GetStatus(
        [HttpTrigger(AuthorizationLevel.Function, "get", Route = "knowledge/status")] HttpRequestData req)
    {
        _logger.LogInformation("GetKnowledgeBaseStatus function triggered");

        try
        {
            var query = new GetKnowledgeBaseStatusQuery();
            var status = await _mediator.Send(query);

            var response = req.CreateResponse(HttpStatusCode.OK);
            response.Headers.Add("Content-Type", "application/json");
            await response.WriteStringAsync(JsonSerializer.Serialize(status));

            return response;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting knowledge base status");
            var errorResponse = req.CreateResponse(HttpStatusCode.InternalServerError);
            await errorResponse.WriteStringAsync($"{{\"error\":\"Internal server error\",\"message\":\"{ex.Message}\"}}");
            return errorResponse;
        }
    }
}
