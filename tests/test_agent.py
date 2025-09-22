"""
Basic tests for the Kenyan Real Estate AI Agent
"""
import pytest
import asyncio
from app.agent import RealEstateAgent, KnowledgeBase
from app.models import ChatRequest, ChatResponse
from config.settings import settings


@pytest.fixture
def agent():
    """Create an agent instance for testing"""
    return RealEstateAgent()


@pytest.fixture
def knowledge_base():
    """Create a knowledge base instance for testing"""
    return KnowledgeBase()


class TestKnowledgeBase:
    """Test the knowledge base functionality"""
    
    @pytest.mark.asyncio
    async def test_knowledge_base_initialization(self, knowledge_base):
        """Test that knowledge base can be initialized"""
        assert knowledge_base is not None
        assert hasattr(knowledge_base, 'embeddings_model')
        assert hasattr(knowledge_base, 'documents')
    
    @pytest.mark.asyncio
    async def test_load_documents(self, knowledge_base):
        """Test loading documents from knowledge base"""
        try:
            await knowledge_base.load_documents()
            # Should not raise exception even if no documents found
            assert True
        except Exception as e:
            pytest.fail(f"Document loading failed: {e}")


class TestRealEstateAgent:
    """Test the main AI agent functionality"""
    
    def test_agent_initialization(self, agent):
        """Test that agent can be initialized"""
        assert agent is not None
        assert hasattr(agent, 'together_client')
        assert hasattr(agent, 'knowledge_base')
        assert hasattr(agent, 'conversations')
    
    @pytest.mark.asyncio
    async def test_agent_initialize(self, agent):
        """Test agent initialization"""
        try:
            await agent.initialize()
            assert True
        except Exception as e:
            # May fail if Together AI key is invalid, but shouldn't crash
            assert "Together AI" in str(e) or "knowledge" in str(e).lower()
    
    def test_system_prompt_creation(self, agent):
        """Test system prompt creation"""
        prompt = agent._create_system_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 100
        assert "Kenyan real estate" in prompt.lower()
        assert "properties" in prompt.lower()


class TestUtilityFunctions:
    """Test utility functions"""
    
    def test_extract_property_details(self):
        """Test property detail extraction from queries"""
        from app.utils import extract_property_details
        
        # Test basic query
        query1 = "I'm looking for a 3-bedroom house in Karen for under 20 million"
        details1 = extract_property_details(query1)
        
        assert details1.get('bedrooms') == 3
        assert details1.get('location') == 'Karen'
        assert details1.get('property_type') == 'house'
        
        # Test rental query
        query2 = "2-bedroom apartment for rent in Westlands"
        details2 = extract_property_details(query2)
        
        assert details2.get('bedrooms') == 2
        assert details2.get('property_type') == 'apartment'
        assert details2.get('transaction_type') == 'rent'
    
    def test_format_price(self):
        """Test price formatting"""
        from app.utils import format_price
        
        # Test millions
        assert "million" in format_price(5000000).lower()
        
        # Test thousands
        assert "k" in format_price(50000).lower()
        
        # Test regular amounts
        result = format_price(500)
        assert "KSH" in result
    
    def test_sanitize_input(self):
        """Test input sanitization"""
        from app.utils import sanitize_input
        
        # Test harmful characters removal
        dirty_input = "<script>alert('hack')</script>What are property prices?"
        clean_input = sanitize_input(dirty_input)
        
        assert "<script>" not in clean_input
        assert "What are property prices?" in clean_input
        
        # Test length limit
        long_input = "a" * 2000
        limited_input = sanitize_input(long_input, max_length=100)
        assert len(limited_input) <= 103  # 100 + "..."


class TestAPIModels:
    """Test Pydantic models"""
    
    def test_chat_request_validation(self):
        """Test ChatRequest model validation"""
        from app.models import ChatRequest
        
        # Valid request
        valid_request = ChatRequest(query="What are property prices in Nairobi?")
        assert valid_request.query == "What are property prices in Nairobi?"
        assert valid_request.max_tokens == 1000  # default
        
        # Test with all fields
        full_request = ChatRequest(
            query="Test query",
            conversation_id="test-123",
            max_tokens=500,
            temperature=0.5
        )
        assert full_request.conversation_id == "test-123"
        assert full_request.max_tokens == 500
        assert full_request.temperature == 0.5
    
    def test_chat_response_creation(self):
        """Test ChatResponse model creation"""
        from app.models import ChatResponse
        from datetime import datetime
        
        response = ChatResponse(
            response="Test response",
            conversation_id="test-123",
            sources=["source1.txt"],
            confidence=0.85
        )
        
        assert response.response == "Test response"
        assert response.conversation_id == "test-123"
        assert response.sources == ["source1.txt"]
        assert response.confidence == 0.85
        assert isinstance(response.timestamp, datetime)


@pytest.mark.integration
class TestIntegration:
    """Integration tests (require actual API keys and setup)"""
    
    @pytest.mark.asyncio
    async def test_full_query_processing(self, agent):
        """Test full query processing pipeline"""
        if not settings.together_api_key or settings.together_api_key == "your_api_key_here":
            pytest.skip("No valid Together AI API key configured")
        
        try:
            await agent.initialize()
            
            query = "What are typical property prices in Westlands?"
            response = await agent.process_query(query)
            
            assert isinstance(response, ChatResponse)
            assert len(response.response) > 0
            assert response.conversation_id is not None
            assert 0 <= response.confidence <= 1
            
        except Exception as e:
            if "api" in str(e).lower() or "key" in str(e).lower():
                pytest.skip(f"API configuration issue: {e}")
            else:
                raise


if __name__ == "__main__":
    # Run basic tests
    pytest.main([__file__, "-v"])
