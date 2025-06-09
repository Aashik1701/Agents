#!/usr/bin/env python3
"""
Quick MongoDB Data Viewer
Simple command-line tool to view your MongoDB data
"""

from pymongo import MongoClient
from config import LOCAL_MONGODB_URI, MONGODB_DATABASE

def quick_view():
    """Quick view of all FAQs"""
    client = MongoClient(LOCAL_MONGODB_URI)
    db = client[MONGODB_DATABASE]
    faqs = db.faqs
    
    print("🗄️  MONGODB DATABASE VIEWER")
    print("=" * 60)
    print(f"📊 Database: {MONGODB_DATABASE}")
    print(f"📈 Total FAQs: {faqs.count_documents({})}")
    print("=" * 60)
    
    docs = list(faqs.find({}).sort('_id', 1))
    
    for i, doc in enumerate(docs, 1):
        print(f"\n📝 FAQ #{i}")
        print(f"❓ Question: {doc['question']}")
        print(f"💬 Answer: {doc['answer']}")
        print(f"🆔 ID: {doc['_id']}")
        print("-" * 40)
    
    client.close()

if __name__ == "__main__":
    quick_view()