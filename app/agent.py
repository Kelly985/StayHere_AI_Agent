"""
Kenyan Real Estate AI Agent - Core Intelligence Module
"""
import os
import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import json
from datetime import datetime
import uuid

# Vector processing and embeddings
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss

# Together AI
from together import Together

# File processing
import PyPDF2
from docx import Document

from config.settings import settings
from app.models import SearchResult, ChatResponse


class KnowledgeBase:
    """Manages the real estate knowledge base with vector search"""
    
    def __init__(self):
        self.embeddings_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.documents: List[Dict[str, Any]] = []
        self.embeddings: Optional[np.ndarray] = None
        self.index: Optional[faiss.IndexFlatIP] = None
        self.loaded = False
        
    async def load_documents(self) -> None:
        """Load all documents from the knowledge base directory"""
        try:
            knowledge_path = Path(settings.knowledge_base_path)
            if not knowledge_path.exists():
                raise FileNotFoundError(f"Knowledge base path not found: {knowledge_path}")
            
            self.documents = []
            texts_to_embed = []
            
            for file_path in knowledge_path.glob("**/*"):
                if file_path.is_file() and file_path.suffix.lower() in settings.supported_file_types:
                    content = await self._extract_text(file_path)
                    if content:
                        # Split content into chunks
                        chunks = self._split_text(content)
                        for i, chunk in enumerate(chunks):
                            doc_info = {
                                'content': chunk,
                                'source': file_path.name,
                                'chunk_id': i,
                                'file_path': str(file_path),
                                'metadata': {
                                    'file_type': file_path.suffix,
                                    'file_size': file_path.stat().st_size,
                                    'modified': datetime.fromtimestamp(file_path.stat().st_mtime)
                                }
                            }
                            self.documents.append(doc_info)
                            texts_to_embed.append(chunk)
            
            if texts_to_embed:
                # Generate embeddings
                logging.info(f"Generating embeddings for {len(texts_to_embed)} text chunks...")
                self.embeddings = self.embeddings_model.encode(texts_to_embed, convert_to_numpy=True)
                
                # Create FAISS index
                dimension = self.embeddings.shape[1]
                self.index = faiss.IndexFlatIP(dimension)
                
                # Normalize embeddings for cosine similarity
                faiss.normalize_L2(self.embeddings)
                self.index.add(self.embeddings)
                
                self.loaded = True
                logging.info(f"Knowledge base loaded: {len(self.documents)} documents, {len(texts_to_embed)} chunks")
            else:
                logging.warning("No documents found in knowledge base")
                
        except Exception as e:
            logging.error(f"Error loading knowledge base: {str(e)}")
            raise
    
    async def _extract_text(self, file_path: Path) -> Optional[str]:
        """Extract text from different file types"""
        try:
            if file_path.suffix.lower() == '.txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            
            elif file_path.suffix.lower() == '.pdf':
                text = ""
                with open(file_path, 'rb') as f:
                    pdf_reader = PyPDF2.PdfReader(f)
                    for page in pdf_reader.pages:
                        text += page.extract_text() + "\n"
                return text
            
            elif file_path.suffix.lower() == '.docx':
                doc = Document(file_path)
                text = ""
                for paragraph in doc.paragraphs:
                    text += paragraph.text + "\n"
                return text
            
            return None
            
        except Exception as e:
            logging.error(f"Error extracting text from {file_path}: {str(e)}")
            return None
    
    def _split_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Split text into overlapping chunks"""
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence endings near the chunk boundary
                for i in range(min(100, chunk_size - overlap), 0, -1):
                    if end - i < len(text) and text[end - i] in '.!?':
                        end = end - i + 1
                        break
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - overlap
            
        return chunks
    
    async def search(self, query: str, top_k: int = 5) -> List[SearchResult]:
        """Search for relevant documents using vector similarity"""
        if not self.loaded or self.index is None:
            await self.load_documents()
        
        if not self.loaded:
            return []
        
        try:
            # Generate query embedding
            query_embedding = self.embeddings_model.encode([query], convert_to_numpy=True)
            faiss.normalize_L2(query_embedding)
            
            # Search for similar documents
            scores, indices = self.index.search(query_embedding, min(top_k, len(self.documents)))
            
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if score >= settings.similarity_threshold:
                    doc = self.documents[idx]
                    result = SearchResult(
                        content=doc['content'],
                        source=doc['source'],
                        score=float(score),
                        metadata=doc['metadata']
                    )
                    results.append(result)
            
            return results
            
        except Exception as e:
            logging.error(f"Error searching knowledge base: {str(e)}")
            return []


class RealEstateAgent:
    """Kenyan Real Estate AI Agent with Together AI integration"""
    
    def __init__(self):
        self.together_client = Together(api_key=settings.together_api_key)
        self.knowledge_base = KnowledgeBase()
        self.conversations: Dict[str, List[Dict[str, str]]] = {}
        self.system_prompt = self._create_system_prompt()
        
    async def initialize(self):
        """Initialize the agent and load knowledge base"""
        await self.knowledge_base.load_documents()
        logging.info("Real Estate Agent initialized successfully")
    
    def _create_system_prompt(self) -> str:
        """Create the system prompt for the AI agent"""
        return """You are a highly knowledgeable AI assistant specializing in the Kenyan real estate market. You have comprehensive knowledge about:

- Property prices across all major cities and towns in Kenya
- Residential, commercial, and industrial real estate markets
- Rental rates and market trends
- Investment opportunities and analysis
- Legal and regulatory aspects of property transactions in Kenya
- Infrastructure developments affecting property values
- Regional market variations and growth patterns

Your expertise covers:
🏠 Residential properties (houses, apartments, condos)
🏢 Commercial properties (offices, retail, malls, warehouses)
🏭 Industrial properties and land
💰 Property investments and ROI analysis
📈 Market trends and price predictions
🗺️ Location-specific advice across Kenya
📋 Property buying, selling, and rental processes

Guidelines for responses:
1. Provide accurate, up-to-date information based on your knowledge base
2. Include specific price ranges, locations, and market insights when relevant
3. Offer practical advice and actionable recommendations
4. Consider the user's budget, preferences, and investment goals
5. Mention relevant infrastructure, amenities, and growth factors
6. Be conversational but professional
7. When uncertain, clearly state limitations and suggest further research
8. Always provide context about market conditions and timing

Remember: You are helping people make informed real estate decisions in Kenya. Be helpful, accurate, and thorough in your responses."""
    
    async def process_query(
        self, 
        query: str, 
        conversation_id: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> ChatResponse:
        """Process a real estate query and generate response"""
        
        try:
            # Generate conversation ID if not provided
            if not conversation_id:
                conversation_id = str(uuid.uuid4())
            
            # Search knowledge base for relevant information
            search_results = await self.knowledge_base.search(query)
            
            # Prepare context from search results
            context = self._prepare_context(search_results)
            
            # Build conversation history
            conversation_history = self.conversations.get(conversation_id, [])
            
            # Create the full prompt
            full_prompt = self._build_prompt(query, context, conversation_history)
            
            # Generate response using Together AI
            response = await self._generate_response(
                full_prompt, max_tokens, temperature
            )
            
            # Calculate confidence score
            confidence = self._calculate_confidence(search_results, response)
            
            # Update conversation history
            conversation_history.extend([
                {"role": "user", "content": query},
                {"role": "assistant", "content": response}
            ])
            self.conversations[conversation_id] = conversation_history[-10:]  # Keep last 10 exchanges
            
            # Extract source filenames
            sources = [result.source for result in search_results]
            
            return ChatResponse(
                response=response,
                conversation_id=conversation_id,
                sources=sources,
                confidence=confidence
            )
            
        except Exception as e:
            logging.error(f"Error processing query: {str(e)}")
            return ChatResponse(
                response="I apologize, but I'm experiencing technical difficulties. Please try again later.",
                conversation_id=conversation_id or str(uuid.uuid4()),
                sources=[],
                confidence=0.0
            )
    
    def _prepare_context(self, search_results: List[SearchResult]) -> str:
        """Prepare context from search results"""
        if not search_results:
            return "No specific information found in knowledge base."
        
        context_parts = []
        for result in search_results:
            context_parts.append(f"Source: {result.source}\n{result.content}\n")
        
        context = "\n---\n".join(context_parts)
        
        # Limit context length
        if len(context) > settings.max_context_length:
            context = context[:settings.max_context_length] + "..."
        
        return context
    
    def _build_prompt(self, query: str, context: str, history: List[Dict[str, str]]) -> str:
        """Build the complete prompt for the AI model"""
        prompt_parts = [self.system_prompt]
        
        if context:
            prompt_parts.append(f"\n\nRelevant Information from Knowledge Base:\n{context}")
        
        if history:
            prompt_parts.append("\n\nConversation History:")
            for exchange in history[-4:]:  # Include last 4 exchanges for context
                role = exchange['role'].title()
                content = exchange['content']
                prompt_parts.append(f"{role}: {content}")
        
        prompt_parts.append(f"\n\nUser Question: {query}")
        prompt_parts.append("\nAssistant:")
        
        return "\n".join(prompt_parts)
    
    async def _generate_response(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """Generate response using Together AI"""
        try:
            response = self.together_client.completions.create(
                model=settings.together_model,
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=0.9,
                repetition_penalty=1.1
            )
            
            if response.choices and len(response.choices) > 0:
                return response.choices[0].text.strip()
            else:
                return "I apologize, but I couldn't generate a response at this time."
                
        except Exception as e:
            logging.error(f"Error generating response with Together AI: {str(e)}")
            return f"I'm experiencing connectivity issues. Please ensure your Together AI configuration is correct and try again."
    
    def _calculate_confidence(self, search_results: List[SearchResult], response: str) -> float:
        """Calculate confidence score based on search results and response quality"""
        if not search_results:
            return 0.3  # Low confidence without knowledge base matches
        
        # Base confidence on search result scores
        avg_score = sum(result.score for result in search_results) / len(search_results)
        
        # Adjust based on response length and content
        response_factor = min(len(response) / 500, 1.0)  # Longer responses tend to be more comprehensive
        
        # Boost if multiple sources were found
        source_factor = min(len(search_results) / 5, 1.0)
        
        confidence = (avg_score * 0.5 + response_factor * 0.3 + source_factor * 0.2)
        return round(min(confidence, 1.0), 2)
    
    def get_conversation_history(self, conversation_id: str) -> List[Dict[str, str]]:
        """Get conversation history for a given conversation ID"""
        return self.conversations.get(conversation_id, [])
    
    def clear_conversation(self, conversation_id: str) -> None:
        """Clear conversation history for a given conversation ID"""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
    
    async def get_knowledge_base_status(self) -> Dict[str, Any]:
        """Get status of the knowledge base"""
        if not self.knowledge_base.loaded:
            await self.knowledge_base.load_documents()
        
        documents_info = []
        processed_files = set()
        
        for doc in self.knowledge_base.documents:
            if doc['source'] not in processed_files:
                processed_files.add(doc['source'])
                documents_info.append({
                    'filename': doc['source'],
                    'file_type': doc['metadata']['file_type'],
                    'size': doc['metadata']['file_size'],
                    'last_modified': doc['metadata']['modified'].isoformat()
                })
        
        return {
            'total_documents': len(processed_files),
            'total_chunks': len(self.knowledge_base.documents),
            'last_updated': datetime.utcnow().isoformat(),
            'loaded': self.knowledge_base.loaded,
            'documents': documents_info
        }
