import streamlit as st
import psycopg2
from components.transaction_form import render_transaction_form
from components.dashboard import render_dashboard

# Page config
st.set_page_config(
    page_title="Personal Finance Manager",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

def init_db():
    try:
        conn = psycopg2.connect(
            dbname=st.secrets["PGDATABASE"],
            user=st.secrets["PGUSER"],
            password=st.secrets["PGPASSWORD"],
            host=st.secrets["PGHOST"],
            port=st.secrets["PGPORT"]
        )
        
        with conn.cursor() as cur:
            with open('assets/schema.sql', 'r') as file:
                cur.execute(file.read())
        conn.commit()
        conn.close()
    except Exception as e:
        st.error(f"Database initialization failed: {str(e)}")

def main():
    # Initialize database
    init_db()
    
    # Sidebar
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Dashboard", "Add Transaction"])
    
    # Theme toggle
    theme = st.sidebar.select_slider(
        "Theme",
        options=["Light", "Dark"],
        value="Dark"
    )
    
    # Main content
    st.title("Personal Finance Manager")
    
    if page == "Dashboard":
        render_dashboard()
    else:
        render_transaction_form()

if __name__ == "__main__":
    main()
