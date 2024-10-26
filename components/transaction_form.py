import streamlit as st
from datetime import datetime, timedelta, date
from services.openai_service import OpenAIService
from services.ollama_service import OllamaService
from models.transaction import Transaction
from utils.helpers import format_currency, get_text
from components.manage_categories import render_category_selector
import logging

logger = logging.getLogger(__name__)

def render_transaction_form():
    st.subheader(get_text('navigation.add_transaction'))
    
    # Example transaction placeholder
    st.markdown(f"""
    💡 **{get_text('transaction.example_formats')}**
    - "internet domowy 20zł miesięcznie"
    - "wypłata 5000 złotych"
    - "czynsz 1500 PLN"
    """)
    
    description = st.text_input(
        get_text('common.description'),
        help=get_text('transaction.description_help')
    )
    
    if st.button(get_text('transaction.analyze')):
        # Create placeholders for status messages and progress
        status_placeholder = st.empty()
        progress_placeholder = st.empty()
        result_placeholder = st.empty()
        progress_bar = st.progress(0)
        
        def update_status(message):
            # Determine progress based on message content
            if get_text('transaction.processing') in message:
                progress = 0.6
                status_placeholder.info(f"⚙️ {message}")
            elif get_text('transaction.success') in message:
                progress = 1.0
                status_placeholder.success(f"✅ {message}")
            elif get_text('transaction.error') in message:
                progress = 0
                status_placeholder.error(f"❌ {message}")
            else:
                progress = 0.5
                status_placeholder.info(f"ℹ️ {message}")
            
            progress_bar.progress(progress)
        
        update_status(get_text('transaction.processing'))
        
        try:
            # Use the selected AI model
            ai_service = OpenAIService() if st.session_state.ai_model == "OpenAI" else OllamaService()
            classification = ai_service.classify_transaction(description, status_callback=update_status)
            
            if classification is None:
                status_placeholder.error(get_text('transaction.error'))
                progress_bar.progress(0)
                return
            
            if 'amount' in classification and classification['amount']:
                st.session_state.classification = classification
                result_placeholder.success(f"""
                ✅ {get_text('transaction.success')}
                - {get_text('common.type')}: {classification['type']}
                - {get_text('common.category')}: {classification['category']}
                - {get_text('common.amount')}: {format_currency(classification['amount'])}
                - {get_text('common.cycle')}: {classification['cycle']}
                """)
            else:
                status_placeholder.warning(f"""
                ⚠️ {get_text('transaction.error')}
                {get_text('transaction.description_help')}:
                - 20zł
                - 100 PLN
                - 50 złotych
                """)
                progress_bar.progress(0)
        except Exception as e:
            logger.error(f"Error during transaction analysis: {str(e)}")
            status_placeholder.error(f"❌ {get_text('transaction.error')}: {str(e)}")
            progress_bar.progress(0)
    
    if 'classification' in st.session_state:
        class_data = st.session_state.classification
        
        st.write("### Detected Transaction Details")
        
        # Show and allow editing of extracted amount
        detected_amount = class_data.get('amount', 0)
        amount = st.number_input(
            f"{get_text('common.amount')} ({get_text('transaction.description_help')})",
            value=float(detected_amount),
            min_value=0.01,
            step=0.01,
            help=get_text('transaction.description_help')
        )
        
        type = st.selectbox(get_text('common.type'), ["income", "expense"], 
                           index=0 if class_data['type'] == 'income' else 1)
        
        # Use the new category selector component
        category = render_category_selector(
            key="transaction_category",
            help_text=get_text('common.category')
        )
        if not category:
            category = class_data['category']
            
        cycle = st.selectbox(get_text('common.cycle'), ["none", "daily", "weekly", "monthly", "yearly"],
                          index=["none", "daily", "weekly", "monthly", "yearly"].index(class_data['cycle']))
        
        # Set default dates
        today = date.today()
        default_end_date = today + timedelta(days=365 * 5)  # 5 years from today
        
        if cycle != "none":
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input(get_text('budget.start_date'), value=today)
            with col2:
                end_date = st.date_input(get_text('budget.end_date'), value=default_end_date)
                
            # Show due_date field for monthly and yearly transactions
            if cycle in ["monthly", "yearly"]:
                # For monthly transactions, default to same day of month as start_date
                default_due_date = start_date
                due_date = st.date_input(
                    "Due Date (payment date)",
                    value=default_due_date,
                    help="The date when the monthly/yearly payment is due"
                )
            else:
                due_date = None
        else:
            start_date = None
            end_date = None
            due_date = None
        
        if st.button(get_text('common.save')):
            transaction = Transaction()
            try:
                # Convert Streamlit date_input values to Python date objects
                start_date = start_date if isinstance(start_date, date) else None
                end_date = end_date if isinstance(end_date, date) else None
                due_date = due_date if isinstance(due_date, date) else None
                
                # Ensure category is not None
                if not category:
                    raise ValueError(get_text('error.no_category'))
                
                transaction.create_transaction(
                    description=description,
                    amount=amount,
                    type=type,
                    category=category,
                    cycle=cycle,
                    start_date=start_date,
                    end_date=end_date,
                    due_date=due_date
                )
                st.success(f"✅ {get_text('common.success')}")
                st.session_state.pop('classification', None)
                
                # Show summary of saved transaction
                st.write("### Transaction Summary")
                st.write(f"- {get_text('common.description')}: {description}")
                st.write(f"- {get_text('common.amount')}: {format_currency(amount)}")
                st.write(f"- {get_text('common.type')}: {type}")
                st.write(f"- {get_text('common.category')}: {category}")
                st.write(f"- {get_text('common.cycle')}: {cycle}")
                if cycle != "none":
                    st.write(f"- {get_text('budget.start_date')}: {start_date}")
                    st.write(f"- {get_text('budget.end_date')}: {end_date}")
                    if cycle in ["monthly", "yearly"]:
                        st.write(f"- Due Date: {due_date}")
                
            except Exception as e:
                logger.error(f"Error saving transaction: {str(e)}")
                st.error(f"❌ {get_text('transaction.error')}: {str(e)}")
