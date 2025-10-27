"""
FastAPI main application for Kenyan Real Estate AI Agent
"""
import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, Any, Optional
import time

import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config.settings import settings
from app.agent_simple import SimpleRealEstateAgent as RealEstateAgent
from app.models import (
    ChatRequest, 
    ChatResponse, PropertyQuery, PropertyResponse,
    SystemStatus, KnowledgeBaseStatus, ErrorResponse
)
from app.logging_config import (
    setup_logging, ConversationLogger, log_api_request, log_api_response,
    get_logger, set_conversation_context, log_performance
)
from app.utils import get_system_health, extract_property_details

# from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
import json


# Global agent instance
# Global agent instance
agent: RealEstateAgent = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    global agent
    
    # Startup
    setup_logging(log_level=settings.debug and "DEBUG" or "INFO")
    logger = get_logger(__name__)
    logger.info("Starting Kenyan Real Estate AI Agent...", extra={
        'app_name': settings.app_name,
        'app_version': settings.app_version,
        'debug_mode': settings.debug
    })
    
    # Initialize the AI agent
    start_time = time.time()
    agent = RealEstateAgent()
    await agent.initialize()
    init_duration = time.time() - start_time
    
    logger.info("AI Agent initialized successfully", extra={
        'initialization_time_seconds': init_duration,
        'knowledge_base_loaded': True
    })
    
    logger.info("Application startup complete")
    yield
    
    # Shutdown
    logger.info("Shutting down application...")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="Intelligent AI agent specialized in Kenyan real estate market analysis and property recommendations",
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests and responses"""
    start_time = time.time()
    
    # Extract potential conversation ID from request without consuming body
    conversation_id = "unknown"
    try:
        if request.method == "POST" and request.url.path in ["/chat", "/property/search"]:
            # Read body and store it for reuse
            body_bytes = await request.body()
            if body_bytes:
                import json
                body = json.loads(body_bytes.decode())
                if isinstance(body, dict) and "conversation_id" in body:
                    conversation_id = body.get("conversation_id", "unknown")
                
                # Create a new request with the body restored
                async def receive():
                    return {"type": "http.request", "body": body_bytes}
                
                request._receive = receive
    except Exception as e:
        # If we can't parse the body, that's fine - just continue
        pass
    
    # Log incoming request
    log_api_request(
        endpoint=str(request.url.path),
        method=request.method,
        conversation_id=conversation_id,
        client_ip=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", "unknown")
    )
    
    # Process request
    response = await call_next(request)
    
    # Calculate duration and log response
    duration = time.time() - start_time
    log_api_response(
        endpoint=str(request.url.path),
        status_code=response.status_code,
        duration=duration,
        conversation_id=conversation_id
    )
    
    return response


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Welcome to the Kenyan Real Estate AI Agent",
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "chat": "/chat",
            "test": "/test",
            "property_search": "/property/search",
            "market_analysis": "/market/analysis",
            "knowledge_base": "/knowledge/status"
        }
    }


@app.get("/test", tags=["Testing"])
async def test_endpoint():
    """Simple test endpoint to verify API is working"""
    return {
        "status": "success",
        "message": "API is working correctly",
        "timestamp": datetime.utcnow().isoformat(),
        "server": "Kenyan Real Estate AI Agent"
    }


@app.post("/test", tags=["Testing"])
async def test_post_endpoint(data: dict = None):
    """Test POST endpoint to verify request handling"""
    return {
        "status": "success",
        "message": "POST request received successfully",
        "received_data": data,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health", response_model=SystemStatus, tags=["System"])
async def health_check():
    """System health check endpoint"""
    try:
        global agent
        
        # Check system metrics
        system_health = get_system_health()
        
        # Check Together AI status
        together_status = "healthy"
        try:
            if agent and hasattr(agent, 'together_client'):
                # Test connection by making a simple call
                # Note: We don't actually make the call to avoid costs during health checks
                together_status = "healthy"
        except Exception as e:
            together_status = f"error: {str(e)}"
        
        # Check knowledge base status
        kb_status = "healthy"
        try:
            if agent and agent.knowledge_base.loaded:
                kb_status = "healthy"
            else:
                kb_status = "not_loaded"
        except Exception as e:
            kb_status = f"error: {str(e)}"
        
        # Calculate uptime (simplified)
        uptime = "Available"
        
        overall_status = "healthy"
        if system_health.get('status') == 'error' or 'error' in together_status or 'error' in kb_status:
            overall_status = "degraded"
        
        return SystemStatus(
            status=overall_status,
            together_ai_status=together_status,
            knowledge_base_status=kb_status,
            uptime=uptime,
            version=settings.app_version
        )
        
    except Exception as e:
        logging.error(f"Health check failed: {str(e)}")
        return SystemStatus(
            status="down",
            together_ai_status="unknown",
            knowledge_base_status="unknown",
            uptime="unknown",
            version=settings.app_version
        )


@app.post("/chat", response_model=ChatResponse, tags=["AI Chat"])
async def chat_endpoint(request: ChatRequest):
    """Main chat endpoint for real estate queries"""
    logger = get_logger(__name__)
    
    try:
        if not agent:
            logger.error("AI Agent not available", extra={'endpoint': '/chat'})
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI Agent not initialized"
            )
        
        # Use conversation logger for detailed tracking
        conversation_id = request.conversation_id or f"chat_{int(time.time())}"
        
        with ConversationLogger(conversation_id, request.query) as conv_logger:
            conv_logger.log_step("request_validation", "Processing chat request", extra={
                'query_length': len(request.query),
                'max_tokens': request.max_tokens,
                'temperature': request.temperature
            })
            
            # Process the query with enhanced logging
            start_time = time.time()
            response = await agent.process_query(
                query=request.query,
                conversation_id=conversation_id,
                max_tokens=request.max_tokens,
                temperature=request.temperature
            )
            processing_time = time.time() - start_time
            
            conv_logger.log_step("query_processed", "Query processing completed", extra={
                'processing_time_seconds': processing_time,
                'response_length': len(response.response),
                'confidence_score': response.confidence,
                'sources_used': len(response.sources)
            })
            
            # Log performance if slow
            if processing_time > 5.0:
                log_performance("chat_query", processing_time, 
                               conversation_id=conversation_id,
                               query_length=len(request.query),
                               response_length=len(response.response))
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Chat endpoint error", extra={
            'error': str(e),
            'query': request.query[:100] + '...' if len(request.query) > 100 else request.query,
            'conversation_id': request.conversation_id
        }, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing query: {str(e)}"
        )





@app.get("/properties")
async def get_properties(
    request: Request,
    property_id: Optional[str] = None,
    location: Optional[str] = None,
    amenity: Optional[str] = None
):
    """
    Return properties optionally filtered by:
      - property_id
      - location
      - amenity (supports comma-separated values)
    
    Examples:
      GET /properties?property_id=P1001
      GET /properties?location=kileleshwa
      GET /properties?amenity=pool,gym
    """

    # Load data
    try:
        with open("properties_data.json", "r", encoding="utf-8") as f:
            properties = json.load(f)
    except FileNotFoundError:
        return JSONResponse(
            {"count": 0, "filters": {"location": location, "amenity": amenity, "property_id": property_id}, "properties": []},
            status_code=404
        )

    # ✅ If property_id is provided, short-circuit and return that property only
    if property_id:
        match = next(
            (p for p in properties if str(p.get("property_id")).lower() == property_id.lower()), 
            None
        )
        if not match:
            return JSONResponse(
                {"Status": "404", "Message": f"No property found with ID '{property_id}'."},
                status_code=404
            )

        base = str(request.base_url).rstrip("/")
        match["listing_url"] = f"{base}/properties?property_id={match.get('property_id')}"
        # return JSONResponse(
        #     {"Status": "000", "Message": "Success", "count": 1, "Property": match}
        # )
        return JSONResponse(
            {"Property": match}
        )

    # Normalize inputs
    location_q = location.strip().lower() if isinstance(location, str) and location.strip() else None
    amenity_q = amenity.strip().lower() if isinstance(amenity, str) and amenity.strip() else None

    # Support comma-separated amenities (e.g. amenity=pool,gym)
    amenity_list: Optional[List[str]] = None
    if amenity_q:
        amenity_list = [a.strip() for a in amenity_q.split(",") if a.strip()]

    filtered = []
    base = str(request.base_url).rstrip("/")  # e.g. http://127.0.0.1:8000

    for p in properties:
        try:
            # Location matching on several fields
            loc_fields = []
            loc = p.get("location", {}) or {}
            for key in ("suburb", "city", "county", "street"):
                val = loc.get(key)
                if val and isinstance(val, str):
                    loc_fields.append(val.lower())

            match_location = True
            if location_q:
                match_location = any(location_q in lf for lf in loc_fields)

            match_amenity = True
            if amenity_list:
                prop_amenities = [a.lower() for a in (p.get("amenities") or []) if isinstance(a, str)]
                match_amenity = all(any(req in pa for pa in prop_amenities) for req in amenity_list)

            if match_location and match_amenity:
                prop_copy = p.copy()
                prop_copy["listing_url"] = f"{base}/properties?property_id={p.get('property_id')}"
                filtered.append(prop_copy)

        except Exception:
            continue

    return {
        # "Status": "000",
        # "Message": "Success",
        # "count": len(filtered),
        # "filters": {"property_id": property_id, "location": location, "amenity": amenity},
        "properties": filtered
    }






# router = APIRouter()

class RecommendRequest(BaseModel):
    query: str
    conversation_id: str | None = None
    max_results: int = 10
    filters: dict | None = None  # Example: {"location": "Kilimani", "price_max": 100000}
    temperature: float = 0.7


class RecommendResponse(BaseModel):
    Status: str
    Message: str
    Data: dict



@app.post("/respondandrecommend", response_model=RecommendResponse, tags=["AI Recommendations"])
async def respond_and_recommend_endpoint(request: ChatRequest):
    """Handles property recommendation and filtering based on user query"""
    logger = get_logger(__name__)

    try:
        if not agent:
            logger.error("AI Agent not available", extra={'endpoint': '/respondandrecommend'})
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI Agent not initialized"
            )

        query = request.query
        conversation_id = request.conversation_id or f"recommend_{int(time.time())}"
        temperature = request.temperature
        max_tokens = getattr(request, "max_tokens", 800)
        filters = getattr(request, "filters", {})
        max_results = getattr(request, "max_results", 3)

        if not query or not isinstance(query, str):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing or invalid 'query' field"
            )

        with ConversationLogger(conversation_id, query) as conv_logger:
            conv_logger.log_step("request_validation", "Processing recommendation request", extra={
                'filters': filters,
                'max_results': max_results,
                'temperature': temperature
            })

            start_time = time.time()

            # ✅ Call updated method
            response_data = await agent.respond_and_recommend_properties(
                query=query,
                conversation_id=conversation_id,
                filters=filters,
                max_results=max_results,
                temperature=temperature
            )

            processing_time = time.time() - start_time
            conv_logger.log_step("recommendation_processed", "Property recommendation completed", extra={
                'processing_time_seconds': processing_time,
                'properties_returned': len(response_data.get("recommended_properties", []))
            })

        # ✅ Build final JSONResponse
        return JSONResponse({
            "Status": "000",
            "Message": response_data.get("response", ""),
            "Data": {
                "RecommendedListings": response_data.get("recommended_properties", []),
                "conversation_id": response_data.get("conversation_id"),
                "confidence": response_data.get("confidence"),
                "timestamp": response_data.get("timestamp"),
            }
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Recommendation endpoint error", extra={
            'error': str(e),
            'query': query if 'query' in locals() else 'unknown',
            'conversation_id': conversation_id if 'conversation_id' in locals() else 'unknown'
        }, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing recommendation request: {str(e)}"
        )



@app.post("/property/search", response_model=PropertyResponse, tags=["Property"])
async def property_search(query: PropertyQuery):
    """Search for properties based on specific criteria"""
    try:
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI Agent not initialized"
            )
        
        # Build search query from structured input
        search_parts = []
        
        if query.property_type:
            search_parts.append(f"{query.property_type} properties")
        
        if query.location:
            search_parts.append(f"in {query.location}")
        
        if query.bedrooms:
            search_parts.append(f"with {query.bedrooms} bedrooms")
        
        if query.budget_min or query.budget_max:
            budget_part = "budget"
            if query.budget_min and query.budget_max:
                budget_part += f" between KSH {query.budget_min:,.0f} and KSH {query.budget_max:,.0f}"
            elif query.budget_min:
                budget_part += f" above KSH {query.budget_min:,.0f}"
            elif query.budget_max:
                budget_part += f" below KSH {query.budget_max:,.0f}"
            search_parts.append(budget_part)
        
        if query.transaction_type:
            if query.transaction_type == "rent":
                search_parts.append("for rental")
            elif query.transaction_type == "buy":
                search_parts.append("for sale")
            elif query.transaction_type == "invest":
                search_parts.append("for investment")
        
        search_query = " ".join(search_parts)
        if not search_query:
            search_query = "property information"
        
        # Get AI response
        chat_response = await agent.process_query(search_query)
        
        # For now, we return the AI response as market insights
        # In a full implementation, you would parse and structure the response
        return PropertyResponse(
            properties=[],  # Would be populated with actual property data
            market_insights=chat_response.response,
            recommendations=[],
            price_trends={}
        )
        
    except Exception as e:
        logging.error(f"Property search error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching properties: {str(e)}"
        )


@app.get("/market/analysis/{location}", tags=["Market Analysis"])
async def market_analysis(location: str):
    """Get market analysis for a specific location"""
    try:
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI Agent not initialized"
            )
        
        query = f"Provide comprehensive market analysis for {location} including property prices, trends, investment potential, infrastructure development, and rental yields"
        
        response = await agent.process_query(query)
        
        return {
            "location": location,
            "analysis": response.response,
            "sources": response.sources,
            "confidence": response.confidence,
            "timestamp": response.timestamp
        }
        
    except Exception as e:
        logging.error(f"Market analysis error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating market analysis: {str(e)}"
        )


@app.get("/knowledge/status", response_model=Dict[str, Any], tags=["Knowledge Base"])
async def knowledge_base_status():
    """Get knowledge base status and statistics"""
    try:
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI Agent not initialized"
            )
        
        status_info = await agent.get_knowledge_base_status()
        return status_info
        
    except Exception as e:
        logging.error(f"Knowledge base status error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting knowledge base status: {str(e)}"
        )


@app.post("/knowledge/reload", tags=["Knowledge Base"])
async def reload_knowledge_base(background_tasks: BackgroundTasks):
    """Reload the knowledge base (admin endpoint)"""
    try:
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI Agent not initialized"
            )
        
        # Reload knowledge base in background
        background_tasks.add_task(agent.knowledge_base.load_documents)
        
        return {"message": "Knowledge base reload initiated"}
        
    except Exception as e:
        logging.error(f"Knowledge base reload error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error reloading knowledge base: {str(e)}"
        )


@app.get("/conversation/{conversation_id}", tags=["Conversation"])
async def get_conversation_history(conversation_id: str):
    """Get conversation history for a specific conversation ID"""
    try:
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI Agent not initialized"
            )
        
        history = agent.get_conversation_history(conversation_id)
        
        return {
            "conversation_id": conversation_id,
            "history": history,
            "message_count": len(history)
        }
        
    except Exception as e:
        logging.error(f"Conversation history error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving conversation history: {str(e)}"
        )


@app.delete("/conversation/{conversation_id}", tags=["Conversation"])
async def clear_conversation(conversation_id: str):
    """Clear conversation history for a specific conversation ID"""
    try:
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI Agent not initialized"
            )
        
        agent.clear_conversation(conversation_id)
        
        return {"message": f"Conversation {conversation_id} cleared successfully"}
        
    except Exception as e:
        logging.error(f"Clear conversation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error clearing conversation: {str(e)}"
        )


@app.get("/properties/price-estimate", tags=["Property"])
async def estimate_property_price(
    property_type: str,
    location: str,
    bedrooms: int = None,
    size_sqft: float = None
):
    """Get property price estimate based on parameters"""
    try:
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI Agent not initialized"
            )
        
        # Build query for price estimation
        query_parts = [f"What is the current market price for {property_type} in {location}"]
        
        if bedrooms:
            query_parts.append(f"with {bedrooms} bedrooms")
        
        if size_sqft:
            query_parts.append(f"approximately {size_sqft} square feet")
        
        query = " ".join(query_parts) + "? Please provide price ranges and market factors affecting the price."
        
        response = await agent.process_query(query)
        
        return {
            "property_type": property_type,
            "location": location,
            "bedrooms": bedrooms,
            "size_sqft": size_sqft,
            "price_analysis": response.response,
            "confidence": response.confidence,
            "sources": response.sources
        }
        
    except Exception as e:
        logging.error(f"Price estimation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error estimating property price: {str(e)}"
        )


# Exception handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": "The requested endpoint was not found",
            "available_endpoints": [
                "/", "/health", "/chat", "/property/search",
                "/market/analysis/{location}", "/knowledge/status"
            ]
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "timestamp": datetime.utcnow().isoformat()
        }
    )


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level="info"
    )
