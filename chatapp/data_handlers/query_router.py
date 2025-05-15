from typing import Dict, Any
import logging
from .product_handler import ProductHandler
from .faq_handler import FAQHandler
from .order_handler import OrderHandler

logger = logging.getLogger(__name__)

class QueryRouter:
    def __init__(self):
        self.product_handler = ProductHandler()
        self.faq_handler = FAQHandler()
        self.order_handler = OrderHandler()

        # Define patterns for each type of query
        self.routing_patterns = {
            'product': [
                'price', 'cost', 'how much', 'product', 'item', 'buy',
                'available', 'in stock', 'features', 'specifications', 'about'
            ],
            'order': [
                'order', 'tracking', 'delivery', 'shipped', 'package',
                '#', 'cancel', 'modify', 'change order'
            ],
            'faq': [
                'how to', 'how do i', 'what is', 'why', 'help',
                'guide', 'instructions', 'return policy', 'shipping policy'
            ]
        }

    def determine_query_type(self, query: str) -> str:
        """Determine the type of query to route to appropriate handler"""
        query_lower = query.lower()
        
        # Check for order number pattern first
        import re
        if re.search(r'#\d+|order\s+\d+|order\s*number\s*\d+', query_lower):
            return 'order'
        
        # Check other patterns
        scores = {
            'product': 0,
            'order': 0,
            'faq': 0
        }
        
        for query_type, patterns in self.routing_patterns.items():
            for pattern in patterns:
                if pattern in query_lower:
                    scores[query_type] += 1
        
        # Get the query type with highest score
        max_score = max(scores.values())
        if max_score > 0:
            for query_type, score in scores.items():
                if score == max_score:
                    return query_type
        
        # Default to FAQ if no clear match
        return 'faq'

    def handle_query(self, query: str) -> str:
        """Route the query to appropriate handler and return response"""
        try:
            query_type = self.determine_query_type(query)
            logger.info(f"Query type determined as: {query_type}")

            if query_type == 'product':
                return self.product_handler.handle_query(query)
            elif query_type == 'order':
                return self.order_handler.handle_query(query)
            elif query_type == 'faq':
                return self.faq_handler.handle_query(query)
            else:
                return "I'm not sure how to help with that. Could you please rephrase your question?"

        except Exception as e:
            logger.error(f"Error routing query: {e}")
            return "I apologize, but I encountered an error while processing your request." 