# chatbot_gpt.py - Alternative chatbot with OpenAI GPT support
import openai
import os

# Set your OpenAI API key here or in environment variable
openai.api_key = os.getenv('OPENAI_API_KEY', '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')

def get_response(user_input):
    """
    Get response using OpenAI's GPT model
    Make sure to set your OPENAI_API_KEY environment variable
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful and friendly assistant. Keep your responses concise and helpful."},
                {"role": "user", "content": user_input}
            ],
            max_tokens=150,
            temperature=0.7
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        return f"Sorry, I'm having trouble connecting to my AI brain. Error: {str(e)}"
