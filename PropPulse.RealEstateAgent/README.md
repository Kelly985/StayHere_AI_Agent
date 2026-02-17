# PropPulse Real Estate AI Agent - .NET 8 Azure Function

A high-scale property leasing and purchase platform module built with .NET 8 Azure Functions, following Clean Architecture and Domain-Driven Design (DDD) principles.

## Architecture

This solution follows **Clean Architecture** with strict layering:

### Project Structure

```
PropPulse.RealEstateAgent/
├── PropPulse.RealEstateAgent.Domain/          # Domain Layer (No dependencies)
│   ├── Entities/                              # Domain entities
│   └── ValueObjects/                          # Value objects
├── PropPulse.RealEstateAgent.Application/      # Application Layer
│   ├── Commands/                              # CQRS Commands
│   ├── Queries/                               # CQRS Queries
│   ├── DTOs/                                  # Data Transfer Objects
│   ├── Handlers/                              # Command/Query Handlers
│   └── Interfaces/                            # Repository interfaces
├── PropPulse.RealEstateAgent.Infrastructure/  # Infrastructure Layer
│   ├── Repositories/                          # Repository implementations
│   ├── Services/                              # External service integrations
│   └── DependencyInjection.cs                # DI configuration
└── PropPulse.RealEstateAgent.Api/             # API Layer (Azure Functions)
    ├── Functions/                             # Azure Function endpoints
    ├── Middleware/                            # JWT validation middleware
    └── Program.cs                             # Startup configuration
```

## Features

- ✅ **Clean Architecture** with strict layering
- ✅ **CQRS Pattern** using MediatR
- ✅ **Repository Pattern** for data persistence
- ✅ **JWT Token Validation** via Entra ID/APIM
- ✅ **Structured Logging** with Serilog
- ✅ **OpenTelemetry** integration (Application Insights)
- ✅ **Azure Functions Isolated Worker** (.NET 8)

## Prerequisites

- .NET 8 SDK
- Azure Functions Core Tools v4
- Azure Storage Emulator (for local development)

## Configuration

### local.settings.json

Configure the following settings:

```json
{
  "Values": {
    "OpenRouter:ApiKey": "your-openrouter-api-key",
    "OpenRouter:Model": "deepseek/deepseek-chat-v3.1:free",
    "KnowledgeBasePath": "./knowledgebase",
    "PropertiesDataPath": "./properties_data.json",
    "BasePropertyUrl": "https://your-domain.com/properties",
    "AzureAd:TenantId": "your-tenant-id",
    "AzureAd:Audience": "your-api-audience"
  }
}
```

## API Endpoints

### Chat
- **POST** `/api/chat` - Process real estate queries
  ```json
  {
    "query": "What are property prices in Kilimani?",
    "conversationId": "optional-conversation-id",
    "maxTokens": 1000,
    "temperature": 0.7
  }
  ```

### Property Recommendations
- **POST** `/api/respondandrecommend` - Get AI response and property recommendations
  ```json
  {
    "query": "I need a 2-bedroom apartment in Westlands",
    "conversationId": "optional-conversation-id",
    "maxResults": 10,
    "filters": {
      "location": "Westlands",
      "min_price": 50000,
      "max_price": 150000
    },
    "temperature": 0.7
  }
  ```

### Properties
- **GET** `/api/properties?property_id=P1001` - Get property by ID
- **GET** `/api/properties?location=kileleshwa` - Search by location
- **GET** `/api/properties?amenity=pool,gym` - Search by amenities

### Knowledge Base
- **GET** `/api/knowledge/status` - Get knowledge base status

### Health
- **GET** `/api/health` - Health check endpoint

## Security

All endpoints (except `/health`) require JWT tokens issued by Entra ID via APIM. The `JwtValidationMiddleware` validates:
- Token signature
- Token expiration
- Issuer (Azure AD)
- Audience
- Roles and scopes

## Development

### Build
```bash
dotnet build
```

### Run Locally
```bash
func start
```

### Test
```bash
dotnet test
```

## Deployment

### Azure Deployment

1. **Create Azure Function App**
   ```bash
   az functionapp create --resource-group <rg> --consumption-plan-location <location> --runtime dotnet-isolated --functions-version 4 --name <app-name> --storage-account <storage-account>
   ```

2. **Configure Application Settings**
   - Set all configuration values from `local.settings.json` as Application Settings in Azure Portal

3. **Deploy**
   ```bash
   func azure functionapp publish <app-name>
   ```

4. **Configure Managed Identity**
   - Enable System-assigned managed identity
   - Grant necessary permissions (Key Vault, Storage, etc.)

## Observability

- **Serilog** for structured logging (console and file)
- **Application Insights** for distributed tracing
- **OpenTelemetry** integration (via Application Insights)

## Terraform

Infrastructure as Code templates should be created for:
- Azure Function App
- Application Insights
- Key Vault (for secrets)
- Storage Account
- Managed Identities

## Notes

- The current implementation uses in-memory repositories for conversations and file-based storage for properties
- In production, replace with:
  - Cosmos DB or SQL Database for conversations
  - Cosmos DB or SQL Database for properties
  - Azure Blob Storage for knowledge base documents
  - Vector database (Azure Cognitive Search) for semantic search

## License

Proprietary - PropPulse Platform
