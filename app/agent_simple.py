"""
Simplified Kenyan Real Estate AI Agent - Basic Version
This version uses simple text search instead of vector embeddings to get the system working quickly
"""
import os
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
import re
from datetime import datetime
import uuid

# OpenRouter AI (OpenAI-compatible)
import httpx
import json

from config.settings import settings
from app.models import SearchResult, ChatResponse
from app.logging_config import (
    get_logger, set_conversation_context, log_ai_interaction, 
    log_knowledge_search, log_performance
)
from difflib import SequenceMatcher

class SimpleKnowledgeBase:
    """Simple knowledge base using text search instead of vector embeddings"""
    
    def __init__(self):
        self.documents: List[Dict[str, Any]] = []
        self.loaded = False
        
    async def load_documents(self) -> None:
        """Load all documents from the knowledge base directory"""
        logger = get_logger(__name__)
        start_time = time.time()
        
        try:
            set_conversation_context('system', '', 'loading_knowledge_base')
            
            knowledge_path = Path(settings.knowledge_base_path)
            if not knowledge_path.exists():
                logger.error("Knowledge base path not found", extra={
                    'path': str(knowledge_path),
                    'exists': knowledge_path.exists()
                })
                raise FileNotFoundError(f"Knowledge base path not found: {knowledge_path}")
            
            self.documents = []
            processed_files = []
            
            logger.info("Starting knowledge base loading", extra={
                'knowledge_base_path': str(knowledge_path),
                'supported_types': settings.supported_file_types
            })
            
            for file_path in knowledge_path.glob("**/*"):
                if file_path.is_file() and file_path.suffix.lower() in settings.supported_file_types:
                    file_start_time = time.time()
                    content = self._extract_text(file_path)
                    if content:
                        # Split content into chunks
                        chunks = self._split_text(content)
                        file_chunks = 0
                        
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
                            file_chunks += 1
                        
                        file_duration = time.time() - file_start_time
                        processed_files.append({
                            'file_name': file_path.name,
                            'chunks': file_chunks,
                            'size_bytes': file_path.stat().st_size,
                            'processing_time': file_duration
                        })
                        
                        logger.debug("File processed", extra={
                            'processed_file': file_path.name,
                            'chunks_created': file_chunks,
                            'file_size_bytes': file_path.stat().st_size,
                            'processing_time_seconds': file_duration
                        })
            
            self.loaded = True
            total_duration = time.time() - start_time
            
            logger.info("Knowledge base loaded successfully", extra={
                'total_documents': len(processed_files),
                'total_chunks': len(self.documents),
                'loading_time_seconds': total_duration,
                'processed_files': processed_files
            })
            
            if total_duration > 2.0:
                log_performance("knowledge_base_loading", total_duration, 
                               files_processed=len(processed_files),
                               total_chunks=len(self.documents))
                
        except Exception as e:
            logger.error("Error loading knowledge base", extra={
                'error': str(e),
                'path': str(knowledge_path) if 'knowledge_path' in locals() else 'unknown'
            }, exc_info=True)
            raise
    
    def _extract_text(self, file_path: Path) -> Optional[str]:
        """Extract text from different file types"""
        try:
            if file_path.suffix.lower() == '.txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            # For now, only support .txt files to avoid complex dependencies
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
        """Search for relevant documents using simple text matching"""
        logger = get_logger(__name__)
        start_time = time.time()
        
        if not self.loaded:
            logger.info("Knowledge base not loaded, loading now...")
            await self.load_documents()
        
        if not self.loaded:
            logger.error("Knowledge base failed to load")
            return []
        
        try:
            # Simple keyword-based search
            query_words = set(re.findall(r'\b\w+\b', query.lower()))
            results = []
            documents_checked = 0
            
            logger.debug("Starting knowledge base search", extra={
                'query': query[:100] + '...' if len(query) > 100 else query,
                'query_words_count': len(query_words),
                'total_documents': len(self.documents),
                'top_k': top_k
            })
            
            for doc in self.documents:
                documents_checked += 1
                content_lower = doc['content'].lower()
                content_words = set(re.findall(r'\b\w+\b', content_lower))
                
                # Calculate simple similarity based on word overlap
                overlap = len(query_words.intersection(content_words))
                if overlap > 0:
                    similarity = overlap / len(query_words.union(content_words))
                    
                    if similarity > 0.1:  # Simple threshold
                        result = SearchResult(
                            content=doc['content'],
                            source=doc['source'],
                            score=similarity,
                            metadata=doc['metadata']
                        )
                        results.append(result)
            
            # Sort by similarity score
            results.sort(key=lambda x: x.score, reverse=True)
            final_results = results[:top_k]
            
            search_duration = time.time() - start_time
            
            # Log search results
            log_knowledge_search(
                query=query,
                results_count=len(final_results),
                duration=search_duration,
                documents_searched=documents_checked,
                total_matches=len(results)
            )
            
            logger.debug("Knowledge base search completed", extra={
                'results_found': len(final_results),
                'total_potential_matches': len(results),
                'documents_searched': documents_checked,
                'search_time_seconds': search_duration,
                'average_score': sum(r.score for r in final_results) / len(final_results) if final_results else 0
            })
            
            return final_results
            
        except Exception as e:
            search_duration = time.time() - start_time
            logger.error("Error searching knowledge base", extra={
                'error': str(e),
                'query': query[:100] + '...' if len(query) > 100 else query,
                'search_duration_seconds': search_duration
            }, exc_info=True)
            return []


class SimpleRealEstateAgent:
    """Simplified Kenyan Real Estate AI Agent"""
    
    def __init__(self):
        # OpenRouter configuration
        self.openrouter_api_key = settings.openrouter_api_key
        self.openrouter_model = settings.openrouter_model
        
        # Debug logging
        logger = get_logger(__name__)
        logger.debug(f"OpenRouter API Key loaded: {'Yes' if self.openrouter_api_key else 'No'}")
        logger.debug(f"OpenRouter API Key length: {len(self.openrouter_api_key) if self.openrouter_api_key else 0}")
        logger.debug(f"OpenRouter Model: {self.openrouter_model}")
        
        self.knowledge_base = SimpleKnowledgeBase()
        self.conversations: Dict[str, List[Dict[str, str]]] = {}
        self.system_prompt = self._create_system_prompt()
        
    async def initialize(self):
        """Initialize the agent and load knowledge base"""
        logger = get_logger(__name__)
        start_time = time.time()
        
        set_conversation_context('system', '', 'agent_initialization')
        
        logger.info("Initializing Real Estate AI Agent...", extra={
            'agent_type': 'SimpleRealEstateAgent',
            'openrouter_model': settings.openrouter_model
        })
        
        await self.knowledge_base.load_documents()
        
        init_duration = time.time() - start_time
        logger.info("Real Estate AI Agent initialized successfully", extra={
            'initialization_time_seconds': init_duration,
            'knowledge_base_loaded': self.knowledge_base.loaded,
            'total_documents': len(self.knowledge_base.documents)
        })
    
    def _create_system_prompt(self) -> str:
        """Create the system prompt for the AI agent"""
        return """You are a knowledgeable Kenyan real estate assistant. Have natural conversations about property prices, locations, and market trends in Kenya.

CONVERSATION RULES:
- Keep responses conversational and concise (2-4 sentences max)
- Only use greetings like "Hey" or "Hi" for the FIRST message in a conversation
- For follow-up messages, jump straight to the answer
- Remember what you've discussed and build on it naturally
- Stay on topic and reference previous questions when relevant
- Don't repeat information you've already provided

RESPONSE STYLE:
- Give specific prices and examples when possible
- Use natural, friendly tone without being overly casual
- If unsure, give reasonable estimates and suggest checking current sources
- Focus directly on what they're asking

You know about property markets across Kenya, especially Nairobi areas like Westlands, Karen, Kilimani, etc.

Be helpful, context-aware, and conversational."""
    
    async def process_query(
        self, 
        query: str, 
        conversation_id: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> ChatResponse:
        """Process a real estate query and generate response"""
        logger = get_logger(__name__)
        start_time = time.time()
        
        try:
            # Generate conversation ID if not provided
            if not conversation_id:
                conversation_id = str(uuid.uuid4())
            
            set_conversation_context(conversation_id, query, 'query_processing')
            
            logger.info("Processing real estate query", extra={
                'query': query[:200] + '...' if len(query) > 200 else query,
                'conversation_id': conversation_id,
                'max_tokens': max_tokens,
                'temperature': temperature
            })
            
            # Search knowledge base for relevant information
            set_conversation_context(conversation_id, query, 'knowledge_search')
            search_start = time.time()
            search_results = await self.knowledge_base.search(query)
            search_duration = time.time() - search_start
            
            logger.debug("Knowledge base search completed", extra={
                'search_results_count': len(search_results),
                'search_duration_seconds': search_duration,
                'top_score': search_results[0].score if search_results else 0
            })
            
            # Prepare context from search results
            set_conversation_context(conversation_id, query, 'context_preparation')
            context = self._prepare_context(search_results)
            context_length = len(context)
            
            # Build conversation history
            conversation_history = self.conversations.get(conversation_id, [])
            history_length = len(conversation_history)
            
            # Create the full prompt
            set_conversation_context(conversation_id, query, 'prompt_building')
            full_prompt = self._build_prompt(query, context, conversation_history)
            prompt_length = len(full_prompt)
            
            logger.debug("Prompt prepared", extra={
                'context_length': context_length,
                'conversation_history_entries': history_length,
                'total_prompt_length': prompt_length
            })
            
            # Generate response using OpenRouter with optimized settings for concise responses
            set_conversation_context(conversation_id, query, 'ai_generation')
            ai_start = time.time()
            # Optimize parameters for shorter, more focused responses
            concise_max_tokens = min(max_tokens, 250)  # Limit response length
            concise_temperature = min(temperature, 0.7)  # Less randomness for focused answers
            response = await self._generate_response(
                full_prompt, concise_max_tokens, concise_temperature
            )
            ai_duration = time.time() - ai_start
            
            # Log AI interaction
            log_ai_interaction(
                model=settings.openrouter_model,
                prompt_length=prompt_length,
                response_length=len(response),
                duration=ai_duration,
                conversation_id=conversation_id
            )
            
            # Calculate confidence score
            set_conversation_context(conversation_id, query, 'confidence_calculation')
            confidence = self._calculate_confidence(search_results, response)
            
            # Update conversation history
            conversation_history.extend([
                {"role": "user", "content": query},
                {"role": "assistant", "content": response}
            ])
            self.conversations[conversation_id] = conversation_history[-10:]  # Keep last 10 exchanges
            
            # Extract source filenames
            sources = [result.source for result in search_results]
            
            total_duration = time.time() - start_time
            
            logger.info("Query processing completed successfully", extra={
                'conversation_id': conversation_id,
                'total_processing_time_seconds': total_duration,
                'response_length': len(response),
                'confidence_score': confidence,
                'sources_used': len(sources),
                'search_time_seconds': search_duration,
                'ai_generation_time_seconds': ai_duration
            })
            
            return ChatResponse(
                response=response,
                conversation_id=conversation_id,
                sources=sources,
                confidence=confidence
            )
            
        except Exception as e:
            total_duration = time.time() - start_time
            logger.error("Error processing query", extra={
                'error': str(e),
                'conversation_id': conversation_id or 'unknown',
                'query': query[:200] + '...' if len(query) > 200 else query,
                'processing_time_seconds': total_duration
            }, exc_info=True)
            
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
        
        # Add conversation context
        is_first_message = len(history) == 0
        conversation_context = "\n\nCONVERSATION CONTEXT:"
        if is_first_message:
            conversation_context += "\n- This is the FIRST message in this conversation"
            conversation_context += "\n- You may use a brief, natural greeting if appropriate"
        else:
            conversation_context += "\n- This is a FOLLOW-UP message in an ongoing conversation"
            conversation_context += "\n- NO greetings needed - jump straight to answering"
            conversation_context += "\n- Reference previous discussion when relevant"
        
        prompt_parts.append(conversation_context)
        
        if context:
            prompt_parts.append(f"\n\nRelevant Information from Knowledge Base:\n{context}")
        
        if history and len(history) > 0:
            prompt_parts.append("\n\nPrevious Conversation:")
            # Include last 4 exchanges but make it more natural
            recent_history = history[-4:]
            for exchange in recent_history:
                role = "You" if exchange['role'] == 'assistant' else "User"
                content = exchange['content']
                prompt_parts.append(f"{role}: {content}")
        
        prompt_parts.append(f"\n\nCurrent User Question: {query}")
        prompt_parts.append("\nYour Response:")
        
        return "\n".join(prompt_parts)
    
    async def _generate_response(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """Generate response using OpenRouter AI"""
        logger = get_logger(__name__)
        start_time = time.time()
        
        try:
            logger.debug("Sending request to OpenRouter", extra={
                'model': self.openrouter_model,
                'prompt_length': len(prompt),
                'max_tokens': max_tokens,
                'temperature': temperature
            })
            
            # OpenRouter API (OpenAI-compatible)
            url = "https://openrouter.ai/api/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.openrouter_api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:8000",  # Optional: for tracking
                "X-Title": "Kenyan Real Estate AI Agent"  # Optional: for tracking
            }
            
            # Convert prompt to OpenAI chat format
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ]
            
            data = {
                "model": self.openrouter_model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": 0.9,
                "stream": False
            }
            
            async with httpx.AsyncClient() as client:
                api_response = await client.post(url, headers=headers, json=data, timeout=60.0)
                api_response.raise_for_status()
                response = api_response.json()
            
            generation_time = time.time() - start_time
            
            # Parse OpenAI-compatible response
            generated_text = ""
            if response and 'choices' in response and len(response['choices']) > 0:
                choice = response['choices'][0]
                if 'message' in choice and 'content' in choice['message']:
                    generated_text = choice['message']['content'].strip()
                elif 'text' in choice:
                    generated_text = choice['text'].strip()
                
                logger.debug("Raw API response structure", extra={
                    'response_type': type(response).__name__,
                    'response_keys': list(response.keys()) if isinstance(response, dict) else 'not_dict',
                    'choices_count': len(response.get('choices', [])),
                    'usage': response.get('usage', {})
                })
                
            if generated_text:
                logger.debug("OpenRouter response received", extra={
                    'response_length': len(generated_text),
                    'generation_time_seconds': generation_time,
                    'tokens_per_second': len(generated_text.split()) / generation_time if generation_time > 0 else 0,
                    'model_used': self.openrouter_model
                })
                
                return generated_text
            else:
                logger.warning("OpenRouter returned empty response", extra={
                    'response_structure': str(response) if response else 'None',
                    'generation_time_seconds': generation_time
                })
                return "I apologize, but I couldn't generate a response at this time."
                
        except Exception as e:
            generation_time = time.time() - start_time
            logger.error("Error generating response with OpenRouter", extra={
                'error': str(e),
                'model': self.openrouter_model,
                'prompt_length': len(prompt),
                'generation_time_seconds': generation_time,
                'api_key_provided': bool(self.openrouter_api_key)
            }, exc_info=True)
            
            # Return a helpful error message based on the error type
            error_str = str(e).lower()
            if 'api key' in error_str or 'authentication' in error_str or '401' in error_str:
                return "I'm experiencing authentication issues with the AI service. Please check the API configuration."
            elif 'rate limit' in error_str or 'quota' in error_str or '429' in error_str:
                return "I'm experiencing rate limiting from the AI service. Please try again in a moment."
            elif 'network' in error_str or 'connection' in error_str:
                return "I'm experiencing network connectivity issues. Please try again."
            else:
                return f"I'm experiencing technical difficulties with the AI service. Please try again later."
    
    def _calculate_confidence(self, search_results: List[SearchResult], response: str) -> float:
        """Calculate confidence score based on search results and response quality"""
        if not search_results:
            return 0.3  # Low confidence without knowledge base matches
        
        # Base confidence on search result scores
        avg_score = sum(result.score for result in search_results) / len(search_results)
        
        # Adjust based on response length and content
        response_factor = min(len(response) / 500, 1.0)
        
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
                    'file_name': doc['source'],
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





    async def respond_and_recommend_properties(
        self,
        query: str,
        conversation_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        max_results: int = 3,
        max_tokens: int = 800,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Responds to a user query and recommends the most relevant properties.
        Prioritizes correct location and property type relevance.
        """
        logger = get_logger(__name__)
        start_time = time.time()

        try:
            if not conversation_id:
                conversation_id = str(uuid.uuid4())

            # --- Step 1: AI-generated conversational reply
            ai_response = await self.process_query(query, conversation_id, max_tokens, temperature)

            # --- Step 2: Load property dataset
            properties_path = Path("properties_data.json")
            if not properties_path.exists():
                logger.error("Property data file missing", extra={'path': str(properties_path)})
                return {
                    "response": f"{ai_response.response}\n\n⚠️ Property data unavailable.",
                    "recommended_properties": [],
                    "conversation_id": conversation_id,
                    "confidence": ai_response.confidence,
                    "timestamp": datetime.utcnow().isoformat()
                }

            with open(properties_path, 'r', encoding='utf-8') as f:
                properties = json.load(f)

            # --- Step 3: Parse query context
            query_lower = query.lower()
            likely_location = None
            likely_type = None

            # crude but effective inference
            for prop in properties:
                suburb = prop["location"]["suburb"].lower()
                if suburb in query_lower:
                    likely_location = suburb
                    break

            for t in ["apartment", "bedsitter", "studio", "house", "maisonette"]:
                if t in query_lower:
                    likely_type = t
                    break

            # --- Step 4: Apply filters (if provided)
            if filters:
                logger.info("Applying filters", extra={'filters': filters})
                filtered_props = []
                for prop in properties:
                    include = True
                    if "location" in filters:
                        loc = filters["location"].lower()
                        include &= loc in prop["location"]["suburb"].lower() or loc in prop["location"]["city"].lower()
                    if "min_price" in filters:
                        include &= prop["price"] >= filters["min_price"]
                    if "max_price" in filters:
                        include &= prop["price"] <= filters["max_price"]
                    if "bedrooms" in filters:
                        include &= prop["bedrooms"] >= filters["bedrooms"]
                    if "bathrooms" in filters:
                        include &= prop["bathrooms"] >= filters["bathrooms"]
                    if "furnished" in filters:
                        include &= prop["furnished"] == filters["furnished"]
                    if "property_type" in filters:
                        include &= prop["property_type"].lower() == filters["property_type"].lower()

                    if include:
                        filtered_props.append(prop)

                properties = filtered_props
                logger.info(f"Filtered property count: {len(properties)}", extra={'filters': filters})

            # --- Step 5: Relevance scoring
            scored: List[Dict[str, Any]] = []
            for prop in properties:
                prop_text = " ".join([
                    prop["title"],
                    prop["description"],
                    prop["property_type"],
                    prop["listing_type"],
                    prop["location"]["suburb"],
                    " ".join(prop["amenities"])
                ]).lower()

                text_similarity = SequenceMatcher(None, query_lower, prop_text).ratio()

                # Stronger bonuses and penalties
                location_bonus = 0.4 if likely_location and likely_location == prop["location"]["suburb"].lower() else 0
                type_bonus = 0.3 if likely_type and likely_type == prop["property_type"].lower() else 0
                furnished_bonus = 0.05 if ("furnished" in query_lower and prop["furnished"]) else 0
                price_bonus = 0.1 if "affordable" in query_lower and prop["price"] < 100000 else 0

                # Penalties for mismatches
                location_penalty = -0.3 if likely_location and likely_location != prop["location"]["suburb"].lower() else 0
                type_penalty = -0.25 if likely_type and likely_type != prop["property_type"].lower() else 0

                score = text_similarity + location_bonus + type_bonus + furnished_bonus + price_bonus + location_penalty + type_penalty
                prop["match_score"] = round(score, 3)
                scored.append(prop)

            # --- Step 6: Filter out weak matches (< 0.25)
            scored = [p for p in scored if p["match_score"] >= 0.25]
            top_props = sorted(scored, key=lambda x: x["match_score"], reverse=True)[:max_results]

            # --- Step 7: Prepare structured recommendations
            recommended_listings = [
                {
                    "Title": prop["title"],
                    "Location": prop["location"]["suburb"],
                    "Price": prop["price"],
                    "Bedrooms": prop["bedrooms"],
                    "Bathrooms": prop["bathrooms"],
                    "Type": prop["property_type"],
                    "Furnished": prop["furnished"],
                    "Amenities": prop["amenities"][:4],
                    "Rating": prop["rating"],
                    "MatchScore": prop["match_score"],
                    "ImageURL": prop["images"][0] if prop["images"] else None
                }
                for prop in top_props
            ]

            total_time = round(time.time() - start_time, 2)
            logger.info("Respond and Recommend complete", extra={
                'conversation_id': conversation_id,
                'query': query,
                'matches_found': len(top_props),
                'processing_time_s': total_time
            })

            # --- Step 8: Return structured data
            return {
                "response": ai_response.response,
                "recommended_properties": recommended_listings,
                "conversation_id": conversation_id,
                "confidence": ai_response.confidence,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error("Error in respond_and_recommend_properties", extra={'error': str(e)}, exc_info=True)
            return {
                "response": "⚠️ Sorry, I'm having trouble fetching property recommendations right now.",
                "recommended_properties": [],
                "conversation_id": conversation_id or str(uuid.uuid4()),
                "confidence": 0.0,
                "timestamp": datetime.utcnow().isoformat()
            }
