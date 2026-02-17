using Microsoft.Azure.Functions.Worker;
using Microsoft.Azure.Functions.Worker.Http;
using Microsoft.Azure.Functions.Worker.Middleware;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using Microsoft.IdentityModel.Tokens;
using System.IdentityModel.Tokens.Jwt;
using System.Net;
using System.Security.Claims;

namespace PropPulse.RealEstateAgent.Middleware;

/// <summary>
/// Middleware to validate JWT tokens from Entra ID via APIM
/// </summary>
public class JwtValidationMiddleware : IFunctionsWorkerMiddleware
{
    private readonly IConfiguration _configuration;
    private readonly ILogger<JwtValidationMiddleware> _logger;

    public JwtValidationMiddleware(IConfiguration configuration, ILogger<JwtValidationMiddleware> logger)
    {
        _configuration = configuration;
        _logger = logger;
    }

    public async Task Invoke(FunctionContext context, FunctionExecutionDelegate next)
    {
        // Skip validation for health check and public endpoints
        var request = await context.GetHttpRequestDataAsync();
        if (request == null)
        {
            await next(context);
            return;
        }

        var path = request.Url.AbsolutePath.ToLower();
        if (path == "/health" || path == "/" || path == "/api/health" || path == "/api/")
        {
            await next(context);
            return;
        }

        // Get token from Authorization header
        if (!request.Headers.TryGetValues("Authorization", out var authHeaders))
        {
            _logger.LogWarning("Missing Authorization header for {Path}", path);
            await ReturnUnauthorized(context);
            return;
        }

        var authHeader = authHeaders.FirstOrDefault();
        if (string.IsNullOrEmpty(authHeader) || !authHeader.StartsWith("Bearer ", StringComparison.OrdinalIgnoreCase))
        {
            _logger.LogWarning("Invalid Authorization header format for {Path}", path);
            await ReturnUnauthorized(context);
            return;
        }

        var token = authHeader.Substring("Bearer ".Length).Trim();

        try
        {
            // Validate JWT token
            var tokenHandler = new JwtSecurityTokenHandler();
            var validationParameters = GetTokenValidationParameters();

            var principal = tokenHandler.ValidateToken(token, validationParameters, out var validatedToken);

            // Verify roles and scopes
            var roles = principal.Claims
                .Where(c => c.Type == ClaimTypes.Role || c.Type == "roles")
                .Select(c => c.Value)
                .ToList();

            var scopes = principal.Claims
                .Where(c => c.Type == "scp" || c.Type == "scope")
                .SelectMany(c => c.Value.Split(' '))
                .ToList();

            // Add claims to context for use in functions
            context.Items["UserPrincipal"] = principal;
            context.Items["Roles"] = roles;
            context.Items["Scopes"] = scopes;

            _logger.LogDebug("JWT token validated successfully for {Path}", path);
        }
        catch (SecurityTokenException ex)
        {
            _logger.LogWarning(ex, "JWT token validation failed for {Path}", path);
            await ReturnUnauthorized(context);
            return;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error validating JWT token for {Path}", path);
            await ReturnUnauthorized(context);
            return;
        }

        await next(context);
    }

    private TokenValidationParameters GetTokenValidationParameters()
    {
        var tenantId = _configuration["AzureAd:TenantId"];
        var audience = _configuration["AzureAd:Audience"];

        return new TokenValidationParameters
        {
            ValidateIssuer = true,
            ValidIssuer = $"https://login.microsoftonline.com/{tenantId}/v2.0",
            ValidateAudience = true,
            ValidAudience = audience,
            ValidateLifetime = true,
            ValidateIssuerSigningKey = true,
            IssuerSigningKeyResolver = (token, securityToken, kid, parameters) =>
            {
                // In production, fetch signing keys from Azure AD metadata endpoint
                // For now, this is a placeholder - implement proper key resolution
                return new List<SecurityKey>();
            },
            ClockSkew = TimeSpan.FromMinutes(5)
        };
    }

    private async Task ReturnUnauthorized(FunctionContext context)
    {
        var request = await context.GetHttpRequestDataAsync();
        if (request == null) return;

        var response = request.CreateResponse(HttpStatusCode.Unauthorized);
        response.Headers.Add("Content-Type", "application/json");
        await response.WriteStringAsync("{\"error\":\"Unauthorized\",\"message\":\"Invalid or missing JWT token\"}");

        var invocationResult = context.GetInvocationResult();
        invocationResult.Value = response;
    }
}
