from models.database import Database
from datetime import datetime, date
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class Budget:
    def __init__(self):
        """Initialize Budget with database connection."""
        self.db = Database()
    
    def get_unique_categories(self) -> List[str]:
        """Get unique categories from transactions table."""
        query = """
            SELECT DISTINCT category 
            FROM transactions 
            ORDER BY category;
        """
        results = self.db.fetch_all(query)
        return [row['category'] for row in results] if results else []
    
    def create_budget(
        self,
        category: str,
        amount: float,
        period: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        notification_threshold: float = 0.8
    ) -> bool:
        """Create a new budget."""
        try:
            query = """
                INSERT INTO budgets (category, amount, period, start_date, end_date, notification_threshold)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id;
            """
            params = (category, amount, period, start_date, end_date, notification_threshold)
            result = self.db.execute(query, params)
            return result is not None
            
        except Exception as e:
            logger.error(f"Error creating budget: {str(e)}")
            raise
    
    def get_all_budgets(self) -> List[Dict[str, Any]]:
        """Get all budgets."""
        query = "SELECT * FROM budgets ORDER BY category, period"
        return self.db.fetch_all(query) or []
    
    def get_budget_progress(self, budget_id: int) -> Dict[str, float]:
        """Get budget progress including spent amount and remaining amount."""
        try:
            # Get budget details
            budget_query = "SELECT * FROM budgets WHERE id = %s"
            budget = self.db.fetch_one(budget_query, (budget_id,))
            
            if not budget:
                return {'spent': 0.0, 'remaining': 0.0}
            
            # Calculate total spent for this category within the budget period
            spent_query = """
                SELECT COALESCE(SUM(amount), 0) as total_spent
                FROM transactions
                WHERE category = %s
                AND type = 'expense'
                AND created_at >= %s
                AND (created_at <= %s OR %s IS NULL)
            """
            
            params = (
                budget['category'],
                budget['start_date'] or datetime.min,
                budget['end_date'],
                budget['end_date']
            )
            
            result = self.db.fetch_one(spent_query, params)
            total_spent = float(result['total_spent']) if result else 0.0
            budget_amount = float(budget['amount'])
            
            return {
                'spent': total_spent,
                'remaining': budget_amount - total_spent
            }
            
        except Exception as e:
            logger.error(f"Error getting budget progress: {str(e)}")
            return {'spent': 0.0, 'remaining': 0.0}
    
    def delete_budget(self, budget_id: int) -> bool:
        """Delete a budget."""
        try:
            query = "DELETE FROM budgets WHERE id = %s"
            return self.db.execute(query, (budget_id,)) is not None
        except Exception as e:
            logger.error(f"Error deleting budget: {str(e)}")
            raise
