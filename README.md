# Kenyan Real Estate AI Agent

A comprehensive AI-powered agent specialized in the Kenyan real estate market, providing intelligent property recommendations, market analysis, and investment insights using Together AI's DeepSeek model.

## 🏠 Features

- **Intelligent Property Search**: Natural language queries for finding properties
- **Market Analysis**: Comprehensive analysis of different Kenyan locations
- **Price Estimation**: AI-powered property valuation and price trends
- **Investment Insights**: ROI analysis and investment recommendations
- **Real-time Responses**: Fast API responses using Together AI
- **Comprehensive Knowledge Base**: Detailed information about Kenyan real estate market
- **Conversation Memory**: Context-aware conversations
- **RESTful API**: Easy integration with web and mobile applications

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- Docker and Docker Compose (optional)
- Together AI API key

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd GeneralAIAgent
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the root directory:
   ```bash
   # Copy the example and modify
   cp .env.example .env
   ```
   
   Edit `.env` with your configuration:
   ```env
   TOGETHER_API_KEY=your_together_api_key_here
   TOGETHER_MODEL=deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free
   API_HOST=0.0.0.0
   API_PORT=8000
   DEBUG=True
   ```

5. **Run the application**
   ```bash
   python run.py
   ```

The API will be available at `http://localhost:8000`
- API Documentation: `http://localhost:8000/docs`
- Interactive API: `http://localhost:8000/redoc`

## 🐳 Docker Deployment

### Quick Start with Docker

```bash
# Build and run with docker-compose
docker-compose up -d

# Or build manually
docker build -t kenyan-real-estate-ai .
docker run -p 8000:8000 kenyan-real-estate-ai
```

### Production Deployment with Nginx

```bash
# Run with nginx proxy
docker-compose --profile production up -d
```

## 📚 API Usage

### Basic Chat Query

```bash
curl -X POST "http://localhost:8000/chat" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "What are the property prices in Westlands for 2-bedroom apartments?",
       "max_tokens": 1000,
       "temperature": 0.7
     }'
```

### Property Search

```bash
curl -X POST "http://localhost:8000/property/search" \
     -H "Content-Type: application/json" \
     -d '{
       "property_type": "apartment",
       "location": "Kilimani",
       "bedrooms": 2,
       "budget_max": 20000000,
       "transaction_type": "buy"
     }'
```

### Market Analysis

```bash
curl -X GET "http://localhost:8000/market/analysis/Karen"
```

### Price Estimation

```bash
curl -X GET "http://localhost:8000/properties/price-estimate?property_type=house&location=Runda&bedrooms=4"
```

## 🗂️ Project Structure

```
GeneralAIAgent/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── models.py            # Pydantic models
│   ├── agent.py             # AI agent logic
│   └── utils.py             # Utility functions
├── knowledgebase/           # Training data
│   ├── nairobi_properties.txt
│   ├── kenya_real_estate_market.txt
│   ├── property_prices_2024.txt
│   ├── commercial_properties.txt
│   └── rental_market_data.txt
├── config/
│   └── settings.py          # Configuration
├── tests/
├── .env                     # Environment variables
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## 🎯 Use Cases

### For Property Buyers
- Find properties within budget and location preferences
- Get market insights and price trends
- Compare different neighborhoods
- Understand investment potential

### For Real Estate Agents
- Quick market analysis for clients
- Property valuation assistance
- Investment recommendations
- Market trend insights

### For Investors
- ROI analysis and projections
- Market timing recommendations
- Growth area identification
- Risk assessment

### For Renters
- Rental price comparisons
- Neighborhood analysis
- Amenity information
- Market availability insights

## 📊 Knowledge Base

The AI agent is trained on comprehensive data about:

### Geographic Coverage
- **Nairobi**: All major areas (Karen, Westlands, Kilimani, Runda, etc.)
- **Mombasa**: Coastal properties and commercial areas
- **Major Cities**: Kisumu, Nakuru, Eldoret, Thika
- **Satellite Towns**: Kitengela, Syokimau, Ongata Rongai
- **Growth Areas**: Konza, Tatu City, LAPSSET corridor

### Property Types
- Residential (houses, apartments, condos)
- Commercial (offices, retail, malls)
- Industrial (warehouses, manufacturing)
- Land and development opportunities

### Market Data
- Current property prices (2024)
- Historical price trends
- Rental rates and yields
- Infrastructure impact analysis
- Investment opportunities

## 🔧 Configuration Options

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `TOGETHER_API_KEY` | Together AI API key | Required |
| `TOGETHER_MODEL` | AI model to use | deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free |
| `API_HOST` | Server host | 0.0.0.0 |
| `API_PORT` | Server port | 8000 |
| `DEBUG` | Debug mode | True |
| `KNOWLEDGE_BASE_PATH` | Knowledge base directory | ./knowledgebase |
| `MAX_CONTEXT_LENGTH` | Max context for AI queries | 4000 |

### Advanced Configuration

You can modify `config/settings.py` for advanced options:
- Vector database settings
- Similarity thresholds
- File processing options
- CORS settings

## 🧪 Testing

```bash
# Run tests
python -m pytest tests/

# Run with coverage
python -m pytest tests/ --cov=app
```

## 📈 Performance

- **Response Time**: < 3 seconds for most queries
- **Throughput**: 100+ requests per minute
- **Knowledge Base**: 5 comprehensive documents, 1000+ text chunks
- **Vector Search**: Sub-second similarity matching

## 🔍 Monitoring and Health Checks

### Health Check Endpoint
```bash
curl http://localhost:8000/health
```

### Knowledge Base Status
```bash
curl http://localhost:8000/knowledge/status
```

### System Metrics
The application provides built-in monitoring for:
- API response times
- Together AI connection status
- Knowledge base health
- System resource usage

## 🚨 Troubleshooting

### Common Issues

1. **Together AI Connection Error**
   - Verify API key is correct
   - Check internet connection
   - Ensure sufficient API credits

2. **Knowledge Base Not Loading**
   - Verify files exist in `knowledgebase/` directory
   - Check file permissions
   - Look for file format issues

3. **Memory Issues**
   - Reduce `MAX_CONTEXT_LENGTH`
   - Increase system RAM
   - Use Docker with memory limits

4. **Slow Responses**
   - Check Together AI API status
   - Optimize knowledge base size
   - Use faster embedding models

### Debug Mode

Enable debug logging:
```bash
export DEBUG=True
python run.py
```

### Logs

Application logs are saved to `app.log` and include:
- API requests and responses
- AI model interactions
- Knowledge base operations
- Error details

## 🔐 Security Considerations

- **API Keys**: Store securely, never commit to version control
- **Rate Limiting**: Implemented via nginx configuration
- **Input Validation**: All user inputs are sanitized
- **CORS**: Configure appropriately for your domain
- **HTTPS**: Use SSL certificates in production

## 🚀 Deployment Options

### Local Development
```bash
python run.py
```

### Docker Container
```bash
docker-compose up -d
```

### Cloud Platforms
- Digital Ocean (see DEPLOYMENT_GUIDE.md)
- AWS ECS/Fargate
- Google Cloud Run
- Azure Container Instances

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

### Development Setup

```bash
# Install development dependencies
pip install -r requirements.txt
pip install black flake8 pytest pytest-cov

# Format code
black app/

# Run linter
flake8 app/

# Run tests
pytest tests/
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 💬 Support

- **Issues**: GitHub Issues
- **Documentation**: `/docs` endpoint
- **Email**: your-email@domain.com

## 🔮 Future Enhancements

- [ ] Integration with MLS systems
- [ ] Mobile app development
- [ ] Advanced analytics dashboard
- [ ] Multi-language support
- [ ] Machine learning price predictions
- [ ] Integration with property photos
- [ ] Virtual property tours
- [ ] SMS/WhatsApp bot interface

## 📊 Sample Queries

Try these example queries:

```
"What are the best investment areas in Nairobi under 10 million?"
"Compare rental yields between Kilimani and Westlands"
"Show me 3-bedroom houses in Karen for sale"
"What's the price trend for commercial properties in Mombasa?"
"Is now a good time to invest in Syokimau properties?"
```

---

**Built with ❤️ for the Kenyan Real Estate Market**
