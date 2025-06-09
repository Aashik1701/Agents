# MongoDB Connection Guide

## 🖥️ MongoDB Compass (GUI)
MongoDB Compass is a free GUI tool for exploring MongoDB data.

### Installation:
```bash
# Download from: https://www.mongodb.com/products/compass
# Or install via Homebrew:
brew install --cask mongodb-compass
```

### Connection:
1. Open MongoDB Compass
2. Use connection string: `mongodb://localhost:27017`
3. Navigate to database: `chatbotDB`
4. Open collection: `faqs`

## 🐚 MongoDB Shell (CLI)
Connect directly to MongoDB using the shell:

```bash
# Connect to local MongoDB
mongosh mongodb://localhost:27017

# Switch to your database
use chatbotDB

# View all FAQs
db.faqs.find().pretty()

# Count documents
db.faqs.count()

# Find specific question
db.faqs.find({"question": "hello"})

# Search questions containing keyword
db.faqs.find({"question": /mongodb/i})

# Show only questions
db.faqs.find({}, {"question": 1, "_id": 0})

# Export data
mongoexport --db=chatbotDB --collection=faqs --out=faqs_export.json
```

## 🐍 Python Scripts

### Quick view all data:
```python
from pymongo import MongoClient
client = MongoClient("mongodb://localhost:27017")
db = client.chatbotDB
for doc in db.faqs.find():
    print(f"Q: {doc['question']}")
    print(f"A: {doc['answer']}")
    print("-" * 40)
```

### Search functionality:
```python
# Search for keyword in questions or answers
keyword = "mongodb"
results = db.faqs.find({
    "$or": [
        {"question": {"$regex": keyword, "$options": "i"}},
        {"answer": {"$regex": keyword, "$options": "i"}}
    ]
})
for doc in results:
    print(f"Q: {doc['question']}")
```
