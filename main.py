import streamlit as st
from components.transaction_form import render_transaction_form
from components.dashboard import render_dashboard
from components.manage_transactions import render_manage_transactions

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
    page = st.sidebar.radio("Go to", ["Dashboard", "Add Transaction", "Manage Transactions"])
    
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
    else:
        render_transaction_form()

if __name__ == "__main__":
    main()
