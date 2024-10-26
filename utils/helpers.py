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
