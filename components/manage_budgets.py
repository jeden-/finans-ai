import streamlit as st
from models.budget import Budget
from models.transaction import Transaction
from datetime import date, datetime, timedelta
from components.manage_categories import get_all_categories
from utils.helpers import format_currency
import pandas as pd
import plotly.express as px
import logging

logger = logging.getLogger(__name__)

def render_budget_planning():
    st.subheader("Budget Planning & Tracking")
    
    budget_model = Budget()
    
    # Create tabs for different budget views
    tabs = st.tabs(["Budget Overview", "Create Budget", "Manage Budgets"])
    
    with tabs[0]:
        render_budget_overview(budget_model)
    
    with tabs[1]:
        render_create_budget(budget_model)
    
    with tabs[2]:
        render_manage_budgets(budget_model)

def render_budget_overview(budget_model):
    """Render budget overview with progress bars and statistics."""
    st.write("### Budget Overview")
    
    active_budgets = budget_model.get_active_budgets()
    
    if not active_budgets:
        st.info("No active budgets found. Create a budget to start tracking your spending!")
        return
    
    # Show progress for each active budget
    for budget in active_budgets:
        progress = budget_model.get_budget_progress(budget['id'])
        
        # Create an expander for each budget
        with st.expander(f"📊 {budget['category']} ({budget['period'].title()} Budget)", expanded=True):
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                # Calculate progress percentage
                progress_pct = min(progress['percentage_spent'], 100)
                
                # Choose color based on status
                color = (
                    "red" if progress['status'] == 'over_budget' else
                    "orange" if progress['status'] == 'warning' else
                    "green"
                )
                
                st.progress(progress_pct / 100, text=f"{progress_pct:.1f}%")
                
            with col2:
                st.metric("Spent", format_currency(progress['total_spent']))
                
            with col3:
                st.metric("Remaining", format_currency(progress['remaining']))
            
            # Show warning if over budget or near threshold
            if progress['status'] == 'over_budget':
                st.error(f"⚠️ Over budget by {format_currency(abs(progress['remaining']))}")
            elif progress['status'] == 'warning':
                st.warning(f"⚠️ Approaching budget limit ({progress['percentage_spent']:.1f}% spent)")
            
            # Show period details
            st.caption(f"Period: {budget['start_date']} to {budget['end_date'] or 'Ongoing'}")

def render_create_budget(budget_model):
    """Form for creating a new budget."""
    st.write("### Create New Budget")
    
    # Get existing categories
    categories = get_all_categories()
    if not categories:
        st.warning("No transaction categories found. Add some transactions first!")
        return
    
    with st.form("create_budget_form"):
        # Basic budget information
        category = st.selectbox("Category", categories)
        amount = st.number_input("Budget Amount (PLN)", min_value=0.01, step=0.01)
        period = st.selectbox("Budget Period", ["monthly", "yearly"])
        
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", value=date.today())
        with col2:
            end_date = st.date_input("End Date (optional)", 
                                   value=None,
                                   help="Leave empty for ongoing budget")
        
        # Advanced settings
        with st.expander("Advanced Settings"):
            notification_threshold = st.slider(
                "Notification Threshold (%)",
                min_value=50,
                max_value=100,
                value=80,
                help="Get warned when spending reaches this percentage of budget"
            )
        
        if st.form_submit_button("Create Budget"):
            try:
                budget_model.create_budget(
                    category=category,
                    amount=amount,
                    period=period,
                    start_date=start_date,
                    end_date=end_date,
                    notification_threshold=notification_threshold
                )
                st.success("✅ Budget created successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error creating budget: {str(e)}")

def render_manage_budgets(budget_model):
    """Interface for managing existing budgets."""
    st.write("### Manage Budgets")
    
    budgets = budget_model.get_all_budgets()
    if not budgets:
        st.info("No budgets found. Create a budget to get started!")
        return
    
    # Show each budget with edit/delete options
    for budget in budgets:
        with st.expander(f"🎯 {budget['category']} - {format_currency(budget['amount'])} ({budget['period']})"):
            # Edit form
            with st.form(f"edit_budget_{budget['id']}"):
                amount = st.number_input("Budget Amount (PLN)",
                                       value=float(budget['amount']),
                                       min_value=0.01,
                                       step=0.01)
                period = st.selectbox("Budget Period",
                                    ["monthly", "yearly"],
                                    index=0 if budget['period'] == 'monthly' else 1)
                
                col1, col2 = st.columns(2)
                with col1:
                    start_date = st.date_input("Start Date",
                                             value=budget['start_date'])
                with col2:
                    end_date = st.date_input("End Date",
                                           value=budget['end_date'])
                
                notification_threshold = st.slider(
                    "Notification Threshold (%)",
                    min_value=50,
                    max_value=100,
                    value=int(budget['notification_threshold'])
                )
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("Update Budget"):
                        try:
                            budget_model.update_budget(
                                budget['id'],
                                {
                                    'amount': amount,
                                    'period': period,
                                    'start_date': start_date,
                                    'end_date': end_date,
                                    'notification_threshold': notification_threshold
                                }
                            )
                            st.success("✅ Budget updated successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error updating budget: {str(e)}")
                
                with col2:
                    if st.form_submit_button("Delete Budget", type="secondary"):
                        if st.checkbox("Confirm deletion?"):
                            try:
                                budget_model.delete_budget(budget['id'])
                                st.success("✅ Budget deleted successfully!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Error deleting budget: {str(e)}")
