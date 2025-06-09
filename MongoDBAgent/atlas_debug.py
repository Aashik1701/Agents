#!/usr/bin/env python3
"""
Enhanced Atlas Connection Debugger
"""

import socket
from pymongo import MongoClient
from config import MONGODB_URI, MONGODB_USERNAME, MONGODB_PASSWORD, MONGODB_CLUSTER

def test_dns_resolution():
    """Test if the cluster hostname resolves"""
    print("🔍 Testing DNS Resolution...")
    try:
        cluster_host = MONGODB_CLUSTER
        ip = socket.gethostbyname(cluster_host)
        print(f"✅ DNS Resolution successful: {cluster_host} -> {ip}")
        return True
    except Exception as e:
        print(f"❌ DNS Resolution failed: {e}")
        return False

def test_simplified_connection():
    """Test with a simplified connection string"""
    print("\n🧪 Testing Simplified Connection...")
    try:
        simple_uri = f"mongodb+srv://{MONGODB_USERNAME}:{MONGODB_PASSWORD}@{MONGODB_CLUSTER}/test"
        
        client = MongoClient(simple_uri, serverSelectionTimeoutMS=10000)
        client.admin.command('ping')
        print("✅ Simplified connection successful!")
        client.close()
        return True
        
    except Exception as e:
        print(f"❌ Simplified connection failed: {e}")
        return False

def get_public_ip():
    """Get current public IP"""
    try:
        import urllib.request
        ip = urllib.request.urlopen('https://api.ipify.org', timeout=5).read().decode('utf8')
        return ip
    except:
        return "Unable to detect"

def main():
    """Run Atlas debugging"""
    print("🚀 MongoDB Atlas Connection Debugger")
    print("=" * 50)
    
    print(f"🔧 Configuration:")
    print(f"   Username: {MONGODB_USERNAME}")
    print(f"   Password: {'*' * len(MONGODB_PASSWORD)}")
    print(f"   Cluster: {MONGODB_CLUSTER}")
    print(f"   Your IP: {get_public_ip()}")
    
    # Run tests
    dns_ok = test_dns_resolution()
    simple_ok = test_simplified_connection()
    
    if simple_ok:
        print("\n🎉 Atlas connection is working!")
    else:
        print("\n❌ Atlas connection needs troubleshooting")
        print("\n💡 Common fixes:")
        print("1. Add your IP to Atlas Network Access whitelist")
        print("2. Verify username/password in Atlas Database Access")
        print("3. Ensure cluster is not paused")
        print("4. Check cluster name is correct")

if __name__ == "__main__":
    main()
