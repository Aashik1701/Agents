#!/usr/bin/env python3
"""
Direct Atlas Connection Test
Test the exact connection string provided by the user
"""

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import requests

def get_current_ip():
    """Get current public IP address"""
    try:
        response = requests.get("https://ipinfo.io/ip", timeout=5)
        return response.text.strip()
    except:
        return "Unable to detect"

def test_atlas_direct():
    """Test Atlas connection with the provided credentials"""
    
    print("🚀 Direct Atlas Connection Test")
    print("=" * 40)
    
    # Current IP
    current_ip = get_current_ip()
    print(f"📍 Your current IP: {current_ip}")
    
    # Connection string with actual credentials
    username = "aashik1701"
    password = "Sustainabyte"
    uri = f"mongodb+srv://{username}:{password}@cluster20526.g4udhpz.mongodb.net/?retryWrites=true&w=majority&appName=Cluster20526"
    
    print(f"🔗 Testing URI: {uri[:50]}...")
    
    try:
        # Create client with Server API
        client = MongoClient(uri, server_api=ServerApi('1'))
        
        # Test connection
        print("🧪 Attempting to ping MongoDB Atlas...")
        result = client.admin.command('ping')
        
        print("✅ SUCCESS! Connected to MongoDB Atlas!")
        print(f"   Ping result: {result}")
        
        # Test database access
        print("🗄️  Testing database access...")
        db = client.chatbotDB
        collection = db.faqs
        
        # Try to count documents
        count = collection.count_documents({})
        print(f"✅ Database access successful!")
        print(f"   Found {count} documents in faqs collection")
        
        # Try to insert a test document
        test_doc = {
            "question": "atlas connection test",
            "answer": "Atlas connection is working perfectly!",
            "test": True
        }
        
        result = collection.insert_one(test_doc)
        print(f"✅ Write test successful!")
        print(f"   Inserted document with ID: {result.inserted_id}")
        
        # Clean up test document
        collection.delete_one({"_id": result.inserted_id})
        print("🧹 Cleaned up test document")
        
        client.close()
        
        # Successfully connected - auto-update config to use Atlas
        print("\n🔄 Auto-updating config.py to use Atlas...")
        try:
            with open('config.py', 'r') as f:
                config_content = f.read()
            
            updated_config = config_content.replace('USE_ATLAS = False', 'USE_ATLAS = True')
            
            with open('config.py', 'w') as f:
                f.write(updated_config)
            
            print("✅ Updated config.py: USE_ATLAS = True")
            
        except Exception as e:
            print(f"❌ Could not update config.py: {e}")
            print("   Please manually set USE_ATLAS = True")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        
        # Check if it's an IP whitelist issue
        if "SSL handshake failed" in str(e):
            print("\n🔐 This appears to be an IP whitelist issue!")
            print("   Solution: Add your IP to Atlas Network Access")
            print(f"   1. Go to MongoDB Atlas → Network Access")
            print(f"   2. Click 'Add IP Address'")
            print(f"   3. Add this IP: {current_ip}")
            print(f"   4. Or add 0.0.0.0/0 for testing (less secure)")
        
        elif "authentication failed" in str(e).lower():
            print("\n🔑 This appears to be a credential issue!")
            print("   1. Verify username: aashik1701")
            print("   2. Verify password: Sustainabyte")
            print("   3. Check Database Access in Atlas")
        
        return False

def test_local_fallback():
    """Test if local MongoDB is still working"""
    print("\n🏠 Testing local MongoDB fallback...")
    
    try:
        client = MongoClient("mongodb://localhost:27017/")
        client.admin.command('ping')
        
        db = client.chatbotDB
        count = db.faqs.count_documents({})
        
        print(f"✅ Local MongoDB working - {count} FAQs available")
        client.close()
        return True
        
    except Exception as e:
        print(f"❌ Local MongoDB not available: {e}")
        return False

if __name__ == "__main__":
    print("🌟 MongoDB Atlas Connection Diagnostics")
    print("=" * 50)
    
    atlas_success = test_atlas_direct()
    
    if not atlas_success:
        test_local_fallback()
        
        print("\n" + "=" * 50)
        print("🎯 NEXT STEPS:")
        print("1. ❗ Add your IP to Atlas Network Access whitelist")
        print("2. ❗ Verify credentials in Atlas Database Access")
        print("3. ❗ Ensure cluster is not paused")
        print("4. 🔄 Run this test again after Atlas setup")
        
    else:
        print("\n🎉 Atlas is working! Your chatbot can now use live Atlas data!")
        print("   Run your app with: python app.py")
