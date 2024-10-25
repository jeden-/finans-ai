import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from models.transaction import Transaction
from utils.helpers import (
    prepare_transaction_data, calculate_monthly_totals, format_currency,
    calculate_monthly_income_expenses, calculate_category_trends,
    calculate_daily_spending, get_top_spending_categories,
    calculate_mom_changes, calculate_average_spending,
    get_upcoming_recurring_payments, predict_next_month_spending,
    export_to_csv
)
import logging
import pandas as pd

logger = logging.getLogger(__name__)

def render_dashboard():
    st.subheader("Financial Dashboard")
    
    try:
        transaction_model = Transaction()
        transactions = transaction_model.get_all_transactions()
        
        if not transactions:
            st.info("No transactions found. Start by adding some transactions!")
            return
        
        df = prepare_transaction_data(transactions)
        
        # Date range filter
        col1, col2 = st.columns(2)
        with col1:
            start_date = df['created_at'].min().date()
            start_date = st.date_input("From date", value=start_date)
        with col2:
            end_date = df['created_at'].max().date()
            end_date = st.date_input("To date", value=end_date)
        
        # Filter data based on date range
        mask = (df['created_at'].dt.date >= start_date) & (df['created_at'].dt.date <= end_date)
        filtered_df = df[mask]
        
        if filtered_df.empty:
            st.warning("No transactions found for the selected date range.")
            return

        # Create tabs for different analyses
        tabs = st.tabs([
            "Overview", 
            "Income vs Expenses", 
            "Category Analysis",
            "Spending Patterns",
            "Insights & Forecasting"
        ])
        
        # Overview Tab
        with tabs[0]:
            render_overview_tab(filtered_df)
        
        # Income vs Expenses Tab
        with tabs[1]:
            render_income_expenses_tab(filtered_df)
        
        # Category Analysis Tab
        with tabs[2]:
            render_category_analysis_tab(filtered_df)
        
        # Spending Patterns Tab
        with tabs[3]:
            render_spending_patterns_tab(filtered_df)
        
        # Insights & Forecasting Tab
        with tabs[4]:
            render_insights_forecasting_tab(filtered_df)
        
        # Export functionality
        st.divider()
        st.subheader("Export Data")
        if st.download_button(
            "Download as CSV",
            data=export_to_csv(filtered_df),
            file_name="transactions.csv",
            mime="text/csv",
        ):
            st.success("Data exported successfully!")
            
    except Exception as e:
        logger.error(f"Error rendering dashboard: {str(e)}")
        st.error("An error occurred while loading the dashboard. Please try again later or contact support if the problem persists.")

def render_overview_tab(df):
    """Render overview metrics and charts."""
    # Summary metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_income = df[df['type'] == 'income']['amount'].sum()
        st.metric("Total Income", format_currency(total_income))
    
    with col2:
        total_expenses = df[df['type'] == 'expense']['amount'].sum()
        st.metric("Total Expenses", format_currency(total_expenses))
    
    with col3:
        balance = total_income - total_expenses
        st.metric("Current Balance", format_currency(balance))
    
    # Monthly trend
    st.subheader("Monthly Transaction Trend")
    monthly_data = calculate_monthly_totals(df)
    
    if len(monthly_data) > 0:
        x_values = list(monthly_data.keys())
        y_values = list(monthly_data.values())
        
        fig = px.line(
            x=x_values,
            y=y_values,
            labels={"x": "Month", "y": "Amount"},
            title="Monthly Transaction Trend"
        )
        fig.update_layout(yaxis_title="Amount (PLN)")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Not enough data to show monthly trends.")

def render_income_expenses_tab(df):
    """Render income vs expenses analysis."""
    st.subheader("Income vs Expenses Analysis")
    
    # Monthly income vs expenses
    monthly_ie = calculate_monthly_income_expenses(df)
    if not monthly_ie.empty and len(monthly_ie) > 0:
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=monthly_ie.index,
            y=monthly_ie['Income'],
            name='Income',
            marker_color='green'
        ))
        fig.add_trace(go.Bar(
            x=monthly_ie.index,
            y=monthly_ie['Expenses'],
            name='Expenses',
            marker_color='red'
        ))
        fig.update_layout(
            title="Monthly Income vs Expenses",
            barmode='group',
            xaxis_title="Month",
            yaxis_title="Amount (PLN)"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Net income trend
        net_income = monthly_ie['Income'] - monthly_ie['Expenses']
        if len(net_income) > 0:
            fig = px.line(
                x=net_income.index,
                y=net_income.values,
                title="Net Income Trend",
                labels={"x": "Month", "y": "Net Income"}
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Not enough data to show income vs expenses analysis.")

def render_category_analysis_tab(df):
    """Render category-wise analysis."""
    st.subheader("Spending by Category")
    
    expense_df = df[df['type'] == 'expense']
    if not expense_df.empty:
        # Pie chart for overall category distribution
        category_data = expense_df.groupby('category')['amount'].sum()
        if len(category_data) > 0:
            fig = px.pie(
                values=category_data.values,
                names=category_data.index,
                title="Overall Spending Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Category trends over time
            category_trends = calculate_category_trends(df)
            if not category_trends.empty:
                fig = px.line(
                    category_trends,
                    title="Category Spending Trends",
                    labels={"value": "Amount (PLN)"}
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Not enough data to show category trends over time.")
        else:
            st.info("No expense categories found in the selected date range.")
    else:
        st.info("No expense transactions found in the selected date range.")

def render_spending_patterns_tab(df):
    """Render spending patterns analysis."""
    st.subheader("Daily Spending Patterns")
    
    # Daily spending
    daily_spending = calculate_daily_spending(df)
    if len(daily_spending) > 0:
        fig = px.line(
            x=daily_spending.index,
            y=daily_spending.values,
            title="Daily Spending Pattern",
            labels={"x": "Date", "y": "Amount"}
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Weekly pattern
        weekly_avg = daily_spending.groupby(daily_spending.index.dayofweek).mean()
        if len(weekly_avg) > 0:
            days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            fig = px.bar(
                x=days,
                y=weekly_avg.values,
                title="Average Spending by Day of Week",
                labels={"x": "Day", "y": "Average Amount"}
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Not enough data to show weekly spending patterns.")
    else:
        st.info("Not enough data to show daily spending patterns.")

def render_insights_forecasting_tab(df):
    """Render insights and forecasting analysis."""
    st.subheader("Financial Insights & Forecasting")
    
    expense_df = df[df['type'] == 'expense']
    if not expense_df.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            # Top spending categories
            top_categories = get_top_spending_categories(df)
            if len(top_categories) > 0:
                fig = px.bar(
                    x=top_categories.index,
                    y=top_categories.values,
                    title="Top Spending Categories",
                    labels={"x": "Category", "y": "Total Amount"}
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Not enough data to show top spending categories.")
        
        with col2:
            # Month-over-month changes
            mom_changes = calculate_mom_changes(df)
            if len(mom_changes) > 1:  # Need at least 2 months for changes
                fig = px.line(
                    x=mom_changes.index,
                    y=mom_changes.values * 100,
                    title="Monthly Spending Changes (%)",
                    labels={"x": "Month", "y": "Change (%)"}
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Not enough data to show month-over-month changes.")
        
        # Average spending patterns
        st.subheader("Average Spending Patterns")
        avg_spending = calculate_average_spending(df)
        col1, col2, col3 = st.columns(3)
        
        with col1:
            daily_avg = avg_spending['daily'].mean()
            if not pd.isna(daily_avg):
                st.metric("Daily Average", format_currency(daily_avg))
        with col2:
            weekly_avg = avg_spending['weekly'].mean()
            if not pd.isna(weekly_avg):
                st.metric("Weekly Average", format_currency(weekly_avg))
        with col3:
            monthly_avg = avg_spending['monthly'].mean()
            if not pd.isna(monthly_avg):
                st.metric("Monthly Average", format_currency(monthly_avg))
        
        # Upcoming recurring payments
        st.subheader("Upcoming Recurring Payments")
        upcoming = get_upcoming_recurring_payments(df)
        if not upcoming.empty:
            for _, payment in upcoming.iterrows():
                st.write(f"📅 {payment['description']}: {format_currency(payment['amount'])} - Due: {payment['due_date'].strftime('%Y-%m-%d')}")
        else:
            st.info("No upcoming recurring payments found.")
        
        # Forecasting
        if len(df) >= 2:  # Need at least 2 transactions for forecasting
            st.subheader("Spending Forecast")
            next_month_forecast = predict_next_month_spending(df)
            if not pd.isna(next_month_forecast):
                current_avg = df[df['type'] == 'expense']['amount'].mean()
                st.metric(
                    "Predicted Next Month Spending",
                    format_currency(next_month_forecast),
                    delta=format_currency(next_month_forecast - current_avg)
                )
        else:
            st.info("Not enough historical data for spending forecast.")
    else:
        st.info("No expense transactions found in the selected date range.")
