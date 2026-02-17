using MediatR;
using Microsoft.Azure.Functions.Worker;
using Microsoft.Azure.Functions.Worker.Http;
using Microsoft.Extensions.Logging;
using PropPulse.RealEstateAgent.Application.Queries;
using System.Net;
using System.Text.Json;

namespace PropPulse.RealEstateAgent.Functions;

/// <summary>
/// Azure Function for property endpoints
/// </summary>
public class PropertyFunction
{
    private readonly IMediator _mediator;
    private readonly ILogger<PropertyFunction> _logger;

    public PropertyFunction(IMediator mediator, ILogger<PropertyFunction> logger)
    {
        _mediator = mediator;
        _logger = logger;
    }

    [Function("GetProperties")]
    public async Task<HttpResponseData> GetProperties(
        [HttpTrigger(AuthorizationLevel.Function, "get", Route = "properties")] HttpRequestData req)
    {
        _logger.LogInformation("GetProperties function triggered");

        try
        {
            var queryString = req.Url.Query;
            var queryParams = ParseQueryString(queryString);
            var propertyId = queryParams.GetValueOrDefault("property_id");
            var location = queryParams.GetValueOrDefault("location");
            var amenity = queryParams.GetValueOrDefault("amenity");

            var queryRequest = new GetPropertyQuery
            {
                PropertyId = propertyId,
                Location = location,
                Amenity = amenity
            };

            var properties = await _mediator.Send(queryRequest);

            var okResponse = req.CreateResponse(HttpStatusCode.OK);
            okResponse.Headers.Add("Content-Type", "application/json");
            
            var response = new { properties = properties };
            await okResponse.WriteStringAsync(JsonSerializer.Serialize(response));

            return okResponse;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting properties");
            var errorResponse = req.CreateResponse(HttpStatusCode.InternalServerError);
            await errorResponse.WriteStringAsync($"{{\"error\":\"Internal server error\",\"message\":\"{ex.Message}\"}}");
            return errorResponse;
        }
    }

    private Dictionary<string, string> ParseQueryString(string queryString)
    {
        var result = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
        if (string.IsNullOrEmpty(queryString) || !queryString.StartsWith("?"))
            return result;

        var pairs = queryString.Substring(1).Split('&');
        foreach (var pair in pairs)
        {
            var parts = pair.Split('=', 2);
            if (parts.Length == 2)
            {
                var key = Uri.UnescapeDataString(parts[0]);
                var value = Uri.UnescapeDataString(parts[1]);
                result[key] = value;
            }
        }
        return result;
    }
}
