import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List
import io

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

def prepare_export_data(df):
    """Prepare data for export by formatting and selecting relevant columns."""
    export_df = df.copy()
    
    # Format currency amounts
    export_df['amount'] = export_df['amount'].apply(lambda x: f"{x:,.2f} PLN")
    
    # Format dates - Handle each date column carefully
    date_columns = ['created_at', 'start_date', 'end_date', 'due_date']
    for col in date_columns:
        if col in export_df.columns:
            # Handle potentially missing or invalid dates
            export_df[col] = pd.to_datetime(export_df[col], errors='coerce')
            # Format datetime values, replacing NaT with empty string
            export_df[col] = export_df[col].apply(lambda x: x.strftime('%Y-%m-%d %H:%M:%S') if pd.notnull(x) else '')
    
    # Select and rename columns for export
    columns_map = {
        'description': 'Description',
        'amount': 'Amount',
        'type': 'Type',
        'category': 'Category',
        'cycle': 'Cycle',
        'start_date': 'Start Date',
        'end_date': 'End Date',
        'due_date': 'Due Date',
        'created_at': 'Created At'
    }
    
    export_df = export_df[columns_map.keys()].rename(columns=columns_map)
    return export_df

def export_to_csv(df):
    """Export transactions to CSV format."""
    export_df = prepare_export_data(df)
    return export_df.to_csv(index=False).encode('utf-8')

def export_to_excel(df):
    """Export transactions to Excel format with formatting."""
    export_df = prepare_export_data(df)
    
    # Create Excel writer object using xlsxwriter engine
    buffer = io.BytesIO()
    writer = pd.ExcelWriter(
        buffer,
        engine='xlsxwriter',
        engine_kwargs={'options': {'in_memory': True}}
    )
    
    # Write dataframe to excel
    export_df.to_excel(writer, sheet_name='Transactions', index=False)
    
    # Get workbook and worksheet objects
    workbook = writer.book
    worksheet = writer.sheets['Transactions']
    
    # Add formats
    header_format = workbook.add_format({
        'bold': True,
        'text_wrap': True,
        'valign': 'top',
        'border': 1
    })
    
    # Format headers
    for col_num, value in enumerate(export_df.columns.values):
        worksheet.write(0, col_num, value, header_format)
        
    # Adjust column widths
    for i, col in enumerate(export_df.columns):
        max_length = max(
            export_df[col].astype(str).apply(len).max(),
            len(col)
        )
        worksheet.set_column(i, i, max_length + 2)
    
    # Save the workbook
    writer.close()
    
    # Get the value of the BytesIO buffer
    excel_data = buffer.getvalue()
    buffer.close()
    
    return excel_data
