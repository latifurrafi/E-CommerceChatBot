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
        logger.info("Chatbot service initialized successfully")

    def process_query(self, query: str) -> str:
        """Process a user query and return a response"""
        try:
            # Clean the query
            query = query.strip()
            if not query:
                return "Please ask a question or provide some details about what you'd like to know."

            # Log the incoming query
            logger.info(f"Processing query: {query}")

            # Get initial response from the appropriate handler
            initial_response = self.query_router.handle_query(query)
            logger.info(f"Initial response: {initial_response}")

            # Enhance the response using the model manager
            enhanced_response = self.model_manager.process_query(query, initial_response)
            logger.info(f"Enhanced response: {enhanced_response}")

            return enhanced_response

        except Exception as e:
            logger.error(f"Error processing query: {e}", exc_info=True)
            return "I apologize, but I encountered an error while processing your request. Please try again."