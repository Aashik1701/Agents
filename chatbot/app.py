from flask import Flask, render_template, request, jsonify
from chatbot_gemini import get_response  # Using Gemini-powered chatbot

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/get", methods=["POST"])
def chatbot_response():
    user_input = request.json.get("message")
    response = get_response(user_input)
    return jsonify({"reply": response})

if __name__ == "__main__":
    app.run(debug=True, port=5004)
