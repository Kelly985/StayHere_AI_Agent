namespace PropPulse.RealEstateAgent.Application.DTOs;

/// <summary>
/// Response DTO for property queries
/// </summary>
public class PropertyResponseDto
{
    public List<PropertyDto> Properties { get; set; } = new();
    public string MarketInsights { get; set; } = string.Empty;
    public List<string> Recommendations { get; set; } = new();
    public Dictionary<string, object> PriceTrends { get; set; } = new();
}

/// <summary>
/// Property DTO
/// </summary>
public class PropertyDto
{
    public string PropertyId { get; set; } = string.Empty;
    public string Title { get; set; } = string.Empty;
    public string Description { get; set; } = string.Empty;
    public string PropertyType { get; set; } = string.Empty;
    public string Location { get; set; } = string.Empty;
    public decimal Price { get; set; }
    public int Bedrooms { get; set; }
    public int Bathrooms { get; set; }
    public bool Furnished { get; set; }
    public List<string> Amenities { get; set; } = new();
    public string? ListingUrl { get; set; }
    public string? ImageUrl { get; set; }
    public double MatchScore { get; set; }
}
