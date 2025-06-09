from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import os
from config import MONGODB_URI, MONGODB_DATABASE, USE_ATLAS, LOCAL_MONGODB_URI

app = Flask(__name__)

# MongoDB connection
if USE_ATLAS:
    # MongoDB Atlas connection
    try:
        client = MongoClient(MONGODB_URI, server_api=ServerApi('1'))
        # Test the connection
        client.admin.command('ping')
        print("✅ Successfully connected to MongoDB Atlas!")
        print(f"🌐 Cluster: cluster20526.g4udhpz.mongodb.net")
    except Exception as e:
        print(f"❌ Failed to connect to Atlas: {e}")
        print("🔄 Falling back to local MongoDB...")
        client = MongoClient(LOCAL_MONGODB_URI)
else:
    # Local MongoDB connection
    client = MongoClient(LOCAL_MONGODB_URI)
    print("🏠 Using local MongoDB connection")

db = client[MONGODB_DATABASE]
faqs = db.faqs

def get_answer(user_input):
    """
    Find answer for user input from MongoDB Atlas (real-time data)
    """
    try:
        user_input = user_input.lower().strip()

        # Method 1: Exact match (case-insensitive)
        record = faqs.find_one({"question": {"$regex": f"^{user_input}$", "$options": "i"}})
        
        if record:
            return record['answer']
        
        # Method 2: Partial match with word boundaries
        record = faqs.find_one({"question": {"$regex": user_input, "$options": "i"}})
        
        if record:
            return record['answer']
        
        # Method 3: Text search (if text index exists)
        try:
            record = faqs.find_one({"$text": {"$search": user_input}})
            if record:
                return record['answer']
        except:
            pass  # Text index might not exist
        
        # Method 4: Check if collection is empty
        total_docs = faqs.count_documents({})
        if total_docs == 0:
            return "🔄 I'm currently learning! Please add some Q&A data to my database first."
        
        # Default response with helpful suggestions
        sample_questions = list(faqs.find({}, {"question": 1, "_id": 0}).limit(3))
        if sample_questions:
            questions_text = ", ".join([f'"{q["question"]}"' for q in sample_questions])
            return f"Sorry, I don't know the answer to that. Try asking: {questions_text}"
        else:
            return "Sorry, I don't know the answer to that. Try asking something else!"
            
    except Exception as e:
        print(f"Error in get_answer: {e}")
        return "I'm having trouble accessing my knowledge base. Please try again."

@app.route("/")
def home():
    """
    Render the main chat interface
    """
    return render_template("index.html")

@app.route("/get", methods=["POST"])
def respond():
    """
    Handle chat messages and return bot responses
    """
    user_input = request.json.get("message")
    if not user_input:
        return jsonify({"reply": "Please enter a message."})
    
    response = get_answer(user_input)
    return jsonify({"reply": response})

@app.route("/health")
def health():
    """
    Health check endpoint with database statistics
    """
    try:
        # Test MongoDB connection
        client.admin.command('ping')
        
        # Get collection stats
        total_faqs = faqs.count_documents({})
        
        # Get connection info
        connection_type = "MongoDB Atlas" if USE_ATLAS else "Local MongoDB"
        
        return jsonify({
            "status": "healthy", 
            "database": "connected",
            "connection_type": connection_type,
            "total_faqs": total_faqs,
            "database_name": MONGODB_DATABASE,
            "collection_name": "faqs"
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/stats")
def stats():
    """
    Get database statistics
    """
    try:
        total_faqs = faqs.count_documents({})
        sample_questions = list(faqs.find({}, {"question": 1, "_id": 0}).limit(5))
        
        return jsonify({
            "total_faqs": total_faqs,
            "sample_questions": [q["question"] for q in sample_questions],
            "database": MONGODB_DATABASE,
            "connection_type": "MongoDB Atlas" if USE_ATLAS else "Local MongoDB"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/add_faq", methods=["POST"])
def add_faq():
    """
    Add new FAQ to the database (for real-time updates)
    """
    try:
        data = request.json
        question = data.get("question", "").strip()
        answer = data.get("answer", "").strip()
        
        if not question or not answer:
            return jsonify({"error": "Both question and answer are required"}), 400
        
        # Check if question already exists
        existing = faqs.find_one({"question": {"$regex": f"^{question}$", "$options": "i"}})
        if existing:
            return jsonify({"error": "Question already exists"}), 400
        
        # Insert new FAQ
        result = faqs.insert_one({"question": question.lower(), "answer": answer})
        
        return jsonify({
            "message": "FAQ added successfully",
            "id": str(result.inserted_id),
            "question": question,
            "answer": answer
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/view_faqs")
def view_faqs():
    """
    Web interface to view all FAQs in the database
    """
    try:
        # Get all FAQs
        all_faqs = list(faqs.find({}).sort('_id', 1))
        
        # Convert ObjectId to string for display
        for faq in all_faqs:
            faq['_id'] = str(faq['_id'])
        
        # Create HTML response
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>MongoDB FAQs Viewer</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
                .container { max-width: 1000px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .header { background: #4CAF50; color: white; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
                .stats { background: #e8f5e9; padding: 10px; border-radius: 5px; margin-bottom: 20px; }
                .faq-item { border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px; background: #fafafa; }
                .question { font-weight: bold; color: #2e7d32; margin-bottom: 8px; }
                .answer { color: #333; line-height: 1.4; }
                .id { font-size: 11px; color: #666; margin-top: 8px; }
                .search-box { width: 100%; padding: 10px; margin-bottom: 20px; border: 1px solid #ddd; border-radius: 5px; }
                .actions { margin-bottom: 20px; }
                .btn { background: #4CAF50; color: white; padding: 8px 15px; border: none; border-radius: 3px; cursor: pointer; margin-right: 10px; text-decoration: none; display: inline-block; }
                .btn:hover { background: #45a049; }
            </style>
            <script>
                function filterFAQs() {
                    const searchTerm = document.getElementById('searchBox').value.toLowerCase();
                    const faqItems = document.querySelectorAll('.faq-item');
                    
                    faqItems.forEach(item => {
                        const question = item.querySelector('.question').textContent.toLowerCase();
                        const answer = item.querySelector('.answer').textContent.toLowerCase();
                        
                        if (question.includes(searchTerm) || answer.includes(searchTerm)) {
                            item.style.display = 'block';
                        } else {
                            item.style.display = 'none';
                        }
                    });
                }
            </script>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🗄️ MongoDB FAQs Database Viewer</h1>
                    <p>Real-time view of your chatbot's knowledge base</p>
                </div>
                
                <div class="stats">
                    <strong>📊 Database Stats:</strong> 
                    {total_faqs} FAQs | Database: {database} | Connection: {connection_type}
                </div>
                
                <div class="actions">
                    <a href="/" class="btn">🏠 Back to Chat</a>
                    <a href="/stats" class="btn">📈 API Stats</a>
                    <button onclick="location.reload()" class="btn">🔄 Refresh</button>
                </div>
                
                <input type="text" id="searchBox" class="search-box" placeholder="🔍 Search FAQs..." onkeyup="filterFAQs()">
                
                <div class="faqs">
                    {faq_items}
                </div>
            </div>
        </body>
        </html>
        """
        
        # Generate FAQ items HTML
        faq_items_html = ""
        for i, faq in enumerate(all_faqs, 1):
            faq_items_html += f"""
            <div class="faq-item">
                <div class="question">#{i}. Q: {faq['question']}</div>
                <div class="answer">A: {faq['answer']}</div>
                <div class="id">ID: {faq['_id']}</div>
            </div>
            """
        
        # Fill in the template
        html = html.format(
            total_faqs=len(all_faqs),
            database=MONGODB_DATABASE,
            connection_type="MongoDB Atlas" if USE_ATLAS else "Local MongoDB",
            faq_items=faq_items_html
        )
        
        return html
        
    except Exception as e:
        return f"<h1>Error viewing FAQs</h1><p>{str(e)}</p>", 500

@app.route("/api/faqs")
def api_faqs():
    """
    JSON API endpoint to get all FAQs
    """
    try:
        all_faqs = list(faqs.find({}).sort('_id', 1))
        
        # Convert ObjectId to string for JSON serialization
        for faq in all_faqs:
            faq['_id'] = str(faq['_id'])
        
        return jsonify({
            "total": len(all_faqs),
            "faqs": all_faqs,
            "database": MONGODB_DATABASE,
            "connection_type": "MongoDB Atlas" if USE_ATLAS else "Local MongoDB"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    print("🚀 Starting MongoDB Chatbot...")
    print(f"💾 Database: {MONGODB_DATABASE}")
    print("📊 Collection: faqs")
    print(f"🌐 Connection: {'MongoDB Atlas' if USE_ATLAS else 'Local MongoDB'}")
    print("🔗 Endpoints:")
    print("   • http://127.0.0.1:5001/ - Chat interface")
    print("   • http://127.0.0.1:5001/health - Health check")
    print("   • http://127.0.0.1:5001/stats - Database stats")
    print("   • http://127.0.0.1:5001/add_faq - Add new FAQ (POST)")
    app.run(debug=True, host='0.0.0.0', port=5001)
