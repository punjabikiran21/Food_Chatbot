# AI Food Order Chatbot Documentation

## Architecture Overview

The chatbot system consists of three main components:
1. RAG (Retrieval Augmented Generation) System
2. Food Order Agent
3. Database Layer

### 1. RAG System Implementation

The RAG system combines retrieval-based and generative approaches to provide accurate menu-related information.

#### Key Features:
- **Embedding Model**: Uses `sentence-transformers/all-MiniLM-L6-v2` for semantic understanding
- **Vector Store**: FAISS for efficient similarity search
- **Menu Context**: Structures menu data with detailed information including prices, ingredients, and dietary info

#### Methods:
- `semantic_search(query, k=3)`: Retrieves k most relevant menu items
- `generate_response(query)`: Generates natural language responses using Groq LLM

### 2. Food Order Agent

The agent handles order processing, intent classification, and customer interaction.


#### Key Components:

1. **Intent Analysis and Classification**:
   - Uses LangChain's ChatPromptTemplate for intent classification
   - Processes user input with context from menu and chat history
   - Returns structured Intent objects

2. **Order Processing**:
   - Maintains current order state
   - Validates menu items
   - Generates order summaries
   - Handles order placement

3. **Menu Inquiries**:
   - Leverages RAG for detailed menu information
   - Handles dietary and ingredient queries


### LangChain Integration

The system uses several LangChain components:

1. **Chat Models**:
   - Uses `ChatGroq` for natural language generation
   - Configured with low temperature (0.1) for consistent responses

2. **Prompt Templates**:
   - Structured prompts for intent classification
   - System and user message formatting

3. **Output Parsing**:
   - `PydanticOutputParser` for structured data handling
   - Type validation and error handling

### Best Practices

1. **Error Handling**:
   - Implement try-catch blocks for database operations
   - Fallback responses for failed intent classification
   - Validation of menu items before order placement

2. **Context Management**:
   - Maintain chat history for context-aware responses
   - Store current order state
   - Track suggested items for follow-up queries

3. **Response Generation**:
   - Clear, formatted order summaries
   - Natural language responses for menu inquiries
   - Confirmation messages with order details
