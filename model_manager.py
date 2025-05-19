import google.generativeai as genai
from typing import Dict, Any, List, Tuple
import logging
import os
from dotenv import load_dotenv
import json
import re

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ModelManager:
    def __init__(self):
        """Initialize the model manager with Gemini API"""
        # Load environment variables
        load_dotenv()
        
        # Initialize Gemini API
        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            logger.error("GEMINI_API_KEY not found in environment variables")
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        # Log the first few characters of the API key for debugging (safely)
        logger.info(f"API key loaded (first 4 chars): {self.api_key[:4]}...")
        
        try:
            # Configure the Gemini API
            genai.configure(api_key=self.api_key)
            
            # Test the API key with a simple generation
            test_model = genai.GenerativeModel('gemini-2.0-flash')  # Using gemini-pro as it's the standard model
            test_response = test_model.generate_content("Test connection")
            if test_response:
                logger.info("Successfully connected to Gemini API")
            
            # Store the model instance
            self.model = test_model
            
        except Exception as e:
            logger.error(f"Error initializing Gemini model: {str(e)}")
            if "API_KEY_INVALID" in str(e):
                logger.error("API key validation failed. Please check if the key is correctly formatted and has the necessary permissions.")
            raise
        
        # Define prompt templates with improved structure and instructions
        self.prompt_templates = {
            'query_refinement': """You are an AI assistant for an e-commerce platform. Analyze this user query:
            "{query}"
            
            Provide the following information in JSON format:
            {
                "intent": "product_info|order_status|general_help|price_query|availability|feedback|comparison",
                "product_category": "specific product category if mentioned",
                "specific_product": "specific product name if mentioned",
                "attributes": ["list of specific attributes mentioned"],
                "constraints": ["list of constraints like price, brand, etc."],
                "user_context": "previous_purchase|browsing|new_user",
                "refined_query": "clear and specific version of the query"
            }""",
            
            'response_enhancement': """You are a helpful e-commerce assistant. Enhance this product information response:

            QUERY: "{query}"
            ORIGINAL RESPONSE: "{raw_response}"
            
            Rules:
            1. Start with a friendly, personalized greeting
            2. Structure the response clearly:
               - Main answer/recommendation
               - Key features and benefits
               - Pricing and availability
               - Related suggestions (max 2)
            3. Use markdown for formatting:
               - **Bold** for important points
               - * Bullet points for lists
               - > Blockquotes for highlights
            4. End with a clear call-to-action
            5. Keep it concise but informative
            6. Only include factual information from the original response""",
            
            'context_generation': """Generate relevant context for an e-commerce query:
            QUERY: "{query}"
            
            Focus on:
            1. User Intent Analysis
            2. Product Category Context
            3. Relevant Features/Specs
            4. Purchase Considerations
            5. Related Categories
            
            Format as JSON:
            {
                "user_intent": "string",
                "category_context": ["list"],
                "key_features": ["list"],
                "considerations": ["list"],
                "related_categories": ["list"]
            }"""
        }

    def refine_query(self, query: str) -> Dict[str, Any]:
        """Refine and analyze the user query using Gemini"""
        try:
            prompt = self.prompt_templates['query_refinement'].format(query=query)
            response = self.model.generate_content(prompt)
            return self._parse_refinement_response(response.text)
        except Exception as e:
            logger.error(f"Error refining query: {e}")
            return {
                'original_query': query,
                'intent': 'unknown',
                'entities': [],
                'attributes': [],
                'refined_query': query
            }

    def enhance_response(self, query: str, raw_response: str) -> str:
        """Enhance the raw response using Gemini"""
        try:
            prompt = self.prompt_templates['response_enhancement'].format(
                query=query,
                raw_response=raw_response
            )
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Error enhancing response: {e}")
            return raw_response

    def generate_context(self, query: str) -> Dict[str, Any]:
        """Generate additional context for the query"""
        try:
            prompt = self.prompt_templates['context_generation'].format(query=query)
            response = self.model.generate_content(prompt)
            
            # Parse JSON response
            context_match = re.search(r'\{[\s\S]*\}', response.text)
            if context_match:
                return json.loads(context_match.group(0))
            return {}
        except Exception as e:
            logger.error(f"Error generating context: {e}")
            return {}

    def _parse_refinement_response(self, response_text: str) -> Dict[str, Any]:
        """Parse the refinement response from Gemini"""
        default_response = {
            'intent': 'unknown',
            'product_category': '',
            'specific_product': '',
            'attributes': [],
            'constraints': [],
            'user_context': 'new_user',
            'refined_query': ''
        }
        
        try:
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                parsed_data = json.loads(json_match.group(0))
                # Update default_response with parsed data
                for key in default_response.keys():
                    if key in parsed_data:
                        default_response[key] = parsed_data[key]
                logger.info(f"Successfully parsed refinement response")
            return default_response
        except Exception as e:
            logger.error(f"Error parsing refinement response: {e}")
            return default_response

    def process_query(self, query: str, handler_response: str) -> str:
        """Process a query through the enhanced model pipeline"""
        try:
            # Step 1: Refine the query
            refined_info = self.refine_query(query)
            logger.info(f"Refined query info: {refined_info}")
            
            # Step 2: Generate context
            context_info = self.generate_context(refined_info.get('refined_query', query))
            logger.info(f"Generated context: {context_info}")
            
            # Step 3: Enhance the response with context
            enhanced_response = self.enhance_response(
                refined_info.get('refined_query', query),
                f"{handler_response}\n\nContext: {json.dumps(context_info, indent=2)}"
            )
            
            return enhanced_response
        except Exception as e:
            logger.error(f"Error in query processing pipeline: {e}")
            return handler_response
