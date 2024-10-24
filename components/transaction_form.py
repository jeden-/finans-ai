import streamlit as st
from datetime import datetime
from services.ollama_service import OllamaService
from models.transaction import Transaction
from utils.helpers import format_currency
import logging

logger = logging.getLogger(__name__)

def render_transaction_form():
    st.subheader("New Transaction")
    
    # Example transaction placeholder
    st.markdown("""
    💡 **Example formats:**
    - "internet domowy 20zł miesięcznie"
    - "wypłata 5000 złotych"
    - "czynsz 1500 PLN"
    """)
    
    description = st.text_input(
        "Transaction Description (include amount in PLN/zł)",
        help="Enter transaction description including the amount in Polish currency format (e.g., 20zł, 100 PLN, 50 złotych)"
    )
    
    if st.button("Analyze Transaction"):
        ollama = OllamaService()
        
        with st.spinner("Analyzing transaction..."):
            try:
                classification = ollama.classify_transaction(description)
                
                if classification is None:
                    st.error("""
                    ⚠️ Could not connect to Ollama service. Please ensure:
                    1. Ollama is installed and running
                    2. Run 'ollama run llama2' in terminal
                    3. Try again after Ollama is running
                    """)
                    return
                
                if 'amount' in classification and classification['amount']:
                    st.session_state.classification = classification
                    st.success(f"""
                    ✅ Transaction analyzed successfully!
                    - Type: {classification['type']}
                    - Category: {classification['category']}
                    - Amount: {format_currency(classification['amount'])}
                    - Cycle: {classification['cycle']}
                    """)
                else:
                    st.warning("""
                    ⚠️ Could not detect amount in the description.
                    Please include the amount in PLN or zł format, for example:
                    - 20zł
                    - 100 PLN
                    - 50 złotych
                    """)
            except Exception as e:
                logger.error(f"Error during transaction analysis: {str(e)}")
                st.error("An error occurred while analyzing the transaction. Please try again.")
    
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
        else:
            start_date = None
            end_date = None
        
        if st.button("Save Transaction"):
            transaction = Transaction()
            try:
                transaction.create_transaction(
                    description=description,
                    amount=amount,
                    type=type,
                    category=category,
                    cycle=cycle,
                    start_date=start_date,
                    end_date=end_date
                )
                st.success("✅ Transaction saved successfully!")
                st.session_state.pop('classification', None)
                
                # Show summary of saved transaction
                st.write("### Transaction Summary")
                st.write(f"- Description: {description}")
                st.write(f"- Amount: {format_currency(amount)}")
                st.write(f"- Type: {type}")
                st.write(f"- Category: {category}")
                st.write(f"- Cycle: {cycle}")
                if cycle != "none":
                    st.write(f"- Start Date: {start_date}")
                    st.write(f"- End Date: {end_date}")
                
            except Exception as e:
                logger.error(f"Error saving transaction: {str(e)}")
                st.error(f"Error saving transaction: {str(e)}")
