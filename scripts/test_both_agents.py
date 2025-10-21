import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from agents.schema_guardian import SchemaGuardian
from agents.anomaly_detective import AnomalyDetective

load_dotenv()

def test_integrated_system():
    """Test both agents working together"""
    
    print("=" * 60)
    print("INTEGRATED SYSTEM TEST")
    print("=" * 60)
    
    # Test Schema Guardian
    print("\n1. Testing Schema Guardian...")
    guardian = SchemaGuardian(
        project_id=os.getenv("PROJECT_ID"),
        dataset_id=os.getenv("DATASET_ID"),
        table_id=os.getenv("TABLE_ID")
    )
    
    baseline = guardian.capture_baseline_schema()
    print(f"   ✅ Schema baseline: {len(baseline)} columns")
    
    changes = guardian.detect_schema_drift()
    if any(len(v) > 0 for v in changes.values() if isinstance(v, list)):
        print(f"   ⚠️  Schema changes detected")
    else:
        print(f"   ✅ Schema stable")
    
    # Test Anomaly Detective
    print("\n2. Testing Anomaly Detective...")
    detective = AnomalyDetective(
        project_id=os.getenv("PROJECT_ID"),
        dataset_id=os.getenv("DATASET_ID"),
        table_id=os.getenv("TABLE_ID")
    )
    
    result = detective.run_check()
    print(f"   ✅ Analysis complete: {result.get('confidence', 0):.0%} confidence")
    
    if result.get('has_anomalies'):
        print(f"   ⚠️  Found {len(result.get('anomalies', []))} anomaly types")
        for anomaly in result.get('anomalies', []):
            print(f"      - {anomaly['type']}: {anomaly['severity']}")
    else:
        print(f"   ✅ No anomalies detected")
    
    # Summary
    print("\n" + "=" * 60)
    print("SYSTEM STATUS")
    print("=" * 60)
    print("✅ Agent 1 (Schema Guardian): Operational")
    print("✅ Agent 2 (Anomaly Detective): Operational")
    print(f"✅ Vertex AI Gemini: {result.get('agent', 'Unknown')}")
    print("\n🚀 Both agents ready for Day 8 checkpoint!")
    print("=" * 60)

if __name__ == "__main__":
    test_integrated_system()
