"""
Enhanced logging configuration for Kenyan Real Estate AI Agent
Provides conversation-based logging for better debugging and monitoring
"""
import logging
import logging.handlers
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import uuid
from threading import local

# Thread-local storage for conversation context
_context = local()

class ConversationFilter(logging.Filter):
    """Custom filter to add conversation ID and request context to log records"""
    
    def filter(self, record):
        # Add conversation ID if available
        record.conversation_id = getattr(_context, 'conversation_id', 'system')
        record.user_query = getattr(_context, 'user_query', '')
        record.step = getattr(_context, 'step', '')
        return True


class StructuredFormatter(logging.Formatter):
    """Structured JSON formatter for better log parsing"""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'conversation_id': getattr(record, 'conversation_id', 'system'),
            'step': getattr(record, 'step', ''),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add user query if available (truncate if too long)
        if hasattr(record, 'user_query') and record.user_query:
            log_entry['user_query'] = record.user_query[:200] + '...' if len(record.user_query) > 200 else record.user_query
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'exc_info', 'exc_text', 'stack_info',
                          'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                          'thread', 'threadName', 'processName', 'process', 'getMessage',
                          'conversation_id', 'user_query', 'step']:
                if not key.startswith('_'):
                    log_entry[key] = str(value)
        
        return json.dumps(log_entry, ensure_ascii=False)


class ReadableFormatter(logging.Formatter):
    """Human-readable formatter for console output"""
    
    def __init__(self):
        super().__init__(
            fmt='%(asctime)s | %(levelname)-8s | [%(conversation_id)s] | %(step)s | %(name)s:%(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    def format(self, record):
        # Ensure conversation_id and step are available
        if not hasattr(record, 'conversation_id'):
            record.conversation_id = 'system'
        if not hasattr(record, 'step'):
            record.step = ''
        
        # Truncate step if too long
        if len(record.step) > 15:
            record.step = record.step[:12] + '...'
        
        return super().format(record)


def set_conversation_context(conversation_id: str, user_query: str = '', step: str = ''):
    """Set conversation context for current thread"""
    _context.conversation_id = conversation_id
    _context.user_query = user_query
    _context.step = step


def clear_conversation_context():
    """Clear conversation context for current thread"""
    _context.conversation_id = 'system'
    _context.user_query = ''
    _context.step = ''


def setup_logging(log_level: str = "INFO", logs_dir: str = "logs") -> None:
    """
    Setup comprehensive logging configuration
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        logs_dir: Directory to store log files
    """
    # Create logs directory
    logs_path = Path(logs_dir)
    logs_path.mkdir(exist_ok=True)
    
    # Clear existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    
    # Set log level
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    root_logger.setLevel(numeric_level)
    
    # Create custom filter
    conversation_filter = ConversationFilter()
    
    # 1. Console handler with readable format
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(ReadableFormatter())
    console_handler.addFilter(conversation_filter)
    root_logger.addHandler(console_handler)
    
    # 2. Main application log file (structured JSON)
    app_log_handler = logging.handlers.RotatingFileHandler(
        logs_path / "app.json",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    app_log_handler.setLevel(numeric_level)
    app_log_handler.setFormatter(StructuredFormatter())
    app_log_handler.addFilter(conversation_filter)
    root_logger.addHandler(app_log_handler)
    
    # 3. Error log file (errors and above only)
    error_log_handler = logging.handlers.RotatingFileHandler(
        logs_path / "errors.json",
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    error_log_handler.setLevel(logging.ERROR)
    error_log_handler.setFormatter(StructuredFormatter())
    error_log_handler.addFilter(conversation_filter)
    root_logger.addHandler(error_log_handler)
    
    # 4. Conversation-specific logs (separate file per conversation)
    # This will be handled dynamically as conversations occur
    
    # 5. Performance log for slow operations
    perf_logger = logging.getLogger('performance')
    perf_handler = logging.handlers.RotatingFileHandler(
        logs_path / "performance.json",
        maxBytes=5*1024*1024,
        backupCount=2,
        encoding='utf-8'
    )
    perf_handler.setFormatter(StructuredFormatter())
    perf_handler.addFilter(conversation_filter)
    perf_logger.addHandler(perf_handler)
    perf_logger.setLevel(logging.INFO)
    perf_logger.propagate = False
    
    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info("Logging system initialized", extra={
        'log_level': log_level,
        'logs_directory': str(logs_path.absolute()),
        'handlers': ['console', 'app_json', 'errors_json', 'performance_json']
    })


class ConversationLogger:
    """Context manager for conversation-specific logging"""
    
    def __init__(self, conversation_id: str, user_query: str = ''):
        self.conversation_id = conversation_id
        self.user_query = user_query
        self.logger = logging.getLogger(f'conversation.{conversation_id[:8]}')
        self.start_time = None
        
        # Create conversation-specific log file
        logs_path = Path('logs')
        self.conv_handler = logging.handlers.RotatingFileHandler(
            logs_path / f"conversation_{conversation_id[:8]}.json",
            maxBytes=2*1024*1024,  # 2MB
            backupCount=1,
            encoding='utf-8'
        )
        self.conv_handler.setFormatter(StructuredFormatter())
        self.conv_handler.addFilter(ConversationFilter())
        self.logger.addHandler(self.conv_handler)
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = True
    
    def __enter__(self):
        self.start_time = datetime.utcnow()
        set_conversation_context(self.conversation_id, self.user_query, 'conversation_start')
        
        self.logger.info("Conversation started", extra={
            'user_query': self.user_query,
            'conversation_id': self.conversation_id
        })
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (datetime.utcnow() - self.start_time).total_seconds()
        
        if exc_type:
            self.logger.error("Conversation ended with error", extra={
                'duration_seconds': duration,
                'error_type': exc_type.__name__,
                'error_message': str(exc_val)
            })
        else:
            self.logger.info("Conversation completed successfully", extra={
                'duration_seconds': duration
            })
        
        # Clean up handler
        self.logger.removeHandler(self.conv_handler)
        self.conv_handler.close()
        
        clear_conversation_context()
    
    def log_step(self, step_name: str, message: str, **kwargs):
        """Log a specific step in the conversation"""
        set_conversation_context(self.conversation_id, self.user_query, step_name)
        self.logger.info(message, extra=kwargs)
    
    def log_error(self, step_name: str, message: str, **kwargs):
        """Log an error in a specific step"""
        set_conversation_context(self.conversation_id, self.user_query, step_name)
        self.logger.error(message, extra=kwargs)


def log_performance(operation: str, duration: float, **kwargs):
    """Log performance metrics for slow operations"""
    perf_logger = logging.getLogger('performance')
    perf_logger.info(f"{operation} completed", extra={
        'operation': operation,
        'duration_seconds': duration,
        'slow_operation': duration > 2.0,  # Mark as slow if > 2 seconds
        **kwargs
    })


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the conversation filter applied"""
    logger = logging.getLogger(name)
    
    # Ensure the conversation filter is applied
    has_filter = any(isinstance(f, ConversationFilter) for f in logger.filters)
    if not has_filter:
        logger.addFilter(ConversationFilter())
    
    return logger


# Convenience functions for common logging patterns
def log_api_request(endpoint: str, method: str, **kwargs):
    """Log API request details"""
    logger = get_logger('api.request')
    set_conversation_context(
        kwargs.get('conversation_id', 'unknown'), 
        kwargs.get('query', ''), 
        'api_request'
    )
    
    logger.info(f"{method} {endpoint}", extra={
        'endpoint': endpoint,
        'method': method,
        **kwargs
    })


def log_api_response(endpoint: str, status_code: int, duration: float, **kwargs):
    """Log API response details"""
    logger = get_logger('api.response')
    set_conversation_context(
        kwargs.get('conversation_id', 'unknown'), 
        '', 
        'api_response'
    )
    
    level = logging.INFO if status_code < 400 else logging.ERROR
    logger.log(level, f"Response {status_code} for {endpoint}", extra={
        'endpoint': endpoint,
        'status_code': status_code,
        'duration_seconds': duration,
        **kwargs
    })


def log_ai_interaction(model: str, prompt_length: int, response_length: int, duration: float, **kwargs):
    """Log AI model interactions"""
    logger = get_logger('ai.interaction')
    set_conversation_context(
        kwargs.get('conversation_id', 'unknown'), 
        '', 
        'ai_generation'
    )
    
    logger.info(f"AI response generated using {model}", extra={
        'model': model,
        'prompt_length': prompt_length,
        'response_length': response_length,
        'duration_seconds': duration,
        'tokens_per_second': response_length / duration if duration > 0 else 0,
        **kwargs
    })


def log_knowledge_search(query: str, results_count: int, duration: float, **kwargs):
    """Log knowledge base search operations"""
    logger = get_logger('knowledge.search')
    set_conversation_context(
        kwargs.get('conversation_id', 'unknown'), 
        query, 
        'knowledge_search'
    )
    
    logger.info(f"Knowledge search completed", extra={
        'search_query': query[:100] + '...' if len(query) > 100 else query,
        'results_found': results_count,
        'duration_seconds': duration,
        'search_effective': results_count > 0,
        **kwargs
    })
