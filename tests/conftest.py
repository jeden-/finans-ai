import pytest
from models.database import Database
from datetime import datetime, date
import os

@pytest.fixture
def mock_db():
    """Create a test database connection."""
    return Database()

@pytest.fixture
def sample_transaction_data():
    """Provide sample transaction data for tests."""
    return {
        'description': 'Test transaction',
        'amount': 100.0,
        'type': 'expense',
        'category': 'groceries',
        'cycle': 'none',
        'created_at': datetime.now(),
        'due_date': None
    }

@pytest.fixture
def sample_budget_data():
    """Provide sample budget data for tests."""
    return {
        'category': 'groceries',
        'amount': 500.0,
        'period': 'monthly',
        'start_date': date.today(),
        'end_date': None,
        'notification_threshold': 0.8
    }

@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response."""
    return {
        'choices': [{
            'message': {
                'content': 'Test response'
            }
        }]
    }

@pytest.fixture
def mock_ollama_response():
    """Mock Ollama API response."""
    return {
        'response': 'Test response'
    }
