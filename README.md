# Personal Finance Manager

A Streamlit-based personal finance manager with local AI processing using Ollama for intelligent transaction classification.

## Features

- Database integration for transaction management
- AI-powered transaction classification using Ollama
- Financial dashboard with multiple analysis tabs
- Custom category management
- Budget planning and tracking
- Advanced financial analytics and forecasting
- RAG-powered financial chat assistant
- Data export functionality (CSV/Excel)

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
- `OPENAI_API_KEY` (Optional, for OpenAI integration)
- Database configuration (automatically handled by Replit)

3. Run the application:
```bash
streamlit run main.py
```

## Project Structure

- `components/`: UI components and pages
- `models/`: Database models and data access
- `services/`: Business logic and external services
- `utils/`: Helper functions and utilities
- `tests/`: Test suite

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License
