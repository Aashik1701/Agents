from pymongo import MongoClient
from pymongo.server_api import ServerApi
from config import MONGODB_URI, MONGODB_DATABASE
import json

def add_faq_interactive():
    """
    Add FAQ interactively
    """
    try:
        client = MongoClient(MONGODB_URI, server_api=ServerApi('1'))
        db = client[MONGODB_DATABASE]
        faqs = db.faqs
        
        print("➕ Add New FAQ")
        print("-" * 20)
        
        question = input("Question: ").strip()
        answer = input("Answer: ").strip()
        
        if not question or not answer:
            print("❌ Both question and answer are required")
            return
        
        # Check if exists
        existing = faqs.find_one({"question": {"$regex": f"^{question}$", "$options": "i"}})
        if existing:
            print("⚠️  Question already exists!")
            return
        
        # Insert
        result = faqs.insert_one({"question": question.lower(), "answer": answer})
        print(f"✅ Added FAQ with ID: {result.inserted_id}")
        
        client.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

def list_all_faqs():
    """
    List all FAQs in the database
    """
    try:
        client = MongoClient(MONGODB_URI, server_api=ServerApi('1'))
        db = client[MONGODB_DATABASE]
        faqs = db.faqs
        
        total = faqs.count_documents({})
        print(f"📋 Total FAQs: {total}")
        print("=" * 50)
        
        for i, doc in enumerate(faqs.find(), 1):
            print(f"{i}. Q: {doc['question']}")
            print(f"   A: {doc['answer']}")
            print()
        
        client.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

def delete_faq():
    """
    Delete a FAQ by question
    """
    try:
        client = MongoClient(MONGODB_URI, server_api=ServerApi('1'))
        db = client[MONGODB_DATABASE]
        faqs = db.faqs
        
        question = input("Enter question to delete: ").strip()
        
        result = faqs.delete_one({"question": {"$regex": f"^{question}$", "$options": "i"}})
        
        if result.deleted_count > 0:
            print("✅ FAQ deleted successfully")
        else:
            print("❌ FAQ not found")
        
        client.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

def import_from_json():
    """
    Import FAQs from JSON file
    """
    try:
        filename = input("Enter JSON filename: ").strip()
        
        with open(filename, 'r') as f:
            data = json.load(f)
        
        client = MongoClient(MONGODB_URI, server_api=ServerApi('1'))
        db = client[MONGODB_DATABASE]
        faqs = db.faqs
        
        # Validate data format
        if not isinstance(data, list):
            print("❌ JSON should contain a list of FAQ objects")
            return
        
        valid_data = []
        for item in data:
            if isinstance(item, dict) and "question" in item and "answer" in item:
                valid_data.append({
                    "question": item["question"].lower().strip(),
                    "answer": item["answer"].strip()
                })
        
        if valid_data:
            result = faqs.insert_many(valid_data)
            print(f"✅ Imported {len(result.inserted_ids)} FAQs")
        else:
            print("❌ No valid FAQ data found")
        
        client.close()
        
    except FileNotFoundError:
        print("❌ File not found")
    except json.JSONDecodeError:
        print("❌ Invalid JSON format")
    except Exception as e:
        print(f"❌ Error: {e}")

def main_menu():
    """
    Main menu for FAQ management
    """
    while True:
        print("\n🛠️  MongoDB Atlas FAQ Manager")
        print("=" * 30)
        print("1. List all FAQs")
        print("2. Add new FAQ")
        print("3. Delete FAQ")
        print("4. Import from JSON")
        print("5. Exit")
        
        choice = input("\nChoose option (1-5): ").strip()
        
        if choice == "1":
            list_all_faqs()
        elif choice == "2":
            add_faq_interactive()
        elif choice == "3":
            delete_faq()
        elif choice == "4":
            import_from_json()
        elif choice == "5":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice")

if __name__ == "__main__":
    main_menu()
