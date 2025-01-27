# AI Food Order Chatbot

## Project Overview
An AI-powered chatbot for taking food orders using Streamlit, Langchain, and RAG (Retrieval-Augmented Generation).


## Setup Instructions
1. Clone the repository
2. Create a virtual environment
3. Install dependencies:
```bash
pip install -r requirements.txt
```
4. Run the docker compose file:
```bash
docker-compose up -d mysql
```

5. Create ev file in the root directory and add the following environment variables:
```bash
GROQ_API_KEY=your_groq_api_key
DB_HOST=your_db_host
DB_USER=your_db_username
DB_PASSWORD=your_db_password
DB_PORT=your_db_port
DB_NAME=your_db_name
```

6. Run the application:
```bash
streamlit run main.py
```

## Project Structure
- `main.py`: Streamlit frontend
- `chatbot/agent.py`: Order processing logic
- `chatbot/rag.py`: Menu retrieval system
- `chatbot/database.py`: SQL database management
- `menu_data.json`: Restaurant menu data
- `docker-compose.yml`: Docker compose file for running the application
