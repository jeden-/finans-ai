import streamlit as st
from datetime import datetime
from services.ollama_service import OllamaService
from models.transaction import Transaction

def render_transaction_form():
    st.subheader("New Transaction")
    
    description = st.text_input("Transaction Description")
    amount = st.number_input("Amount", min_value=0.01, step=0.01)
    
    if st.button("Analyze Transaction"):
        ollama = OllamaService()
        with st.spinner("Analyzing transaction..."):
            classification = ollama.classify_transaction(description)
            
        if classification:
            st.session_state.classification = classification
            st.success("Transaction analyzed successfully!")
    
    if 'classification' in st.session_state:
        class_data = st.session_state.classification
        
        type = st.selectbox("Type", ["income", "expense"], 
                           index=0 if class_data['type'] == 'income' else 1)
        category = st.text_input("Category", value=class_data['category'])
        cycle = st.selectbox("Cycle", ["none", "daily", "weekly", "monthly", "yearly"],
                           index=["none", "daily", "weekly", "monthly", "yearly"].index(class_data['cycle']))
        
        if cycle != "none":
            start_date = st.date_input("Start Date", datetime.now())
            end_date = st.date_input("End Date", datetime.now())
        
        if st.button("Save Transaction"):
            transaction = Transaction()
            transaction.create_transaction(
                description=description,
                amount=amount,
                type=type,
                category=category,
                cycle=cycle,
                start_date=start_date if cycle != "none" else None,
                end_date=end_date if cycle != "none" else None
            )
            st.success("Transaction saved successfully!")
            st.session_state.pop('classification', None)
