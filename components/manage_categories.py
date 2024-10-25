import streamlit as st
from models.transaction import Transaction
from models.database import Database
import pandas as pd
import logging

logger = logging.getLogger(__name__)

def get_all_categories():
    """Get all unique categories from transactions."""
    db = Database()
    query = """
    SELECT DISTINCT category 
    FROM transactions 
    ORDER BY category;
    """
    try:
        categories = db.fetch_all(query)
        return [cat['category'] for cat in categories]
    except Exception as e:
        logger.error(f"Error fetching categories: {str(e)}")
        return []

def get_category_usage():
    """Get usage count for each category."""
    db = Database()
    query = """
    SELECT category, COUNT(*) as usage_count, 
           SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) as total_expenses,
           SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) as total_income
    FROM transactions 
    GROUP BY category 
    ORDER BY usage_count DESC;
    """
    try:
        return db.fetch_all(query)
    except Exception as e:
        logger.error(f"Error fetching category usage: {str(e)}")
        return []

def update_category(old_category, new_category):
    """Update category name in transactions."""
    if old_category == new_category:
        return
        
    db = Database()
    query = """
    UPDATE transactions 
    SET category = %s 
    WHERE category = %s;
    """
    try:
        db.execute(query, (new_category, old_category))
        st.success(f"✅ Category '{old_category}' renamed to '{new_category}'")
    except Exception as e:
        logger.error(f"Error updating category: {str(e)}")
        st.error(f"❌ Error updating category: {str(e)}")

def delete_category(category):
    """Delete all transactions with given category."""
    db = Database()
    query = "DELETE FROM transactions WHERE category = %s;"
    try:
        db.execute(query, (category,))
        st.success(f"✅ Category '{category}' and all its transactions deleted")
    except Exception as e:
        logger.error(f"Error deleting category: {str(e)}")
        st.error(f"❌ Error deleting category: {str(e)}")

def render_manage_categories():
    st.subheader("Manage Categories")
    
    # Get current categories and their usage
    category_usage = get_category_usage()
    
    if not category_usage:
        st.info("No categories found. Start by adding transactions!")
        return
        
    # Convert to DataFrame for better display
    df = pd.DataFrame(category_usage)
    
    # Display category statistics
    st.write("### Category Statistics")
    for _, row in df.iterrows():
        with st.expander(f"📊 {row['category']} ({row['usage_count']} transactions)"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Usage Count", row['usage_count'])
            with col2:
                st.metric("Total Expenses", f"{float(row['total_expenses']):,.2f} zł" if row['total_expenses'] else "0.00 zł")
            with col3:
                st.metric("Total Income", f"{float(row['total_income']):,.2f} zł" if row['total_income'] else "0.00 zł")
            
            # Category actions
            col1, col2 = st.columns(2)
            with col1:
                new_name = st.text_input(
                    "New category name",
                    value=row['category'],
                    key=f"rename_{row['category']}"
                )
                if st.button("Update", key=f"update_{row['category']}"):
                    update_category(row['category'], new_name)
                    st.rerun()
            
            with col2:
                if st.button("Delete", key=f"delete_{row['category']}"):
                    if st.checkbox(f"Confirm deletion of '{row['category']}' and all its transactions?", key=f"confirm_{row['category']}"):
                        delete_category(row['category'])
                        st.rerun()
    
    # Add new category section
    st.write("### Add New Category")
    st.info("""
    ℹ️ Note: New categories are added automatically when you create transactions. 
    You can also rename existing categories above.
    """)

def render_category_selector(key=None, help_text=None):
    """Reusable category selector component with autocomplete."""
    categories = get_all_categories()
    
    # Allow both selection from existing and entering new
    selected = st.selectbox(
        "Category",
        options=[""] + categories,
        key=key,
        help=help_text or "Select existing or type new category"
    )
    
    if not selected:
        new_category = st.text_input(
            "New category name",
            key=f"new_{key}" if key else None
        )
        return new_category
    
    return selected
