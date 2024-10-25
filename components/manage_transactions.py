import streamlit as st
from models.transaction import Transaction
from utils.helpers import format_currency, prepare_export_data, export_to_csv, export_to_excel
from datetime import datetime, timedelta, date
from components.manage_categories import render_category_selector
import json
import pandas as pd

def render_manage_transactions():
    st.subheader("Manage Transactions")
    
    # Initialize transaction model
    transaction_model = Transaction()
    
    # Get all transactions
    transactions = transaction_model.get_all_transactions()
    
    if not transactions:
        st.info("No transactions found. Start by adding some transactions!")
        return
    
    # Create tabs for management and export
    manage_tab, export_tab = st.tabs(["Manage Transactions", "Export Data"])
    
    with manage_tab:
        render_transaction_management(transactions, transaction_model)
    
    with export_tab:
        render_export_section(transactions)

def render_transaction_management(transactions, transaction_model):
    """Render the transaction management interface."""
    # Create a form for editing
    if "editing_transaction" in st.session_state:
        st.write("### Edit Transaction")
        edit_transaction_form(st.session_state.editing_transaction, transaction_model)
        if st.button("Cancel Edit"):
            del st.session_state.editing_transaction
        st.divider()
    
    # Display transactions table
    st.write("### Transactions List")
    
    # Convert transactions to a format suitable for display
    for tx in transactions:
        # Add action buttons
        col1, col2, col3, col4, col5, col6, col7 = st.columns([2, 1, 1, 1, 1, 0.5, 0.5])
        
        with col1:
            st.write(f"**{tx['description']}**")
            if tx['metadata']:
                st.caption(f"Metadata: {json.dumps(tx['metadata'], indent=2)}")
        
        with col2:
            st.write(format_currency(tx['amount']))
        
        with col3:
            st.write(tx['category'])
        
        with col4:
            st.write(tx['type'])
        
        with col5:
            st.write(tx['cycle'])
            if tx['cycle'] != 'none':
                st.caption(f"From: {tx['start_date']}")
                if tx['end_date']:
                    st.caption(f"To: {tx['end_date']}")
                if tx['cycle'] in ["monthly", "yearly"] and tx['due_date']:
                    st.caption(f"Due: {tx['due_date']}")
        
        with col6:
            if st.button("📝", key=f"edit_{tx['id']}", help="Edit transaction"):
                st.session_state.editing_transaction = tx
        
        with col7:
            if st.button("🗑️", key=f"delete_{tx['id']}", help="Delete transaction"):
                if 'delete_confirm' not in st.session_state:
                    st.session_state.delete_confirm = tx['id']
                    st.warning(f"Are you sure you want to delete this transaction? This cannot be undone.")
                    st.button("Yes, delete", key=f"confirm_delete_{tx['id']}", 
                             on_click=lambda: delete_transaction(transaction_model, tx['id']))
                    st.button("No, keep", key=f"cancel_delete_{tx['id']}", 
                             on_click=lambda: st.session_state.pop('delete_confirm', None))
        
        st.divider()

def render_export_section(transactions):
    """Render the data export interface."""
    st.write("### Export Transactions")
    
    # Convert transactions to DataFrame
    df = pd.DataFrame(transactions)
    
    # Date range filter
    st.write("#### Select Date Range")
    col1, col2 = st.columns(2)
    with col1:
        min_date = pd.to_datetime(df['created_at']).min().date()
        start_date = st.date_input("From", value=min_date)
    with col2:
        max_date = pd.to_datetime(df['created_at']).max().date()
        end_date = st.date_input("To", value=max_date)
    
    # Filter data based on date range
    df['created_at'] = pd.to_datetime(df['created_at'])
    mask = (df['created_at'].dt.date >= start_date) & (df['created_at'].dt.date <= end_date)
    filtered_df = df[mask]
    
    # Export format selection
    st.write("#### Export Format")
    export_format = st.radio(
        "Choose format:",
        ["CSV", "Excel"],
        help="CSV is better for importing into other software. Excel includes formatting and is better for viewing."
    )
    
    # Show export button and handle download
    if export_format == "CSV":
        if st.download_button(
            "📥 Download CSV",
            data=export_to_csv(filtered_df),
            file_name=f"transactions_{start_date}_to_{end_date}.csv",
            mime="text/csv",
        ):
            st.success("✅ CSV file downloaded successfully!")
    else:
        if st.download_button(
            "📥 Download Excel",
            data=export_to_excel(filtered_df),
            file_name=f"transactions_{start_date}_to_{end_date}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ):
            st.success("✅ Excel file downloaded successfully!")
    
    # Preview of data to be exported
    st.write("#### Data Preview")
    preview_df = prepare_export_data(filtered_df).head(5)
    st.dataframe(preview_df, use_container_width=True)
    
    st.caption(f"Total records to be exported: {len(filtered_df)}")

def edit_transaction_form(transaction, transaction_model):
    """Form for editing a transaction."""
    with st.form(key=f"edit_form_{transaction['id']}"):
        description = st.text_input("Description", value=transaction['description'])
        amount = st.number_input("Amount", value=float(transaction['amount']), min_value=0.01, step=0.01)
        type = st.selectbox("Type", ["income", "expense"], 
                           index=0 if transaction['type'] == 'income' else 1)
        
        # Use the new category selector component
        category = render_category_selector(
            key=f"edit_category_{transaction['id']}",
            help_text="Select an existing category or create a new one"
        )
        if not category:
            category = transaction['category']
            
        cycle = st.selectbox("Cycle", ["none", "daily", "weekly", "monthly", "yearly"],
                           index=["none", "daily", "weekly", "monthly", "yearly"].index(transaction['cycle']))
        
        today = date.today()
        if cycle != "none":
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Start Date", 
                                       value=transaction['start_date'] if transaction['start_date'] else today)
            with col2:
                default_end_date = (start_date if isinstance(start_date, date) else today) + timedelta(days=365 * 5)
                end_date = st.date_input("End Date", 
                                     value=transaction['end_date'] if transaction['end_date'] else default_end_date)
            
            # Show due_date field for both monthly and yearly transactions
            if cycle in ["monthly", "yearly"]:
                due_date = st.date_input(
                    "Due Date (payment date)",
                    value=transaction['due_date'] if transaction['due_date'] else start_date,
                    help="The date when the monthly/yearly payment is due"
                )
            else:
                due_date = None
        else:
            start_date = None
            end_date = None
            due_date = None
        
        if st.form_submit_button("Save Changes"):
            try:
                # Convert Streamlit date_input values to Python date objects
                start_date = start_date if isinstance(start_date, date) else None
                end_date = end_date if isinstance(end_date, date) else None
                due_date = due_date if isinstance(due_date, date) else None
                
                # Ensure category is not None
                if not category:
                    raise ValueError("Category cannot be empty")
                    
                transaction_model.update_transaction(
                    transaction['id'],
                    {
                        'description': description,
                        'amount': amount,
                        'type': type,
                        'category': category,
                        'cycle': cycle,
                        'start_date': start_date,
                        'end_date': end_date,
                        'due_date': due_date
                    }
                )
                st.success("✅ Transaction updated successfully!")
                del st.session_state.editing_transaction
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error updating transaction: {str(e)}")

def delete_transaction(transaction_model, transaction_id):
    """Delete a transaction and handle UI updates."""
    try:
        transaction_model.delete_transaction(transaction_id)
        st.success("✅ Transaction deleted successfully!")
        st.session_state.pop('delete_confirm', None)
        st.rerun()
    except Exception as e:
        st.error(f"❌ Error deleting transaction: {str(e)}")
