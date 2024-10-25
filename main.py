import streamlit as st
from components.transaction_form import render_transaction_form
from components.dashboard import render_dashboard
from components.manage_transactions import render_manage_transactions
from components.manage_categories import render_manage_categories
from components.manage_budgets import render_budget_planning

# Page config
st.set_page_config(
    page_title="Personal Finance Manager",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    # Sidebar
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Go to", 
        ["Dashboard", "Add Transaction", "Manage Transactions", 
         "Manage Categories", "Budget Planning"]
    )
    
    # Theme toggle
    theme = st.sidebar.select_slider(
        "Theme",
        options=["Light", "Dark"],
        value="Dark"
    )
    
    # Main content
    st.title("Personal Finance Manager")
    
    if page == "Dashboard":
        render_dashboard()
    elif page == "Manage Transactions":
        render_manage_transactions()
    elif page == "Manage Categories":
        render_manage_categories()
    elif page == "Budget Planning":
        render_budget_planning()
    else:
        render_transaction_form()

if __name__ == "__main__":
    main()
