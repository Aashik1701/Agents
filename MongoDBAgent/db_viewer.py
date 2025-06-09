#!/usr/bin/env python3
"""
MongoDB Database Viewer
Interactive tool to explore your MongoDB database
"""

import json
from datetime import datetime
from pymongo import MongoClient
from config import LOCAL_MONGODB_URI, MONGODB_DATABASE, USE_ATLAS, MONGODB_URI

def get_client():
    """Get MongoDB client based on configuration"""
    if USE_ATLAS:
        return MongoClient(MONGODB_URI)
    else:
        return MongoClient(LOCAL_MONGODB_URI)

def show_database_overview():
    """Show database overview and statistics"""
    client = get_client()
    db = client[MONGODB_DATABASE]
    faqs = db.faqs
    
    print("🗄️  DATABASE OVERVIEW")
    print("=" * 50)
    print(f"Database: {MONGODB_DATABASE}")
    print(f"Connection: {'Atlas' if USE_ATLAS else 'Local MongoDB'}")
    print(f"Collection: faqs")
    print(f"Total documents: {faqs.count_documents({})}")
    
    # Get some stats
    try:
        stats = db.command("collStats", "faqs")
        print(f"Storage size: {stats.get('storageSize', 'N/A')} bytes")
        print(f"Index size: {stats.get('totalIndexSize', 'N/A')} bytes")
    except:
        print("Storage stats: Not available")
    
    client.close()

def show_all_faqs():
    """Display all FAQs in a formatted way"""
    client = get_client()
    db = client[MONGODB_DATABASE]
    faqs = db.faqs
    
    print("\n📋 ALL FAQs")
    print("=" * 50)
    
    docs = list(faqs.find({}).sort('_id', 1))
    
    for i, doc in enumerate(docs, 1):
        print(f"\n{i:2d}. Question: {doc['question']}")
        print(f"    Answer: {doc['answer']}")
        print(f"    ID: {doc['_id']}")
        
        # Show creation time if available
        if hasattr(doc['_id'], 'generation_time'):
            print(f"    Created: {doc['_id'].generation_time}")
    
    client.close()

def show_recent_faqs(limit=5):
    """Show most recently added FAQs"""
    client = get_client()
    db = client[MONGODB_DATABASE]
    faqs = db.faqs
    
    print(f"\n🆕 RECENT FAQs (Last {limit})")
    print("=" * 50)
    
    docs = list(faqs.find({}).sort('_id', -1).limit(limit))
    
    for i, doc in enumerate(docs, 1):
        print(f"\n{i}. Question: {doc['question']}")
        print(f"   Answer: {doc['answer']}")
        if hasattr(doc['_id'], 'generation_time'):
            print(f"   Added: {doc['_id'].generation_time}")
    
    client.close()

def search_faqs(keyword):
    """Search FAQs by keyword"""
    client = get_client()
    db = client[MONGODB_DATABASE]
    faqs = db.faqs
    
    print(f"\n🔍 SEARCH RESULTS for '{keyword}'")
    print("=" * 50)
    
    # Search in both questions and answers
    query = {
        "$or": [
            {"question": {"$regex": keyword, "$options": "i"}},
            {"answer": {"$regex": keyword, "$options": "i"}}
        ]
    }
    
    docs = list(faqs.find(query))
    
    if docs:
        for i, doc in enumerate(docs, 1):
            print(f"\n{i}. Question: {doc['question']}")
            print(f"   Answer: {doc['answer']}")
    else:
        print(f"No FAQs found containing '{keyword}'")
    
    client.close()

def export_to_json():
    """Export all FAQs to a JSON file"""
    client = get_client()
    db = client[MONGODB_DATABASE]
    faqs = db.faqs
    
    docs = list(faqs.find({}))
    
    # Convert ObjectId to string for JSON serialization
    for doc in docs:
        doc['_id'] = str(doc['_id'])
    
    filename = f"faqs_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(filename, 'w') as f:
        json.dump(docs, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 EXPORTED {len(docs)} FAQs to: {filename}")
    
    client.close()

def show_questions_only():
    """Show just the questions for a quick overview"""
    client = get_client()
    db = client[MONGODB_DATABASE]
    faqs = db.faqs
    
    print("\n❓ ALL QUESTIONS")
    print("=" * 50)
    
    docs = list(faqs.find({}, {"question": 1}).sort('_id', 1))
    
    for i, doc in enumerate(docs, 1):
        print(f"{i:2d}. {doc['question']}")
    
    client.close()

def interactive_menu():
    """Interactive menu for exploring database"""
    while True:
        print("\n" + "="*60)
        print("🗄️  MONGODB DATABASE EXPLORER")
        print("="*60)
        print("1. Database Overview")
        print("2. Show All FAQs")
        print("3. Show Recent FAQs")
        print("4. Show Questions Only")
        print("5. Search FAQs")
        print("6. Export to JSON")
        print("7. Exit")
        print("-" * 60)
        
        choice = input("Choose an option (1-7): ").strip()
        
        if choice == '1':
            show_database_overview()
        elif choice == '2':
            show_all_faqs()
        elif choice == '3':
            limit = input("How many recent FAQs? (default 5): ").strip()
            limit = int(limit) if limit.isdigit() else 5
            show_recent_faqs(limit)
        elif choice == '4':
            show_questions_only()
        elif choice == '5':
            keyword = input("Enter search keyword: ").strip()
            if keyword:
                search_faqs(keyword)
        elif choice == '6':
            export_to_json()
        elif choice == '7':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please try again.")
        
        input("\nPress Enter to continue...")

def main():
    """Main function with command line options"""
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'overview':
            show_database_overview()
        elif command == 'all':
            show_all_faqs()
        elif command == 'recent':
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 5
            show_recent_faqs(limit)
        elif command == 'questions':
            show_questions_only()
        elif command == 'search':
            if len(sys.argv) > 2:
                search_faqs(' '.join(sys.argv[2:]))
            else:
                print("Usage: python db_viewer.py search <keyword>")
        elif command == 'export':
            export_to_json()
        else:
            print("Commands: overview, all, recent, questions, search, export")
    else:
        interactive_menu()

if __name__ == "__main__":
    main()
