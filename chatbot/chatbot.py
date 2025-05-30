# chatbot.py

def get_response(user_input):
    user_input = user_input.lower()

    if "hello" in user_input or "hi" in user_input:
        return "Hello! How can I help you today?"
    elif "your name" in user_input or "what's your name" in user_input:
        return "I'm your friendly chatbot!"
    elif "how are you" in user_input:
        return "I'm doing great! Thanks for asking. How can I assist you?"
    elif "what can you do" in user_input or "help" in user_input:
        return "I can chat with you, answer basic questions, and help with simple tasks. Try asking me about myself or saying hello!"
    elif "weather" in user_input:
        return "I don't have access to real-time weather data, but I hope it's nice where you are!"
    elif "time" in user_input:
        return "I don't have access to the current time, but you can check your device's clock!"
    elif "thank" in user_input:
        return "You're welcome! I'm happy to help."
    elif "bye" in user_input or "goodbye" in user_input:
        return "Goodbye! Have a great day!"
    else:
        return "I'm not sure how to answer that. Try asking me something else or type 'help' for suggestions!"
