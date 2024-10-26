import pytest
from services.financial_chat_service import FinancialChatService
from services.openai_service import OpenAIService
from services.ollama_service import OllamaService
from unittest.mock import patch, MagicMock

def test_chat_service_initialization():
    """Test chat service initialization."""
    service = FinancialChatService()
    assert service is not None
    assert service.rag_service is not None

@patch('services.openai_service.OpenAI')
def test_openai_chat_completion(mock_openai, mock_openai_response):
    """Test OpenAI chat completion."""
    service = OpenAIService()
    mock_openai.return_value.chat.completions.create.return_value = mock_openai_response
    
    response = service.get_chat_completion("Test query")
    assert response == "Test response"

def test_ollama_chat_completion(mock_ollama_response):
    """Test Ollama chat completion."""
    with patch('requests.post') as mock_post:
        mock_post.return_value.json.return_value = mock_ollama_response
        mock_post.return_value.status_code = 200
        
        service = OllamaService()
        response = service.get_chat_completion("Test query")
        assert response == "Test response"

def test_error_handling():
    """Test error handling in chat services."""
    service = FinancialChatService()
    response = service.get_chat_response("Invalid query that should trigger an error")
    assert 'error' in response or response.get('response') is not None
