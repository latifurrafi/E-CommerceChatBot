from typing import Dict, Any, List
import logging
from ..models import Order, OrderItem

logger = logging.getLogger(__name__)

class OrderHandler:
    def __init__(self):
        self.query_patterns = {
            'status': ['status', 'where is', 'track', 'when will'],
            'details': ['details', 'what did', 'items', 'products in'],
            'cancel': ['cancel', 'stop', 'return'],
            'modify': ['change', 'modify', 'update'],
            'payment': ['payment', 'paid', 'refund', 'charge']
        }

    def extract_info(self, query: str) -> Dict[str, Any]:
        """Extract order-related information from the query"""
        query_lower = query.lower().strip()
        info = {
            'query_type': None,
            'order_number': None,
            'specific_detail': None
        }

        # Detect query type
        for query_type, patterns in self.query_patterns.items():
            if any(pattern in query_lower for pattern in patterns):
                info['query_type'] = query_type
                break

        # Extract order number (assuming format: #1234 or order 1234)
        import re
        order_patterns = [
            r'#(\d+)',
            r'order\s+(\d+)',
            r'order\s*number\s*(\d+)',
            r'order\s*id\s*(\d+)'
        ]

        for pattern in order_patterns:
            match = re.search(pattern, query_lower)
            if match:
                info['order_number'] = match.group(1)
                break

        return info

    def get_order_data(self, order_number: str) -> Dict[str, Any]:
        """Retrieve order data from the database"""
        try:
            order = Order.objects.filter(order_number=order_number).first()
            if order:
                # Get order items
                items = OrderItem.objects.filter(order=order)
                items_data = [{
                    'product_name': item.product.name,
                    'quantity': item.quantity,
                    'price': float(item.price)
                } for item in items]

                return {
                    'order_number': order.order_number,
                    'customer_name': order.customer_name,
                    'status': order.status,
                    'total_amount': float(order.total_amount),
                    'created_at': order.created_at,
                    'items': items_data
                }
            return None
        except Exception as e:
            logger.error(f"Error retrieving order data: {e}")
            return None

    def format_order_response(self, order_data: Dict[str, Any], query_info: Dict[str, Any]) -> str:
        """Format the response based on the query type and order data"""
        try:
            if not order_data:
                return "I couldn't find any information about that order. Please check the order number and try again."

            query_type = query_info.get('query_type')

            if query_type == 'status':
                created_date = order_data['created_at'].strftime('%Y-%m-%d')
                return (
                    f"Order #{order_data['order_number']} status: {order_data['status'].upper()}\n"
                    f"Ordered on: {created_date}\n"
                    f"Customer: {order_data['customer_name']}"
                )

            elif query_type == 'details':
                response = f"Order #{order_data['order_number']} details:\n\n"
                response += f"Customer: {order_data['customer_name']}\n"
                response += f"Status: {order_data['status'].upper()}\n"
                response += f"Total Amount: ${order_data['total_amount']:.2f}\n\n"
                response += "Items:\n"
                for item in order_data['items']:
                    response += f"- {item['quantity']}x {item['product_name']} (${item['price']:.2f} each)\n"
                return response

            elif query_type == 'cancel':
                if order_data['status'] == 'delivered':
                    return "This order has already been delivered and cannot be cancelled. Please refer to our return policy for more information."
                elif order_data['status'] == 'cancelled':
                    return "This order has already been cancelled."
                else:
                    return (
                        f"To cancel order #{order_data['order_number']}, please contact our customer service. "
                        f"Current status: {order_data['status'].upper()}"
                    )

            elif query_type == 'modify':
                if order_data['status'] in ['shipped', 'delivered']:
                    return f"Order #{order_data['order_number']} cannot be modified as it has already been {order_data['status']}."
                return "To modify your order, please contact our customer service with your order number."

            elif query_type == 'payment':
                return f"Order #{order_data['order_number']} total amount: ${order_data['total_amount']:.2f}"

            else:
                # Default to full order details
                return self.format_order_response(order_data, {'query_type': 'details'})

        except Exception as e:
            logger.error(f"Error formatting order response: {e}")
            return "I apologize, but I encountered an error while formatting the order information."

    def handle_query(self, query: str) -> str:
        """Main method to handle order-related queries"""
        try:
            # Extract information from the query
            query_info = self.extract_info(query)
            
            if not query_info['order_number']:
                return "Could you please provide an order number? (Format: #1234 or 'order 1234')"

            # Get order data
            order_data = self.get_order_data(query_info['order_number'])
            
            if not order_data:
                return f"I couldn't find any order with number #{query_info['order_number']}. Please check the number and try again."

            # Format and return the response
            return self.format_order_response(order_data, query_info)

        except Exception as e:
            logger.error(f"Error handling order query: {e}")
            return "I apologize, but I encountered an error while processing your order query." 