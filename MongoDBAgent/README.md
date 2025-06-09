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
