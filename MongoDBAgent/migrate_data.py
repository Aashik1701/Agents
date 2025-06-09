#!/usr/bin/env python3
"""
MongoDB Data Migration Tool
Migrate FAQs between local MongoDB and Atlas
"""

import sys
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import json
from datetime import datetime

class MongoDBMigrator:
    def __init__(self):
        # Local MongoDB connection
        self.local_client = MongoClient("mongodb://localhost:27017/")
        self.local_db = self.local_client.chatbotDB
        self.local_collection = self.local_db.faqs
        
        # Atlas connection (will be set when available)
        self.atlas_client = None
        self.atlas_db = None
        self.atlas_collection = None
    
    def connect_to_atlas(self, atlas_uri):
        """Connect to MongoDB Atlas"""
        try:
            self.atlas_client = MongoClient(atlas_uri, server_api=ServerApi('1'))
            
            # Test connection
            self.atlas_client.admin.command('ping')
            
            self.atlas_db = self.atlas_client.chatbotDB
            self.atlas_collection = self.atlas_db.faqs
            
            print("✅ Connected to Atlas successfully")
            return True
            
        except Exception as e:
            print(f"❌ Atlas connection failed: {e}")
            return False
    
    def get_local_faqs(self):
        """Get all FAQs from local MongoDB"""
        try:
            faqs = list(self.local_collection.find({}))
            print(f"📊 Found {len(faqs)} FAQs in local database")
            return faqs
        except Exception as e:
            print(f"❌ Error reading local FAQs: {e}")
            return []
    
    def get_atlas_faqs(self):
        """Get all FAQs from Atlas"""
        if not self.atlas_collection:
            print("❌ Atlas not connected")
            return []
        
        try:
            faqs = list(self.atlas_collection.find({}))
            print(f"📊 Found {len(faqs)} FAQs in Atlas database")
            return faqs
        except Exception as e:
            print(f"❌ Error reading Atlas FAQs: {e}")
            return []
    
    def migrate_to_atlas(self, overwrite=False):
        """Migrate FAQs from local to Atlas"""
        if not self.atlas_collection:
            print("❌ Atlas not connected")
            return False
        
        local_faqs = self.get_local_faqs()
        if not local_faqs:
            print("❌ No local FAQs to migrate")
            return False
        
        try:
            if overwrite:
                # Clear Atlas collection first
                result = self.atlas_collection.delete_many({})
                print(f"🗑️  Cleared {result.deleted_count} existing Atlas FAQs")
            
            # Insert local FAQs into Atlas
            # Remove _id field to avoid conflicts
            faqs_to_insert = []
            for faq in local_faqs:
                faq_copy = faq.copy()
                if '_id' in faq_copy:
                    del faq_copy['_id']
                faqs_to_insert.append(faq_copy)
            
            result = self.atlas_collection.insert_many(faqs_to_insert)
            print(f"✅ Migrated {len(result.inserted_ids)} FAQs to Atlas")
            
            return True
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            return False
    
    def migrate_from_atlas(self, overwrite=False):
        """Migrate FAQs from Atlas to local"""
        atlas_faqs = self.get_atlas_faqs()
        if not atlas_faqs:
            print("❌ No Atlas FAQs to migrate")
            return False
        
        try:
            if overwrite:
                # Clear local collection first
                result = self.local_collection.delete_many({})
                print(f"🗑️  Cleared {result.deleted_count} existing local FAQs")
            
            # Insert Atlas FAQs into local
            faqs_to_insert = []
            for faq in atlas_faqs:
                faq_copy = faq.copy()
                if '_id' in faq_copy:
                    del faq_copy['_id']
                faqs_to_insert.append(faq_copy)
            
            result = self.local_collection.insert_many(faqs_to_insert)
            print(f"✅ Migrated {len(result.inserted_ids)} FAQs to local")
            
            return True
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            return False
    
    def export_faqs_to_json(self, source='local', filename=None):
        """Export FAQs to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"faqs_backup_{source}_{timestamp}.json"
        
        if source == 'local':
            faqs = self.get_local_faqs()
        elif source == 'atlas':
            faqs = self.get_atlas_faqs()
        else:
            print("❌ Invalid source. Use 'local' or 'atlas'")
            return False
        
        if not faqs:
            print(f"❌ No FAQs found in {source}")
            return False
        
        try:
            # Convert ObjectId to string for JSON serialization
            for faq in faqs:
                if '_id' in faq:
                    faq['_id'] = str(faq['_id'])
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(faqs, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Exported {len(faqs)} FAQs to {filename}")
            return True
            
        except Exception as e:
            print(f"❌ Export failed: {e}")
            return False
    
    def show_comparison(self):
        """Show comparison between local and Atlas databases"""
        print("\n📊 Database Comparison")
        print("=" * 40)
        
        local_faqs = self.get_local_faqs()
        atlas_faqs = self.get_atlas_faqs() if self.atlas_collection else []
        
        print(f"Local MongoDB:  {len(local_faqs)} FAQs")
        print(f"Atlas MongoDB:  {len(atlas_faqs)} FAQs")
        
        if local_faqs:
            print(f"\nLocal FAQ samples:")
            for i, faq in enumerate(local_faqs[:3]):
                print(f"  {i+1}. Q: {faq.get('question', 'N/A')[:50]}...")
        
        if atlas_faqs:
            print(f"\nAtlas FAQ samples:")
            for i, faq in enumerate(atlas_faqs[:3]):
                print(f"  {i+1}. Q: {faq.get('question', 'N/A')[:50]}...")
    
    def close_connections(self):
        """Close database connections"""
        if self.local_client:
            self.local_client.close()
        if self.atlas_client:
            self.atlas_client.close()

def main():
    print("🔄 MongoDB Data Migration Tool")
    print("=" * 40)
    
    migrator = MongoDBMigrator()
    
    try:
        # Show current local data
        migrator.show_comparison()
        
        print("\n🛠️  Available Actions:")
        print("1. Export local FAQs to JSON backup")
        print("2. Test Atlas connection and compare")
        print("3. Migrate local → Atlas (when Atlas is ready)")
        print("4. Show detailed FAQ comparison")
        
        action = input("\nSelect action (1-4) or press Enter to skip: ").strip()
        
        if action == "1":
            success = migrator.export_faqs_to_json('local')
            if success:
                print("💾 Backup created successfully")
        
        elif action == "2":
            # Get Atlas URI from config or user input
            try:
                from config import MONGODB_URI
                atlas_uri = MONGODB_URI
            except:
                atlas_uri = input("Enter Atlas connection string: ").strip()
            
            if atlas_uri and migrator.connect_to_atlas(atlas_uri):
                migrator.show_comparison()
            
        elif action == "3":
            atlas_uri = input("Enter Atlas connection string: ").strip()
            if atlas_uri and migrator.connect_to_atlas(atlas_uri):
                overwrite = input("Overwrite existing Atlas data? (y/N): ").lower() == 'y'
                migrator.migrate_to_atlas(overwrite)
        
        elif action == "4":
            migrator.show_comparison()
        
        print("\n✅ Migration tool completed")
        
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        migrator.close_connections()

if __name__ == "__main__":
    main()
