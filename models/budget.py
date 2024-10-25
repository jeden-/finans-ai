from datetime import datetime, date
from models.database import Database
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class Budget:
    def __init__(self):
        self.db = Database()

    def create_budget(self, category: str, amount: float, period: str,
                     start_date: date, end_date: Optional[date] = None,
                     notification_threshold: Optional[float] = 80.0,
                     metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a new budget for a category."""
        logger.info(f"Creating budget for category: {category}")
        
        query = """
        INSERT INTO budgets 
        (category, amount, period, start_date, end_date, notification_threshold, metadata, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """
        
        try:
            self.db.execute(query, (
                category, amount, period, start_date, end_date,
                notification_threshold, metadata, datetime.now()
            ))
            
            # Verify budget was created
            verify_query = """
            SELECT * FROM budgets 
            WHERE category = %s AND period = %s 
            ORDER BY created_at DESC LIMIT 1
            """
            created_budget = self.db.fetch_one(verify_query, (category, period))
            logger.info(f"Created budget: {created_budget}")
            return created_budget
            
        except Exception as e:
            logger.error(f"Failed to create budget: {str(e)}")
            raise

    def get_all_budgets(self) -> List[Dict[str, Any]]:
        """Get all budgets."""
        query = "SELECT * FROM budgets ORDER BY category, period"
        return self.db.fetch_all(query)

    def get_active_budgets(self, as_of_date: Optional[date] = None) -> List[Dict[str, Any]]:
        """Get active budgets as of a specific date."""
        if as_of_date is None:
            as_of_date = date.today()
            
        query = """
        SELECT * FROM budgets 
        WHERE start_date <= %s 
        AND (end_date IS NULL OR end_date >= %s)
        ORDER BY category, period
        """
        return self.db.fetch_all(query, (as_of_date, as_of_date))

    def get_budget_progress(self, budget_id: int, current_date: Optional[date] = None) -> Dict[str, Any]:
        """Get progress for a specific budget."""
        if current_date is None:
            current_date = date.today()
            
        # First get the budget details
        budget_query = "SELECT * FROM budgets WHERE id = %s"
        budget = self.db.fetch_one(budget_query, (budget_id,))
        
        if not budget:
            raise ValueError(f"Budget with id {budget_id} not found")
            
        # Calculate the spending for this budget's period
        spending_query = """
        SELECT COALESCE(SUM(amount), 0) as total_spent
        FROM transactions
        WHERE category = %s
        AND type = 'expense'
        AND created_at >= %s
        AND created_at <= %s
        """
        
        start_date = budget['start_date']
        end_date = min(current_date, budget['end_date']) if budget['end_date'] else current_date
        
        spending = self.db.fetch_one(spending_query, (budget['category'], start_date, end_date))
        total_spent = float(spending['total_spent']) if spending else 0.0
        
        # Calculate percentage spent
        budget_amount = float(budget['amount'])
        percentage_spent = (total_spent / budget_amount * 100) if budget_amount > 0 else 0
        
        return {
            'budget': budget,
            'total_spent': total_spent,
            'remaining': budget_amount - total_spent,
            'percentage_spent': percentage_spent,
            'status': 'over_budget' if percentage_spent > 100 else
                     'warning' if percentage_spent >= budget['notification_threshold'] else 'ok'
        }

    def update_budget(self, budget_id: int, data: Dict[str, Any]) -> None:
        """Update a budget by ID."""
        valid_fields = [
            'category', 'amount', 'period', 'start_date', 
            'end_date', 'notification_threshold', 'metadata'
        ]
        
        # Filter valid fields and build query
        updates = {k: v for k, v in data.items() if k in valid_fields}
        if not updates:
            logger.warning("No valid fields to update")
            return
            
        set_clause = ", ".join(f"{k} = %s" for k in updates.keys())
        values = list(updates.values()) + [budget_id]
        
        query = f"UPDATE budgets SET {set_clause} WHERE id = %s"
        self.db.execute(query, values)
        logger.info(f"Budget {budget_id} updated successfully")

    def delete_budget(self, budget_id: int) -> None:
        """Delete a budget by ID."""
        query = "DELETE FROM budgets WHERE id = %s"
        self.db.execute(query, (budget_id,))
        logger.info(f"Budget {budget_id} deleted successfully")
