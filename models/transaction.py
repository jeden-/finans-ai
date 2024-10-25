from datetime import datetime, timedelta, date
from models.database import Database
from typing import Optional, Dict, Any
import json
import logging

# Configure logging
logger = logging.getLogger(__name__)

class Transaction:
    def __init__(self):
        self.db = Database()

    def create_transaction(self, description: str, amount: float, type: str, 
                         category: str, cycle: str, start_date: Optional[date] = None, 
                         end_date: Optional[date] = None, due_date: Optional[date] = None,
                         metadata: Dict[str, Any] = None):
        """Create a new transaction with support for recurring amounts."""
        logger.info(f"Creating transaction: {description}, amount: {amount}")
        
        if cycle != "none":
            # Set default start_date to today if not provided
            if not start_date:
                start_date = date.today()
            
            # Set default end_date to 5 years from start if not provided
            if not end_date:
                end_date = start_date + timedelta(days=365 * 5)
            
            # For yearly transactions, set due_date if not provided
            if cycle == "yearly" and not due_date:
                due_date = start_date

        query = """
        INSERT INTO transactions 
        (description, amount, type, category, cycle, start_date, end_date, due_date, created_at, transaction_text, metadata)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """
        
        params = (
            description, amount, type, category, cycle, 
            start_date, end_date, due_date, datetime.now(), 
            description,  # Store original text
            json.dumps(metadata) if metadata else None
        )
        
        try:
            self.db.execute(query, params)
            logger.info("Transaction created successfully")
            
            # Verify transaction was created
            verify_query = "SELECT * FROM transactions WHERE description = %s ORDER BY created_at DESC LIMIT 1"
            created_tx = self.db.fetch_one(verify_query, (description,))
            logger.info(f"Verified created transaction: {created_tx}")
            return created_tx
            
        except Exception as e:
            logger.error(f"Failed to create transaction: {str(e)}")
            raise

    def get_all_transactions(self):
        logger.info("Attempting to fetch all transactions")
        query = "SELECT * FROM transactions ORDER BY created_at DESC"
        results = self.db.fetch_all(query)
        logger.info(f"Found {len(results) if results else 0} transactions")
        return results

    def get_transactions_for_period(self, start_date: date, end_date: date):
        """Get transactions for a specific period, calculating recurring amounts."""
        logger.info(f"Fetching transactions for period: {start_date} to {end_date}")
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
        params = (
            end_date, start_date,  # For daily
            end_date, start_date,  # For weekly
            end_date, start_date, end_date, start_date,  # For monthly
            end_date, start_date,  # For yearly
            start_date, end_date,  # For non-recurring
            end_date, start_date  # For recurring date range
        )
        results = self.db.fetch_all(query, params)
        logger.info(f"Found {len(results)} transactions for period")
        return results

    def delete_transaction(self, transaction_id: int):
        """Delete a transaction by ID."""
        logger.info(f"Deleting transaction with ID: {transaction_id}")
        query = "DELETE FROM transactions WHERE id = %s"
        self.db.execute(query, (transaction_id,))
        logger.info("Transaction deleted successfully")

    def update_transaction(self, transaction_id: int, data: Dict[str, Any]):
        """Update a transaction by ID."""
        logger.info(f"Updating transaction {transaction_id} with data: {data}")
        valid_fields = [
            'description', 'amount', 'type', 'category', 
            'cycle', 'start_date', 'end_date', 'due_date', 'metadata'
        ]
        
        # Filter valid fields and build query
        updates = {k: v for k, v in data.items() if k in valid_fields}
        if not updates:
            logger.warning("No valid fields to update")
            return
        
        set_clause = ", ".join(f"{k} = %s" for k in updates.keys())
        values = list(updates.values()) + [transaction_id]
        
        query = f"UPDATE transactions SET {set_clause} WHERE id = %s"
        self.db.execute(query, values)
        logger.info("Transaction updated successfully")
