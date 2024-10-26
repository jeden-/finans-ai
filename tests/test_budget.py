import pytest
from models.budget import Budget
from decimal import Decimal
import datetime

def test_budget_creation(mock_db, sample_budget_data):
    """Test budget creation functionality."""
    budget = Budget()
    result = budget.create_budget(**sample_budget_data)
    assert result is True

def test_budget_progress_calculation(mock_db):
    """Test budget progress calculation."""
    budget = Budget()
    progress = budget.get_budget_progress(1)
    assert isinstance(progress['spent'], float)
    assert isinstance(progress['remaining'], float)

def test_decimal_float_conversion(mock_db, sample_budget_data):
    """Test decimal to float conversion in budget calculations."""
    budget = Budget()
    # Create a budget with Decimal amount
    sample_budget_data['amount'] = Decimal('500.00')
    budget.create_budget(**sample_budget_data)
    
    # Get progress and verify types
    progress = budget.get_budget_progress(1)
    assert isinstance(progress['spent'], float)
    assert isinstance(progress['remaining'], float)

def test_get_unique_categories(mock_db):
    """Test retrieving unique categories."""
    budget = Budget()
    categories = budget.get_unique_categories()
    assert isinstance(categories, list)

def test_invalid_budget_amount(mock_db):
    """Test budget creation with invalid amount."""
    budget = Budget()
    with pytest.raises(ValueError):
        budget.create_budget(
            category='test',
            amount=-100,
            period='monthly'
        )

def test_date_validation(mock_db):
    """Test budget date validation."""
    budget = Budget()
    with pytest.raises(ValueError):
        budget.create_budget(
            category='test',
            amount=100,
            period='monthly',
            start_date=datetime.date(2024, 1, 1),
            end_date=datetime.date(2023, 1, 1)  # End date before start date
        )
