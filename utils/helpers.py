import pandas as pd

def format_currency(amount):
    # Format number with thousands separator and 2 decimal places
    # Convert decimal point to comma
    formatted = f"{amount:,.2f}".replace(",", " ").replace(".", ",")
    return f"{formatted} zł"

def prepare_transaction_data(transactions):
    df = pd.DataFrame(transactions)
    df['created_at'] = pd.to_datetime(df['created_at'])
    return df

def calculate_monthly_totals(df):
    monthly = df.set_index('created_at').resample('M')['amount'].sum()
    return monthly.to_dict()
