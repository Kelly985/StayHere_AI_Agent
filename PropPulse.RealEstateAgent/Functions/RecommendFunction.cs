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
/// Azure Function for property recommendation endpoint
/// </summary>
public class RecommendFunction
{
    private readonly IMediator _mediator;
    private readonly ILogger<RecommendFunction> _logger;

    public RecommendFunction(IMediator mediator, ILogger<RecommendFunction> logger)
    {
        _mediator = mediator;
        _logger = logger;
    }

    [Function("RespondAndRecommend")]
    public async Task<HttpResponseData> Run(
        [HttpTrigger(AuthorizationLevel.Function, "post", Route = "respondandrecommend")] HttpRequestData req)
    {
        _logger.LogInformation("RespondAndRecommend function triggered");

        try
        {
            var requestBody = await new StreamReader(req.Body).ReadToEndAsync();
            var recommendRequest = JsonSerializer.Deserialize<RecommendRequestDto>(requestBody, new JsonSerializerOptions
            {
                PropertyNameCaseInsensitive = true
            });

            if (recommendRequest == null || string.IsNullOrEmpty(recommendRequest.Query))
            {
                var badRequestResponse = req.CreateResponse(HttpStatusCode.BadRequest);
                await badRequestResponse.WriteStringAsync("{\"error\":\"Invalid request. Query is required.\"}");
                return badRequestResponse;
            }

            var command = new RecommendPropertiesCommand { Request = recommendRequest };
            var response = await _mediator.Send(command);

            var okResponse = req.CreateResponse(HttpStatusCode.OK);
            okResponse.Headers.Add("Content-Type", "application/json");
            await okResponse.WriteStringAsync(JsonSerializer.Serialize(response));

            return okResponse;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error processing recommendation request");
            var errorResponse = req.CreateResponse(HttpStatusCode.InternalServerError);
            await errorResponse.WriteStringAsync($"{{\"error\":\"Internal server error\",\"message\":\"{ex.Message}\"}}");
            return errorResponse;
        }
    }
}
