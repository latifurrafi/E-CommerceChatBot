import os
import json
import logging
from sentence_transformers import SentenceTransformer
from transformers import pipeline
import numpy as np

logger = logging.getLogger(__name__)

class ChatbotService:
    def __init__(self):
        """Initialize the chatbot service with necessary models and knowledge base"""
        try:
            # Initialize the sentence transformer model for semantic search
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Initialize the text generation pipeline
            self.generator = pipeline('text-generation', model='gpt2')
            
            # Initialize product knowledge base
            self.product_knowledge = {
                'electronics': {
                    'description': 'Electronic devices and accessories',
                    'features': ['Warranty', 'Compatibility', 'Technical specifications'],
                    'common_questions': [
                        'What is the warranty period?',
                        'Is it compatible with my device?',
                        'What are the technical specifications?'
                    ]
                },
                'clothing': {
                    'description': 'Fashion and apparel items',
                    'features': ['Size guide', 'Material', 'Care instructions'],
                    'common_questions': [
                        'What sizes are available?',
                        'What material is it made of?',
                        'How should I care for this item?'
                    ]
                },
                'home': {
                    'description': 'Home and living products',
                    'features': ['Dimensions', 'Assembly', 'Care instructions'],
                    'common_questions': [
                        'What are the dimensions?',
                        'Does it require assembly?',
                        'How do I clean this item?'
                    ]
                }
            }
            
            # Common queries and responses
            self.common_queries = {
                'shipping': {
                    'questions': [
                        'How long does shipping take?',
                        'What are the shipping costs?',
                        'Do you offer international shipping?'
                    ],
                    'responses': {
                        'time': 'Standard shipping takes 3-5 business days.',
                        'cost': 'Free shipping on orders over $50.',
                        'international': 'Yes, we ship to most countries worldwide.'
                    }
                },
                'returns': {
                    'questions': [
                        'What is your return policy?',
                        'How do I return an item?',
                        'How long do I have to return?'
                    ],
                    'responses': {
                        'policy': '30-day return policy for unused items in original packaging.',
                        'process': 'Contact customer service to initiate a return.',
                        'timeframe': 'You have 30 days from delivery to return items.'
                    }
                }
            }
            
            logger.info("Chatbot service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize chatbot service: {str(e)}")
            raise

    def process_query(self, query, product_id=None):
        """
        Process a user query and return a response
        Args:
            query (str): The user's query
            product_id (str, optional): The ID of the product being discussed
        Returns:
            str: The chatbot's response
        """
        try:
            # Clean the query
            query = query.strip().lower()
            
            # Log the incoming query
            logger.info(f"Processing query: {query}")
            
            # Get product context if available
            product_context = self._get_product_context(product_id) if product_id else None
            
            # Process the query based on context
            if product_context:
                response = self._handle_product_query(query, product_context)
            else:
                response = self._handle_general_query(query)
            
            # Generate suggestions based on the query
            suggestions = self._generate_suggestions(query, product_context)
            
            # Add suggestions to the response
            if suggestions:
                response += "\n\nYou might also want to know:\n" + "\n".join(f"- {s}" for s in suggestions)
            
            logger.info(f"Generated response: {response}")
            return response
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return "I apologize, but I'm having trouble processing your request. Please try again."

    def _get_product_context(self, product_id):
        """Get product information from the database"""
        try:
            # TODO: Implement database query to get product details
            # For now, return a mock product context
            return {
                'id': product_id,
                'name': 'Sample Product',
                'category': 'electronics',
                'price': 99.99,
                'stock': 10
            }
        except Exception as e:
            logger.error(f"Error getting product context: {str(e)}")
            return None

    def _handle_product_query(self, query, product_context):
        """Handle queries about specific products"""
        try:
            # Check for price-related queries
            if any(word in query for word in ['price', 'cost', 'how much']):
                return self._format_price_response(product_context)
            
            # Check for stock-related queries
            if any(word in query for word in ['stock', 'available', 'in stock']):
                return self._format_stock_response(product_context)
            
            # Check for feature-related queries
            if any(word in query for word in ['feature', 'specification', 'what can it do']):
                return self._format_features_response(product_context)
            
            # Default response
            return f"I can tell you about {product_context['name']}. What would you like to know? You can ask about its price, features, or availability."
            
        except Exception as e:
            logger.error(f"Error handling product query: {str(e)}")
            return "I'm having trouble finding information about this product. Please try asking something else."

    def _handle_general_query(self, query):
        """Handle general queries not related to specific products"""
        try:
            # Check for shipping-related queries
            if any(word in query for word in ['shipping', 'delivery', 'when will it arrive']):
                return self._format_shipping_response()
            
            # Check for return-related queries
            if any(word in query for word in ['return', 'refund', 'exchange']):
                return self._format_return_response()
            
            # Check for category-related queries
            for category, info in self.product_knowledge.items():
                if category in query:
                    return self._format_category_response(category, info)
            
            # Default response
            return "I can help you with product information, shipping, returns, and more. What would you like to know?"
            
        except Exception as e:
            logger.error(f"Error handling general query: {str(e)}")
            return "I'm having trouble understanding your question. Could you please rephrase it?"

    def _format_price_response(self, product_context):
        """Format response for price-related queries"""
        return f"The {product_context['name']} is priced at ${product_context['price']}."

    def _format_stock_response(self, product_context):
        """Format response for stock-related queries"""
        if product_context['stock'] > 0:
            return f"Yes, the {product_context['name']} is in stock. We have {product_context['stock']} units available."
        return f"Sorry, the {product_context['name']} is currently out of stock."

    def _format_features_response(self, product_context):
        """Format response for feature-related queries"""
        category = product_context.get('category', 'general')
        features = self.product_knowledge.get(category, {}).get('features', [])
        return f"The {product_context['name']} comes with the following features:\n" + "\n".join(f"- {feature}" for feature in features)

    def _format_shipping_response(self):
        """Format response for shipping-related queries"""
        return "We offer free standard shipping on orders over $50. Orders are typically processed within 1-2 business days."

    def _format_return_response(self):
        """Format response for return-related queries"""
        return "We accept returns within 30 days of delivery. Items must be in original condition with tags attached."

    def _format_category_response(self, category, info):
        """Format response for category-related queries"""
        return f"{info['description']}\n\nCommon features include:\n" + "\n".join(f"- {feature}" for feature in info['features'])

    def _generate_suggestions(self, query, product_context=None):
        """Generate relevant follow-up suggestions based on the query"""
        try:
            suggestions = []
            
            if product_context:
                # Add product-specific suggestions
                category = product_context.get('category', 'general')
                if category in self.product_knowledge:
                    suggestions.extend(self.product_knowledge[category]['common_questions'])
            else:
                # Add general suggestions
                suggestions.extend([
                    "What are your best-selling products?",
                    "Do you offer international shipping?",
                    "What is your return policy?"
                ])
            
            return suggestions[:3]  # Return top 3 suggestions
            
        except Exception as e:
            logger.error(f"Error generating suggestions: {str(e)}")
            return []