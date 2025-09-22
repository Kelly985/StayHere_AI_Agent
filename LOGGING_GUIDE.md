# Enhanced Logging System - Kenyan Real Estate AI Agent

This guide explains the comprehensive logging system implemented for better debugging and monitoring of the AI agent.

## 🎯 Overview

The logging system provides conversation-based tracking, structured JSON logging, performance monitoring, and detailed debugging information for every step of the AI processing pipeline.

## 📁 Log File Structure

```
logs/
├── app.json                    # Main application logs (structured JSON)
├── errors.json                 # Error logs only  
├── performance.json            # Performance and slow operation logs
└── conversation_[ID].json      # Individual conversation logs
```

## 🔧 Log Formats

### Console Output (Human Readable)
```
2024-09-21 19:45:23 | INFO     | [conv_abc123] | query_processing | app.main:chat_endpoint:215 | Processing real estate query
```

### JSON Files (Machine Readable)
```json
{
  "timestamp": "2024-09-21T19:45:23.123456Z",
  "level": "INFO", 
  "logger": "app.main",
  "message": "Processing real estate query",
  "conversation_id": "conv_abc123",
  "step": "query_processing",
  "module": "main",
  "function": "chat_endpoint",
  "line": 215,
  "user_query": "What are property prices in Westlands?",
  "query_length": 35,
  "max_tokens": 1000,
  "temperature": 0.7
}
```

## 📊 Logging Levels and Usage

### INFO
- System startup and initialization
- Successful operations
- API requests and responses
- Conversation start/end

### DEBUG  
- Detailed step-by-step processing
- Knowledge base search details
- AI prompt construction
- Internal state changes

### ERROR
- Exceptions and failures
- API errors
- Configuration issues
- Processing failures

### WARNING
- Unexpected but recoverable situations
- Performance degradation
- Missing optional components

## 🔍 Conversation Tracking

Every user interaction is tracked with a unique conversation ID that appears in all related log entries:

```python
# Automatic conversation tracking in endpoints
with ConversationLogger(conversation_id, user_query) as conv_logger:
    conv_logger.log_step("knowledge_search", "Searching knowledge base")
    conv_logger.log_step("ai_generation", "Generating AI response")
```

## 📈 Performance Monitoring

Performance logs track slow operations and system metrics:

```json
{
  "operation": "chat_query",
  "duration_seconds": 8.5,
  "slow_operation": true,
  "conversation_id": "conv_abc123",
  "query_length": 150,
  "response_length": 1200
}
```

## 🔍 Key Logged Operations

### 1. API Requests
- Endpoint accessed
- HTTP method and status
- Client IP and user agent
- Request duration
- Conversation ID extraction

### 2. Knowledge Base Operations
- Document loading and processing
- Search queries and results
- Processing times and effectiveness
- File-by-file processing metrics

### 3. AI Interactions
- Model used and parameters
- Prompt length and construction
- Response generation time
- Token generation rate
- Error handling and retries

### 4. System Health
- Memory and CPU usage
- Startup and shutdown events
- Configuration validation
- Service availability

## 🛠️ Using the Logging System

### Basic Logger Usage
```python
from app.logging_config import get_logger

logger = get_logger(__name__)
logger.info("Operation completed", extra={'key': 'value'})
```

### Conversation Context
```python
from app.logging_config import set_conversation_context

set_conversation_context(conversation_id, user_query, "processing_step")
logger.info("Step completed")
```

### Performance Logging  
```python
from app.logging_config import log_performance

log_performance("operation_name", duration_seconds, 
                conversation_id=conv_id, additional_data="value")
```

### Specific Log Types
```python
from app.logging_config import log_api_request, log_ai_interaction, log_knowledge_search

# Log API interactions
log_api_request("/chat", "POST", conversation_id=conv_id, query="user question")
log_api_response("/chat", 200, 2.5, conversation_id=conv_id)

# Log AI interactions  
log_ai_interaction("model-name", 1500, 800, 3.2, conversation_id=conv_id)

# Log knowledge base searches
log_knowledge_search("user query", 5, 0.8, conversation_id=conv_id)
```

## 📋 Log Analysis Examples

### Find Slow Queries
```bash
# Find queries taking longer than 5 seconds
grep -r "processing_time_seconds.*[5-9]\." logs/ | head -10
```

### Track Conversation Flow
```bash
# Follow a specific conversation
grep "conv_abc123" logs/app.json | jq '.step, .message'
```

### Monitor Error Patterns
```bash
# Count error types
jq -r '.message' logs/errors.json | sort | uniq -c | sort -nr
```

### Performance Analysis
```bash
# Average AI response times
jq -r 'select(.operation=="ai_generation") | .duration_seconds' logs/performance.json | awk '{sum+=$1; n++} END {print "Average:", sum/n, "seconds"}'
```

## 🔧 Configuration

### Log Levels
Set via environment variable or settings:
```bash
export DEBUG=true   # Enables DEBUG level logging
export DEBUG=false  # INFO level and above
```

### Log Rotation
- **app.json**: 10MB max, 5 backup files
- **errors.json**: 5MB max, 3 backup files  
- **performance.json**: 5MB max, 2 backup files
- **conversation logs**: 2MB max, 1 backup file per conversation

### Custom Configuration
Modify `app/logging_config.py` to adjust:
- Log file sizes and rotation
- Log formats and fields
- Performance thresholds
- Additional log files

## 📊 Monitoring Dashboard

### Key Metrics to Track
1. **Response Times**: Average query processing time
2. **Error Rates**: Errors per hour/day
3. **Conversation Volume**: Active conversations per period
4. **Knowledge Base Efficiency**: Search hit rates and performance
5. **AI Model Performance**: Token generation rates and failures

### Health Indicators
- **Green**: < 3 second average response time, < 1% error rate
- **Yellow**: 3-10 second responses, 1-5% error rate
- **Red**: > 10 seconds or > 5% errors

## 🚨 Troubleshooting

### Common Issues

**1. Missing Conversation ID in Logs**
- Check that endpoints properly extract conversation_id from requests
- Verify ConversationLogger is used for chat operations

**2. Performance Logs Not Appearing**
- Confirm operations are taking longer than thresholds
- Check that log_performance() is called after timing operations

**3. Log Files Not Rotating**
- Verify write permissions to logs/ directory
- Check disk space availability
- Ensure logging handlers are properly configured

**4. JSON Parse Errors in Log Files**
- Usually indicates logging during exception handling
- Check that all logged objects are JSON serializable
- Verify proper exception handling in logging statements

### Debug Commands

```bash
# Check log file permissions
ls -la logs/

# Monitor logs in real-time  
tail -f logs/app.json | jq .

# Validate JSON format
jq . logs/app.json > /dev/null && echo "Valid JSON" || echo "Invalid JSON"

# Check log sizes
du -sh logs/*
```

## 🎯 Best Practices

1. **Always include conversation_id** in user-facing operations
2. **Use appropriate log levels** - DEBUG for details, INFO for status, ERROR for problems
3. **Include timing information** for performance-critical operations
4. **Add contextual data** via the `extra` parameter
5. **Avoid logging sensitive data** like API keys or personal information
6. **Use structured data** for easier parsing and analysis
7. **Monitor log file sizes** to prevent disk space issues

## 📈 Future Enhancements

- Integration with monitoring tools (Prometheus, Grafana)
- Automated alerting on error patterns
- Log aggregation for multi-instance deployments
- Real-time log analysis dashboard
- Machine learning-based anomaly detection

This comprehensive logging system provides complete visibility into the AI agent's operation, making debugging and monitoring much more effective.
