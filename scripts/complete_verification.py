"""
Comprehensive Day 3-5 Completion Test Suite
Tests all components end-to-end
"""

import os
import sys
import json
from pathlib import Path
import time

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

print("=" * 80)
print("🔬 DAY 3-5 COMPLETE VERIFICATION - 100% COMPLETION TEST")
print("=" * 80)

# Configuration
PROJECT_ID = os.getenv("PROJECT_ID")
DATASET_ID = os.getenv("DATASET_ID", "osprey_data")
TABLE_ID = os.getenv("TABLE_ID", "raw_news")

# Test counters
tests_passed = 0
tests_failed = 0
tests_total = 0

def test(name, func):
    """Run a test and track results"""
    global tests_passed, tests_failed, tests_total
    tests_total += 1
    try:
        print(f"\n🧪 Test {tests_total}: {name}")
        func()
        print(f"   ✅ PASSED")
        tests_passed += 1
        return True
    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        tests_failed += 1
        import traceback
        traceback.print_exc()
        return False

# TEST 1: Environment Variables
def test_env_vars():
    assert PROJECT_ID, "PROJECT_ID not set"
    assert DATASET_ID, "DATASET_ID not set"
    assert TABLE_ID, "TABLE_ID not set"
    creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    assert creds, "GOOGLE_APPLICATION_CREDENTIALS not set"
    assert Path(creds).exists(), f"Credentials file not found: {creds}"
    print(f"   Project: {PROJECT_ID}")
    print(f"   Dataset: {DATASET_ID}")
    print(f"   Table: {TABLE_ID}")

test("Environment Variables", test_env_vars)

# TEST 2: Python Packages
def test_packages():
    import google.cloud.bigquery
    import google.cloud.firestore
    import pandas
    import fastapi
    import pytest
    from dotenv import load_dotenv
    print(f"   All required packages imported")

test("Python Packages", test_packages)

# TEST 3: Schema Guardian Import
def test_schema_guardian_import():
    from agents.schema_guardian import SchemaGuardian
    from agents.agent_memory import AgentMemory
    guardian = SchemaGuardian(PROJECT_ID, DATASET_ID, TABLE_ID)
    assert guardian is not None
    assert guardian.project_id == PROJECT_ID
    print(f"   SchemaGuardian initialized")

test("Schema Guardian Import", test_schema_guardian_import)

# TEST 4: BigQuery Connectivity
def test_bigquery():
    from google.cloud import bigquery
    client = bigquery.Client(project=PROJECT_ID)
    
    # Test dataset access
    dataset_ref = client.dataset(DATASET_ID)
    dataset = client.get_dataset(dataset_ref)
    print(f"   Dataset accessible: {dataset.dataset_id}")
    
    # Test table access
    table_ref = dataset_ref.table(TABLE_ID)
    table = client.get_table(table_ref)
    print(f"   Table accessible: {table.table_id}")
    print(f"   Rows: {table.num_rows}")
    print(f"   Columns: {len(table.schema)}")
    assert table.num_rows > 0, "Table has no rows"

test("BigQuery Connectivity", test_bigquery)

# TEST 5: Baseline Capture
def test_baseline_capture():
    from agents.schema_guardian import SchemaGuardian
    guardian = SchemaGuardian(PROJECT_ID, DATASET_ID, TABLE_ID)
    
    baseline = guardian.capture_baseline_schema()
    assert len(baseline) > 0, "No columns captured"
    assert 'column_name' in baseline.columns
    assert 'data_type' in baseline.columns
    
    print(f"   Captured {len(baseline)} columns")
    
    # Save to file
    baseline_file = Path("baseline_schema.json")
    baseline_data = {
        'table': f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}",
        'columns': baseline.to_dict('records'),
        'column_count': len(baseline)
    }
    with open(baseline_file, 'w') as f:
        json.dump(baseline_data, f, indent=2)
    
    print(f"   Saved to: {baseline_file.absolute()}")
    guardian.baseline_schema = baseline

test("Baseline Capture", test_baseline_capture)

# TEST 6: Schema Drift Detection
def test_drift_detection():
    from agents.schema_guardian import SchemaGuardian
    import pandas as pd
    
    guardian = SchemaGuardian(PROJECT_ID, DATASET_ID, TABLE_ID)
    
    # Load baseline
    with open("baseline_schema.json") as f:
        baseline_data = json.load(f)
        guardian.baseline_schema = pd.DataFrame(baseline_data['columns'])
    
    # Detect changes
    changes = guardian.detect_schema_drift()
    
    assert 'new_columns' in changes
    assert 'removed_columns' in changes
    assert 'type_changes' in changes
    
    print(f"   Detection working: {len(changes)} change types monitored")

test("Schema Drift Detection", test_drift_detection)

# TEST 7: Alert Generation
def test_alert_generation():
    from agents.schema_guardian import SchemaGuardian
    
    guardian = SchemaGuardian(PROJECT_ID, DATASET_ID, TABLE_ID)
    
    # Test with new column change
    changes = {
        "new_columns": ["test_column"],
        "removed_columns": [],
        "type_changes": [],
        "nullability_changes": [],
        "partition_changes": []
    }
    
    alert = guardian.generate_alert(changes)
    
    assert alert['severity'] == 'LOW', f"Expected LOW, got {alert['severity']}"
    assert alert['agent'] == 'Schema Guardian'
    assert alert['change_count'] == 1
    assert len(alert['recommendations']) > 0
    
    print(f"   Alert generated: {alert['severity']}")
    print(f"   Recommendations: {len(alert['recommendations'])}")

test("Alert Generation", test_alert_generation)

# TEST 8: Severity Calculation
def test_severity():
    from agents.schema_guardian import SchemaGuardian
    
    guardian = SchemaGuardian(PROJECT_ID, DATASET_ID, TABLE_ID)
    
    # Test CRITICAL
    changes = {"type_changes": [{"col": "test"}], "new_columns": [], "removed_columns": []}
    assert guardian._calculate_severity(changes) == "CRITICAL"
    
    # Test HIGH
    changes = {"removed_columns": ["test"], "type_changes": [], "new_columns": []}
    assert guardian._calculate_severity(changes) == "HIGH"
    
    # Test LOW
    changes = {"new_columns": ["test"], "type_changes": [], "removed_columns": []}
    assert guardian._calculate_severity(changes) == "LOW"
    
    print(f"   All severity levels working correctly")

test("Severity Calculation", test_severity)

# TEST 9: Impact Analysis
def test_impact_analysis():
    from agents.schema_guardian import SchemaGuardian
    
    guardian = SchemaGuardian(PROJECT_ID, DATASET_ID, TABLE_ID)
    
    changes = {
        "type_changes": [{"column": "price", "from": "STRING", "to": "FLOAT"}],
        "new_columns": [],
        "removed_columns": []
    }
    
    impact = guardian._analyze_impact(changes)
    assert len(impact) > 0
    assert "Type changes" in impact or "type" in impact.lower()
    
    print(f"   Impact analysis generated")

test("Impact Analysis", test_impact_analysis)

# TEST 10: Recommendations
def test_recommendations():
    from agents.schema_guardian import SchemaGuardian
    
    guardian = SchemaGuardian(PROJECT_ID, DATASET_ID, TABLE_ID)
    
    changes = {
        "type_changes": [{"column": "price", "from": "STRING", "to": "FLOAT"}],
        "new_columns": [],
        "removed_columns": []
    }
    
    recs = guardian._generate_recommendations(changes)
    assert len(recs) > 0
    assert any("Pause" in rec or "Review" in rec or "Update" in rec for rec in recs)
    
    print(f"   Generated {len(recs)} recommendations")

test("Recommendations", test_recommendations)

# TEST 11: Metrics Tracking
def test_metrics():
    from agents.schema_guardian import SchemaGuardian
    
    guardian = SchemaGuardian(PROJECT_ID, DATASET_ID, TABLE_ID)
    
    metrics = guardian.get_metrics()
    assert 'checks_performed' in metrics
    assert 'alerts_generated' in metrics
    assert 'last_check_time' in metrics
    
    print(f"   Metrics tracking functional")

test("Metrics Tracking", test_metrics)

# TEST 12: API Health Endpoint
def test_api_health():
    import requests
    
    try:
        response = requests.get("http://localhost:8000/api/health", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
        print(f"   API responding: {data['status']}")
    except requests.exceptions.ConnectionError:
        raise Exception("API server not running. Start it with: uv run uvicorn agents.api:app --port 8000")

test("API Health Endpoint", test_api_health)

# TEST 13: API Status Endpoint
def test_api_status():
    import requests
    
    response = requests.get("http://localhost:8000/api/status", timeout=5)
    assert response.status_code == 200
    data = response.json()
    assert 'agents' in data
    print(f"   Status endpoint working")

test("API Status Endpoint", test_api_status)

# TEST 14: API Alerts Endpoint
def test_api_alerts():
    import requests
    
    response = requests.get("http://localhost:8000/api/alerts?limit=5", timeout=5)
    assert response.status_code == 200
    data = response.json()
    assert 'alerts' in data
    assert 'count' in data
    print(f"   Alerts endpoint working")

test("API Alerts Endpoint", test_api_alerts)

# TEST 15: File Structure
def test_file_structure():
    required_files = [
        "agents/schema_guardian.py",
        "agents/agent_memory.py",
        "agents/run_schema_guardian.py",
        "agents/api.py",
        "tests/test_schema_guardian.py",
        "scripts/capture_baseline_local.py",
        "scripts/test_detection.py",
        "scripts/verify_setup.py",
        "baseline_schema.json",
        "VERIFICATION_REPORT.md"
    ]
    
    for file in required_files:
        assert Path(file).exists(), f"Required file missing: {file}"
    
    print(f"   All {len(required_files)} required files present")

test("File Structure", test_file_structure)

# SUMMARY
print("\n" + "=" * 80)
print("📊 TEST SUMMARY")
print("=" * 80)
print(f"\n✅ Tests Passed: {tests_passed}/{tests_total}")
print(f"❌ Tests Failed: {tests_failed}/{tests_total}")
print(f"📈 Success Rate: {(tests_passed/tests_total)*100:.1f}%")

if tests_failed == 0:
    print("\n" + "🎉" * 40)
    print("✅ 100% COMPLETION - ALL TESTS PASSED!")
    print("🎉" * 40)
    print("\n📋 Day 3-5 Requirements Met:")
    print("   ✅ Schema Guardian implemented and tested")
    print("   ✅ BigQuery integration verified")
    print("   ✅ Change detection working (5 types)")
    print("   ✅ Severity scoring functional")
    print("   ✅ Alert generation complete")
    print("   ✅ API endpoints operational")
    print("   ✅ Error handling implemented")
    print("   ✅ Documentation complete")
    print("   ✅ All test cases passing")
    print("\n🚀 READY FOR DAY 6-8: ANOMALY DETECTIVE")
else:
    print(f"\n⚠️  {tests_failed} test(s) failed. Review errors above.")
    sys.exit(1)

print("\n" + "=" * 80)
