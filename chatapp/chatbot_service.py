import os
import numpy as np
import json
from sentence_transformers import SentenceTransformer
from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer
import logging
from django.core.cache import cache
from typing import List, Dict, Any
import re
from .data_handlers.query_router import QueryRouter
from model_manager import ModelManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ChatbotService:
    def __init__(self):
        """Initialize the chatbot service"""
        logger.info("Initializing chatbot service...")
        self.query_router = QueryRouter()
        self.model_manager = ModelManager()
        
        # Initialize product knowledge base
        self.product_knowledge = {
            'categories': {
                'electronics': {
                    'description': 'Latest gadgets and electronic devices',
                    'features': ['Warranty', 'Technical Support', 'Compatibility Guide'],
                    'common_questions': [
                        'What is the warranty period?',
                        'Is it compatible with my device?',
                        'What are the technical specifications?'
                    ]
                },
                'clothing': {
                    'description': 'Fashion and apparel for all seasons',
                    'features': ['Size Guide', 'Care Instructions', 'Return Policy'],
                    'common_questions': [
                        'How do I find my size?',
                        'What is the return policy?',
                        'What are the care instructions?'
                    ]
                },
                'home': {
                    'description': 'Home decor and furniture',
                    'features': ['Assembly Guide', 'Dimensions', 'Material Info'],
                    'common_questions': [
                        'What are the dimensions?',
                        'Does it require assembly?',
                        'What materials is it made of?'
                    ]
                }
            },
            'common_queries': {
                'shipping': {
                    'questions': [
                        'How long does shipping take?',
                        'What are the shipping costs?',
                        'Do you offer international shipping?'
                    ],
                    'responses': {
                        'shipping_time': 'Standard shipping takes 3-5 business days. Express shipping is available for 1-2 business days delivery.',
                        'shipping_cost': 'Shipping is free for orders over $50. Standard shipping costs $5.99, and express shipping costs $12.99.',
                        'international': 'Yes, we ship to most countries. International shipping costs and delivery times vary by location.'
                    }
                },
                'returns': {
                    'questions': [
                        'What is your return policy?',
                        'How do I return an item?',
                        'How long do I have to return?'
                    ],
                    'responses': {
                        'policy': 'We offer a 30-day return policy for most items. Items must be unused and in original packaging.',
                        'process': 'To return an item, please contact our customer service or initiate a return through your account dashboard.',
                        'timeframe': 'You have 30 days from the delivery date to initiate a return.'
                    }
                }
            }
        }
        
        logger.info("Chatbot service initialized successfully")

    def process_query(self, query: str, product_context=None) -> str:
        """
        Process a user query and return a response
        
        Args:
            query: The user's query
            product_context: Optional context about a product the user is asking about
        """
        try:
            # Clean the query
            query = query.strip().lower()
            if not query:
                return "Please ask a question or provide some details about what you'd like to know."

            # Log the incoming query
            logger.info(f"Processing query: {query}")
            
            # If we have product context, enhance the response with product details
            if product_context:
                logger.info(f"Query has product context: {product_context['name']}")
                response = self._handle_product_query(query, product_context)
            else:
                # Handle general queries
                response = self._handle_general_query(query)
            
            # Add relevant suggestions
            suggestions = self._generate_suggestions(query, response, product_context)
            if suggestions:
                response += "\n\nYou might also want to know:\n" + "\n".join([f"- {s}" for s in suggestions])
            
            return response

        except Exception as e:
            logger.error(f"Error processing query: {e}", exc_info=True)
            return "I apologize, but I encountered an error while processing your request. Please try again."

    def _handle_product_query(self, query: str, product_context: Dict) -> str:
        """Handle queries about specific products"""
        # Extract category information
        category = product_context.get('category', '').lower()
        category_info = self.product_knowledge['categories'].get(category, {})
        
        # Check for common product questions
        if any(word in query for word in ['feature', 'spec', 'detail']):
            return self._format_product_features(product_context, category_info)
        elif any(word in query for word in ['price', 'cost']):
            return self._format_product_price(product_context)
        elif any(word in query for word in ['stock', 'available']):
            return self._format_stock_info(product_context)
        elif any(word in query for word in ['similar', 'like', 'related']):
            return self._format_similar_products(product_context)
        else:
            # Generic product response
            return self._format_generic_product_response(product_context, category_info)

    def _handle_general_query(self, query: str) -> str:
        """Handle general queries not related to specific products"""
        # Check for shipping related queries
        if any(word in query for word in ['shipping', 'delivery', 'ship']):
            return self._format_shipping_info()
        # Check for return related queries
        elif any(word in query for word in ['return', 'refund', 'exchange']):
            return self._format_return_info()
        # Check for category related queries
        elif any(word in query for word in ['category', 'type', 'kind']):
            return self._format_category_info()
        else:
            return "I can help you with information about our products, shipping, returns, and more. What would you like to know?"

    def _format_product_features(self, product: Dict, category_info: Dict) -> str:
        """Format product features in a readable way"""
        features = category_info.get('features', [])
        return f"The {product['name']} comes with the following features:\n" + \
               "\n".join([f"- {feature}" for feature in features]) + \
               f"\n\n{product['description']}"

    def _format_product_price(self, product: Dict) -> str:
        """Format product price information"""
        return f"The {product['name']} is priced at ${product['price']}. " + \
               "We offer various payment methods and financing options are available for eligible purchases."

    def _format_stock_info(self, product: Dict) -> str:
        """Format stock information"""
        if product['stock'] > 0:
            return f"Yes, the {product['name']} is currently in stock with {product['stock']} units available. " + \
                   "You can add it to your cart and proceed with checkout."
        else:
            return f"I'm sorry, but the {product['name']} is currently out of stock. " + \
                   "Would you like me to notify you when it becomes available?"

    def _format_similar_products(self, product: Dict) -> str:
        """Format information about similar products"""
        return f"I can help you find similar products to the {product['name']}. " + \
               "Would you like me to show you items in the same category or with similar features?"

    def _format_generic_product_response(self, product: Dict, category_info: Dict) -> str:
        """Format a generic response about a product"""
        return f"The {product['name']} is a {category_info.get('description', 'great product')}. " + \
               f"{product['description']}\n\n" + \
               "Would you like to know more about its features, price, or availability?"

    def _format_shipping_info(self) -> str:
        """Format shipping information"""
        shipping_info = self.product_knowledge['common_queries']['shipping']['responses']
        return f"Here's our shipping information:\n" + \
               f"- {shipping_info['shipping_time']}\n" + \
               f"- {shipping_info['shipping_cost']}\n" + \
               f"- {shipping_info['international']}"

    def _format_return_info(self) -> str:
        """Format return policy information"""
        return_info = self.product_knowledge['common_queries']['returns']['responses']
        return f"Here's our return policy:\n" + \
               f"- {return_info['policy']}\n" + \
               f"- {return_info['process']}\n" + \
               f"- {return_info['timeframe']}"

    def _format_category_info(self) -> str:
        """Format category information"""
        categories = self.product_knowledge['categories']
        return "We offer products in the following categories:\n" + \
               "\n".join([f"- {cat.title()}: {info['description']}" for cat, info in categories.items()])

    def _generate_suggestions(self, query: str, response: str, product_context: Dict = None) -> List[str]:
        """Generate relevant follow-up suggestions"""
        suggestions = []
        
        if product_context:
            # Add product-specific suggestions
            category = product_context.get('category', '').lower()
            category_info = self.product_knowledge['categories'].get(category, {})
            suggestions.extend(category_info.get('common_questions', []))
        else:
            # Add general suggestions
            if 'shipping' in query:
                suggestions.extend(self.product_knowledge['common_queries']['shipping']['questions'])
            elif 'return' in query:
                suggestions.extend(self.product_knowledge['common_queries']['returns']['questions'])
            else:
                suggestions.extend([
                    "What are your best-selling products?",
                    "How can I track my order?",
                    "What payment methods do you accept?"
                ])
        
        return suggestions[:3]  # Limit to 3 suggestions