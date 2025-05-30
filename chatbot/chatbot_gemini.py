# chatbot_gemini.py - Chatbot with Google Gemini API support
import os
import requests

# Configure Gemini API
# Set your Gemini API key here or in environment variable
import requests

def get_response(user_input):
    """
    Get response using Google's Gemini model
    Make sure to set your GEMINI_API_KEY environment variable
    """
    api_key = os.getenv('GEMINI_API_KEY', 'AIzaSyAqib60Hqzz36ygA5cv4QRl8y6CKO9spLs')
    
    try:
        # Try direct REST API approach to bypass referrer restrictions
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={api_key}"
        
        headers = {
            'Content-Type': 'application/json',
        }
        
        data = {
            "contents": [{
                "parts": [{
                    "text": f"You are a helpful and friendly assistant. Keep your responses concise and helpful. User question: {user_input}"
                }]
            }],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 150
            }
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if 'candidates' in result and len(result['candidates']) > 0:
                text = result['candidates'][0]['content']['parts'][0]['text']
                return text.strip()
            else:
                return "🤖 I received an empty response. Please try again."
        else:
            error_info = response.json() if response.content else {"error": "Unknown error"}
            if response.status_code == 403:
                return "🔒 API Access Denied: Please check your Gemini API key permissions and restrictions in Google AI Studio."
            elif response.status_code == 400:
                return "🔧 Invalid request: There might be an issue with the request format."
            else:
                return f"🚨 API Error ({response.status_code}): {error_info.get('error', {}).get('message', 'Unknown error')}"
    
    except requests.exceptions.Timeout:
        return "⏰ Request timeout: The API is taking too long to respond. Please try again."
    except requests.exceptions.ConnectionError:
        return "🌐 Connection error: Unable to connect to Gemini API. Please check your internet connection."
    except Exception as e:
        error_msg = str(e)
        if "API_KEY_HTTP_REFERRER_BLOCKED" in error_msg:
            return "🔒 API Key Issue: The Gemini API key has referrer restrictions. Please check the API key configuration in Google AI Studio to allow requests from localhost or remove referrer restrictions."
        elif "403" in error_msg:
            return "🔑 Permission denied: Please check your Gemini API key permissions and quota."
        elif "API_KEY_INVALID" in error_msg:
            return "❌ Invalid API key: Please check your Gemini API key."
        else:
            return f"🤖 AI connection issue: {error_msg[:100]}..."
