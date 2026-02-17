using MediatR;
using Microsoft.Extensions.Logging;
using PropPulse.RealEstateAgent.Application.DTOs;
using PropPulse.RealEstateAgent.Application.Interfaces;
using PropPulse.RealEstateAgent.Application.Queries;

namespace PropPulse.RealEstateAgent.Application.Handlers;

/// <summary>
/// Handler for getting properties
/// </summary>
public class GetPropertyQueryHandler : IRequestHandler<GetPropertyQuery, List<PropertyDto>>
{
    private readonly IPropertyRepository _propertyRepository;
    private readonly ILogger<GetPropertyQueryHandler> _logger;

    public GetPropertyQueryHandler(
        IPropertyRepository propertyRepository,
        ILogger<GetPropertyQueryHandler> logger)
    {
        _propertyRepository = propertyRepository;
        _logger = logger;
    }

    public async Task<List<PropertyDto>> Handle(GetPropertyQuery request, CancellationToken cancellationToken)
    {
        _logger.LogInformation("Getting properties with filters: PropertyId={PropertyId}, Location={Location}, Amenity={Amenity}",
            request.PropertyId, request.Location, request.Amenity);

        var properties = await _propertyRepository.SearchAsync(
            request.Location,
            request.Amenity,
            request.PropertyId,
            cancellationToken);

        return properties.Select(p => new PropertyDto
        {
            PropertyId = p.PropertyId,
            Title = p.Title,
            Description = p.Description,
            PropertyType = p.PropertyType.ToString(),
            Location = $"{p.Location.Suburb}, {p.Location.City}",
            Price = p.Price,
            Bedrooms = p.Bedrooms,
            Bathrooms = p.Bathrooms,
            Furnished = p.Furnished,
            Amenities = p.Amenities,
            ImageUrl = p.Images.FirstOrDefault()
        }).ToList();
    }
}
