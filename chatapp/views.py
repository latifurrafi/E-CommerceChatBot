from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import logging
from ecommerce.models import Product  # Import Product model for integration

from .chatbot_service import ChatbotService

# Initialize the chatbot service
chatbot = None

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def initialize_chatbot():
    """Initialize the chatbot service only once"""
    global chatbot
    if chatbot is None:
        try:
            logger.info("Initializing chatbot service...")
            chatbot = ChatbotService()
            logger.info("Chatbot service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize chatbot: {e}", exc_info=True)
            return False
    return True

def chat_view(request):
    """Render the chat interface"""
    if not initialize_chatbot():
        return render(request, 'error.html', {'error': 'Failed to initialize chatbot'})
    
    context = {}
    
    # Check if there's a product parameter in the query string
    product_id = request.GET.get('product')
    if product_id:
        try:
            product = Product.objects.get(pk=product_id)
            context['product'] = product
            context['initial_message'] = f"Hi, I'd like to know more about the {product.name}."
        except (Product.DoesNotExist, ValueError):
            # If product doesn't exist, ignore and show normal chat
            pass
    
    return render(request, 'chat.html', context)

@csrf_exempt
def process_message(request):
    """Process a chat message and return a response"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)
    
    if not initialize_chatbot():
        return JsonResponse({'error': 'Chatbot service unavailable'}, status=500)
    
    try:
        # Parse request body
        data = json.loads(request.body)
        
        query = data.get('message', '').strip()
        
        if not query:
            return JsonResponse({'error': 'Empty message'}, status=400)
        
        # Check for product context in the query parameters
        product_id = request.GET.get('product_id')
        product_context = None
        
        if product_id:
            try:
                product = Product.objects.get(pk=product_id)
                product_context = {
                    'id': product.id,
                    'name': product.name,
                    'description': product.description,
                    'price': float(product.price),
                    'category': product.category.name if product.category else None,
                    'sku': product.sku,
                    'stock': product.stock,
                }
                # Pass the product context to the chatbot
                response = chatbot.process_query(query, product_context=product_context)
            except (Product.DoesNotExist, ValueError):
                # If product doesn't exist, proceed without context
                response = chatbot.process_query(query)
        else:
            # Process the query normally
            response = chatbot.process_query(query)
        
        # Ensure response is JSON serializable
        if not isinstance(response, (str, int, float, bool, list, dict)):
            response = str(response)
        
        return JsonResponse({'response': response})
    
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        return JsonResponse({
            'error': 'Internal server error',
            'message': str(e)
        }, status=500)
