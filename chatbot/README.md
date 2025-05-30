# Chatbot Project

A simple chatbot built with Python Flask that can answer user questions through a web interface.

## Features

- Clean, modern web interface
- Rule-based chatbot responses
- Real-time chat functionality
- Responsive design
- Optional OpenAI GPT integration

## Project Structure

```
chatbot/
├── app.py                # Flask backend
├── templates/
│   └── index.html        # Frontend chat UI
├── static/
│   └── style.css         # Styling
├── chatbot.py            # Rule-based chat logic
├── chatbot_gpt.py        # GPT-powered chat logic (optional)
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## Setup and Installation

1. **Clone or download the project files**

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application:**
   ```bash
   python app.py
   ```

4. **Open your browser and go to:**
   ```
   http://127.0.0.1:5000/
   ```

## Using Google Gemini (Optional)

To use the Gemini-powered chatbot instead of the rule-based one:

1. **Get a Gemini API key** from [Google AI Studio](https://makersuite.google.com/app/apikey)

2. **Set your API key as an environment variable:**
   ```bash
   export GEMINI_API_KEY="your_api_key_here"
   ```

3. **Modify app.py** to import from `chatbot_gemini` instead of `chatbot`:
   ```python
   from chatbot_gemini import get_response  # Change this line
   ```

## Customization

- **Add more responses:** Edit `chatbot.py` to add more rule-based responses
- **Modify the UI:** Edit `templates/index.html` and `static/style.css`
- **Add features:** Extend the Flask app in `app.py`

## Future Enhancements

- User sessions and chat history
- Integration with messaging platforms
- Voice input/output
- Sentiment analysis
- Database storage for conversations

## Troubleshooting

- Make sure all dependencies are installed: `pip install -r requirements.txt`
- Check that Flask is running on the correct port (5000 by default)
- For GPT functionality, ensure your OpenAI API key is correctly set

Enjoy chatting with your bot! 🤖
