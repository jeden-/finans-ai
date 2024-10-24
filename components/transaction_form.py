import streamlit as st
from datetime import datetime
from services.ollama_service import OllamaService
from models.transaction import Transaction
from utils.helpers import format_currency

def render_transaction_form():
    st.subheader("New Transaction")
    
    description = st.text_input("Transaction Description (include amount in PLN/zł)")
    
    if st.button("Analyze Transaction"):
        ollama = OllamaService()
        with st.spinner("Analyzing transaction..."):
            classification = ollama.classify_transaction(description)
            
        if classification:
            if 'amount' in classification and classification['amount']:
                st.session_state.classification = classification
                st.success("Transaction analyzed successfully!")
            else:
                st.error("Could not detect amount in the description. Please include the amount in PLN or zł.")
    
    if 'classification' in st.session_state:
        class_data = st.session_state.classification
        
        st.write("### Detected Transaction Details")
        
        # Show and allow editing of extracted amount
        detected_amount = class_data.get('amount', 0)
        amount = st.number_input(
            "Amount (detected from description)",
            value=float(detected_amount),
            min_value=0.01,
            step=0.01,
            help="You can adjust the amount if it wasn't detected correctly"
        )
        
        type = st.selectbox("Type", ["income", "expense"], 
                           index=0 if class_data['type'] == 'income' else 1)
        category = st.text_input("Category", value=class_data['category'])
        cycle = st.selectbox("Cycle", ["none", "daily", "weekly", "monthly", "yearly"],
                           index=["none", "daily", "weekly", "monthly", "yearly"].index(class_data['cycle']))
        
        if cycle != "none":
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Start Date", datetime.now())
            with col2:
                end_date = st.date_input("End Date", datetime.now())
        
        if st.button("Save Transaction"):
            transaction = Transaction()
            try:
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
            except Exception as e:
                st.error(f"Error saving transaction: {str(e)}")
