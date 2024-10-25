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
    
    # Sidebar
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Go to", 
        ["Dashboard", "Add Transaction", "Manage Transactions", 
         "Manage Categories", "Budget Planning", "Chat Assistant"]
    )
    
    # Settings section in sidebar
    with st.sidebar:
        st.divider()
        st.subheader("Settings")
        
        # Appearance settings
        st.write("##### Appearance")
        theme = st.select_slider(
            "Theme",
            options=["Light", "Dark"],
            value="Dark"
        )
        
        # AI Model settings
        st.write("##### AI Configuration")
        
        # Create tabs for different AI services
        ai_tabs = st.tabs(["OpenAI", "Ollama"])

        with ai_tabs[0]:  # OpenAI tab
            # API Key input
            openai_key = st.text_input(
                "OpenAI API Key",
                type="password",
                value=os.environ.get("OPENAI_API_KEY", ""),
                help="Enter your OpenAI API key here"
            )
            if openai_key:
                st.session_state.openai_api_key = openai_key
                os.environ["OPENAI_API_KEY"] = openai_key
                
            # Model selection
            openai_model = st.selectbox(
                "Model",
                ["gpt-3.5-turbo", "gpt-4"],
                index=0,
                help="Select OpenAI model to use"
            )
            st.session_state.openai_model = openai_model

        with ai_tabs[1]:  # Ollama tab
            # Get available Ollama models
            try:
                response = requests.get("http://localhost:11434/api/tags")
                if response.status_code == 200:
                    available_models = [model['name'] for model in response.json()['models']]
                else:
                    available_models = ["llama2"]
            except:
                available_models = ["llama2"]
                
            ollama_model = st.selectbox(
                "Model",
                options=available_models,
                index=0,
                help="Select Ollama model to use"
            )
            st.session_state.ollama_model = ollama_model

        # AI service selection
        ai_service = st.selectbox(
            "Active AI Service",
            ["OpenAI", "Ollama"],
            index=0 if st.session_state.get('ai_model') == "OpenAI" else 1,
            help="Choose which AI service to use"
        )
        st.session_state.ai_model = ai_service
    
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
