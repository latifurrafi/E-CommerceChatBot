from typing import Dict, Any, List
import logging
from ..models import FAQ

logger = logging.getLogger(__name__)

class FAQHandler:
    def __init__(self):
        self.query_patterns = {
            'how_to': ['how to', 'how do i', 'steps to', 'guide'],
            'what_is': ['what is', 'what are', 'explain', 'define'],
            'troubleshoot': ['problem', 'issue', 'error', 'not working', 'help'],
            'policy': ['policy', 'return', 'warranty', 'shipping', 'payment'],
            'general': ['can i', 'do you', 'is it possible']
        }

    def extract_info(self, query: str) -> Dict[str, Any]:
        """Extract FAQ-related information from the query"""
        query_lower = query.lower().strip()
        info = {
            'query_type': None,
            'keywords': [],
            'category': None
        }

        # Detect query type
        for query_type, patterns in self.query_patterns.items():
            if any(pattern in query_lower for pattern in patterns):
                info['query_type'] = query_type
                break

        # Extract keywords (remove common words)
        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'is', 'are', 'was', 'were'}
        words = query_lower.split()
        info['keywords'] = [word for word in words if word not in common_words]

        return info

    def get_relevant_faqs(self, query_info: Dict[str, Any], limit: int = 3) -> List[Dict[str, Any]]:
        """Retrieve relevant FAQs based on query information"""
        try:
            # Start with all FAQs
            faqs = FAQ.objects.all()

            # Filter by category if specified
            if query_info['category']:
                faqs = faqs.filter(category=query_info['category'])

            # Filter by keywords
            from django.db.models import Q
            keyword_query = Q()
            for keyword in query_info['keywords']:
                keyword_query |= Q(question__icontains=keyword) | Q(answer__icontains=keyword)
            
            faqs = faqs.filter(keyword_query)

            # Convert to list of dictionaries
            faq_list = []
            for faq in faqs[:limit]:
                faq_list.append({
                    'question': faq.question,
                    'answer': faq.answer,
                    'category': faq.category
                })

            return faq_list

        except Exception as e:
            logger.error(f"Error retrieving FAQs: {e}")
            return []

    def format_faq_response(self, faqs: List[Dict[str, Any]], query_info: Dict[str, Any]) -> str:
        """Format the FAQ response based on the query type and FAQs found"""
        try:
            if not faqs:
                return "I couldn't find any FAQs matching your question. Could you please rephrase or be more specific?"

            if len(faqs) == 1:
                faq = faqs[0]
                response = f"Q: {faq['question']}\nA: {faq['answer']}"
                return response

            # Multiple FAQs found
            response = "I found several relevant questions that might help:\n\n"
            for i, faq in enumerate(faqs, 1):
                response += f"{i}. Q: {faq['question']}\nA: {faq['answer']}\n\n"
            return response.strip()

        except Exception as e:
            logger.error(f"Error formatting FAQ response: {e}")
            return "I apologize, but I encountered an error while formatting the FAQ information."

    def handle_query(self, query: str) -> str:
        """Main method to handle FAQ-related queries"""
        try:
            # Extract information from the query
            query_info = self.extract_info(query)
            
            if not query_info['keywords']:
                return "Could you please provide more details about what you'd like to know?"

            # Get relevant FAQs
            faqs = self.get_relevant_faqs(query_info)
            
            # Format and return the response
            return self.format_faq_response(faqs, query_info)

        except Exception as e:
            logger.error(f"Error handling FAQ query: {e}")
            return "I apologize, but I encountered an error while processing your FAQ query." 