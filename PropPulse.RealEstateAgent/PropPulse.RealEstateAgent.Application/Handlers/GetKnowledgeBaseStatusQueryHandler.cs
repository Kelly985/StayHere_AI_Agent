using MediatR;
using Microsoft.Extensions.Logging;
using PropPulse.RealEstateAgent.Application.Interfaces;
using PropPulse.RealEstateAgent.Application.Queries;

namespace PropPulse.RealEstateAgent.Application.Handlers;

/// <summary>
/// Handler for getting knowledge base status
/// </summary>
public class GetKnowledgeBaseStatusQueryHandler : IRequestHandler<GetKnowledgeBaseStatusQuery, Dictionary<string, object>>
{
    private readonly IKnowledgeBaseRepository _knowledgeBaseRepository;
    private readonly ILogger<GetKnowledgeBaseStatusQueryHandler> _logger;

    public GetKnowledgeBaseStatusQueryHandler(
        IKnowledgeBaseRepository knowledgeBaseRepository,
        ILogger<GetKnowledgeBaseStatusQueryHandler> logger)
    {
        _knowledgeBaseRepository = knowledgeBaseRepository;
        _logger = logger;
    }

    public async Task<Dictionary<string, object>> Handle(GetKnowledgeBaseStatusQuery request, CancellationToken cancellationToken)
    {
        _logger.LogInformation("Getting knowledge base status");

        return await _knowledgeBaseRepository.GetStatusAsync(cancellationToken);
    }
}
