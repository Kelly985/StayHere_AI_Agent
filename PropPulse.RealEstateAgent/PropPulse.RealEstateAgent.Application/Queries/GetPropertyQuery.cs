using MediatR;
using PropPulse.RealEstateAgent.Application.DTOs;

namespace PropPulse.RealEstateAgent.Application.Queries;

/// <summary>
/// Query for retrieving properties with filters
/// </summary>
public class GetPropertyQuery : IRequest<List<PropertyDto>>
{
    public string? PropertyId { get; set; }
    public string? Location { get; set; }
    public string? Amenity { get; set; }
}
