import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List
import io
import streamlit as st
from translations import TRANSLATIONS

def get_text(key: str, language: str = None) -> str:
    '''Get translated text for the given key.'''
    if language is None:
        language = st.session_state.get('language', 'en')
    
    # Split the key into sections (e.g., 'navigation.dashboard')
    sections = key.split('.')
    current = TRANSLATIONS[language]
    
    try:
        for section in sections:
            current = current[section]
        return current
    except (KeyError, TypeError):
        # Fallback to English if translation not found
        current = TRANSLATIONS['en']
        for section in sections:
            current = current[section]
        return current

def format_currency(amount):
    """Format amount in PLN currency format."""
    if amount is None:
        return "0.00 PLN"
    return f"{float(amount):,.2f} PLN"

def prepare_transaction_data(transactions):
    """Prepare transaction data for analysis."""
    df = pd.DataFrame(transactions)
    df['created_at'] = pd.to_datetime(df['created_at'])
    return df

def calculate_monthly_totals(df):
    """Calculate monthly transaction totals."""
    monthly = df.set_index('created_at').resample('M')['amount'].sum()
    return monthly.to_dict()

def calculate_monthly_income_expenses(df):
    """Calculate monthly income and expenses."""
    monthly = df.set_index('created_at').groupby([pd.Grouper(freq='M'), 'type'])['amount'].sum().unstack()
    monthly.columns = ['Income' if x == 'income' else 'Expenses' for x in monthly.columns]
    return monthly

def calculate_category_trends(df):
    '''Calculate spending trends by category over time.'''
    df_expenses = df[df['type'] == 'expense'].copy()
    category_trends = df_expenses.pivot_table(
        values='amount',
        index='created_at',
        columns='category',
        aggfunc='sum'
    ).fillna(0)
    return category_trends

def calculate_daily_spending(df):
    """Calculate daily spending patterns."""
    df_expenses = df[df['type'] == 'expense'].copy()
    daily_spending = df_expenses.set_index('created_at').resample('D')['amount'].sum().fillna(0)
    return daily_spending

def get_top_spending_categories(df, n=5):
    """Get top spending categories."""
    category_totals = df[df['type'] == 'expense'].groupby('category')['amount'].sum()
    return category_totals.nlargest(n)

def calculate_mom_changes(df):
    """Calculate month-over-month changes in spending."""
    monthly_spending = df[df['type'] == 'expense'].set_index('created_at').resample('M')['amount'].sum()
    mom_changes = monthly_spending.pct_change()
    return mom_changes

def calculate_average_spending(df):
    """Calculate average spending by various time periods."""
    expense_df = df[df['type'] == 'expense']
    return {
        'daily': expense_df.resample('D', on='created_at')['amount'].mean(),
        'weekly': expense_df.resample('W', on='created_at')['amount'].mean(),
        'monthly': expense_df.resample('M', on='created_at')['amount'].mean()
    }

def get_upcoming_recurring_payments(df):
    """Get upcoming recurring payments."""
    recurring = df[df['cycle'] != 'none'].copy()
    if recurring.empty:
        return []
    
    today = datetime.now().date()
    upcoming = []
    
    for _, payment in recurring.iterrows():
        if payment['end_date'] and payment['end_date'] < today:
            continue
            
        next_date = None
        if payment['cycle'] == 'monthly':
            next_date = payment['due_date'].replace(month=today.month, year=today.year)
            if next_date < today:
                next_date = next_date.replace(month=next_date.month + 1)
        elif payment['cycle'] == 'yearly':
            next_date = payment['due_date'].replace(year=today.year)
            if next_date < today:
                next_date = next_date.replace(year=next_date.year + 1)
                
        if next_date:
            upcoming.append({
                'description': payment['description'],
                'amount': payment['amount'],
                'category': payment['category'],
                'due_date': next_date
            })
    
    return sorted(upcoming, key=lambda x: x['due_date'])

def predict_next_month_spending(df):
    """Predict next month's spending based on historical patterns."""
    expense_df = df[df['type'] == 'expense'].copy()
    monthly_spending = expense_df.set_index('created_at').resample('M')['amount'].sum()
    
    if len(monthly_spending) < 3:
        return None
        
    # Simple moving average prediction
    last_3_months = monthly_spending[-3:].mean()
    return last_3_months

def export_to_csv(df):
    """Export DataFrame to CSV."""
    output = io.StringIO()
    df.to_csv(output, index=True)
    return output.getvalue()

def export_to_excel(df):
    """Export DataFrame to Excel."""
    output = io.BytesIO()
    df.to_excel(output, index=True)
    return output.getvalue()
