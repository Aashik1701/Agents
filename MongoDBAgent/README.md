# 🤖 MongoDB Chatbot Agent

A **live MongoDB-powered chatbot** that fetches answers from a real-time database. Add new Q&A pairs dynamically without restarting the application!

## ✨ Features

- **🔄 Real-time Database**: Fetches answers from live MongoDB (local or Atlas)
- **🌐 Web Interface**: Beautiful chat UI with search functionality  
- **📡 RESTful API**: Complete API for FAQ management
- **⚡ Live Updates**: Add FAQs instantly without restart
- **📊 Data Management**: Multiple tools for viewing and managing data
- **🔧 Easy Migration**: Tools for moving data between local and Atlas

## 🚀 Quick Start

### 1. Install Dependencies
```bash
# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

### 2. Start the Application
```bash
python app.py
```

### 3. Access the Chatbot
- **Web Interface**: http://127.0.0.1:5001
- **Database Viewer**: http://127.0.0.1:5001/view_faqs
- **API**: http://127.0.0.1:5001/api/faqs

## 🗄️ Database Configuration

### Current Status
- ✅ **Local MongoDB**: Working (22 FAQs loaded)
- ⏳ **Atlas Connection**: Pending setup (see below)

### MongoDB Atlas Setup

#### 1. Network Access
Add your IP to Atlas whitelist:
- **Your Current IP**: `49.37.214.201`
- Go to Atlas → Network Access → Add IP Address
- Add `49.37.214.201` or `0.0.0.0/0` (less secure)

#### 2. Database Access
Verify your credentials:
- **Username**: `Cluster20526`
- **Password**: `aashik1701`
- **Permissions**: Read and write to any database

#### 3. Get Connection String
1. In Atlas, go to your cluster
2. Click **Connect** → **Connect your application**
3. Copy the connection string
4. Update `config.py` with the correct URI

#### 4. Test Atlas Connection
```bash
python test_atlas_quick.py
```

## 📡 API Endpoints

### Chat & FAQ Management
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main chat interface |
| `/api/ask` | POST | Ask a question |
| `/api/add_faq` | POST | Add new FAQ |
| `/api/faqs` | GET | Get all FAQs (JSON) |
| `/view_faqs` | GET | Web-based FAQ viewer |

### System Info
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/stats` | GET | Database statistics |
| `/health` | GET | Connection status |

### Example API Usage
```bash
# Ask a question
curl -X POST http://127.0.0.1:5001/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "what is your name"}'

# Add new FAQ
curl -X POST http://127.0.0.1:5001/api/add_faq \
  -H "Content-Type: application/json" \
  -d '{"question": "new question", "answer": "new answer"}'
```

## 🛠️ Database Management Tools

### Quick Data Viewer
```bash
python quick_view.py          # Simple CLI viewer
python db_viewer.py           # Interactive explorer
```

### Data Migration & Backup
```bash
python migrate_data.py        # Migration between local/Atlas
```

### Atlas Troubleshooting
```bash
python atlas_troubleshoot.py  # Comprehensive diagnostics
python test_atlas_quick.py    # Quick connection test
```

## 📁 Project Structure

```
MongoDBAgent/
├── app.py                 # Main Flask application
├── config.py              # Database configuration
├── requirements.txt       # Python dependencies
├── templates/
│   └── index.html         # Chat interface
├── static/
│   └── style.css          # UI styling
├── db_viewer.py           # Interactive database explorer
├── quick_view.py          # Simple CLI viewer
├── migrate_data.py        # Data migration tool
├── atlas_troubleshoot.py  # Atlas connection diagnostics
└── test_atlas_quick.py    # Quick Atlas tester
```

## 🔧 Configuration Files

### `config.py`
```python
# MongoDB Atlas Configuration
MONGODB_USERNAME = "Cluster20526"
MONGODB_PASSWORD = "aashik1701"
MONGODB_CLUSTER = "cluster20526.g4udhpz.mongodb.net"
MONGODB_DATABASE = "chatbotDB"

# Connection Control
USE_ATLAS = False  # Set to True when Atlas is configured
```

## 🐛 Troubleshooting

### Atlas Connection Issues

**Problem**: `SSL handshake failed` or `DNS resolution failed`

**Solutions**:
1. **Check Network Access**: Add IP `49.37.214.201` to Atlas whitelist
2. **Verify Credentials**: Confirm username/password in Atlas
3. **Get Correct URI**: Copy connection string from Atlas dashboard
4. **Test Connection**: Run `python test_atlas_quick.py`

### Local MongoDB Issues

**Problem**: `Connection refused` on localhost

**Solutions**:
1. **Install MongoDB**: `brew install mongodb/brew/mongodb-community`
2. **Start Service**: `brew services start mongodb/brew/mongodb-community`
3. **Check Status**: `brew services list | grep mongo`

## 🔄 Data Migration

### From Local to Atlas
```bash
python migrate_data.py
# Select option 3, provide Atlas URI
```

### Create Backup
```bash
python migrate_data.py
# Select option 1 for JSON backup
```

## 📊 Current Database Status

- **Total FAQs**: 22 (including live additions)
- **Connection**: Local MongoDB (`USE_ATLAS = False`)
- **Latest Backup**: `faqs_backup_local_20250609_233945.json`

### Sample Q&A Pairs
1. **Q**: "what is your name" → **A**: "I'm MongoBot, a MongoDB-powered AI agent!"
2. **Q**: "hello" → **A**: "Hi there! How can I help you today?"
3. **Q**: "live database test" → **A**: "Yes! This chatbot fetches answers from a live MongoDB database..."

## 🎯 Next Steps

1. **Atlas Setup**: Add IP `49.37.214.201` to Network Access whitelist
2. **Test Connection**: Run `python test_atlas_quick.py` 
3. **Switch to Atlas**: Set `USE_ATLAS = True` in `config.py`
4. **Migrate Data**: Use `migrate_data.py` to transfer local FAQs to Atlas

## 🚀 Live Demo Features

- **Real-time Updates**: Add FAQs via API, immediately available in chat
- **Multiple Search**: Exact match → Partial match → Text search
- **Web Interface**: Searchable FAQ viewer with modern UI
- **API First**: Complete REST API for integration

---

**Created**: December 2024  
**Status**: ✅ Fully functional with local MongoDB, ⏳ Atlas setup pending

## 🎯 Features

- **MongoDB Integration**: Stores Q&A pairs in MongoDB for fast retrieval
- **Web Interface**: Clean, responsive chat interface
- **Smart Matching**: Supports both exact and partial text matching
- **Real-time Chat**: Instant responses with typing indicators
- **Health Monitoring**: Built-in health check endpoint
- **Easy Setup**: Simple installation and configuration

## 🧰 Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Python, Flask |
| Database | MongoDB |
| Frontend | HTML, CSS, JavaScript |
| ODM | PyMongo |

## 📁 Project Structure

```
MongoDBAgent/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── templates/
│   └── index.html        # Chat interface
├── static/
│   └── style.css         # Styling
└── db/
    └── seed_data.py      # Database setup script
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Navigate to the project directory
cd MongoDBAgent

# Install required packages
pip install -r requirements.txt
```

### 2. Set Up MongoDB

#### Option A: Local MongoDB
```bash
# Install MongoDB (macOS)
brew tap mongodb/brew
brew install mongodb-community

# Start MongoDB service
brew services start mongodb/brew/mongodb-community
```

#### Option B: MongoDB Atlas (Cloud)
1. Create account at [MongoDB Atlas](https://www.mongodb.com/cloud)
2. Create a new cluster
3. Get connection string
4. Update connection strings in `app.py` and `db/seed_data.py`

### 3. Initialize Database

```bash
# Run the database setup script
python db/seed_data.py
```

### 4. Start the Application

```bash
# Run the Flask application
python app.py
```

### 5. Open in Browser

Visit: `http://127.0.0.1:5000/`

## 🛠 Configuration

### MongoDB Connection

Update the connection string in both files:

**For Local MongoDB:**
```python
client = MongoClient("mongodb://localhost:27017/")
```

**For MongoDB Atlas:**
```python
client = MongoClient("mongodb+srv://<username>:<password>@cluster.mongodb.net/chatbotDB?retryWrites=true&w=majority")
```

### Database Structure

The MongoDB collection `faqs` contains documents with this structure:

```json
{
  "_id": ObjectId("..."),
  "question": "hello",
  "answer": "Hi there! How can I help you today?"
}
```

## 📊 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main chat interface |
| `/get` | POST | Send message and get response |
| `/health` | GET | System health check |

### Example API Usage

```javascript
// Send a message
fetch('/get', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message: 'hello' })
})
.then(response => response.json())
.then(data => console.log(data.reply));
```

## 🔧 Customization

### Adding New Q&A Pairs

You can add new questions and answers in several ways:

#### 1. Update seed_data.py
```python
data = [
    {"question": "your question", "answer": "your answer"},
    # Add more here...
]
```

#### 2. Direct MongoDB Insert
```python
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client.chatbotDB
faqs = db.faqs

faqs.insert_one({
    "question": "new question",
    "answer": "new answer"
})
```

#### 3. MongoDB Compass (GUI)
Use MongoDB Compass to manually add documents to the `faqs` collection.

### Improving Search Capabilities

The current implementation supports:
- **Exact matching**: Finds exact question matches
- **Partial matching**: Uses regex for partial matches
- **Case-insensitive**: All searches ignore case

## 🚀 Advanced Features (Future Enhancements)

### 1. Fuzzy Matching
```bash
pip install fuzzywuzzy python-levenshtein
```

### 2. NLP Integration
```bash
pip install spacy sentence-transformers
```

### 3. GPT Fallback
```bash
pip install openai google-generativeai
```

### 4. MongoDB Full-Text Search
```python
# Create text index
faqs.create_index([("question", "text"), ("answer", "text")])

# Search with text index
faqs.find({"$text": {"$search": user_input}})
```

## 🐛 Troubleshooting

### Common Issues

**1. MongoDB Connection Error**
```
pymongo.errors.ServerSelectionTimeoutError
```
- Ensure MongoDB is running
- Check connection string
- Verify network connectivity

**2. Module Not Found**
```
ModuleNotFoundError: No module named 'pymongo'
```
- Run: `pip install -r requirements.txt`

**3. Port Already in Use**
```
OSError: [Errno 48] Address already in use
```
- Change port in `app.py`: `app.run(port=5001)`
- Or kill existing process: `lsof -ti:5000 | xargs kill -9`

### Health Check

Visit `/health` endpoint to check system status:
- ✅ Green: Everything working
- ❌ Red: Database connection issues

## 📝 Sample Questions

Try these sample questions:

- "hello" → Greeting response
- "what is your name" → Bot introduction
- "help" → Help information
- "what is mongodb" → MongoDB explanation
- "joke" → Programming humor
- "bye" → Farewell message

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -am 'Add feature'`
4. Push to branch: `git push origin feature-name`
5. Create Pull Request

## 📄 License

This project is open source and available under the MIT License.

## 🔗 Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [PyMongo Documentation](https://pymongo.readthedocs.io/)
- [MongoDB Documentation](https://docs.mongodb.com/)
- [MongoDB Atlas](https://www.mongodb.com/cloud)

---

**Happy Chatting! 🎉**
