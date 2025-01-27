import os
import streamlit as st
from chatbot.agent import FoodOrderAgent
from chatbot.rag import RAGSystem
from chatbot.database import OrderDatabase
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def main():
    st.title("AI Food Order Chatbot!")

    # Get Groq API key from environment
    groq_api_key = os.getenv('GROQ_API_KEY')
    if not groq_api_key:
        st.error("Please set GROQ_API_KEY in your environment variables")
        return
    
    # Initialize DB, RAG, and Agent in session state
    if 'db' not in st.session_state:
        st.session_state.db = OrderDatabase()
    
    if 'menu_rag' not in st.session_state:
        st.session_state.menu_rag = RAGSystem('menu_data.json', groq_api_key)
    
    if 'agent' not in st.session_state:
        st.session_state.agent = FoodOrderAgent(
            st.session_state.db, 
            st.session_state.menu_rag,
            groq_api_key
        )

    # Conversation history
    if 'messages' not in st.session_state:
        st.session_state.messages = []
        welcome_msg = ("Welcome to our restaurant! 🍽️\n\n"
                      "We have:\n"
                      "🍕 Pizzas\n"
                      "🥗 Salads\n"
                      "🍔 Burgers\n"
                      "🍰 Desserts\n\n"
                      "What would you like to order?")
        st.session_state.messages.append({"role": "assistant", "content": welcome_msg})
    
    # Add this initialization for orders
    if 'orders' not in st.session_state:
        st.session_state.orders = []

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("What would you like to order?"):
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get chatbot response
        with st.chat_message("assistant"):
            chat_history = "\n".join([
                f"{msg['role']}: {msg['content']}" 
                for msg in st.session_state.messages
            ])
            
            response = st.session_state.agent.process_order(prompt, chat_history)
            
            # If order was placed successfully (contains order ID)
            if "Order #" in response:
                order_id = response.split("Order #")[1].split(" ")[0]
                # Add to orders history
                st.session_state.orders.append({
                    'order_id': order_id,
                    'details': response
                })
                # Reset the agent's current_order after successful placement
                st.session_state.agent.current_order = []
            
            st.markdown(response)

        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()
