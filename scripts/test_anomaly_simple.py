import os
from dotenv import load_dotenv
from agents.anomaly_detective import AnomalyDetective

load_dotenv()

def simple_test():
    """Simple test on existing data"""
    print("=" * 60)
    print("ANOMALY DETECTIVE - SIMPLE TEST")
    print("=" * 60)
    
    detective = AnomalyDetective(
        project_id=os.getenv("PROJECT_ID"),
        dataset_id=os.getenv("DATASET_ID"),
        table_id=os.getenv("TABLE_ID")
    )
    
    print("\n1. Sampling latest 20 rows...")
    data = detective.sample_latest_data(limit=20)
    print(f"   ✅ Retrieved {len(data)} rows")
    
    print("\n2. Running Gemini analysis...")
    result = detective.run_check()
    
    print("\n3. Results:")
    print(f"   - Has Anomalies: {result.get('has_anomalies', False)}")
    print(f"   - Confidence: {result.get('confidence', 0):.0%}")
    print(f"   - Anomalies Found: {len(result.get('anomalies', []))}")
    
    if result.get('anomalies'):
        print("\n4. Anomaly Details:")
        for i, anomaly in enumerate(result.get('anomalies', []), 1):
            print(f"\n   Anomaly #{i}:")
            print(f"   - Type: {anomaly.get('type')}")
            print(f"   - Severity: {anomaly.get('severity')}")
            print(f"   - Field: {anomaly.get('field')}")
            print(f"   - Affected Rows: {anomaly.get('affected_row_count')}")
    
    print("\n" + "=" * 60)
    print("✅ TEST COMPLETED SUCCESSFULLY")
    print("=" * 60)
    
    return result

if __name__ == "__main__":
    simple_test()
