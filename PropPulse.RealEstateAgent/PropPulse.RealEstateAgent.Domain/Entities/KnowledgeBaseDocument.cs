namespace PropPulse.RealEstateAgent.Domain.Entities;

/// <summary>
/// Represents a document in the knowledge base
/// </summary>
public class KnowledgeBaseDocument
{
    public string Id { get; set; } = string.Empty;
    public string Content { get; set; } = string.Empty;
    public string Source { get; set; } = string.Empty;
    public int ChunkId { get; set; }
    public string FilePath { get; set; } = string.Empty;
    public DocumentMetadata Metadata { get; set; } = new();
}

/// <summary>
/// Metadata for a knowledge base document
/// </summary>
public class DocumentMetadata
{
    public string FileType { get; set; } = string.Empty;
    public long FileSize { get; set; }
    public DateTime Modified { get; set; }
}
