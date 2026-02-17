namespace PropPulse.RealEstateAgent.Application.DTOs;

/// <summary>
/// DTO for property search queries
/// </summary>
public class PropertyQueryDto
{
    public string? PropertyType { get; set; }
    public string? Location { get; set; }
    public decimal? BudgetMin { get; set; }
    public decimal? BudgetMax { get; set; }
    public int? Bedrooms { get; set; }
    public string? TransactionType { get; set; }
}
