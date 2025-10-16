"""
Test API endpoints
"""

import requests
import json

print("=" * 80)
print("🧪 Testing Osprey API")
print("=" * 80)

base_url = "http://localhost:8000"

# Test 1: Health check
print("\n1. Testing /api/health")
try:
    response = requests.get(f"{base_url}/api/health")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 2: Root endpoint
print("\n2. Testing /")
try:
    response = requests.get(f"{base_url}/")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 3: Agent status
print("\n3. Testing /api/status")
try:
    response = requests.get(f"{base_url}/api/status")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 4: Alerts
print("\n4. Testing /api/alerts")
try:
    response = requests.get(f"{base_url}/api/alerts")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "=" * 80)
print("✅ API testing complete!")
print("=" * 80)
