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
from utils.analytics import (
    analyze_spending_patterns, forecast_spending,
    analyze_category_correlations, get_spending_insights
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
            "Insights & Forecasting",
            "Advanced Analytics"
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
            
        # Advanced Analytics Tab
        with tabs[5]:
            render_advanced_analytics_tab(filtered_df)
        
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
                
            # Category correlations
            correlations = analyze_category_correlations(df)
            if correlations and 'strongest_positive' in correlations:
                st.subheader("Category Correlations")
                col1, col2 = st.columns(2)
                with col1:
                    st.write("Strongest Positive Correlations")
                    for (cat1, cat2), corr in correlations['strongest_positive'].items():
                        st.write(f"- {cat1} & {cat2}: {corr:.2f}")
                with col2:
                    st.write("Strongest Negative Correlations")
                    for (cat1, cat2), corr in correlations['strongest_negative'].items():
                        st.write(f"- {cat1} & {cat2}: {corr:.2f}")
        else:
            st.info("No expense categories found in the selected date range.")
    else:
        st.info("No expense transactions found in the selected date range.")

def render_spending_patterns_tab(df):
    """Render spending patterns analysis."""
    st.subheader("Daily Spending Patterns")
    
    # Get spending patterns analysis
    patterns = analyze_spending_patterns(df)
    
    if patterns:
        # Weekly pattern
        if patterns.get('weekly_pattern'):
            days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            values = [patterns['weekly_pattern'].get(i, 0) for i in range(7)]
            
            fig = px.bar(
                x=days,
                y=values,
                title="Average Spending by Day of Week",
                labels={"x": "Day", "y": "Average Amount"}
            )
            st.plotly_chart(fig, use_container_width=True)
            
        # Monthly pattern
        if patterns.get('monthly_trend'):
            monthly_data = patterns['monthly_trend']
            fig = px.line(
                x=list(monthly_data.keys()),
                y=list(monthly_data.values()),
                title="Monthly Spending Trend",
                labels={"x": "Month", "y": "Amount"}
            )
            st.plotly_chart(fig, use_container_width=True)
            
        # Seasonal patterns
        if patterns.get('high_spending_months'):
            st.subheader("Seasonal Patterns")
            col1, col2 = st.columns(2)
            with col1:
                st.write("High Spending Months")
                for month, amount in patterns['high_spending_months'].items():
                    st.write(f"- {datetime.strptime(str(month), '%m').strftime('%B')}: {format_currency(amount)}")
            with col2:
                st.write("Low Spending Months")
                for month, amount in patterns['low_spending_months'].items():
                    st.write(f"- {datetime.strptime(str(month), '%m').strftime('%B')}: {format_currency(amount)}")
    else:
        st.info("Not enough data to analyze spending patterns.")

def render_insights_forecasting_tab(df):
    """Render insights and forecasting analysis."""
    st.subheader("Financial Insights & Forecasting")
    
    # Get spending insights
    insights = get_spending_insights(df)
    
    if insights:
        # Overall metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Spending", format_currency(insights['total_spending']))
        with col2:
            st.metric("Average Transaction", format_currency(insights['avg_transaction']))
        with col3:
            last_trend = list(insights['spending_trend'].values())[-1] if insights['spending_trend'] else 0
            st.metric("Monthly Change", f"{last_trend*100:.1f}%")
        
        # Unusual transactions
        if insights.get('unusual_transactions'):
            st.subheader("Unusual Transactions")
            for tx in insights['unusual_transactions']:
                st.write(f"- {tx['description']}: {format_currency(tx['amount'])} ({tx['category']})")
        
        # Category insights
        st.subheader("Category Insights")
        for category, stats in insights['category_breakdown'].items():
            with st.expander(f"{category} - {format_currency(stats['sum'])}"):
                st.write(f"- Average transaction: {format_currency(stats['mean'])}")
                st.write(f"- Number of transactions: {int(stats['count'])}")
                
        # Spending forecast
        st.subheader("Spending Forecast")
        forecast_data = forecast_spending(df)
        
        if 'error' not in forecast_data:
            forecast_df = pd.DataFrame({
                'Forecast': forecast_data['forecast'],
                'Lower Bound': forecast_data['lower_bound'],
                'Upper Bound': forecast_data['upper_bound']
            })
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=forecast_df.index,
                y=forecast_df['Forecast'],
                name='Forecast',
                line=dict(color='blue')
            ))
            fig.add_trace(go.Scatter(
                x=forecast_df.index,
                y=forecast_df['Upper Bound'],
                name='Upper Bound',
                line=dict(dash='dash', color='red')
            ))
            fig.add_trace(go.Scatter(
                x=forecast_df.index,
                y=forecast_df['Lower Bound'],
                name='Lower Bound',
                line=dict(dash='dash', color='green')
            ))
            
            fig.update_layout(
                title="3-Month Spending Forecast",
                xaxis_title="Month",
                yaxis_title="Amount (PLN)"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Not enough historical data for forecasting.")
    else:
        st.info("Not enough data to generate insights.")

def render_advanced_analytics_tab(df):
    """Render advanced analytics and detailed insights."""
    st.subheader("Advanced Analytics")
    
    # Create subtabs for different types of analysis
    subtabs = st.tabs(["Trend Analysis", "Spending Behavior", "Pattern Recognition"])
    
    with subtabs[0]:
        st.write("### Trend Analysis")
        
        # Cumulative spending trend
        expense_df = df[df['type'] == 'expense'].copy()
        if not expense_df.empty:
            expense_df['cumulative_sum'] = expense_df.sort_values('created_at')['amount'].cumsum()
            
            fig = px.line(
                expense_df,
                x='created_at',
                y='cumulative_sum',
                title="Cumulative Spending Over Time"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Moving averages
            expense_df.set_index('created_at', inplace=True)
            daily_spending = expense_df.resample('D')['amount'].sum().fillna(0)
            
            ma_7 = daily_spending.rolling(window=7).mean()
            ma_30 = daily_spending.rolling(window=30).mean()
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=daily_spending.index, y=daily_spending.values, name='Daily'))
            fig.add_trace(go.Scatter(x=ma_7.index, y=ma_7.values, name='7-day MA'))
            fig.add_trace(go.Scatter(x=ma_30.index, y=ma_30.values, name='30-day MA'))
            
            fig.update_layout(
                title="Spending Trends with Moving Averages",
                xaxis_title="Date",
                yaxis_title="Amount (PLN)"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with subtabs[1]:
        st.write("### Spending Behavior Analysis")
        
        # Transaction size distribution
        if not expense_df.empty:
            fig = px.histogram(
                expense_df,
                x='amount',
                nbins=50,
                title="Transaction Size Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Spending by day of week and hour
            expense_df['day_of_week'] = expense_df.index.dayofweek
            expense_df['hour'] = expense_df.index.hour
            
            pivot_table = expense_df.pivot_table(
                values='amount',
                index='day_of_week',
                columns='hour',
                aggfunc='sum',
                fill_value=0
            )
            
            fig = px.imshow(
                pivot_table,
                labels=dict(x="Hour of Day", y="Day of Week", color="Amount"),
                x=[str(i).zfill(2) + ":00" for i in range(24)],
                y=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],
                title="Spending Heatmap by Day and Hour"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with subtabs[2]:
        st.write("### Pattern Recognition")
        
        # Category sequence analysis
        expense_df = expense_df.sort_values('created_at')
        category_sequence = expense_df['category'].tolist()
        
        if len(category_sequence) >= 2:
            transitions = {}
            for i in range(len(category_sequence)-1):
                current = category_sequence[i]
                next_cat = category_sequence[i+1]
                
                if current not in transitions:
                    transitions[current] = {}
                if next_cat not in transitions[current]:
                    transitions[current][next_cat] = 0
                transitions[current][next_cat] += 1
            
            st.write("#### Common Spending Sequences")
            for cat, next_cats in transitions.items():
                total = sum(next_cats.values())
                most_common = sorted(next_cats.items(), key=lambda x: x[1], reverse=True)[0]
                pct = (most_common[1] / total) * 100
                if pct >= 20:  # Only show strong patterns
                    st.write(f"- After spending in '{cat}', there's a {pct:.1f}% chance of spending in '{most_common[0]}'")
            
            # Periodic spending detection
            daily_totals = expense_df.resample('D')['amount'].sum().fillna(0)
            acf = pd.Series(daily_totals).autocorr(lag=7)  # Weekly correlation
            
            if abs(acf) > 0.3:  # Strong weekly pattern
                st.write("#### Periodic Spending Detected")
                st.write(f"- Weekly spending pattern strength: {abs(acf)*100:.1f}%")
                if acf > 0:
                    st.write("- Spending tends to follow a weekly cycle")
                else:
                    st.write("- Spending tends to alternate between high and low weeks")
