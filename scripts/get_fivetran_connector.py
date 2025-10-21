"""
Get Fivetran Connector ID

This script fetches your Fivetran connectors and displays details.
Run this to find your connector ID for the .env file.
"""

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def get_connectors():
    """Fetch all Fivetran connectors"""
    api_key = os.getenv("FIVETRAN_API_KEY")
    api_secret = os.getenv("FIVETRAN_API_SECRET")
    
    if not api_key or not api_secret:
        print("❌ Missing FIVETRAN_API_KEY or FIVETRAN_API_SECRET in .env")
        return None
    
    print("🔑 Using API credentials from .env...")
    print(f"   API Key: {api_key[:10]}...")
    
    try:
        response = requests.get(
            "https://api.fivetran.com/v1/connectors",
            auth=(api_key, api_secret),
            headers={"Accept": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            connectors = data.get("data", {}).get("items", [])
            
            print(f"\n✅ Found {len(connectors)} connector(s):\n")
            
            for conn in connectors:
                print("=" * 60)
                print(f"Connector ID: {conn.get('id')}")
                print(f"Service: {conn.get('service')}")
                print(f"Schema: {conn.get('schema')}")
                print(f"Status: {'Paused' if conn.get('paused') else 'Running'}")
                print(f"Sync Frequency: {conn.get('sync_frequency')} minutes")
                print(f"Created: {conn.get('created_at')}")
                
                # Show connection details
                config = conn.get('config', {})
                if config:
                    print(f"\nConfiguration:")
                    for key, value in config.items():
                        # Don't print sensitive data
                        if 'key' in key.lower() or 'secret' in key.lower():
                            print(f"  {key}: ***")
                        else:
                            print(f"  {key}: {value}")
                
                print("=" * 60)
                print()
            
            # If only one connector, suggest adding to .env
            if len(connectors) == 1:
                connector_id = connectors[0].get('id')
                print(f"💡 Add this to your .env file:")
                print(f"   FIVETRAN_CONNECTOR_ID={connector_id}")
            
            return connectors
        
        elif response.status_code == 401:
            print("❌ Authentication failed. Check your API credentials.")
            print(f"   Response: {response.text}")
        else:
            print(f"❌ API request failed: {response.status_code}")
            print(f"   Response: {response.text}")
        
        return None
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_api_access():
    """Simple test to verify API access works"""
    api_key = os.getenv("FIVETRAN_API_KEY")
    api_secret = os.getenv("FIVETRAN_API_SECRET")
    
    print("\n🧪 Testing API access...")
    
    try:
        response = requests.get(
            "https://api.fivetran.com/v1/users",
            auth=(api_key, api_secret)
        )
        
        if response.status_code == 200:
            data = response.json()
            user = data.get("data", {})
            print(f"✅ API access confirmed!")
            print(f"   User: {user.get('given_name')} {user.get('family_name')}")
            print(f"   Email: {user.get('email')}")
        else:
            print(f"❌ API test failed: {response.status_code}")
    
    except Exception as e:
        print(f"❌ Test error: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("FIVETRAN CONNECTOR DISCOVERY")
    print("=" * 60)
    
    # Test API access first
    test_api_access()
    
    # Get connectors
    print()
    connectors = get_connectors()
    
    if not connectors:
        print("\n⚠️  No connectors found or API error.")
        print("\nTroubleshooting:")
        print("1. Verify API credentials in .env are correct")
        print("2. Check you have connectors created in Fivetran UI")
        print("3. Ensure API key has proper permissions")
