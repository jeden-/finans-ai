import streamlit as st
from components.transaction_form import render_transaction_form
from components.dashboard import render_dashboard
from components.manage_transactions import render_manage_transactions
from components.manage_categories import render_manage_categories
from components.manage_budgets import render_budget_planning
from components.chat_assistant import render_chat_assistant

# Page config
st.set_page_config(
    page_title="Personal Finance Manager",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    # Initialize session state for AI model choice if not exists
    if 'ai_model' not in st.session_state:
        st.session_state.ai_model = "OpenAI"
    
    # Sidebar
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Go to", 
        ["Dashboard", "Add Transaction", "Manage Transactions", 
         "Manage Categories", "Budget Planning", "Chat Assistant"]
    )
    
    # Theme toggle
    theme = st.sidebar.select_slider(
        "Theme",
        options=["Light", "Dark"],
        value="Dark"
    )
    
    # Settings section in sidebar
    with st.sidebar:
        st.divider()
        st.subheader("Settings")
        model_choice = st.selectbox(
            "AI Model",
            ["OpenAI", "Ollama"],
            index=0 if st.session_state.ai_model == "OpenAI" else 1,
            help="Choose the AI model for transaction analysis"
        )
        st.session_state.ai_model = model_choice
    
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
    elif page == "Chat Assistant":
        render_chat_assistant()
    else:
        render_transaction_form()

if __name__ == "__main__":
    main()
