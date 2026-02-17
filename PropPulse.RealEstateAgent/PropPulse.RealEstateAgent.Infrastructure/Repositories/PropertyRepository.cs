using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using PropPulse.RealEstateAgent.Application.Interfaces;
using PropPulse.RealEstateAgent.Domain.Entities;
using System.Text.Json;

namespace PropPulse.RealEstateAgent.Infrastructure.Repositories;

/// <summary>
/// File-based implementation of property repository
/// In production, this would use a database (Cosmos DB, SQL, etc.)
/// </summary>
public class PropertyRepository : IPropertyRepository
{
    private readonly IConfiguration _configuration;
    private readonly ILogger<PropertyRepository> _logger;
    private List<Property>? _properties;

    public PropertyRepository(IConfiguration configuration, ILogger<PropertyRepository> logger)
    {
        _configuration = configuration;
        _logger = logger;
    }

    private async Task<List<Property>> LoadPropertiesAsync(CancellationToken cancellationToken)
    {
        if (_properties != null)
            return _properties;

        var propertiesPath = _configuration["PropertiesDataPath"] ?? "properties_data.json";
        
        try
        {
            if (!File.Exists(propertiesPath))
            {
                _logger.LogWarning("Properties file not found at {Path}", propertiesPath);
                return new List<Property>();
            }

            var json = await File.ReadAllTextAsync(propertiesPath, cancellationToken);
            var jsonProperties = JsonSerializer.Deserialize<List<JsonProperty>>(json);

            if (jsonProperties == null)
                return new List<Property>();

            _properties = jsonProperties.Select(ConvertToProperty).ToList();
            _logger.LogInformation("Loaded {Count} properties from {Path}", _properties.Count, propertiesPath);
            return _properties;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error loading properties from {Path}", propertiesPath);
            return new List<Property>();
        }
    }

    public async Task<Property?> GetByIdAsync(string propertyId, CancellationToken cancellationToken = default)
    {
        var properties = await LoadPropertiesAsync(cancellationToken);
        return properties.FirstOrDefault(p => p.PropertyId.Equals(propertyId, StringComparison.OrdinalIgnoreCase));
    }

    public async Task<List<Property>> SearchAsync(
        string? location = null,
        string? amenity = null,
        string? propertyId = null,
        CancellationToken cancellationToken = default)
    {
        var properties = await LoadPropertiesAsync(cancellationToken);

        if (!string.IsNullOrEmpty(propertyId))
        {
            var prop = properties.FirstOrDefault(p => p.PropertyId.Equals(propertyId, StringComparison.OrdinalIgnoreCase));
            return prop != null ? new List<Property> { prop } : new List<Property>();
        }

        var filtered = properties.AsEnumerable();

        if (!string.IsNullOrEmpty(location))
        {
            var locationLower = location.ToLower();
            filtered = filtered.Where(p =>
                p.Location.Suburb.Contains(locationLower, StringComparison.OrdinalIgnoreCase) ||
                p.Location.City.Contains(locationLower, StringComparison.OrdinalIgnoreCase) ||
                p.Location.County.Contains(locationLower, StringComparison.OrdinalIgnoreCase));
        }

        if (!string.IsNullOrEmpty(amenity))
        {
            var amenities = amenity.Split(',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries);
            filtered = filtered.Where(p =>
                amenities.All(a => p.Amenities.Any(pa => pa.Contains(a, StringComparison.OrdinalIgnoreCase))));
        }

        return filtered.ToList();
    }

    public async Task<List<Property>> GetAllAsync(CancellationToken cancellationToken = default)
    {
        return await LoadPropertiesAsync(cancellationToken);
    }

    private Property ConvertToProperty(JsonProperty jsonProp)
    {
        return new Property
        {
            PropertyId = jsonProp.PropertyId ?? jsonProp.Id ?? Guid.NewGuid().ToString(),
            Title = jsonProp.Title ?? string.Empty,
            Description = jsonProp.Description ?? string.Empty,
            PropertyType = ParsePropertyType(jsonProp.PropertyType),
            ListingType = ParseListingType(jsonProp.ListingType),
            Location = new PropertyLocation
            {
                Suburb = jsonProp.Location?.Suburb ?? string.Empty,
                City = jsonProp.Location?.City ?? string.Empty,
                County = jsonProp.Location?.County ?? string.Empty,
                Street = jsonProp.Location?.Street
            },
            Price = jsonProp.Price,
            Bedrooms = jsonProp.Bedrooms,
            Bathrooms = jsonProp.Bathrooms,
            Furnished = jsonProp.Furnished,
            Amenities = jsonProp.Amenities ?? new List<string>(),
            Images = jsonProp.Images ?? new List<string>(),
            Rating = jsonProp.Rating,
            CreatedAt = DateTime.UtcNow,
            UpdatedAt = DateTime.UtcNow
        };
    }

    private PropertyType ParsePropertyType(string? type)
    {
        if (string.IsNullOrEmpty(type))
            return PropertyType.Apartment;

        return type.ToLower() switch
        {
            "apartment" => PropertyType.Apartment,
            "house" => PropertyType.House,
            "bedsitter" => PropertyType.Bedsitter,
            "studio" => PropertyType.Studio,
            "maisonette" => PropertyType.Maisonette,
            "commercial" => PropertyType.Commercial,
            "land" => PropertyType.Land,
            _ => PropertyType.Apartment
        };
    }

    private ListingType ParseListingType(string? type)
    {
        if (string.IsNullOrEmpty(type))
            return ListingType.Rent;

        return type.ToLower() switch
        {
            "rent" or "rental" => ListingType.Rent,
            "sale" or "buy" => ListingType.Sale,
            "investment" => ListingType.Investment,
            _ => ListingType.Rent
        };
    }

    private class JsonProperty
    {
        public string? Id { get; set; }
        public string? PropertyId { get; set; }
        public string? Title { get; set; }
        public string? Description { get; set; }
        public string? PropertyType { get; set; }
        public string? ListingType { get; set; }
        public JsonLocation? Location { get; set; }
        public decimal Price { get; set; }
        public int Bedrooms { get; set; }
        public int Bathrooms { get; set; }
        public bool Furnished { get; set; }
        public List<string>? Amenities { get; set; }
        public List<string>? Images { get; set; }
        public decimal Rating { get; set; }
    }

    private class JsonLocation
    {
        public string? Suburb { get; set; }
        public string? City { get; set; }
        public string? County { get; set; }
        public string? Street { get; set; }
    }
}
