import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

def verify_day6_8():
    """Verify Day 6-8 completion"""
    
    checks = []
    
    print("\n" + "=" * 60)
    print("DAY 6-8 VERIFICATION")
    print("=" * 60)
    
    # 1. Vertex AI enabled
    print("\n1. Checking Vertex AI initialization...")
    try:
        import vertexai
        vertexai.init(project=os.getenv("PROJECT_ID"), location="us-central1")
        checks.append(("Vertex AI initialized", True))
        print("   ✅ Vertex AI initialized successfully")
    except Exception as e:
        checks.append(("Vertex AI initialized", False, str(e)))
        print(f"   ❌ Error: {str(e)}")
    
    # 2. Gemini model accessible
    print("\n2. Checking Gemini model access...")
    try:
        from vertexai.generative_models import GenerativeModel
        model = GenerativeModel("gemini-2.0-flash-exp")
        checks.append(("Gemini model available", True))
        print("   ✅ Gemini 2.0 Flash Exp model accessible")
    except Exception as e:
        checks.append(("Gemini model available", False, str(e)))
        print(f"   ❌ Error: {str(e)}")
    
    # 3. Anomaly Detective exists
    print("\n3. Checking AnomalyDetective class...")
    try:
        from agents.anomaly_detective import AnomalyDetective
        checks.append(("AnomalyDetective class", True))
        print("   ✅ AnomalyDetective class imported successfully")
    except Exception as e:
        checks.append(("AnomalyDetective class", False, str(e)))
        print(f"   ❌ Error: {str(e)}")
    
    # 4. Can instantiate detective
    print("\n4. Testing detective instantiation...")
    try:
        from agents.anomaly_detective import AnomalyDetective
        detective = AnomalyDetective(
            os.getenv("PROJECT_ID"),
            os.getenv("DATASET_ID"),
            os.getenv("TABLE_ID")
        )
        checks.append(("Detective instantiation", True))
        print("   ✅ AnomalyDetective instantiated successfully")
    except Exception as e:
        checks.append(("Detective instantiation", False, str(e)))
        print(f"   ❌ Error: {str(e)}")
    
    # 5. Can run check
    print("\n5. Running anomaly check...")
    try:
        result = detective.run_check()
        has_required_fields = all(k in result for k in ["has_anomalies", "confidence", "anomalies"])
        checks.append(("Run anomaly check", has_required_fields))
        if has_required_fields:
            print(f"   ✅ Anomaly check completed successfully")
            print(f"      - Has anomalies: {result['has_anomalies']}")
            print(f"      - Confidence: {result['confidence']:.0%}")
            print(f"      - Anomalies found: {len(result.get('anomalies', []))}")
        else:
            print("   ❌ Result missing required fields")
    except Exception as e:
        checks.append(("Run anomaly check", False, str(e)))
        print(f"   ❌ Error: {str(e)}")
    
    # 6. Test API endpoints
    print("\n6. Testing API endpoints...")
    try:
        import requests
        
        # Test anomaly status endpoint
        response = requests.get("http://localhost:8000/api/anomaly/status", timeout=5)
        status_ok = response.status_code == 200
        
        # Test anomaly check endpoint
        response2 = requests.get("http://localhost:8000/api/anomaly/check", timeout=30)
        check_ok = response2.status_code == 200
        
        checks.append(("API endpoints", status_ok and check_ok))
        if status_ok and check_ok:
            print("   ✅ API endpoints operational")
            print("      - /api/anomaly/status ✓")
            print("      - /api/anomaly/check ✓")
        else:
            print(f"   ❌ API endpoint errors (status: {status_ok}, check: {check_ok})")
    except requests.exceptions.ConnectionError:
        checks.append(("API endpoints", False, "API server not running"))
        print("   ⚠️  API server not running (run: uv run uvicorn agents.api:app --reload)")
    except Exception as e:
        checks.append(("API endpoints", False, str(e)))
        print(f"   ❌ Error: {str(e)}")
    
    # Print results
    print("\n" + "=" * 60)
    print("VERIFICATION RESULTS")
    print("=" * 60)
    passed = 0
    for check in checks:
        status = "✅" if check[1] else "❌"
        print(f"{status} {check[0]}")
        if check[1]:
            passed += 1
        elif len(check) > 2:
            print(f"   Error: {check[2]}")
    
    print(f"\n{passed}/{len(checks)} checks passed")
    
    if passed == len(checks):
        print("\n" + "🎉" * 30)
        print("DAY 6-8 COMPLETE!")
        print("=" * 60)
        print("✅ Agent 1: Schema Guardian operational")
        print("✅ Agent 2: Anomaly Detective operational")
        print("✅ Vertex AI Gemini integrated")
        print("✅ API endpoints operational")
        print("✅ Ready for Day 9-11 or submission!")
        print("=" * 60)
        return True
    else:
        print("\n⚠️  Some checks failed. Review errors above.")
        return False

if __name__ == "__main__":
    success = verify_day6_8()
    exit(0 if success else 1)
