from datetime import datetime, timedelta, date
from models.database import Database
from typing import Optional, Dict, Any
import json

class Transaction:
    def __init__(self):
        self.db = Database()

    def create_transaction(self, description: str, amount: float, type: str, 
                         category: str, cycle: str, start_date: Optional[date] = None, 
                         end_date: Optional[date] = None, metadata: Dict[str, Any] = None):
        """Create a new transaction with support for recurring amounts."""
        if cycle != "none" and start_date:
            # Set default end_date to 5 years from start if not specified
            if not end_date:
                end_date = start_date + timedelta(days=365 * 5)

        query = """
        INSERT INTO transactions 
        (description, amount, type, category, cycle, start_date, end_date, created_at, transaction_text, metadata)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """
        self.db.execute(query, (
            description, amount, type, category, cycle, 
            start_date, end_date, datetime.now(), 
            description,  # Store original text
            json.dumps(metadata) if metadata else None
        ))

    def get_all_transactions(self):
        query = "SELECT * FROM transactions ORDER BY created_at DESC"
        return self.db.fetch_all(query)

    def get_transactions_for_period(self, start_date: date, end_date: date):
        """Get transactions for a specific period, calculating recurring amounts."""
        query = """
        SELECT *, 
            CASE 
                WHEN cycle = 'daily' THEN 
                    amount * (
                        LEAST(end_date, %s) - GREATEST(start_date, %s)
                    )::integer
                WHEN cycle = 'weekly' THEN 
                    amount * (
                        EXTRACT(WEEK FROM LEAST(end_date, %s)) - 
                        EXTRACT(WEEK FROM GREATEST(start_date, %s))
                    )::integer
                WHEN cycle = 'monthly' THEN 
                    amount * (
                        EXTRACT(MONTH FROM LEAST(end_date, %s)) - 
                        EXTRACT(MONTH FROM GREATEST(start_date, %s)) +
                        12 * (
                            EXTRACT(YEAR FROM LEAST(end_date, %s)) - 
                            EXTRACT(YEAR FROM GREATEST(start_date, %s))
                        )
                    )::integer
                WHEN cycle = 'yearly' THEN 
                    amount * (
                        EXTRACT(YEAR FROM LEAST(end_date, %s)) - 
                        EXTRACT(YEAR FROM GREATEST(start_date, %s))
                    )::integer
                ELSE amount
            END as calculated_amount
        FROM transactions
        WHERE 
            (cycle = 'none' AND created_at BETWEEN %s AND %s)
            OR 
            (cycle != 'none' AND 
             start_date <= %s AND 
             (end_date IS NULL OR end_date >= %s))
        """
        return self.db.fetch_all(query, (
            end_date, start_date,  # For daily
            end_date, start_date,  # For weekly
            end_date, start_date, end_date, start_date,  # For monthly
            end_date, start_date,  # For yearly
            start_date, end_date,  # For non-recurring
            end_date, start_date  # For recurring date range
        ))

    def get_summary_by_category(self, start_date: Optional[date] = None, end_date: Optional[date] = None):
        """Get summary by category for a specific period."""
        if start_date and end_date:
            transactions = self.get_transactions_for_period(start_date, end_date)
        else:
            transactions = self.get_all_transactions()
        
        # Calculate totals using the calculated_amount if available
        category_totals = {}
        for t in transactions:
            amount = t.get('calculated_amount', t['amount'])
            category = t['category']
            category_totals[category] = category_totals.get(category, 0) + amount
        
        return [{'category': k, 'total': v} for k, v in category_totals.items()]

    def delete_transaction(self, transaction_id: int):
        """Delete a transaction by ID."""
        query = "DELETE FROM transactions WHERE id = %s"
        self.db.execute(query, (transaction_id,))

    def update_transaction(self, transaction_id: int, data: Dict[str, Any]):
        """Update a transaction by ID."""
        valid_fields = [
            'description', 'amount', 'type', 'category', 
            'cycle', 'start_date', 'end_date', 'metadata'
        ]
        
        # Filter valid fields and build query
        updates = {k: v for k, v in data.items() if k in valid_fields}
        if not updates:
            return
        
        set_clause = ", ".join(f"{k} = %s" for k in updates.keys())
        values = list(updates.values()) + [transaction_id]
        
        query = f"UPDATE transactions SET {set_clause} WHERE id = %s"
        self.db.execute(query, values)
