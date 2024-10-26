import streamlit as st
from models.budget import Budget
from utils.helpers import format_currency, get_text
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)

def get_unique_budgets():
    """Get list of unique budgets, removing duplicates based on category and period."""
    budgets = Budget().get_all_budgets()
    # Use dictionary to keep only unique budgets based on category and period
    unique_budgets = {}
    for budget in budgets:
        key = f"{budget['category']}_{budget['period']}"
        unique_budgets[key] = budget
    return list(unique_budgets.values())

def render_budget_planning():
    st.subheader(get_text('budget.title'))
    
    # Create tabs for different budget views
    tabs = st.tabs([
        get_text('budget.overview'),
        get_text('budget.create'),
        get_text('budget.manage')
    ])
    
    # Overview Tab
    with tabs[0]:
        render_budget_overview()
    
    # Create Budget Tab
    with tabs[1]:
        render_create_budget()
    
    # Manage Budgets Tab
    with tabs[2]:
        render_manage_budgets()

def render_budget_overview():
    """Render budget overview section."""
    budgets = get_unique_budgets()
    
    if not budgets:
        st.info(get_text('budget.no_budgets'))
        return
    
    for budget in budgets:
        budget_model = Budget()
        progress = budget_model.get_budget_progress(budget['id'])
        
        with st.expander(f"🎯 {budget['category']} - {format_currency(float(budget['amount']))} ({budget['period']})"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(get_text('budget.spent'), format_currency(progress['spent']))
            with col2:
                st.metric(get_text('budget.remaining'), format_currency(progress['remaining']))
            with col3:
                # Convert decimal to float for comparison
                if float(progress['spent']) > float(budget['amount']):
                    st.error(f"{get_text('budget.over_budget')} {format_currency(float(progress['spent']) - float(budget['amount']))}")
                elif float(progress['spent']) >= float(budget['amount']) * 0.8:
                    st.warning(get_text('budget.warning_threshold'))
            
            # Progress bar
            progress_percentage = min((float(progress['spent']) / float(budget['amount'])) * 100, 100)
            st.progress(progress_percentage / 100)

def render_create_budget():
    """Render create budget form."""
    budget_model = Budget()
    
    try:
        # Get unique categories from transactions
        categories = budget_model.get_unique_categories()
        if not categories:
            st.info(get_text('error.no_categories'))
            return
            
        category = st.selectbox(get_text('common.category'), categories)
        amount = st.number_input(get_text('budget.amount'), min_value=0.01, step=10.0)
        period = st.selectbox(get_text('budget.period'), ["monthly", "yearly"])
        notification_threshold = st.slider(get_text('budget.notification'), 0.0, 1.0, 0.8)
        
        with st.expander(get_text('budget.advanced'), expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input(get_text('budget.start_date'))
            with col2:
                end_date = st.date_input(get_text('budget.end_date'))
        
        if st.button(get_text('common.save')):
            try:
                budget_model.create_budget(
                    category=category,
                    amount=amount,
                    period=period,
                    start_date=start_date,
                    end_date=end_date,
                    notification_threshold=notification_threshold
                )
                st.success(get_text('common.success'))
                st.rerun()
            except Exception as e:
                logger.error(f"Error creating budget: {str(e)}")
                st.error(f"{get_text('common.error')}: {str(e)}")
    except Exception as e:
        logger.error(f"Error in budget creation form: {str(e)}")
        st.error(get_text('error.loading_dashboard'))

def render_manage_budgets():
    """Render budget management section."""
    budgets = get_unique_budgets()
    
    if not budgets:
        st.info(get_text('budget.no_budgets'))
        return
        
    for budget in budgets:
        with st.expander(f"🎯 {budget['category']} - {format_currency(float(budget['amount']))} ({budget['period']})"):
            budget_model = Budget()
            
            # Show current settings
            st.write(f"- {get_text('budget.notification')}: {float(budget['notification_threshold'])*100}%")
            st.write(f"- {get_text('budget.start_date')}: {budget['start_date']}")
            st.write(f"- {get_text('budget.end_date')}: {budget['end_date']}")
            
            # Delete budget button
            if st.button(get_text('common.delete'), key=f"delete_{budget['id']}"):
                try:
                    budget_model.delete_budget(budget['id'])
                    st.success(get_text('common.success'))
                    st.rerun()
                except Exception as e:
                    logger.error(f"Error deleting budget: {str(e)}")
                    st.error(f"{get_text('common.error')}: {str(e)}")
