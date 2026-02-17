using MediatR;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using PropPulse.RealEstateAgent.Application.Commands;
using PropPulse.RealEstateAgent.Application.DTOs;
using PropPulse.RealEstateAgent.Application.Interfaces;
using System.Text.Json;
using System.Text.RegularExpressions;

namespace PropPulse.RealEstateAgent.Application.Handlers;

/// <summary>
/// Handler for recommending properties
/// </summary>
public class RecommendPropertiesCommandHandler : IRequestHandler<RecommendPropertiesCommand, RecommendResponseDto>
{
    private readonly IPropertyRepository _propertyRepository;
    private readonly IMediator _mediator;
    private readonly ILogger<RecommendPropertiesCommandHandler> _logger;
    private readonly IConfiguration _configuration;

    public RecommendPropertiesCommandHandler(
        IPropertyRepository propertyRepository,
        IMediator mediator,
        ILogger<RecommendPropertiesCommandHandler> logger,
        IConfiguration configuration)
    {
        _propertyRepository = propertyRepository;
        _mediator = mediator;
        _logger = logger;
        _configuration = configuration;
    }

    public async Task<RecommendResponseDto> Handle(RecommendPropertiesCommand request, CancellationToken cancellationToken)
    {
        var recommendRequest = request.Request;
        var conversationId = recommendRequest.ConversationId ?? Guid.NewGuid().ToString();

        _logger.LogInformation("Processing property recommendation for conversation {ConversationId}", conversationId);

        // Step 1: Get AI response
        var chatCommand = new Commands.ProcessChatCommand
        {
            Request = new ChatRequestDto
            {
                Query = recommendRequest.Query,
                ConversationId = conversationId,
                MaxTokens = 800,
                Temperature = recommendRequest.Temperature
            }
        };

        var aiResponse = await _mediator.Send(chatCommand, cancellationToken);

        // Step 2: Load properties
        var allProperties = await _propertyRepository.GetAllAsync(cancellationToken);

        // Step 3: Apply filters
        var filteredProperties = ApplyFilters(allProperties, recommendRequest.Filters);

        // Step 4: Score and rank properties
        var scoredProperties = ScoreProperties(filteredProperties, recommendRequest.Query);

        // Step 5: Get top results
        var topProperties = scoredProperties
            .Where(p => p.MatchScore >= 0.25)
            .OrderByDescending(p => p.MatchScore)
            .Take(recommendRequest.MaxResults)
            .ToList();

        // Step 6: Build response
        var baseUrl = _configuration["BasePropertyUrl"] ?? "https://stayhere-ai-agent.onrender.com/properties";
        var recommendedListings = topProperties.Select(p => new PropertyDto
        {
            PropertyId = p.Property.PropertyId,
            Title = p.Property.Title,
            Description = p.Property.Description,
            PropertyType = p.Property.PropertyType.ToString(),
            Location = $"{p.Property.Location.Suburb}, {p.Property.Location.City}",
            Price = p.Property.Price,
            Bedrooms = p.Property.Bedrooms,
            Bathrooms = p.Property.Bathrooms,
            Furnished = p.Property.Furnished,
            Amenities = p.Property.Amenities.Take(4).ToList(),
            ListingUrl = $"{baseUrl}?property_id={p.Property.PropertyId}",
            ImageUrl = p.Property.Images.FirstOrDefault(),
            MatchScore = p.MatchScore
        }).ToList();

        return new RecommendResponseDto
        {
            Status = "000",
            Message = aiResponse.Response,
            Data = new RecommendDataDto
            {
                RecommendedListings = recommendedListings,
                ConversationId = conversationId,
                Confidence = aiResponse.Confidence,
                Timestamp = DateTime.UtcNow
            }
        };
    }

    private List<Domain.Entities.Property> ApplyFilters(
        List<Domain.Entities.Property> properties,
        Dictionary<string, object>? filters)
    {
        if (filters == null || !filters.Any())
            return properties;

        var filtered = properties.AsEnumerable();

        if (filters.ContainsKey("location") && filters["location"] is string location)
        {
            filtered = filtered.Where(p =>
                p.Location.Suburb.Contains(location, StringComparison.OrdinalIgnoreCase) ||
                p.Location.City.Contains(location, StringComparison.OrdinalIgnoreCase));
        }

        if (filters.ContainsKey("min_price") && filters["min_price"] is decimal minPrice)
        {
            filtered = filtered.Where(p => p.Price >= minPrice);
        }

        if (filters.ContainsKey("max_price") && filters["max_price"] is decimal maxPrice)
        {
            filtered = filtered.Where(p => p.Price <= maxPrice);
        }

        if (filters.ContainsKey("bedrooms") && filters["bedrooms"] is int bedrooms)
        {
            filtered = filtered.Where(p => p.Bedrooms >= bedrooms);
        }

        if (filters.ContainsKey("property_type") && filters["property_type"] is string propertyType)
        {
            filtered = filtered.Where(p => p.PropertyType.ToString().Equals(propertyType, StringComparison.OrdinalIgnoreCase));
        }

        return filtered.ToList();
    }

    private List<(Domain.Entities.Property Property, double MatchScore)> ScoreProperties(
        List<Domain.Entities.Property> properties,
        string query)
    {
        var queryLower = query.ToLower();
        var queryWords = Regex.Matches(queryLower, @"\b\w+\b").Select(m => m.Value).ToHashSet();

        // Extract likely location and type from query
        var likelyLocation = properties
            .FirstOrDefault(p => queryLower.Contains(p.Location.Suburb.ToLower()))?.Location.Suburb.ToLower();

        var propertyTypes = new[] { "apartment", "bedsitter", "studio", "house", "maisonette" };
        var likelyType = propertyTypes.FirstOrDefault(t => queryLower.Contains(t));

        var scored = new List<(Domain.Entities.Property, double)>();

        foreach (var prop in properties)
        {
            var propText = string.Join(" ",
                prop.Title,
                prop.Description,
                prop.PropertyType.ToString(),
                prop.ListingType.ToString(),
                prop.Location.Suburb,
                string.Join(" ", prop.Amenities)).ToLower();

            var propWords = Regex.Matches(propText, @"\b\w+\b").Select(m => m.Value).ToHashSet();
            var intersection = queryWords.Intersect(propWords).Count();
            var union = queryWords.Union(propWords).Count();
            var textSimilarity = union > 0 ? (double)intersection / union : 0;

            // Weighted scoring
            var locationBonus = likelyLocation != null && prop.Location.Suburb.ToLower() == likelyLocation ? 0.4 : 0;
            var typeBonus = likelyType != null && prop.PropertyType.ToString().ToLower().Contains(likelyType) ? 0.3 : 0;
            var locationPenalty = likelyLocation != null && prop.Location.Suburb.ToLower() != likelyLocation ? -0.3 : 0;
            var typePenalty = likelyType != null && !prop.PropertyType.ToString().ToLower().Contains(likelyType) ? -0.25 : 0;

            var score = textSimilarity + locationBonus + typeBonus + locationPenalty + typePenalty;
            scored.Add((prop, Math.Round(score, 3)));
        }

        return scored;
    }
}
