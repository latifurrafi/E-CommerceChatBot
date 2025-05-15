import requests
import json
import time

def test_chatbot():
    base_url = "http://localhost:8000"
    test_queries = [
        "What are your best-selling products?",
        "I want to track my order #12345",
        "Do you have any discounts on electronics?",
        "What's your return policy?",
        "Can you help me find a laptop under $1000?"
    ]
    
    print("Starting chatbot tests...")
    print("Waiting for server to start...")
    time.sleep(5)  # Give the server some time to start
    
    for query in test_queries:
        try:
            print(f"\nSending query: {query}")
            response = requests.post(
                f"{base_url}/process_message/",
                json={"message": query},
                headers={"Content-Type": "application/json"}
            )
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"Response: {result.get('response', 'No response field found')}")
            else:
                print(f"Error Response: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print(f"Connection failed. Make sure the server is running on {base_url}")
        except Exception as e:
            print(f"Error testing query '{query}': {str(e)}")
            
    print("\nTest completed!")

if __name__ == "__main__":
    test_chatbot() 