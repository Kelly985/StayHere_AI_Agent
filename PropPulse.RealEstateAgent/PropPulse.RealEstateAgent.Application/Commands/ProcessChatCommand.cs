using MediatR;
using PropPulse.RealEstateAgent.Application.DTOs;

namespace PropPulse.RealEstateAgent.Application.Commands;

/// <summary>
/// Command for processing a chat query
/// </summary>
public class ProcessChatCommand : IRequest<ChatResponseDto>
{
    public ChatRequestDto Request { get; set; } = new();
}
