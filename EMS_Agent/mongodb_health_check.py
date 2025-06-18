#!/usr/bin/env python3
"""
MongoDB Connection Health Check Script
Quick diagnostic tool for EMS Agent MongoDB connectivity
"""

import sys
import time
from datetime import datetime
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from config import MONGODB_URI, MONGODB_DATABASE

def test_mongodb_connection():
    """Comprehensive MongoDB connection test"""
    print("🔍 MongoDB Health Check - EMS Agent")
    print("=" * 50)
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🗄️  Database: {MONGODB_DATABASE}")
    
    try:
        # Test basic connection
        print("\n1️⃣ Testing basic connection...")
        start_time = time.time()
        client = MongoClient(MONGODB_URI, server_api=ServerApi('1'), serverSelectionTimeoutMS=5000) # type: ignore
        
        # Ping test
        result = client.admin.command('ping') # type: ignore
        connection_time = time.time() - start_time
        print(f"   ✅ Connection successful ({connection_time:.3f}s)")
        
        # Database access test
        print("\n2️⃣ Testing database access...")
        db = client[MONGODB_DATABASE]
        collections = db.list_collection_names()
        print(f"   ✅ Found {len(collections)} collections: {collections}")
        
        # Data integrity test
        print("\n3️⃣ Testing data integrity...")
        total_docs = 0
        for collection_name in collections:
            count = db[collection_name].estimated_document_count()
            total_docs += count
            print(f"   📚 {collection_name}: {count:,} documents")
        
        print(f"   📊 Total documents: {total_docs:,}")
        
        # Performance test
        print("\n4️⃣ Testing query performance...")
        if 'ems_raw_data' in collections:
            start_time = time.time()
            sample = db.ems_raw_data.find().limit(5)
            results = list(sample)
            query_time = time.time() - start_time
            print(f"   ⚡ Sample query: {query_time:.3f}s ({len(results)} docs)")
        
        # Latest data check
        print("\n5️⃣ Checking latest data...")
        if 'ems_raw_data' in collections:
            latest = db.ems_raw_data.find().sort('timestamp', -1).limit(1)
            latest_doc = list(latest)
            if latest_doc:
                timestamp = latest_doc[0].get('timestamp', 'Unknown')
                print(f"   🕐 Latest reading: {timestamp}")
            else:
                print("   ⚠️  No data found")
        
        client.close()
        
        # Overall health score
        health_score = "EXCELLENT" if total_docs > 50 and connection_time < 1.0 else "GOOD" if total_docs > 0 else "POOR"
        print(f"\n📊 Overall Health: {health_score}")
        print("✅ MongoDB connection is healthy!")
        return True
        
    except Exception as e:
        print(f"\n❌ Connection failed: {str(e)}")
        print(f"🔧 Check your MongoDB configuration in config.py")
        return False

def test_ems_components():
    """Test EMS-specific components"""
    print(f"\n{'='*50}")
    print("🧪 Testing EMS Components")
    print("=" * 50)
    
    try:
        # Test Query Engine
        print("\n1️⃣ Testing EMS Query Engine...")
        from ems_search import EMSQueryEngine
        engine = EMSQueryEngine()
        status = engine.get_system_status("test")
        print(f"   ✅ Query Engine: {status[:100]}...")
        engine.close()
        
        # Test Data Loader
        print("\n2️⃣ Testing EMS Data Loader...")
        from data_loader import EMSDataLoader
        loader = EMSDataLoader()
        stats = loader.get_database_stats()
        print(f"   ✅ Data Loader: {sum(stats.values())} total documents")
        loader.close()
        
        print("\n✅ All EMS components are working!")
        return True
        
    except Exception as e:
        print(f"\n❌ EMS component test failed: {str(e)}")
        return False

def main():
    """Main test function"""
    print("🚀 Starting comprehensive MongoDB health check...\n")
    
    # Test MongoDB connection
    mongo_ok = test_mongodb_connection()
    
    # Test EMS components if MongoDB is working
    if mongo_ok:
        ems_ok = test_ems_components()
        
        if ems_ok:
            print(f"\n{'='*50}")
            print("🎉 ALL SYSTEMS OPERATIONAL!")
            print("✅ MongoDB: Connected")
            print("✅ EMS Query Engine: Working")
            print("✅ EMS Data Loader: Working")
            print(f"{'='*50}")
            return 0
    
    print(f"\n{'='*50}")
    print("⚠️  SYSTEM CHECK FAILED")
    print("Please check the error messages above")
    print(f"{'='*50}")
    return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
