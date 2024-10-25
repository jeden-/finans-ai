import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List

def format_currency(amount):
    # Format number with thousands separator and 2 decimal places
    # Convert decimal point to comma
    formatted = f"{amount:,.2f}".replace(",", " ").replace(".", ",")
    return f"{formatted} zł"

def prepare_transaction_data(transactions):
    df = pd.DataFrame(transactions)
    df['created_at'] = pd.to_datetime(df['created_at'])
    df['start_date'] = pd.to_datetime(df['start_date'])
    df['end_date'] = pd.to_datetime(df['end_date'])
    df['due_date'] = pd.to_datetime(df['due_date'])
    return df

def calculate_monthly_totals(df):
    monthly = df.set_index('created_at').resample('ME')['amount'].sum()
    return monthly.to_dict()

def calculate_monthly_income_expenses(df):
    """Calculate monthly income and expenses."""
    income = df[df['type'] == 'income'].set_index('created_at').resample('ME')['amount'].sum()
    expenses = df[df['type'] == 'expense'].set_index('created_at').resample('ME')['amount'].sum()
    return pd.DataFrame({'Income': income, 'Expenses': expenses}).fillna(0)

def calculate_category_trends(df):
    """Calculate spending trends by category over time."""
    return df[df['type'] == 'expense'].pivot_table(
        index='created_at', 
        columns='category', 
        values='amount',
        aggfunc='sum'
    ).resample('ME').sum().fillna(0)

def calculate_daily_spending(df):
    """Calculate daily spending patterns."""
    daily = df[df['type'] == 'expense'].set_index('created_at').resample('D')['amount'].sum()
    return daily.fillna(0)

def get_top_spending_categories(df, limit=5):
    """Get top spending categories."""
    return df[df['type'] == 'expense'].groupby('category')['amount'].sum().nlargest(limit)

def calculate_mom_changes(df):
    """Calculate month-over-month changes."""
    monthly = df.set_index('created_at').resample('ME')['amount'].sum()
    return monthly.pct_change()

def calculate_average_spending(df):
    """Calculate average spending patterns."""
    expenses = df[df['type'] == 'expense']
    return {
        'daily': expenses.set_index('created_at').resample('D')['amount'].mean().fillna(0),
        'weekly': expenses.set_index('created_at').resample('W')['amount'].mean().fillna(0),
        'monthly': expenses.set_index('created_at').resample('ME')['amount'].mean().fillna(0)
    }

def get_upcoming_recurring_payments(df, days_ahead=30):
    """Get upcoming recurring payments."""
    today = datetime.now()
    end_date = today + timedelta(days=days_ahead)
    recurring = df[
        (df['cycle'].isin(['monthly', 'yearly'])) & 
        (df['end_date'].isna() | (df['end_date'] >= today))
    ]
    return recurring

def predict_next_month_spending(df):
    """Simple prediction for next month's spending based on historical data."""
    monthly_expenses = df[df['type'] == 'expense'].set_index('created_at').resample('ME')['amount'].sum()
    if len(monthly_expenses) >= 3:
        # Use simple moving average of last 3 months
        return monthly_expenses.rolling(3).mean().iloc[-1]
    return monthly_expenses.mean()

def export_to_csv(df):
    """Export transactions to CSV format."""
    return df.to_csv(index=False).encode('utf-8')
