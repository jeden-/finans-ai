import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from models.transaction import Transaction
from utils.helpers import (
    format_currency, get_text, prepare_transaction_data,
    calculate_monthly_totals, calculate_monthly_income_expenses,
    calculate_category_trends, calculate_daily_spending,
    get_top_spending_categories, calculate_mom_changes,
    calculate_average_spending, predict_next_month_spending,
    prepare_export_data, export_to_csv
)
import logging

logger = logging.getLogger(__name__)

def render_dashboard():
    """Render the financial dashboard."""
    st.subheader(get_text('dashboard.financial_dashboard'))
    
    try:
        # Date range selector
        col1, col2 = st.columns(2)
        with col1:
            from_date = st.date_input(get_text('dashboard.from_date'), value=datetime.now().date())
        with col2:
            to_date = st.date_input(get_text('dashboard.to_date'), value=datetime.now().date())
            
        # Create tabs for different views
        tabs = st.tabs([
            get_text('analytics.overview'),
            get_text('analytics.income_vs_expenses'),
            get_text('analytics.category_analysis'),
            get_text('analytics.spending_patterns'),
            get_text('analytics.insights_forecasting'),
            get_text('analytics.advanced_analytics')
        ])
        
        # Get transaction data
        transaction = Transaction()
        transactions = transaction.get_all_transactions()
        
        if not transactions:
            st.info(get_text('error.no_transactions'))
            return
            
        # Prepare data
        df = prepare_transaction_data(transactions)
        
        # Filter by date range
        mask = (df['created_at'].dt.date >= from_date) & (df['created_at'].dt.date <= to_date)
        df_filtered = df[mask]
        
        if df_filtered.empty:
            st.warning(get_text('error.no_data_range'))
            return
            
        # Overview Tab
        with tabs[0]:
            render_overview_tab(df_filtered)
            
        # Income vs Expenses Tab
        with tabs[1]:
            render_income_expenses_tab(df_filtered)
            
        # Category Analysis Tab
        with tabs[2]:
            render_category_analysis_tab(df_filtered)
            
        # Spending Patterns Tab
        with tabs[3]:
            render_spending_patterns_tab(df_filtered)
            
        # Insights & Forecasting Tab
        with tabs[4]:
            render_insights_tab(df_filtered)
            
        # Advanced Analytics Tab
        with tabs[5]:
            render_advanced_analytics_tab(df_filtered)
            
    except Exception as e:
        logger.error(f"Error rendering dashboard: {str(e)}")
        st.error(get_text('error.loading_dashboard'))

def calculate_monthly_totals(df: pd.DataFrame) -> pd.Series:
    """Calculate monthly transaction totals."""
    if df.empty:
        return pd.Series()
    monthly = df.set_index('created_at').resample('M')['amount'].sum()
    return monthly

def calculate_monthly_income_expenses(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate monthly income and expenses."""
    if df.empty:
        return pd.DataFrame(columns=['Income', 'Expenses'])
    monthly = df.set_index('created_at').groupby([pd.Grouper(freq='M'), 'type'])['amount'].sum()
    monthly = monthly.unstack(fill_value=0)
    monthly.columns = ['Income' if x == 'income' else 'Expenses' for x in monthly.columns]
    return monthly

def render_overview_tab(df: pd.DataFrame):
    """Render overview section."""
    # Calculate totals
    total_income = df[df['type'] == 'income']['amount'].sum()
    total_expenses = df[df['type'] == 'expense']['amount'].sum()
    current_balance = total_income - total_expenses
    
    # Display metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(get_text('dashboard.total_income'), format_currency(total_income))
    with col2:
        st.metric(get_text('dashboard.total_expenses'), format_currency(total_expenses))
    with col3:
        st.metric(get_text('dashboard.current_balance'), format_currency(current_balance))
    
    # Monthly trend chart
    st.subheader(get_text('dashboard.monthly_trend'))
    monthly_totals = calculate_monthly_totals(df)
    if not monthly_totals.empty:
        fig = px.line(monthly_totals, title=get_text('dashboard.monthly_trend'))
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

def render_income_expenses_tab(df: pd.DataFrame):
    """Render income vs expenses analysis."""
    st.subheader(get_text('analytics.monthly_income_expenses'))
    
    monthly_data = calculate_monthly_income_expenses(df)
    if not monthly_data.empty:
        fig = px.bar(monthly_data, barmode='group')
        fig.update_layout(
            xaxis_title=get_text('analytics.month'),
            yaxis_title=get_text('analytics.amount')
        )
        st.plotly_chart(fig, use_container_width=True)

def render_category_analysis_tab(df: pd.DataFrame):
    """Render category analysis."""
    st.subheader(get_text('analytics.category_analysis'))
    
    if not df[df['type'] == 'expense'].empty:
        # Category trends over time
        category_trends = calculate_category_trends(df)
        if not category_trends.empty:
            fig = px.line(category_trends)
            fig.update_layout(
                xaxis_title=get_text('analytics.month'),
                yaxis_title=get_text('analytics.amount')
            )
            st.plotly_chart(fig, use_container_width=True)

def render_spending_patterns_tab(df: pd.DataFrame):
    """Render spending patterns analysis."""
    st.subheader(get_text('analytics.spending_patterns'))
    
    if not df[df['type'] == 'expense'].empty:
        # Daily spending pattern
        daily_spending = calculate_daily_spending(df)
        if not daily_spending.empty:
            fig = px.line(daily_spending, title=get_text('analytics.spending_behavior'))
            st.plotly_chart(fig, use_container_width=True)

def render_insights_tab(df: pd.DataFrame):
    """Render insights and forecasting."""
    st.subheader(get_text('analytics.insights_forecasting'))
    
    if not df.empty:
        # Top spending categories
        top_categories = get_top_spending_categories(df)
        if top_categories:
            fig = px.pie(
                values=list(top_categories.values()),
                names=list(top_categories.keys()),
                title=get_text('analytics.category_analysis')
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Month-over-month changes
        mom_changes = calculate_mom_changes(df)
        if mom_changes:
            st.metric(
                get_text('analytics.trend_analysis'),
                f"{mom_changes['last_month_change']*100:.1f}%"
            )

def render_advanced_analytics_tab(df: pd.DataFrame):
    """Render advanced analytics."""
    st.subheader(get_text('analytics.advanced_analytics'))
    
    if not df.empty:
        # Average spending metrics
        averages = calculate_average_spending(df)
        if averages:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Daily Average", format_currency(averages['daily_average']))
            with col2:
                st.metric("Monthly Average", format_currency(averages['monthly_average']))
        
        # Spending forecast
        forecast = predict_next_month_spending(df)
        if forecast:
            st.metric(
                "Next Month Forecast",
                format_currency(forecast['predicted_amount'])
            )
