import google.generativeai as genai
from typing import Dict, Any, List, Tuple
import logging
import os
from dotenv import load_dotenv

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
        print(self.api_key)
        if not self.api_key:
            logger.error("GEMINI_API_KEY not found in environment variables")
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        # Log the first few characters of the API key for debugging (safely)
        logger.info(f"API key loaded (first 4 chars): {self.api_key[:4]}...")
        
        try:
            # Configure the Gemini API
            genai.configure(api_key=self.api_key)
            
            # Test the API key with a simple generation
            test_model = genai.GenerativeModel('gemini-2.0-flash')
            test_response = test_model.generate_content("Test connection")
            if test_response:
                logger.info("Successfully connected to Gemini API")
            
            # Store the model instance
            self.model = test_model
            
        except Exception as e:
            logger.error(f"Error initializing Gemini model: {str(e)}")
            if "API_KEY_INVALID" in str(e):
                logger.error("API key validation failed. Please check if the key is correctly formatted and has the necessary permissions.")
            elif "NOT_FOUND" in str(e):
                logger.error("Model 'gemini-2.0-flash' not found. Please check if the model is available in your region.")
            raise
        
        # Define prompt templates
        self.prompt_templates = {
            'query_refinement': """
            As an AI assistant for an e-commerce platform, help me understand and refine this user query.
            Original query: "{query}"
            
            Please analyze the query and provide:
            1. Main intent (product info, order status, general help, etc.)
            2. Key entities mentioned
            3. Specific attributes requested
            4. Any ambiguities that need clarification
            5. A refined, clear version of the query
            
            Format the response as a JSON-like structure.
            """,
            
            'response_enhancement': """
            I have a raw response from our e-commerce system that needs to be enhanced to sound more natural and helpful.
            
            Original query: "{query}"
            Raw response: "{raw_response}"
            
            Please enhance this response to:
            1. Sound more conversational and friendly
            2. Add relevant context if needed
            3. Suggest related information that might be helpful
            4. Maintain all factual information from the original response
            
            Provide the enhanced response in a clear, well-formatted way.
            """,
            
            'context_generation': """
            Help me generate relevant context for this e-commerce query.
            Query: "{query}"
            
            Consider:
            1. Related products
            2. Common questions about this topic
            3. Relevant policies or FAQs
            4. Potential follow-up questions
            
            Provide a concise summary of relevant context.
            """
        }

    def refine_query(self, query: str) -> Dict[str, Any]:
        """Refine and analyze the user query using Gemini"""
        try:
            # Generate the prompt
            prompt = self.prompt_templates['query_refinement'].format(query=query)
            
            # Get response from Gemini
            response = self.model.generate_content(prompt)
            
            # Parse the response
            refined_info = self._parse_refinement_response(response.text)
            
            return refined_info

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
            # Generate the prompt
            prompt = self.prompt_templates['response_enhancement'].format(
                query=query,
                raw_response=raw_response
            )
            
            # Get enhanced response
            response = self.model.generate_content(prompt)
            
            return response.text

        except Exception as e:
            logger.error(f"Error enhancing response: {e}")
            return raw_response

    def generate_context(self, query: str) -> str:
        """Generate additional context for the query"""
        try:
            # Generate the prompt
            prompt = self.prompt_templates['context_generation'].format(query=query)
            
            # Get context
            response = self.model.generate_content(prompt)
            
            return response.text

        except Exception as e:
            logger.error(f"Error generating context: {e}")
            return ""

    def _parse_refinement_response(self, response_text: str) -> Dict[str, Any]:
        """Parse the refinement response from Gemini"""
        try:
            # Basic parsing - you might want to improve this based on actual response format
            lines = response_text.split('\n')
            refined_info = {
                'intent': '',
                'entities': [],
                'attributes': [],
                'ambiguities': [],
                'refined_query': ''
            }
            
            current_section = ''
            for line in lines:
                line = line.strip()
                if 'intent:' in line.lower():
                    refined_info['intent'] = line.split(':', 1)[1].strip()
                elif 'entities:' in line.lower():
                    current_section = 'entities'
                elif 'attributes:' in line.lower():
                    current_section = 'attributes'
                elif 'ambiguities:' in line.lower():
                    current_section = 'ambiguities'
                elif 'refined query:' in line.lower():
                    refined_info['refined_query'] = line.split(':', 1)[1].strip()
                elif line and current_section:
                    if line.startswith('- '):
                        refined_info[current_section].append(line[2:])
            
            return refined_info

        except Exception as e:
            logger.error(f"Error parsing refinement response: {e}")
            return {
                'intent': 'unknown',
                'entities': [],
                'attributes': [],
                'ambiguities': [],
                'refined_query': ''
            }

    def process_query(self, query: str, handler_response: str) -> str:
        """Main method to process a query through the model pipeline"""
        try:
            # Step 1: Refine the query
            refined_info = self.refine_query(query)
            logger.info(f"Refined query info: {refined_info}")
            
            # Step 2: Generate additional context
            additional_context = self.generate_context(refined_info.get('refined_query', query))
            logger.info(f"Generated context: {additional_context}")
            
            # Step 3: Enhance the response
            enhanced_response = self.enhance_response(
                refined_info.get('refined_query', query),
                handler_response
            )
            
            # Step 4: Combine everything into a well-formatted response
            final_response = enhanced_response
            
            # Add relevant context if available
            if additional_context:
                final_response += f"\n\nAdditional Information:\n{additional_context}"
            
            return final_response

        except Exception as e:
            logger.error(f"Error in query processing pipeline: {e}")
            return handler_response  # Return original response if enhancement fails
