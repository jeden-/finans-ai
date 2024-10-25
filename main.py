import streamlit as st
import os
import requests
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
    if 'openai_model' not in st.session_state:
        st.session_state.openai_model = "gpt-3.5-turbo"
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Go to", 
        ["Dashboard", "Add Transaction", "Manage Transactions", 
         "Manage Categories", "Budget Planning", "Chat Assistant"]
    )
    
    # Settings button in top right corner
    col1, col2 = st.columns([15, 1])  # Create columns for layout
    with col2:
        if st.button("⚙️", help="Settings"):
            st.session_state.show_settings = not st.session_state.get('show_settings', False)

    # Show settings modal if enabled
    if st.session_state.get('show_settings', False):
        with st.sidebar:
            st.markdown("### ⚙️ Settings")
            with st.expander("Appearance", expanded=True):
                theme = st.select_slider(
                    "Theme",
                    options=["Light", "Dark"],
                    value="Dark"
                )
                
            with st.expander("AI Configuration", expanded=True):
                ai_service = st.selectbox(
                    "AI Service",
                    ["OpenAI", "Ollama"],
                    index=0 if st.session_state.get('ai_model') == "OpenAI" else 1
                )
                
                if ai_service == "OpenAI":
                    openai_key = st.text_input(
                        "API Key",
                        type="password",
                        value=os.environ.get("OPENAI_API_KEY", ""),
                        help="Enter your OpenAI API key"
                    )
                    if openai_key:
                        st.session_state.openai_api_key = openai_key
                        os.environ["OPENAI_API_KEY"] = openai_key
                        
                    model = st.selectbox(
                        "Model",
                        ["gpt-3.5-turbo", "gpt-4"],
                        index=0
                    )
                    st.session_state.openai_model = model
                else:
                    try:
                        response = requests.get("http://localhost:11434/api/tags")
                        available_models = [model['name'] for model in response.json()['models']] if response.status_code == 200 else ["llama2"]
                    except:
                        available_models = ["llama2"]
                        
                    model = st.selectbox(
                        "Model",
                        options=available_models,
                        index=0
                    )
                    st.session_state.ollama_model = model
                
                st.session_state.ai_model = ai_service

            if st.button("Close Settings"):
                st.session_state.show_settings = False
    
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
