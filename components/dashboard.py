import streamlit as st
import plotly.express as px
from models.transaction import Transaction
from utils.helpers import prepare_transaction_data, calculate_monthly_totals

def render_dashboard():
    st.subheader("Financial Dashboard")
    
    transaction_model = Transaction()
    transactions = transaction_model.get_all_transactions()
    
    if not transactions:
        st.info("No transactions found. Start by adding some transactions!")
        return
    
    df = prepare_transaction_data(transactions)
    
    # Summary metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_income = df[df['type'] == 'income']['amount'].sum()
        st.metric("Total Income", f"${total_income:,.2f}")
    
    with col2:
        total_expenses = df[df['type'] == 'expense']['amount'].sum()
        st.metric("Total Expenses", f"${total_expenses:,.2f}")
    
    with col3:
        balance = total_income - total_expenses
        st.metric("Current Balance", f"${balance:,.2f}")
    
    # Category breakdown
    st.subheader("Spending by Category")
    category_data = df[df['type'] == 'expense'].groupby('category')['amount'].sum()
    fig = px.pie(values=category_data.values, names=category_data.index)
    st.plotly_chart(fig)
    
    # Monthly trend
    st.subheader("Monthly Transaction Trend")
    monthly_data = calculate_monthly_totals(df)
    fig = px.line(x=list(monthly_data.keys()), y=list(monthly_data.values()))
    st.plotly_chart(fig)
