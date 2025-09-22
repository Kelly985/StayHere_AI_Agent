"""
Pydantic models for the Kenyan Real Estate AI Agent
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    query: str = Field(..., description="User's real estate question")
    conversation_id: Optional[str] = Field(None, description="Conversation ID for context")
    max_tokens: Optional[int] = Field(1000, description="Maximum tokens in response")
    temperature: Optional[float] = Field(0.7, description="Response creativity (0.0-1.0)")


class ChatResponse(BaseModel):
    """Response model for chat endpoint"""
    response: str = Field(..., description="AI agent's response")
    conversation_id: str = Field(..., description="Conversation ID")
    sources: List[str] = Field(default=[], description="Knowledge base sources used")
    confidence: float = Field(..., description="Response confidence score")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PropertyQuery(BaseModel):
    """Model for specific property queries"""
    property_type: Optional[str] = Field(None, description="Type of property (house, apartment, commercial, etc.)")
    location: Optional[str] = Field(None, description="Location/area of interest")
    budget_min: Optional[float] = Field(None, description="Minimum budget")
    budget_max: Optional[float] = Field(None, description="Maximum budget")
    bedrooms: Optional[int] = Field(None, description="Number of bedrooms")
    transaction_type: Optional[str] = Field(None, description="buy, rent, or invest")


class PropertyResponse(BaseModel):
    """Response for property queries"""
    properties: List[Dict[str, Any]] = Field(default=[], description="Matching properties")
    market_insights: str = Field(..., description="Market analysis and insights")
    recommendations: List[str] = Field(default=[], description="Investment recommendations")
    price_trends: Dict[str, Any] = Field(default={}, description="Price trend data")


class DocumentInfo(BaseModel):
    """Information about knowledge base documents"""
    filename: str = Field(..., description="Document filename")
    file_type: str = Field(..., description="File type (.txt, .pdf, etc.)")
    size: int = Field(..., description="File size in bytes")
    last_modified: datetime = Field(..., description="Last modification time")
    content_preview: str = Field(..., description="First 200 characters of content")


class KnowledgeBaseStatus(BaseModel):
    """Status of the knowledge base"""
    total_documents: int = Field(..., description="Number of documents in knowledge base")
    total_chunks: int = Field(..., description="Number of text chunks processed")
    last_updated: datetime = Field(..., description="Last update timestamp")
    documents: List[DocumentInfo] = Field(default=[], description="Document information")


class SystemStatus(BaseModel):
    """Overall system status"""
    status: str = Field(..., description="System status (healthy, degraded, down)")
    together_ai_status: str = Field(..., description="Together AI connection status")
    knowledge_base_status: str = Field(..., description="Knowledge base status")
    uptime: str = Field(..., description="System uptime")
    version: str = Field(..., description="Application version")


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[str] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SearchResult(BaseModel):
    """Search result from knowledge base"""
    content: str = Field(..., description="Relevant content")
    source: str = Field(..., description="Source document")
    score: float = Field(..., description="Similarity score")
    metadata: Dict[str, Any] = Field(default={}, description="Additional metadata")
