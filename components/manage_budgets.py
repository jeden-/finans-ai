import streamlit as st
from models.budget import Budget
from models.transaction import Transaction
from datetime import date, datetime, timedelta
from components.manage_categories import get_all_categories
from utils.helpers import format_currency, get_text
import pandas as pd
import plotly.express as px
import logging

logger = logging.getLogger(__name__)

def render_budget_planning():
    st.subheader(f"{get_text('budget.title')} & {get_text('budget.tracking')}")
    
    budget_model = Budget()
    
    # Create tabs for different budget views
    tabs = st.tabs([
        get_text('budget.overview'),
        get_text('budget.create'),
        get_text('budget.manage')
    ])
    
    with tabs[0]:
        render_budget_overview(budget_model)
    
    with tabs[1]:
        render_create_budget(budget_model)
    
    with tabs[2]:
        render_manage_budgets(budget_model)

def render_budget_overview(budget_model):
    """Render budget overview with progress bars and statistics."""
    st.write(f"### {get_text('budget.overview')}")
    
    active_budgets = budget_model.get_active_budgets()
    
    if not active_budgets:
        st.info(get_text('budget.no_budgets'))
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
                st.metric(get_text('budget.spent'), format_currency(progress['total_spent']))
                
            with col3:
                st.metric(get_text('budget.remaining'), format_currency(progress['remaining']))
            
            # Show warning if over budget or near threshold
            if progress['status'] == 'over_budget':
                st.error(f"⚠️ {get_text('budget.over_budget')} {format_currency(abs(progress['remaining']))}")
            elif progress['status'] == 'warning':
                st.warning(f"⚠️ {get_text('budget.warning_threshold')} ({progress['percentage_spent']:.1f}%)")
            
            # Show period details
            st.caption(f"{get_text('budget.period')}: {budget['start_date']} to {budget['end_date'] or 'Ongoing'}")

def render_create_budget(budget_model):
    """Form for creating a new budget."""
    st.write(f"### {get_text('budget.create')}")
    
    # Get existing categories
    categories = get_all_categories()
    if not categories:
        st.warning("No transaction categories found. Add some transactions first!")
        return
    
    with st.form("create_budget_form"):
        # Basic budget information
        category = st.selectbox(get_text('common.category'), categories)
        amount = st.number_input(get_text('budget.amount'), min_value=0.01, step=0.01)
        period = st.selectbox(get_text('budget.period'), ["monthly", "yearly"])
        
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(get_text('budget.start_date'), value=date.today())
        with col2:
            end_date = st.date_input(
                get_text('budget.end_date'),
                value=None,
                help="Leave empty for ongoing budget"
            )
        
        # Advanced settings
        with st.expander(get_text('budget.advanced')):
            notification_threshold = st.slider(
                get_text('budget.notification'),
                min_value=50,
                max_value=100,
                value=80,
                help="Get warned when spending reaches this percentage of budget"
            )
        
        if st.form_submit_button(get_text('common.save')):
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

def render_manage_budgets(budget_model):
    """Interface for managing existing budgets."""
    st.write(f"### {get_text('budget.manage')}")
    
    budgets = budget_model.get_all_budgets()
    if not budgets:
        st.info(get_text('budget.no_budgets'))
        return
    
    # Show each budget with edit/delete options
    for budget in budgets:
        with st.expander(f"🎯 {budget['category']} - {format_currency(budget['amount'])} ({budget['period']})"):
            # Edit form
            with st.form(f"edit_budget_{budget['id']}"):
                amount = st.number_input(
                    get_text('budget.amount'),
                    value=float(budget['amount']),
                    min_value=0.01,
                    step=0.01
                )
                period = st.selectbox(
                    get_text('budget.period'),
                    ["monthly", "yearly"],
                    index=0 if budget['period'] == 'monthly' else 1
                )
                
                col1, col2 = st.columns(2)
                with col1:
                    start_date = st.date_input(
                        get_text('budget.start_date'),
                        value=budget['start_date']
                    )
                with col2:
                    end_date = st.date_input(
                        get_text('budget.end_date'),
                        value=budget['end_date']
                    )
                
                notification_threshold = st.slider(
                    get_text('budget.notification'),
                    min_value=50,
                    max_value=100,
                    value=int(budget['notification_threshold'])
                )
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button(get_text('common.save')):
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
                            st.success(get_text('common.success'))
                            st.rerun()
                        except Exception as e:
                            st.error(f"{get_text('common.error')}: {str(e)}")
                
                with col2:
                    if st.form_submit_button(get_text('common.delete'), type="secondary"):
                        if st.checkbox(f"{get_text('common.confirm')}?"):
                            try:
                                budget_model.delete_budget(budget['id'])
                                st.success(get_text('common.success'))
                                st.rerun()
                            except Exception as e:
                                st.error(f"{get_text('common.error')}: {str(e)}")
