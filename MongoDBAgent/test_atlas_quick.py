#!/usr/bin/env python3
"""
Quick Atlas Connection Tester
Use this after updating Network Access and verifying credentials
"""

import sys
from pymongo import MongoClient
from pymongo.server_api import ServerApi

def test_connection(uri, test_name="Atlas Connection"):
    """Test a MongoDB connection"""
    print(f"🧪 Testing {test_name}...")
    print(f"   URI: {uri[:50]}...")
    
    try:
        # Create client with timeout
        client = MongoClient(uri, server_api=ServerApi('1'), serverSelectionTimeoutMS=10000)
        
        # Test ping
        result = client.admin.command('ping')
        print(f"✅ {test_name} successful!")
        print(f"   Ping result: {result}")
        
        # Test database access
        db = client.chatbotDB
        collection = db.faqs
        
        # Try to get collection stats
        stats = db.command("collStats", "faqs")
        print(f"✅ Database access successful!")
        print(f"   Collection has {stats.get('count', 0)} documents")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"❌ {test_name} failed: {e}")
        return False

def main():
    print("🚀 Quick Atlas Connection Tester")
    print("=" * 40)
    
    # Test current configuration
    from config import MONGODB_URI
    
    if test_connection(MONGODB_URI, "Current Config"):
        print("\n🎉 Atlas connection working! You can now set USE_ATLAS = True")
        
        # Update config automatically
        try:
            with open('config.py', 'r') as f:
                content = f.read()
            
            updated_content = content.replace('USE_ATLAS = False', 'USE_ATLAS = True')
            
            with open('config.py', 'w') as f:
                f.write(updated_content)
            
            print("✅ Updated config.py to use Atlas")
            
        except Exception as e:
            print(f"❌ Could not update config.py: {e}")
            print("   Please manually set USE_ATLAS = True in config.py")
    
    else:
        print("\n❌ Atlas connection still failing")
        print("\n🔧 Manual Connection Test:")
        print("If you have the correct connection string from Atlas, you can test it here:")
        
        # Allow manual URI input
        manual_uri = input("\nEnter your Atlas connection string (or press Enter to skip): ").strip()
        
        if manual_uri:
            if test_connection(manual_uri, "Manual URI"):
                print(f"\n✅ Manual URI works! Update config.py with this URI:")
                print(f"MONGODB_URI = \"{manual_uri}\"")
            else:
                print("\n❌ Manual URI also failed")
        
        print("\n💡 Next steps:")
        print("1. Verify IP 49.37.214.201 is in Atlas Network Access")
        print("2. Verify Database Access credentials")
        print("3. Get connection string from Atlas Connect button")

if __name__ == "__main__":
    main()
