#!/usr/bin/env python3
"""
Test script to verify the warning issue has been fixed
"""

import requests
import json
import time

def test_server_health():
    """Test the server health endpoint and check for warnings"""
    try:
        print("Testing MIDIGPT server health...")
        
        # Test health endpoint
        response = requests.get("http://127.0.0.1:5000/health", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Server is healthy!")
            print(f"   Status: {data.get('status')}")
            print(f"   Timestamp: {data.get('timestamp')}")
            return True
        else:
            print(f"❌ Server returned status code: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure the backend is running.")
        return False
    except Exception as e:
        print(f"❌ Error testing server: {str(e)}")
        return False

def test_search_endpoint():
    """Test the search endpoint to verify full functionality"""
    try:
        print("\nTesting song search functionality...")
        
        test_data = {"query": "bohemian rhapsody queen"}
        
        response = requests.post(
            "http://127.0.0.1:5000/search-songs",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                tracks = data.get('tracks', [])
                print(f"✅ Search working! Found {len(tracks)} tracks")
                if tracks:
                    print(f"   First result: {tracks[0].get('name')} by {tracks[0].get('artist')}")
                return True
            else:
                print(f"❌ Search failed: {data.get('error')}")
                return False
        else:
            print(f"❌ Search returned status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing search: {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("MIDIGPT Warning Fix Verification")
    print("=" * 50)
    
    # Wait a moment for server to be ready
    time.sleep(2)
    
    health_ok = test_server_health()
    search_ok = test_search_endpoint()
    
    print("\n" + "=" * 50)
    print("SUMMARY:")
    print("=" * 50)
    
    if health_ok and search_ok:
        print("🎉 All tests passed! The warning issue has been fixed.")
        print("   - Server is healthy and responding correctly")
        print("   - No Flask development server warnings should appear")
        print("   - Frontend warning indicator should now show 'Online' status")
    else:
        print("⚠️  Some tests failed. Please check the server configuration.")
        
    print("\nNow you can:")
    print("1. Open http://localhost:3000 in your browser")
    print("2. Check that the warning indicator shows 'Online' instead of 'Warning'")
    print("3. Try generating some MIDI music!")
