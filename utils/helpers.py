import pandas as pd
from datetime import datetime
import json
from typing import Dict, Any, List, Optional
import streamlit as st
from translations import TRANSLATIONS

def get_text(key: str) -> str:
    """Get translated text based on selected language."""
    current = TRANSLATIONS[st.session_state.get('language', 'en')]
    for part in key.split('.'):
        current = current[part]
    return current

def format_currency(amount: float) -> str:
    """Format amount as PLN currency."""
    return f"{amount:.2f} PLN"

def prepare_transaction_data(transactions: List[Dict[str, Any]]) -> pd.DataFrame:
    """Prepare transaction data for analysis."""
    df = pd.DataFrame(transactions)
    df['created_at'] = pd.to_datetime(df['created_at'])
    return df

def calculate_monthly_totals(df: pd.DataFrame) -> pd.Series:
    """Calculate monthly transaction totals."""
    if df.empty:
        return pd.Series()
    monthly = df.set_index('created_at').resample('ME')['amount'].sum()
    # Ensure we return a Series with proper index
    monthly = monthly.fillna(0)
    return monthly

def calculate_monthly_income_expenses(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate monthly income and expenses."""
    if df.empty:
        return pd.DataFrame(columns=['Income', 'Expenses'])
    
    monthly = df.set_index('created_at').groupby([pd.Grouper(freq='ME'), 'type'])['amount'].sum()
    
    # Unstack and handle missing columns
    monthly = monthly.unstack(fill_value=0)
    
    # Ensure both income and expense columns exist
    if 'income' not in monthly.columns:
        monthly['income'] = 0
    if 'expense' not in monthly.columns:
        monthly['expense'] = 0
        
    # Rename columns
    monthly.columns = ['Income' if x == 'income' else 'Expenses' for x in monthly.columns]
    return monthly

def calculate_category_trends(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate spending trends by category."""
    if df.empty or df[df['type'] == 'expense'].empty:
        return pd.DataFrame()
        
    expense_df = df[df['type'] == 'expense'].copy()
    category_monthly = expense_df.pivot_table(
        index='created_at',
        columns='category',
        values='amount',
        aggfunc='sum'
    ).resample('ME').sum().fillna(0)
    
    return category_monthly

def calculate_daily_spending(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate daily spending patterns."""
    if df.empty or df[df['type'] == 'expense'].empty:
        return pd.DataFrame()
        
    expense_df = df[df['type'] == 'expense'].copy()
    daily = expense_df.set_index('created_at').resample('D')['amount'].sum().fillna(0)
    return daily

def get_top_spending_categories(df: pd.DataFrame, n: int = 5) -> Dict[str, float]:
    """Get top spending categories."""
    if df.empty or df[df['type'] == 'expense'].empty:
        return {}
        
    expense_df = df[df['type'] == 'expense']
    categories = expense_df.groupby('category')['amount'].sum().sort_values(ascending=False)
    return categories.head(n).to_dict()

def calculate_mom_changes(df: pd.DataFrame) -> Dict[str, float]:
    """Calculate month-over-month changes."""
    if df.empty:
        return {}
        
    monthly = calculate_monthly_totals(df)
    if len(monthly) < 2:
        return {}
        
    mom_change = (monthly.iloc[-1] - monthly.iloc[-2]) / monthly.iloc[-2] if monthly.iloc[-2] != 0 else 0
    return {'last_month_change': mom_change}

def calculate_average_spending(df: pd.DataFrame) -> Dict[str, float]:
    """Calculate average spending metrics."""
    if df.empty or df[df['type'] == 'expense'].empty:
        return {}
        
    expense_df = df[df['type'] == 'expense']
    daily_avg = expense_df.groupby(expense_df['created_at'].dt.date)['amount'].sum().mean()
    monthly_avg = expense_df.groupby(expense_df['created_at'].dt.to_period('M'))['amount'].sum().mean()
    
    return {
        'daily_average': daily_avg,
        'monthly_average': monthly_avg
    }

def get_upcoming_recurring_payments(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Get list of upcoming recurring payments."""
    if df.empty:
        return []
        
    recurring = df[df['cycle'] != 'none'].copy()
    if recurring.empty:
        return []
        
    upcoming = []
    today = datetime.now()
    
    for _, transaction in recurring.iterrows():
        if transaction['cycle'] in ['monthly', 'yearly']:
            upcoming.append({
                'description': transaction['description'],
                'amount': transaction['amount'],
                'category': transaction['category'],
                'cycle': transaction['cycle'],
                'due_date': transaction['due_date']
            })
    
    return upcoming

def predict_next_month_spending(df: pd.DataFrame) -> Dict[str, float]:
    """Predict next month's spending based on historical data."""
    if df.empty or df[df['type'] == 'expense'].empty:
        return {}
        
    expense_df = df[df['type'] == 'expense']
    monthly_totals = expense_df.groupby(expense_df['created_at'].dt.to_period('M'))['amount'].sum()
    
    if len(monthly_totals) < 2:
        return {'predicted_amount': monthly_totals.mean() if not monthly_totals.empty else 0}
        
    # Simple moving average prediction
    last_3_months = monthly_totals.tail(3).mean()
    return {'predicted_amount': last_3_months}

def prepare_export_data(df: pd.DataFrame) -> pd.DataFrame:
    '''Prepare transaction data for export.'''
    export_df = df.copy()
    # Format dates
    if not export_df.empty:
        # Format date columns if they exist
        if 'created_at' in export_df.columns:
            export_df['created_at'] = export_df['created_at'].dt.strftime('%Y-%m-%d %H:%M:%S')
        if 'start_date' in export_df.columns:
            export_df['start_date'] = pd.to_datetime(export_df['start_date']).dt.strftime('%Y-%m-%d')
        if 'end_date' in export_df.columns:
            export_df['end_date'] = pd.to_datetime(export_df['end_date']).dt.strftime('%Y-%m-%d')
        if 'due_date' in export_df.columns:
            export_df['due_date'] = pd.to_datetime(export_df['due_date']).dt.strftime('%Y-%m-%d')
        # Format amounts
        if 'amount' in export_df.columns:
            export_df['amount'] = export_df['amount'].map(lambda x: f'{float(x):.2f}')
    return export_df

def export_to_csv(df: pd.DataFrame) -> bytes:
    """Export DataFrame to CSV format."""
    return df.to_csv(index=False).encode('utf-8')

def export_to_excel(df: pd.DataFrame) -> bytes:
    '''Export DataFrame to Excel format.'''
    import io
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()
