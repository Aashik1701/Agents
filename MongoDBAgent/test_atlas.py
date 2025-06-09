from pymongo import MongoClient
from pymongo.server_api import ServerApi
from config import MONGODB_URI, MONGODB_DATABASE, USE_ATLAS, LOCAL_MONGODB_URI

def test_atlas_connection():
    """
    Test MongoDB Atlas connection
    """
    print("🔧 Testing MongoDB Atlas Connection...")
    print("=" * 50)
    
    try:
        # Create client with Atlas URI
        client = MongoClient(MONGODB_URI, server_api=ServerApi('1'))
        
        # Test connection
        client.admin.command('ping')
        print("✅ Successfully connected to MongoDB Atlas!")
        
        # Get database info
        db = client[MONGODB_DATABASE]
        faqs = db.faqs
        
        # Check existing data
        total_docs = faqs.count_documents({})
        print(f"📊 Current FAQ count: {total_docs}")
        
        if total_docs > 0:
            print("\n🔍 Sample questions in database:")
            for i, doc in enumerate(faqs.find({}, {"question": 1, "_id": 0}).limit(5), 1):
                print(f"   {i}. {doc['question']}")
        else:
            print("📝 Database is empty. You can:")
            print("   1. Add FAQs through the web interface (/add_faq endpoint)")
            print("   2. Run seed_atlas_data.py to add initial data")
            print("   3. Import data from your existing source")
        
        # Test basic operations
        print(f"\n🏗️ Database: {MONGODB_DATABASE}")
        print(f"📁 Collection: faqs")
        print(f"🌐 Cluster: cluster20526.g4udhpz.mongodb.net")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\n💡 Troubleshooting:")
        print("   1. Check your username and password in config.py")
        print("   2. Ensure your IP is whitelisted in Atlas")
        print("   3. Verify the connection string is correct")
        return False

def seed_minimal_data():
    """
    Add minimal data to get started (optional)
    """
    try:
        client = MongoClient(MONGODB_URI, server_api=ServerApi('1'))
        db = client[MONGODB_DATABASE]
        faqs = db.faqs
        
        # Check if data already exists
        if faqs.count_documents({}) > 0:
            print("⚠️  Data already exists. Skipping seed.")
            return
        
        # Minimal starter data
        starter_data = [
            {"question": "hello", "answer": "Hi! I'm connected to MongoDB Atlas. How can I help you?"},
            {"question": "help", "answer": "I'm a real-time chatbot powered by MongoDB Atlas. Ask me anything!"},
            {"question": "test", "answer": "✅ Atlas connection is working perfectly!"},
        ]
        
        result = faqs.insert_many(starter_data)
        print(f"✅ Added {len(result.inserted_ids)} starter FAQs to Atlas database")
        
        client.close()
        
    except Exception as e:
        print(f"❌ Failed to seed data: {e}")

if __name__ == "__main__":
    print("🧪 MongoDB Atlas Connection Test")
    print("================================")
    
    if test_atlas_connection():
        print("\n🎉 Atlas connection successful!")
        
        # Ask if user wants to add starter data
        add_data = input("\n❓ Add starter data to empty database? (y/n): ").lower().strip()
        if add_data in ['y', 'yes']:
            seed_minimal_data()
        
        print("\n🚀 Ready to run the chatbot!")
        print("   python app.py")
    else:
        print("\n❌ Please fix the connection issues and try again.")
