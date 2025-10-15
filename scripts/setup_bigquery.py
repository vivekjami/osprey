"""
Setup BigQuery tables and deploy connector
This completes Day 2 - 100%
"""
import subprocess
import json
import os
from google.cloud import bigquery
from google.oauth2 import service_account

def setup_bigquery():
    """Setup BigQuery dataset and tables"""
    
    print("=" * 80)
    print("BIGQUERY SETUP - DAY 2 COMPLETION")
    print("=" * 80)
    
    # Set environment variable
    credentials_path = os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
    
    print("\n[STEP 1/5] Loading GCP credentials...")
    try:
        credentials = service_account.Credentials.from_service_account_file(
            credentials_path,
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        
        with open(credentials_path) as f:
            creds_data = json.load(f)
            project_id = creds_data.get("project_id")
        
        print(f"  ✅ Project ID: {project_id}")
        
    except Exception as e:
        print(f"  ❌ Error loading credentials: {e}")
        return False
    
    # Create BigQuery client
    print("\n[STEP 2/5] Connecting to BigQuery...")
    try:
        client = bigquery.Client(
            credentials=credentials,
            project=project_id
        )
        print(f"  ✅ Connected to BigQuery")
    except Exception as e:
        print(f"  ❌ Connection failed: {e}")
        return False
    
    # Create dataset
    dataset_id = "osprey_data"
    dataset_ref = f"{project_id}.{dataset_id}"
    
    print(f"\n[STEP 3/5] Creating dataset: {dataset_id}...")
    try:
        dataset = bigquery.Dataset(dataset_ref)
        dataset.location = "US"
        dataset.description = "Osprey multi-agent data quality system - financial news data"
        
        # Try to create, ignore if exists
        try:
            dataset = client.create_dataset(dataset, exists_ok=True)
            print(f"  ✅ Dataset created/verified: {dataset_id}")
        except Exception as e:
            if "Already Exists" in str(e):
                print(f"  ✅ Dataset already exists: {dataset_id}")
            else:
                raise
    except Exception as e:
        print(f"  ❌ Dataset creation failed: {e}")
        return False
    
    # Create raw_news table
    print("\n[STEP 4/5] Creating raw_news table...")
    try:
        table_id = f"{dataset_ref}.raw_news"
        
        schema = [
            bigquery.SchemaField("article_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("url", "STRING"),
            bigquery.SchemaField("title", "STRING"),
            bigquery.SchemaField("summary", "STRING"),
            bigquery.SchemaField("source", "STRING"),
            bigquery.SchemaField("authors", "STRING"),
            bigquery.SchemaField("category", "STRING"),
            bigquery.SchemaField("published_at", "TIMESTAMP"),
            bigquery.SchemaField("synced_at", "TIMESTAMP"),
            bigquery.SchemaField("stock_symbols", "STRING"),
            bigquery.SchemaField("topics", "STRING"),
            bigquery.SchemaField("sentiment_score", "FLOAT64"),
            bigquery.SchemaField("sentiment_label", "STRING"),
            bigquery.SchemaField("ticker_sentiments", "STRING"),
        ]
        
        table = bigquery.Table(table_id, schema=schema)
        table.description = "Raw financial news articles from NewsAPI"
        
        table = client.create_table(table, exists_ok=True)
        print(f"  ✅ Table created/verified: raw_news")
        
    except Exception as e:
        print(f"  ❌ Table creation failed: {e}")
        return False
    
    # Create agent_logs table
    print("\n[STEP 5/5] Creating agent_logs table...")
    try:
        table_id = f"{dataset_ref}.agent_logs"
        
        schema = [
            bigquery.SchemaField("log_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("agent_name", "STRING"),
            bigquery.SchemaField("timestamp", "TIMESTAMP"),
            bigquery.SchemaField("action", "STRING"),
            bigquery.SchemaField("details", "STRING"),
            bigquery.SchemaField("status", "STRING"),
        ]
        
        table = bigquery.Table(table_id, schema=schema)
        table.description = "Agent activity logs for monitoring"
        
        table = client.create_table(table, exists_ok=True)
        print(f"  ✅ Table created/verified: agent_logs")
        
    except Exception as e:
        print(f"  ❌ Table creation failed: {e}")
        return False
    
    # Verify tables
    print("\n" + "=" * 80)
    print("VERIFICATION")
    print("=" * 80)
    
    tables = list(client.list_tables(dataset_ref))
    print(f"\nTables in {dataset_id}:")
    for table in tables:
        row_count = client.get_table(f"{dataset_ref}.{table.table_id}").num_rows
        print(f"  ✅ {table.table_id} ({row_count} rows)")
    
    print("\n" + "=" * 80)
    print("🎉 BIGQUERY SETUP COMPLETE!")
    print("=" * 80)
    print(f"\nDataset: {dataset_ref}")
    print(f"Tables: raw_news, agent_logs")
    print("\n➡️  NEXT: Load sample data to BigQuery")
    print("\nRun: python ../scripts/load_to_bigquery.py")
    
    return True

if __name__ == "__main__":
    setup_bigquery()
