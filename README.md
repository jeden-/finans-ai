# Personal Finance Manager

A Streamlit-based personal finance manager that uses local AI processing with Ollama for intelligent transaction classification. The application helps you manage your finances by automatically categorizing transactions and providing insightful analytics.

## Features

- Automatic transaction classification using AI (Ollama)
- Support for recurring transactions
- Transaction management (add, edit, delete)
- Financial dashboard with charts and analytics
- Dark/Light theme support
- Polish currency (PLN) support

## Prerequisites

1. Python 3.11+
2. PostgreSQL database
3. [Ollama](https://ollama.ai/) installed locally

## Setup Instructions

1. Clone the repository:
```bash
git clone https://github.com/yourusername/personal-finance-manager.git
cd personal-finance-manager
```

2. Install Python dependencies:
```bash
pip install streamlit pandas plotly psycopg2-binary requests
```

3. Install Ollama:
- Visit [ollama.ai](https://ollama.ai) for installation instructions
- After installation, pull the recommended model:
```bash
ollama pull mistral
```

4. Set up PostgreSQL database and environment variables:
```bash
# Required environment variables
PGDATABASE=your_database
PGUSER=your_user
PGPASSWORD=your_password
PGHOST=localhost
PGPORT=5432
```

## Running the Application

1. Start Ollama in a terminal:
```bash
ollama run mistral
```

2. In a new terminal, start the Streamlit app:
```bash
streamlit run main.py
```

3. Open your browser and navigate to:
```
http://localhost:5000
```

## Usage Instructions

1. **Adding Transactions**:
   - Click "Add Transaction" in the sidebar
   - Enter transaction description (include amount in PLN)
   - The AI will automatically classify the transaction
   - Review and adjust if needed, then save

2. **Managing Transactions**:
   - Use "Manage Transactions" to view all transactions
   - Edit or delete transactions as needed
   - Set up recurring transactions with start/end dates

3. **Dashboard**:
   - View financial summary and analytics
   - Check spending by category
   - Monitor monthly trends

## Dependencies

- streamlit: Web application framework
- pandas: Data manipulation
- plotly: Interactive charts
- psycopg2-binary: PostgreSQL database connector
- requests: HTTP client for Ollama API

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.
