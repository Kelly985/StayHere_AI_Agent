using MediatR;
using PropPulse.RealEstateAgent.Application.DTOs;

namespace PropPulse.RealEstateAgent.Application.Commands;

/// <summary>
/// Command for recommending properties based on query
/// </summary>
public class RecommendPropertiesCommand : IRequest<RecommendResponseDto>
{
    public RecommendRequestDto Request { get; set; } = new();
}
