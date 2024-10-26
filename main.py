import streamlit as st
import os
import requests
from components.transaction_form import render_transaction_form
from components.dashboard import render_dashboard
from components.manage_transactions import render_manage_transactions
from components.manage_categories import render_manage_categories
from components.manage_budgets import render_budget_planning
from components.chat_assistant import render_chat_assistant
from utils.helpers import get_text

# Page config
st.set_page_config(
    page_title=get_text('app.title'),
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    # Initialize session state
    if 'ai_model' not in st.session_state:
        st.session_state.ai_model = "OpenAI"
    if 'openai_model' not in st.session_state:
        st.session_state.openai_model = "gpt-3.5-turbo"
    if 'language' not in st.session_state:
        st.session_state.language = "en"
    
    # Sidebar navigation
    st.sidebar.title(get_text('navigation.title'))
    page = st.sidebar.radio(
        get_text('navigation.go_to'),
        [
            get_text('navigation.dashboard'),
            get_text('navigation.add_transaction'),
            get_text('navigation.manage_transactions'),
            get_text('navigation.manage_categories'),
            get_text('navigation.budget_planning'),
            get_text('navigation.chat_assistant')
        ]
    )
    
    # Settings button in top right corner
    col1, col2 = st.columns([15, 1])
    with col2:
        if st.button("⚙️", help=get_text('settings.title')):
            st.session_state.show_settings = not st.session_state.get('show_settings', False)

    # Show settings modal if enabled
    if st.session_state.get('show_settings', False):
        with st.sidebar:
            st.markdown(f"### ⚙️ {get_text('settings.title')}")
            with st.expander(get_text('settings.appearance'), expanded=True):
                theme = st.select_slider(
                    get_text('settings.theme'),
                    options=["Light", "Dark"],
                    value="Dark"
                )
                language = st.selectbox(
                    "Language / Język",
                    options=["English", "Polski"],
                    index=0 if st.session_state.get('language', 'en') == 'en' else 1,
                    help="Choose application language / Wybierz język aplikacji"
                )
                st.session_state.language = 'en' if language == 'English' else 'pl'
                
            with st.expander(get_text('settings.ai_configuration'), expanded=True):
                ai_service = st.selectbox(
                    "AI Service",
                    ["OpenAI", "Ollama"],
                    index=0 if st.session_state.get('ai_model') == "OpenAI" else 1
                )
                
                if ai_service == "OpenAI":
                    openai_key = st.text_input(
                        get_text('settings.api_key'),
                        type="password",
                        value=os.environ.get("OPENAI_API_KEY", ""),
                        help=get_text('settings.api_key_help')
                    )
                    if openai_key:
                        st.session_state.openai_api_key = openai_key
                        os.environ["OPENAI_API_KEY"] = openai_key
                        
                    model = st.selectbox(
                        get_text('settings.model'),
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
                        get_text('settings.model'),
                        options=available_models,
                        index=0
                    )
                    st.session_state.ollama_model = model
                
                st.session_state.ai_model = ai_service

            if st.button(get_text('settings.close')):
                st.session_state.show_settings = False
    
    # Main content
    st.title(get_text('app.title'))
    
    # Route to appropriate page
    page_map = {
        get_text('navigation.dashboard'): render_dashboard,
        get_text('navigation.manage_transactions'): render_manage_transactions,
        get_text('navigation.manage_categories'): render_manage_categories,
        get_text('navigation.budget_planning'): render_budget_planning,
        get_text('navigation.chat_assistant'): render_chat_assistant,
        get_text('navigation.add_transaction'): render_transaction_form
    }
    
    if page in page_map:
        page_map[page]()

if __name__ == "__main__":
    main()
