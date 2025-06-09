#!/usr/bin/env python3
"""
Push FAQ data from backup file to MongoDB Atlas
"""

import json
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from config import MONGODB_URI, MONGODB_DATABASE

def push_backup_to_atlas(backup_file):
    """Push FAQ data from backup file to Atlas"""
    
    print(f"🚀 Pushing data from {backup_file} to MongoDB Atlas...")
    print("=" * 60)
    
    # Connect to Atlas
    try:
        print("🔗 Connecting to MongoDB Atlas...")
        client = MongoClient(MONGODB_URI, server_api=ServerApi('1'))
        
        # Test connection
        client.admin.command('ping')
        print("✅ Connected to Atlas successfully!")
        
        # Get database and collection
        db = client[MONGODB_DATABASE]
        collection = db.faqs
        
        # Check current Atlas data
        current_count = collection.count_documents({})
        print(f"📊 Current FAQs in Atlas: {current_count}")
        
        # Load backup data
        print(f"📁 Loading backup file: {backup_file}")
        with open(backup_file, 'r') as f:
            faqs = json.load(f)
        
        print(f"📝 Found {len(faqs)} FAQs in backup file")
        
        if not faqs:
            print("❌ No FAQs found in backup file!")
            return False
        
        # Show some samples
        print("\n📋 Sample FAQs from backup:")
        for i, faq in enumerate(faqs[:3]):
            print(f"  {i+1}. Q: {faq.get('question', 'N/A')[:50]}...")
        
        # Ask for confirmation
        if current_count > 0:
            response = input(f"\n⚠️  Atlas already has {current_count} FAQs. Overwrite? (y/N): ").strip().lower()
            if response != 'y':
                print("❌ Operation cancelled")
                return False
            
            # Clear existing data
            print("🗑️  Clearing existing Atlas data...")
            collection.delete_many({})
            print("✅ Existing data cleared")
        
        # Insert backup data
        print("📤 Inserting FAQs into Atlas...")
        
        # Remove _id fields to avoid conflicts
        for faq in faqs:
            if '_id' in faq:
                del faq['_id']
        
        result = collection.insert_many(faqs)
        
        print(f"✅ Successfully inserted {len(result.inserted_ids)} FAQs!")
        
        # Verify the insertion
        final_count = collection.count_documents({})
        print(f"📊 Final FAQ count in Atlas: {final_count}")
        
        # Show some examples from Atlas
        print("\n🔍 Sample FAQs now in Atlas:")
        atlas_samples = list(collection.find().limit(3))
        for i, faq in enumerate(atlas_samples):
            print(f"  {i+1}. Q: {faq.get('question', 'N/A')[:50]}...")
        
        print("\n🎉 Data migration to Atlas completed successfully!")
        print("💡 Your chatbot can now use live Atlas data!")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"❌ Error pushing to Atlas: {e}")
        return False

def main():
    backup_file = "faqs_backup_local_20250609_233945.json"
    
    print("🌟 MongoDB Atlas Data Push Tool")
    print("=" * 40)
    
    # Check if backup file exists
    try:
        with open(backup_file, 'r') as f:
            pass
        print(f"✅ Found backup file: {backup_file}")
    except FileNotFoundError:
        print(f"❌ Backup file not found: {backup_file}")
        return
    
    # Push to Atlas
    success = push_backup_to_atlas(backup_file)
    
    if success:
        print("\n🚀 Next steps:")
        print("  1. Run: python app.py")
        print("  2. Open: http://localhost:5000")
        print("  3. Test the chatbot with your 22 FAQs!")
    else:
        print("\n❌ Migration failed. Please check the error messages above.")

if __name__ == "__main__":
    main()
