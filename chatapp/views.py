from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import logging

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
    
    return render(request, 'chat.html')

@csrf_exempt
def process_message(request):
    """Process a chat message and return a response"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)
    
    if not initialize_chatbot():
        return JsonResponse({'error': 'Chatbot service unavailable'}, status=500)
    
    try:
        # Parse request body
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        
        query = data.get('message', '').strip()
        
        if not query:
            return JsonResponse({'error': 'Empty message'}, status=400)
        
        # Process the query
        response = chatbot.process_query(query)
        
        # Ensure response is JSON serializable
        if not isinstance(response, (str, int, float, bool, list, dict)):
            response = str(response)
        
        return JsonResponse({'response': response})
    
    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        return JsonResponse({
            'error': 'Internal server error',
            'message': str(e)
        }, status=500)
