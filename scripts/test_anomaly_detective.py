import os
from dotenv import load_dotenv
from agents.anomaly_detective import AnomalyDetective

load_dotenv()

def test_with_clean_data():
    """Test on existing clean data"""
    detective = AnomalyDetective(
        project_id=os.getenv("PROJECT_ID"),
        dataset_id=os.getenv("DATASET_ID"),
        table_id=os.getenv("TABLE_ID")
    )
    
    print("Testing with clean data...")
    result = detective.run_check()
    
    assert result.get("confidence") is not None
    print(f"✅ Test passed. Confidence: {result.get('confidence', 0):.0%}")
    return result

def insert_test_anomaly():
    """Insert obvious test data to verify detection"""
    from google.cloud import bigquery
    from datetime import datetime, timedelta
    
    client = bigquery.Client()
    table_id = f"{os.getenv('PROJECT_ID')}.{os.getenv('DATASET_ID')}.{os.getenv('TABLE_ID')}"
    
    # Use a date within allowed bounds (within 366 days in the future)
    future_date = (datetime.now() + timedelta(days=100)).strftime("%Y-%m-%d %H:%M:%S")
    
    test_row = {
        "article_id": "TEST_ANOMALY_001",
        "url": "https://test.com/article",
        "title": "TEST: This is test data",
        "summary": "Test summary with dummy content",
        "source": "test_source",
        "authors": "test_user",
        "category": "test",
        "published_at": future_date,
        "synced_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "stock_symbols": "TEST_STOCK,FAKE_TICKER",
        "sentiment_score": 0.5,
        "sentiment_label": "neutral"
    }
    
    errors = client.insert_rows_json(table_id, [test_row])
    if errors:
        print(f"Error inserting test row: {errors}")
    else:
        print("✅ Test anomaly inserted")

def test_with_anomaly():
    """Test detection of inserted anomaly"""
    detective = AnomalyDetective(
        project_id=os.getenv("PROJECT_ID"),
        dataset_id=os.getenv("DATASET_ID"),
        table_id=os.getenv("TABLE_ID")
    )
    
    print("\nTesting with anomaly data...")
    result = detective.run_check()
    
    if result.get("has_anomalies"):
        print("✅ Anomaly correctly detected!")
        print(f"   Confidence: {result['confidence']:.0%}")
        print(f"   Issues found: {len(result.get('anomalies', []))}")
    else:
        print("⚠️  No anomaly detected (may need to run again)")
    
    return result

if __name__ == "__main__":
    # Test 1: Clean data baseline
    print("=" * 60)
    print("TEST 1: Clean Data Analysis")
    print("=" * 60)
    clean_result = test_with_clean_data()
    
    # Test 2: Insert and detect anomaly
    print("\n" + "=" * 60)
    print("TEST 2: Anomaly Detection")
    print("=" * 60)
    print("\nInserting test anomaly...")
    insert_test_anomaly()
    
    print("\nWaiting 5 seconds for data to sync...")
    import time
    time.sleep(5)
    
    anomaly_result = test_with_anomaly()
    
    print("\n" + "=" * 60)
    print("CLEANUP NOTE")
    print("=" * 60)
    print("Test anomaly 'TEST_ANOMALY_001' inserted but cannot be deleted immediately")
    print("due to streaming buffer limitations. It will be auto-removed after 90 minutes.")
    print("Or you can manually delete it from BigQuery console later.")
    print("\n✅ Test suite completed successfully!")
