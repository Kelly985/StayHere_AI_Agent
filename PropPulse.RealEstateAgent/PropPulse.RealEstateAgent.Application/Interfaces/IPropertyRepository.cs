using PropPulse.RealEstateAgent.Domain.Entities;

namespace PropPulse.RealEstateAgent.Application.Interfaces;

/// <summary>
/// Repository interface for property management
/// </summary>
public interface IPropertyRepository
{
    Task<Property?> GetByIdAsync(string propertyId, CancellationToken cancellationToken = default);
    Task<List<Property>> SearchAsync(
        string? location = null,
        string? amenity = null,
        string? propertyId = null,
        CancellationToken cancellationToken = default);
    Task<List<Property>> GetAllAsync(CancellationToken cancellationToken = default);
}
