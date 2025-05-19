from typing import Dict, Any, List, Optional
import logging
from ..models import Product

logger = logging.getLogger(__name__)

class ProductHandler:
    def __init__(self):
        self.query_patterns = {
            'price': ['price', 'cost', 'how much', 'pricing', 'worth', 'value', '$', 'dollar'],
            'availability': ['available', 'in stock', 'buy', 'purchase', 'get', 'order', 'shipping'],
            'features': ['features', 'capabilities', 'functions', 'can it', 'does it'],
            'specifications': ['specs', 'specifications', 'technical', 'details'],
            'comparison': ['compare', 'difference', 'better', 'best', 'vs', 'versus', 'or'],
            'description': ['what is', 'describe', 'about', 'tell me about']
        }

    def extract_info(self, query: str) -> Dict[str, Any]:
        """Extract product-related information from the query"""
        query_lower = query.lower().strip()
        info = {
            'query_type': None,
            'product_name': None,
            'specific_attribute': None
        }

        # Detect query type
        for query_type, patterns in self.query_patterns.items():
            if any(pattern in query_lower for pattern in patterns):
                info['query_type'] = query_type
                break

        # Extract product name using various patterns
        import re
        patterns = [
            r'"([^"]+)"',
            r'\'([^\']+)\'',
            r'about\s+(\w+[\s\w]+?)(?:\s+(?:price|cost|features|specs|availability)|$)',
            r'(?:price|cost|features|specs|availability)\s+of\s+(\w+[\s\w]+)',
            r'(?:how much|what)\s+(?:is|does)\s+(?:the\s+)?(\w+[\s\w]+?)(?:\s+cost|$)'
        ]

        for pattern in patterns:
            match = re.search(pattern, query_lower)
            if match:
                info['product_name'] = match.group(1).strip()
                break

        return info

    def format_product_response(self, product_data: Dict[str, Any], query_info: Dict[str, Any]) -> str:
        """Format the response based on the query type and product data"""
        try:
            if not product_data:
                return "I couldn't find any information about that product."

            query_type = query_info.get('query_type')

            if query_type == 'price':
                return f"The {product_data['name']} is priced at ${product_data['price']:.2f}."

            elif query_type == 'availability':
                in_stock = product_data.get('in_stock', product_data.get('stock', 0) > 0)
                status = "is available" if in_stock else "is currently out of stock"
                return f"The {product_data['name']} {status}."

            elif query_type == 'features':
                features = product_data.get('features', [])
                if features:
                    feature_list = "\n".join([f"- {feature}" for feature in features])
                    return f"The {product_data['name']} includes the following features:\n{feature_list}"
                return f"Here's what you need to know about {product_data['name']}:\n{product_data['description']}"

            elif query_type == 'specifications':
                specs = product_data.get('specifications', {})
                if specs:
                    spec_list = "\n".join([f"- {key}: {value}" for key, value in specs.items()])
                    return f"Technical specifications for {product_data['name']}:\n{spec_list}"
                return f"Basic information about {product_data['name']}:\n{product_data['description']}"

            else:  # Default to full description
                response = f"Product: {product_data['name']}\n"
                response += f"Description: {product_data['description']}\n"
                response += f"Price: ${product_data['price']:.2f}\n"
                
                # Add stock information if available
                if 'stock' in product_data:
                    response += f"Availability: {'In Stock' if product_data['stock'] > 0 else 'Out of Stock'}\n"
                elif 'in_stock' in product_data:
                    response += f"Availability: {'In Stock' if product_data['in_stock'] else 'Out of Stock'}\n"
                
                # Add SKU if available
                if 'sku' in product_data:
                    response += f"SKU: {product_data['sku']}\n"
                
                # Add category if available
                if 'category' in product_data and product_data['category']:
                    response += f"Category: {product_data['category']}\n"
                
                if product_data.get('features'):
                    response += "\nKey Features:\n"
                    response += "\n".join([f"- {feature}" for feature in product_data['features']])
                
                return response

        except Exception as e:
            logger.error(f"Error formatting product response: {e}")
            return "I apologize, but I encountered an error while formatting the product information."

    def get_product_data(self, product_name: str) -> Dict[str, Any]:
        """Retrieve product data from the database"""
        try:
            product = Product.objects.filter(name__icontains=product_name).first()
            if product:
                return {
                    'name': product.name,
                    'description': product.description,
                    'price': float(product.price),
                    'sku': product.sku,
                    'in_stock': True,  # You can add this field to your model
                    'features': [],  # You can add this field to your model
                    'specifications': {}  # You can add this field to your model
                }
            return None
        except Exception as e:
            logger.error(f"Error retrieving product data: {e}")
            return None

    def detect_query_type_from_message(self, query: str) -> str:
        """Identify what kind of information the user is asking for"""
        query_lower = query.lower()
        
        for query_type, patterns in self.query_patterns.items():
            if any(pattern in query_lower for pattern in patterns):
                return query_type
        
        return 'description'  # Default to general description

    def handle_query(self, query: str, product_data: Optional[Dict] = None) -> str:
        """
        Main method to handle product-related queries
        
        Args:
            query: The user's query
            product_data: Optional data about a specific product if already known
        """
        try:
            # If we already have product data from context, use it
            if product_data:
                # Determine what specific information the user is asking about
                query_info = {
                    'query_type': self.detect_query_type_from_message(query),
                    'product_name': product_data['name']
                }
                
                logger.info(f"Using provided product context for {product_data['name']}")
                return self.format_product_response(product_data, query_info)
            
            # Otherwise, extract product from query
            query_info = self.extract_info(query)
            
            if not query_info['product_name']:
                return "I couldn't identify a specific product in your question. Could you please specify which product you're asking about?"

            # Get product data
            product_data = self.get_product_data(query_info['product_name'])
            
            if not product_data:
                return f"I couldn't find any information about '{query_info['product_name']}'. Please check the product name and try again."

            # Format and return the response
            return self.format_product_response(product_data, query_info)

        except Exception as e:
            logger.error(f"Error handling product query: {e}")
            return "I apologize, but I encountered an error while processing your product query." 