import json
from typing import List, Dict
import os
from groq import Groq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter

curr_dir = os.getcwd()
file_path = os.path.join(curr_dir, 'menu_data.json')

class RAGSystem():
        
        def __init__(self, menu_file, groq_api_key):

            # Initialize Groq client
            self.client = Groq(api_key=groq_api_key)
        
            # Load menu data
            with open(file_path, 'r') as f:
                self.menu_data = json.load(f)
        
            # Embedding setup
            self.embeddings = HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2')
            
            # Create vector store
            self._create_vector_store()


        def _create_vector_store(self):
            menu_texts = []
            for item in self.menu_data['items']:
                text = f"""
                Name: {item['name']}
                Category: {item['category']}
                Description: {item['description']}
                Price: ${item['price']}
                Ingredients: {', '.join(item.get('ingredients', []))}
                Dietary Info: {', '.join(item.get('dietary_info', []))}
                """
                menu_texts.append(text)

            text_splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=50)
            texts = text_splitter.split_text('\n'.join(menu_texts))
        
            self.vector_store = FAISS.from_texts(texts, self.embeddings)


        def semantic_search(self, query, k=3):
            results = self.vector_store.similarity_search(query, k=k)
            return [result.page_content for result in results]
    
        def generate_response(self, query):
            try:
                full_menu_context = ""
                for item in self.menu_data['items']:
                    full_menu_context += f"""
                    Name: {item['name']}
                    Category: {item['category']}
                    Description: {item['description']}
                    Price: ₹ {item['price']}
                    Ingredients: {', '.join(item.get('ingredients', []))}
                    Dietary Info: {', '.join(item.get('dietary_info', []))}
                    """
                messages = [
                {
                    "role": "system",
                    "content": '''You are a helpful restaurant assistant,An automated service to collect orders.
                        You first greet the customer, then start the conversation.
                        You wait to collect the entire order, then summarize it and check for a final time if the customer wants to add anything else. 
                        Make sure to clarify all options uniquely identify the item from the menu.
                        You respond in a short, very conversational friendly style. 
                        Use the provided context to understand user's intent and then answer user queries about the menu.
                        If the user asks for more information, provide a detailed description of the menu item.'''
                },
                {
                    "role": "user",
                    "content": f"Context: {full_menu_context}\n\n Query: {query}"
                }
                ]

                response = self.client.chat.completions.create(model="llama-3.3-70b-versatile",messages=messages)
                return response.choices[0].message.content.strip()
            except Exception as e:
                print(f"Exception raised due to {e}")

        
        def process_query(self, query):
            
            # Semantic search
            context = '\n'.join(self.semantic_search(query))
            
            # Generate response
            response = self.generate_response(query)
        
            return response

  

