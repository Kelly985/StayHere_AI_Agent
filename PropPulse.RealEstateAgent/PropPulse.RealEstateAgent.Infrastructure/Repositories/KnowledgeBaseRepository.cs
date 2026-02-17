using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using PropPulse.RealEstateAgent.Application.Interfaces;
using PropPulse.RealEstateAgent.Domain.Entities;
using PropPulse.RealEstateAgent.Domain.ValueObjects;
using System.Text.RegularExpressions;

namespace PropPulse.RealEstateAgent.Infrastructure.Repositories;

/// <summary>
/// Simple text-based knowledge base repository
/// In production, this would use vector embeddings and a vector database
/// </summary>
public class KnowledgeBaseRepository : IKnowledgeBaseRepository
{
    private readonly IConfiguration _configuration;
    private readonly ILogger<KnowledgeBaseRepository> _logger;
    private List<KnowledgeBaseDocument> _documents = new();
    private bool _loaded = false;
    private readonly object _lock = new();

    public bool IsLoaded => _loaded;

    public KnowledgeBaseRepository(IConfiguration configuration, ILogger<KnowledgeBaseRepository> logger)
    {
        _configuration = configuration;
        _logger = logger;
    }

    public async Task LoadDocumentsAsync(CancellationToken cancellationToken = default)
    {
        if (_loaded)
            return;

        lock (_lock)
        {
            if (_loaded)
                return;

            var knowledgeBasePath = _configuration["KnowledgeBasePath"] ?? "./knowledgebase";
            var supportedTypes = new[] { ".txt" }; // Simplified - only text files

            _logger.LogInformation("Loading knowledge base from {Path}", knowledgeBasePath);

            if (!Directory.Exists(knowledgeBasePath))
            {
                _logger.LogWarning("Knowledge base path not found: {Path}", knowledgeBasePath);
                _loaded = true;
                return;
            }

            var documents = new List<KnowledgeBaseDocument>();

            foreach (var filePath in Directory.GetFiles(knowledgeBasePath, "*.*", SearchOption.AllDirectories))
            {
                var extension = Path.GetExtension(filePath).ToLower();
                if (!supportedTypes.Contains(extension))
                    continue;

                try
                {
                    var content = File.ReadAllText(filePath);
                    var chunks = SplitText(content);

                    for (int i = 0; i < chunks.Count; i++)
                    {
                        documents.Add(new KnowledgeBaseDocument
                        {
                            Id = Guid.NewGuid().ToString(),
                            Content = chunks[i],
                            Source = Path.GetFileName(filePath),
                            ChunkId = i,
                            FilePath = filePath,
                            Metadata = new DocumentMetadata
                            {
                                FileType = extension,
                                FileSize = new FileInfo(filePath).Length,
                                Modified = File.GetLastWriteTime(filePath)
                            }
                        });
                    }
                }
                catch (Exception ex)
                {
                    _logger.LogError(ex, "Error loading file {FilePath}", filePath);
                }
            }

            _documents = documents;
            _loaded = true;
            _logger.LogInformation("Knowledge base loaded: {Count} documents, {Chunks} chunks", 
                documents.GroupBy(d => d.Source).Count(), documents.Count);
        }
    }

    public async Task<List<SearchResult>> SearchAsync(string query, int topK = 5, CancellationToken cancellationToken = default)
    {
        if (!_loaded)
            await LoadDocumentsAsync(cancellationToken);

        var queryWords = Regex.Matches(query.ToLower(), @"\b\w+\b")
            .Select(m => m.Value)
            .ToHashSet();

        var results = new List<SearchResult>();

        foreach (var doc in _documents)
        {
            var contentWords = Regex.Matches(doc.Content.ToLower(), @"\b\w+\b")
                .Select(m => m.Value)
                .ToHashSet();

            var intersection = queryWords.Intersect(contentWords).Count();
            if (intersection > 0)
            {
                var union = queryWords.Union(contentWords).Count();
                var similarity = union > 0 ? (double)intersection / union : 0;

                if (similarity > 0.1) // Simple threshold
                {
                    results.Add(new SearchResult
                    {
                        Content = doc.Content,
                        Source = doc.Source,
                        Score = similarity,
                        Metadata = new Dictionary<string, object>
                        {
                            { "file_type", doc.Metadata.FileType },
                            { "file_size", doc.Metadata.FileSize },
                            { "modified", doc.Metadata.Modified }
                        }
                    });
                }
            }
        }

        return results
            .OrderByDescending(r => r.Score)
            .Take(topK)
            .ToList();
    }

    public async Task<Dictionary<string, object>> GetStatusAsync(CancellationToken cancellationToken = default)
    {
        if (!_loaded)
            await LoadDocumentsAsync(cancellationToken);

        var documentsInfo = _documents
            .GroupBy(d => d.Source)
            .Select(g => new
            {
                filename = g.Key,
                file_type = g.First().Metadata.FileType,
                size = g.First().Metadata.FileSize,
                last_modified = g.First().Metadata.Modified,
                chunks = g.Count()
            })
            .ToList();

        return new Dictionary<string, object>
        {
            { "total_documents", documentsInfo.Count },
            { "total_chunks", _documents.Count },
            { "last_updated", DateTime.UtcNow },
            { "loaded", _loaded },
            { "documents", documentsInfo }
        };
    }

    private List<string> SplitText(string text, int chunkSize = 1000, int overlap = 200)
    {
        if (text.Length <= chunkSize)
            return new List<string> { text };

        var chunks = new List<string>();
        var start = 0;

        while (start < text.Length)
        {
            var end = Math.Min(start + chunkSize, text.Length);

            // Try to break at sentence boundary
            if (end < text.Length)
            {
                for (int i = Math.Min(100, chunkSize - overlap); i > 0; i--)
                {
                    if (end - i < text.Length && ".!?".Contains(text[end - i]))
                    {
                        end = end - i + 1;
                        break;
                    }
                }
            }

            var chunk = text.Substring(start, end - start).Trim();
            if (!string.IsNullOrEmpty(chunk))
                chunks.Add(chunk);

            start = end - overlap;
        }

        return chunks;
    }
}
