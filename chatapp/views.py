from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .chatbot_service import ChatbotService
import json
import logging

logger = logging.getLogger(__name__)

# Initialize chatbot service
chatbot_service = None

def initialize_chatbot():
    global chatbot_service
    try:
        chatbot_service = ChatbotService()
        logger.info("Chatbot service initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize chatbot service: {str(e)}")
        raise

# Initialize chatbot when the module is loaded
try:
    initialize_chatbot()
except Exception as e:
    logger.error(f"Failed to initialize chatbot during module load: {str(e)}")

@csrf_exempt
def process_message(request):
    """
    Process incoming chat messages and return responses
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            message = data.get('message', '')
            product_id = request.GET.get('product_id')
            
            if not message:
                return JsonResponse({'error': 'No message provided'}, status=400)
            
            if not chatbot_service:
                initialize_chatbot()
            
            response = chatbot_service.process_query(message, product_id)
            return JsonResponse({'response': response})
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return JsonResponse({'error': 'Internal server error'}, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)
