import random
from datetime import datetime, timedelta
from decimal import Decimal
from models.transaction import Transaction
from models.budget import Budget

def generate_test_transactions(num_transactions=50):
    """Generate test transaction data."""
    categories = ['groceries', 'utilities', 'entertainment', 'transportation', 'housing']
    types = ['income', 'expense']
    cycles = ['none', 'monthly', 'yearly']
    
    transaction = Transaction()
    
    for _ in range(num_transactions):
        amount = round(random.uniform(10, 1000), 2)
        trans_type = random.choice(types)
        category = random.choice(categories)
        
        # Create transaction with random data
        transaction.create_transaction(
            description=f"Test {trans_type} for {category}",
            amount=amount,
            type=trans_type,
            category=category,
            cycle=random.choice(cycles),
            created_at=datetime.now() - timedelta(days=random.randint(0, 365)),
            due_date=None
        )

def generate_test_budgets():
    """Generate test budget data."""
    categories = ['groceries', 'utilities', 'entertainment', 'transportation', 'housing']
    periods = ['monthly', 'yearly']
    
    budget = Budget()
    
    for category in categories:
        amount = round(random.uniform(500, 5000), 2)
        budget.create_budget(
            category=category,
            amount=amount,
            period=random.choice(periods),
            start_date=datetime.now().date(),
            end_date=None,
            notification_threshold=0.8
        )

if __name__ == "__main__":
    print("Generating test data...")
    generate_test_transactions()
    generate_test_budgets()
    print("Test data generation completed!")
