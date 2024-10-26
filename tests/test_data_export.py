import pytest
import pandas as pd
from utils.helpers import prepare_export_data, export_to_csv, export_to_excel

def test_prepare_export_data():
    """Test data preparation for export."""
    df = pd.DataFrame({
        'amount': [100.50, 200.75],
        'created_at': pd.to_datetime(['2024-01-01', '2024-01-02']),
        'category': ['groceries', 'utilities']
    })
    
    exported_df = prepare_export_data(df)
    assert all(isinstance(x, str) for x in exported_df['amount'])
    assert all(isinstance(x, str) for x in exported_df['created_at'])

def test_csv_export():
    """Test CSV export functionality."""
    df = pd.DataFrame({
        'test': [1, 2, 3]
    })
    csv_data = export_to_csv(df)
    assert isinstance(csv_data, bytes)
    assert b'test' in csv_data

def test_excel_export():
    """Test Excel export functionality."""
    df = pd.DataFrame({
        'test': [1, 2, 3]
    })
    excel_data = export_to_excel(df)
    assert isinstance(excel_data, bytes)
    assert len(excel_data) > 0
