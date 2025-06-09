#!/usr/bin/env python3
"""
MongoDB Atlas Connection Troubleshooter
Comprehensive diagnostics for Atlas connectivity issues
"""

import sys
import socket
import ssl
import urllib.parse
from pymongo import MongoClient
import dns.resolver
import requests

def check_internet_connectivity():
    """Test basic internet connectivity"""
    print("🌐 Testing Internet Connectivity...")
    try:
        response = requests.get("https://www.google.com", timeout=5)
        if response.status_code == 200:
            print("✅ Internet connection working")
            return True
    except Exception as e:
        print(f"❌ Internet connection failed: {e}")
        return False

def check_dns_resolution(hostname):
    """Test DNS resolution for MongoDB Atlas"""
    print(f"🔍 Testing DNS resolution for {hostname}...")
    try:
        # Try different DNS resolvers
        resolvers = ['8.8.8.8', '1.1.1.1', '208.67.222.222']
        
        for resolver_ip in resolvers:
            try:
                resolver = dns.resolver.Resolver()
                resolver.nameservers = [resolver_ip]
                result = resolver.resolve(hostname, 'A')
                print(f"✅ DNS resolution successful with {resolver_ip}")
                for ip in result:
                    print(f"   → {hostname} resolves to {ip}")
                return True
            except Exception as e:
                print(f"❌ DNS resolution failed with {resolver_ip}: {e}")
        
        return False
    except Exception as e:
        print(f"❌ DNS resolution completely failed: {e}")
        return False

def check_port_connectivity(hostname, port=27017):
    """Test if we can connect to MongoDB port"""
    print(f"🔌 Testing port connectivity to {hostname}:{port}...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        result = sock.connect_ex((hostname, port))
        sock.close()
        
        if result == 0:
            print(f"✅ Port {port} is accessible")
            return True
        else:
            print(f"❌ Port {port} is not accessible (error code: {result})")
            return False
    except Exception as e:
        print(f"❌ Port connectivity test failed: {e}")
        return False

def test_ssl_handshake(hostname, port=27017):
    """Test SSL handshake with MongoDB"""
    print(f"🔐 Testing SSL handshake with {hostname}:{port}...")
    try:
        context = ssl.create_default_context()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        
        # Connect to the socket
        sock.connect((hostname, port))
        
        # Wrap with SSL
        ssock = context.wrap_socket(sock, server_hostname=hostname)
        print(f"✅ SSL handshake successful")
        print(f"   SSL Version: {ssock.version()}")
        print(f"   Cipher: {ssock.cipher()}")
        ssock.close()
        return True
        
    except Exception as e:
        print(f"❌ SSL handshake failed: {e}")
        return False

def test_atlas_connection_variations():
    """Test different Atlas connection string variations"""
    print("🧪 Testing Atlas Connection Variations...")
    
    base_configs = [
        {
            "name": "Original Config",
            "username": "Cluster20526",
            "password": "aashik1701",
            "cluster": "cluster20526.g4udhpz.mongodb.net"
        },
        {
            "name": "Without Cluster Prefix",
            "username": "Cluster20526", 
            "password": "aashik1701",
            "cluster": "20526.g4udhpz.mongodb.net"
        }
    ]
    
    connection_options = [
        "?retryWrites=true&w=majority",
        "?retryWrites=true&w=majority&ssl=true",
        "?retryWrites=true&w=majority&tlsInsecure=true",
        "?retryWrites=true&w=majority&ssl=false",
        ""
    ]
    
    for config in base_configs:
        print(f"\n--- Testing {config['name']} ---")
        
        for i, options in enumerate(connection_options):
            print(f"  Variation {i+1}: {options if options else 'No options'}")
            
            uri = f"mongodb+srv://{config['username']}:{urllib.parse.quote(config['password'])}@{config['cluster']}/{options}"
            
            try:
                client = MongoClient(uri, serverSelectionTimeoutMS=5000)
                client.admin.command('ping')
                print(f"  ✅ Connection successful!")
                client.close()
                return uri
            except Exception as e:
                print(f"  ❌ Failed: {str(e)[:100]}...")
    
    return None

def check_ip_and_atlas_access():
    """Check current IP and Atlas access requirements"""
    print("🌍 Checking IP and Atlas Access...")
    
    try:
        # Get current public IP
        ip_response = requests.get("https://ipinfo.io/ip", timeout=5)
        current_ip = ip_response.text.strip()
        print(f"📍 Your current public IP: {current_ip}")
        
        print("\n📋 Atlas Setup Checklist:")
        print("1. Network Access: Add IP address to allowlist")
        print("   - Go to Atlas → Network Access → Add IP Address")
        print(f"   - Add this IP: {current_ip}")
        print("   - Or allow access from anywhere: 0.0.0.0/0 (less secure)")
        
        print("\n2. Database Access: Verify user credentials")
        print("   - Go to Atlas → Database Access")
        print("   - Username should exist and have proper permissions")
        print("   - Password should be correct")
        
        print("\n3. Cluster Status:")
        print("   - Ensure cluster is not paused")
        print("   - Verify cluster name is correct")
        
    except Exception as e:
        print(f"❌ IP check failed: {e}")

def main():
    print("🚀 MongoDB Atlas Connection Troubleshooter")
    print("=" * 50)
    
    # Basic connectivity tests
    if not check_internet_connectivity():
        print("❌ Fix internet connection first")
        return
    
    hostname = "cluster20526.g4udhpz.mongodb.net"
    
    # DNS and network tests
    dns_ok = check_dns_resolution(hostname)
    if not dns_ok:
        print(f"\n❌ DNS resolution failed for {hostname}")
        print("This suggests the cluster name might be incorrect or the cluster doesn't exist")
        
        # Try some common variations
        variations = [
            "cluster20526.mongodb.net",
            "cluster20526.mongodbgov.net", 
            "ac-f5zef2q-shard-00-00.g4udhpz.mongodb.net"
        ]
        
        print("\n🔍 Trying common hostname variations...")
        for variation in variations:
            if check_dns_resolution(variation):
                print(f"✅ Found working hostname: {variation}")
                hostname = variation
                break
    
    if dns_ok:
        check_port_connectivity(hostname)
        test_ssl_handshake(hostname)
    
    # Test Atlas connections
    working_uri = test_atlas_connection_variations()
    
    if working_uri:
        print(f"\n🎉 Found working connection URI:")
        print(f"   {working_uri}")
    else:
        print(f"\n❌ No working connection found")
    
    # IP and access info
    check_ip_and_atlas_access()
    
    print("\n" + "=" * 50)
    print("🔧 Next Steps:")
    if not dns_ok:
        print("1. ❗ Verify cluster name in Atlas dashboard")
        print("2. ❗ Ensure cluster is not paused or deleted")
    print("3. ❗ Add your IP to Network Access whitelist")
    print("4. ❗ Verify Database Access credentials")
    print("5. ❗ Check cluster connection string in Atlas")

if __name__ == "__main__":
    main()
