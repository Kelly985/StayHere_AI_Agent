using MediatR;

namespace PropPulse.RealEstateAgent.Application.Queries;

/// <summary>
/// Query for getting knowledge base status
/// </summary>
public class GetKnowledgeBaseStatusQuery : IRequest<Dictionary<string, object>>
{
}
