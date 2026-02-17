namespace PropPulse.RealEstateAgent.Domain.Entities;

/// <summary>
/// Represents a real estate property
/// </summary>
public class Property
{
    public string PropertyId { get; set; } = string.Empty;
    public string Title { get; set; } = string.Empty;
    public string Description { get; set; } = string.Empty;
    public PropertyType PropertyType { get; set; }
    public ListingType ListingType { get; set; }
    public PropertyLocation Location { get; set; } = new();
    public decimal Price { get; set; }
    public int Bedrooms { get; set; }
    public int Bathrooms { get; set; }
    public bool Furnished { get; set; }
    public List<string> Amenities { get; set; } = new();
    public List<string> Images { get; set; } = new();
    public decimal Rating { get; set; }
    public DateTime CreatedAt { get; set; }
    public DateTime UpdatedAt { get; set; }
}

/// <summary>
/// Property type enumeration
/// </summary>
public enum PropertyType
{
    Apartment,
    House,
    Bedsitter,
    Studio,
    Maisonette,
    Commercial,
    Land
}

/// <summary>
/// Listing type enumeration
/// </summary>
public enum ListingType
{
    Rent,
    Sale,
    Investment
}

/// <summary>
/// Property location value object
/// </summary>
public class PropertyLocation
{
    public string Suburb { get; set; } = string.Empty;
    public string City { get; set; } = string.Empty;
    public string County { get; set; } = string.Empty;
    public string? Street { get; set; }
}
