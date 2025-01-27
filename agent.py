from chatbot.rag import RAGSystem
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class IntentType(str, Enum):
    ORDER = "order"
    MENU_INQUIRY = "menu_inquiry"
    GENERAL_QUERY = "general_query"

class MenuItem(BaseModel):
    name: str
    quantity: int = Field(default=1)
    special_instructions: Optional[str] = None

class Intent(BaseModel):
    intent_type: IntentType
    items: Optional[List[MenuItem]] = None
    query_details: Optional[str] = None

class FoodOrderAgent:
    def __init__(self, database, menu_file, groq_api_key):
        self.database = database
        self.rag_system = RAGSystem(menu_file, groq_api_key)
        self.current_order = []
        #self.last_suggested_item = None
        self.llm = ChatGroq(
            api_key=groq_api_key,
            temperature=0.1,
            model_name="llama3-70b-8192"
        )
    
        self.intent_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a restaurant order assistant. Analyze the user input and classify the intent.
            You must return a valid JSON object in the following format:
            {
                "intent_type": "order" | "menu_inquiry" | "general_query",
                "items": [
                    {
                        "name": "Margherita Pizza",
                        "quantity": 1,
                        "special_instructions": null
                    }
                ],
                "query_details": null
            }

            Rules:
            - For orders: include items array with details
            - For menu inquiries: set items to null, include query_details
            - For general queries: set items to null, include query_details
            - If user says 'yes' to confirm an order, treat it as an ORDER intent"""),
            ("user", "{user_input}"),
            ("system", "Context from menu: {menu_context}")
        ])
        
        self.parser = PydanticOutputParser(pydantic_object=Intent)

    def _find_matching_items(self, query: str) -> List[dict]:
            """Find menu items that match the user's query"""
            matching_items = []
            
            # Dynamically build categories and keywords from menu data
            categories = {}
            for item in self.rag_system.menu_data['items']:
                category = item['category'].lower()
                if category not in categories:
                    categories[category] = set()
                
                # Add category name itself as a keyword
                categories[category].add(category)
                
                # Add item name words as keywords
                categories[category].update(item['name'].lower().split())
                
                # Add keywords from description if available
                if 'description' in item:
                    categories[category].update(item['description'].lower().split())
            
            # Convert sets to lists for easier handling
            categories = {k: list(v) for k, v in categories.items()}
            
            # Find category matches
            category_matches = []
            for category, keywords in categories.items():
                if category in query or any(keyword in query for keyword in keywords):
                    category_matches.append(category)
            
            # Find items from matching categories or direct item matches
            for item in self.rag_system.menu_data['items']:
                item_name_lower = item['name'].lower()
                item_category_lower = item['category'].lower()
                
                # Check if item matches query directly or belongs to matching category
                if (query in item_name_lower or 
                    any(category in item_category_lower for category in category_matches) or
                    any(keyword in item_name_lower for keywords in categories.values() for keyword in keywords)):
                    matching_items.append(item)
            
            return matching_items

    def process_order(self, user_input: str, chat_history: str) -> str:

        # Get relevant menu context
        menu_context = self._get_relevant_context(user_input)
        
        # Analyze intent using LLM with chat history
        intent = self._analyze_intent(user_input, menu_context, chat_history)
        
        if intent.intent_type == IntentType.ORDER:
            print("current_order in order intent: ", self.current_order)
            if intent.items:

                print("intent.items in order intent: ", intent.items)
                item_name = ""
                for item in intent.items:
                    self.current_order.append({
                        "name": item.name,
                        "quantity": item.quantity,
                        "price": self._find_menu_item(item.name)['price'],
                        "special_instructions": item.special_instructions
                    })
                    item_name += item.name
                response = f"Great! I've added items {item_name} to your order.\n"
                response += self._generate_order_summary(self.current_order)
                print("current_order in order intent after adding items: ", self.current_order)
                return response

            if not intent.items and self.current_order:
                return self.place_order()
            elif not intent.items:
                return "I couldn't identify any items to order. Could you please specify what you'd like to order?"
    
        
        elif intent.intent_type == IntentType.MENU_INQUIRY:

            matching_items = self._find_matching_items(user_input.lower())
            print("in query intent : ", matching_items)            
            if matching_items:
                if len(matching_items) == 1:
                    # If only one item matches, suggest it
                    #self.last_suggested_item = matching_items[0]
                    return (f"We have the {matching_items[0]['name']}, {matching_items[0]['description']} "
                           f"for ₹{matching_items[0]['price']}. Would you like to order this?")
                else:
                    # If multiple items match, list them all
                    response = "Here are the options available:\n\n"
                    for item in matching_items:
                        response += f"• {item['name']} - ₹{item['price']}\n"
                        response += f"  {item['description']}\n\n"
                    response += "Which one would you like to order?"
                    return response
            return self._handle_menu_inquiry(intent.query_details)
        else:
            return self._handle_general_query(intent.query_details)
        


    def _analyze_intent(self, user_input: str, menu_context: str, chat_history: str) -> Intent:
        
        self.intent_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a restaurant order assistant. Analyze the user input and classify the intent.
            You must return a valid JSON object in the following format:
                'intent_type': 'order' | 'menu_inquiry' | 'general_query',
                'items' should be an array of objects with the following properties:
                    'name': 'Margherita Pizza',
                    'quantity': 1,
                    'special_instructions': null             
                'query_details': null

            Rules:
            - For orders: include items array with details
            - For menu inquiries: set items to null, include query_details
            - For general queries: set items to null, include query_details
            - If user says express intent to confirm or place their order (using phrases like 'yes','confirm','place order','order as it is','thats it' etc.) 
              treat it as an ORDER intent"""),
            ("user", "{user_input}"),
            ("system", "Context from menu: {menu_context}")
        ])
        
        
        prompt = self.intent_prompt.format_messages(
            user_input=user_input,
            menu_context=menu_context,
            chat_history=chat_history
        )
        response = self.llm.predict_messages(prompt)
        print("response in analyze_intent: ", response)
        
        try:
            # Parse the JSON response
            intent = self.parser.parse(response.content)
            return intent
        except Exception as e:
            print("JSON parsing failed: ", e)

            # Fallback to default general query intent
            return Intent(
                intent_type=IntentType.GENERAL_QUERY,
                query_details=user_input
            )

    # def _handle_order(self, items: List[MenuItem]) -> str:
    #     if not items:
    #         return "I couldn't identify any items to order. Could you please specify what you'd like to order?"
        
        
    #     valid_items = []
    #     invalid_items = []
        
    #     for item in items:
    #         menu_item = self._find_menu_item(item.name)
    #         if menu_item:
    #             valid_items.append({
    #                 **menu_item,
    #                 "quantity": item.quantity,
    #                 "special_instructions": item.special_instructions
    #             })
    #         else:
    #             invalid_items.append(item.name)
        
    #     # Generate response
    #     response = ""
    #     if valid_items:
    #         self.current_order.extend(valid_items)
    #         response += self._generate_order_summary(valid_items)
        
    #     if invalid_items:
    #         response += (f"\n\nSorry, I couldn't find the following items in our menu: {', '.join(invalid_items)} \n\n"
    #                  "Here's our menu:\n\n"
    #                "🍕 Pizzas: Margherita Pizza\n"
    #                "🥗 Salads: Caesar Salad, Grilled Chicken Salad\n"
    #                "🍔 Burgers: Chicken Burger, Veggie Black Bean Burger\n"
    #                "🍰 Desserts: Chocolate Lava Cake, Fresh Fruit Parfait\n"
    #                "What would you like to order?")
        
    #     return response

    def _handle_menu_inquiry(self, query_details: str) -> str:
        # Use RAG to get detailed menu information
        context = self.rag_system.semantic_search(query_details)
        
        # Use LLM to generate natural response
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful restaurant assistant. Generate a natural response about menu items using the provided context."),
            ("user", query_details),
            ("system", f"Context: {context}")
        ])
        
        response = self.llm.predict_messages(prompt)
        return response.content

    def _handle_general_query(self, query_details: str) -> str:
        # Use RAG for general queries
        return self.rag_system.process_query(query_details)

    def _get_relevant_context(self, query: str) -> str:
        context = self.rag_system.semantic_search(query)
        return '\n'.join(context)

    def _find_menu_item(self, item_name: str) -> Optional[dict]:
        for item in self.rag_system.menu_data['items']:
            if item['name'].lower() == item_name.lower():
                return item
        return None

    def _generate_order_summary(self, items: List[dict]) -> str:
        summary = "Here's your order summary:\n"
        total = 0
        
        for item in items:
            item_total = item['price'] * item['quantity']
            summary += f"- {item['quantity']}x {item['name']} (₹{item['price']} each) = ₹{item_total:.2f}\n"
            if item.get('special_instructions'):
                summary += f"  Special instructions: {item['special_instructions']}\n"
            total += item_total
        
        summary += f"\nTotal: ₹{total:.2f}"
        
        if self.current_order:
            summary += "\n\n✨ Would you like to:\n"
            summary += "1. Add more items to your order\n"
            summary += "2. Type 'place order' to confirm and complete your order"
        
        return summary

    def place_order(self) -> str:
        """Place the current order in the database"""    
        try:
            # Calculate total price
            total_price = sum(item['price'] * item['quantity'] for item in self.current_order)
            print("items in place_order: ", self.current_order)
            # Save order to database
            order_id = self.database.save_order(self.current_order, total_price)
            
            # Generate detailed order confirmation
            confirmation = (
                f"Order #{order_id} has been placed successfully!\n\n"
                f"Order Details:\n"
                f"══════════════════\n\n"
            )
            
            for item in self.current_order:
                item_total = item['price'] * item['quantity']
                print("item in place_order: ", item)
                confirmation += (
                    f"• {item['quantity']}x {item['name']}\n"
                    f"  Price: ₹{item['price']} each\n\n"
                )
                if item.get('special_instructions'):
                    confirmation += f"Note: {item['special_instructions']}\n"
                confirmation += "──────────────────\n\n"
            
            confirmation += (
                f"\n Total Amount: ₹{total_price:.2f}\n\n"
                f"Thank you for your order! Your food will be prepared shortly.\n"
                f"Your order ID is: #{order_id} (please save this for reference)"
            )
            
            return confirmation
            
        except Exception as e:
            return f"Sorry, there was an error placing your order: {str(e)}"