"""
Load warehouse.db data to BigQuery
Uses GOOGLE_APPLICATION_CREDENTIALS environment variable
"""
import duckdb
import os
from google.cloud import bigquery
import json
from datetime import datetime

def load_to_bigquery():
    """Load local warehouse data to BigQuery"""
    
    print("=" * 80)
    print("LOADING DATA TO BIGQUERY - DAY 2 COMPLETION")
    print("=" * 80)
    
    # Use environment variable for credentials
    credentials_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    
    if not credentials_path:
        print("❌ GOOGLE_APPLICATION_CREDENTIALS environment variable not set")
        print("\nSet it with:")
        print('  $env:GOOGLE_APPLICATION_CREDENTIALS="D:\\osprey\\osprey-credentials.json"')
        return False
    
    if not os.path.exists(credentials_path):
        print(f"❌ Credentials file not found: {credentials_path}")
        return False
    
    # Get project ID from credentials
    with open(credentials_path) as f:
        creds_data = json.load(f)
        project_id = creds_data.get("project_id")
    
    print(f"\n✅ Using credentials: {credentials_path}")
    print(f"✅ Project ID: {project_id}")
    
    # Create BigQuery client
    bq_client = bigquery.Client(project=project_id)
    
    # Connect to local warehouse
    print("\n[STEP 1/4] Reading local warehouse data...")
    db_path = "D:/osprey/connector/files/warehouse.db"
    
    if not os.path.exists(db_path):
        print(f"  ❌ Warehouse not found: {db_path}")
        print("  Run: cd D:/osprey/connector && fivetran debug --configuration test_config.json")
        return False
    
    conn = duckdb.connect(db_path)
    
    # Get column names and filter out Fivetran internal columns
    columns_query = conn.execute("SELECT * FROM tester.raw_news LIMIT 0").description
    all_columns = [desc[0] for desc in columns_query]
    
    fivetran_columns = ['_fivetran_deleted', '_fivetran_synced', '_fivetran_id']
    data_columns = [col for col in all_columns if col not in fivetran_columns]
    
    select_clause = ", ".join(data_columns)
    
    print(f"  Exporting {len(data_columns)} columns...")
    
    # Export data
    result = conn.execute(f"SELECT {select_clause} FROM tester.raw_news").fetchall()
    
    records = []
    for row in result:
        record = {}
        for col, val in zip(data_columns, row):
            if isinstance(val, datetime):
                record[col] = val.isoformat()
            else:
                record[col] = val
        records.append(record)
    
    conn.close()
    
    print(f"  ✅ Loaded {len(records)} articles from warehouse")
    
    # Upload to BigQuery
    print("\n[STEP 2/4] Uploading to BigQuery...")
    table_id = f"{project_id}.osprey_data.raw_news"
    
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_TRUNCATE",
        autodetect=False
    )
    
    try:
        job = bq_client.load_table_from_json(
            records,
            table_id,
            job_config=job_config
        )
        
        job.result()
        print(f"  ✅ Uploaded {len(records)} records to BigQuery")
        
    except Exception as e:
        print(f"  ❌ Upload failed: {e}")
        return False
    
    # Add table partitioning
    print("\n[STEP 3/4] Adding table partitioning on published_at...")
    try:
        # Create partitioned table
        partitioned_table_id = f"{project_id}.osprey_data.raw_news_partitioned"
        
        create_query = f"""
        CREATE OR REPLACE TABLE `{partitioned_table_id}`
        PARTITION BY DATE(published_at)
        CLUSTER BY stock_symbols, sentiment_label
        AS SELECT * FROM `{table_id}`
        """
        
        job = bq_client.query(create_query)
        job.result()
        
        print(f"  ✅ Created partitioned table: raw_news_partitioned")
        print(f"     Partitioned by: DATE(published_at)")
        print(f"     Clustered by: stock_symbols, sentiment_label")
        
        # Get partition info
        partition_query = f"""
        SELECT 
            COUNT(DISTINCT DATE(published_at)) as num_partitions,
            MIN(DATE(published_at)) as earliest_partition,
            MAX(DATE(published_at)) as latest_partition
        FROM `{partitioned_table_id}`
        """
        
        result = bq_client.query(partition_query).result()
        for row in result:
            print(f"     Partitions: {row.num_partitions}")
            print(f"     Date range: {row.earliest_partition} to {row.latest_partition}")
        
    except Exception as e:
        print(f"  ⚠️  Partitioning warning: {e}")
        print(f"  Continuing with non-partitioned table...")
    
    # Verify data
    print("\n[STEP 4/4] Verifying data in BigQuery...")
    
    verify_query = f"""
        SELECT 
            COUNT(*) as total,
            COUNT(DISTINCT stock_symbols) as unique_stocks,
            COUNT(DISTINCT sentiment_label) as unique_sentiments,
            COUNT(DISTINCT source) as unique_sources,
            MIN(published_at) as earliest,
            MAX(published_at) as latest
        FROM `{table_id}`
        WHERE DATE(published_at) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
    """
    
    result = bq_client.query(verify_query).result()
    
    for row in result:
        print(f"\n  📊 Data Statistics:")
        print(f"     Total articles: {row.total}")
        print(f"     Unique stocks: {row.unique_stocks}")
        print(f"     Unique sentiments: {row.unique_sentiments}")
        print(f"     Unique sources: {row.unique_sources}")
        print(f"     Date range: {row.earliest} to {row.latest}")
    
    # Sample data
    sample_query = f"""
        SELECT title, source, stock_symbols, sentiment_label, published_at
        FROM `{table_id}`
        WHERE DATE(published_at) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
        ORDER BY published_at DESC
        LIMIT 5
    """
    
    print("\n  📰 Sample Articles:")
    result = bq_client.query(sample_query).result()
    
    for i, row in enumerate(result, 1):
        print(f"\n  [{i}] {row.title[:65]}...")
        print(f"      Source: {row.source} | Stocks: {row.stock_symbols}")
        print(f"      Sentiment: {row.sentiment_label} | Date: {row.published_at}")
    
    print("\n" + "=" * 80)
    print("✅ BIGQUERY LOADING COMPLETE!")
    print("=" * 80)
    
    return True, project_id, len(records)

if __name__ == "__main__":
    success, project_id, count = load_to_bigquery()
    
    if success:
        print(f"\n📍 Data Location:")
        print(f"   Project: {project_id}")
        print(f"   Dataset: osprey_data")
        print(f"   Table: raw_news ({count} rows)")
        print(f"\n➡️  Next: Run end-to-end tests")
        print(f"   python ..\\scripts\\test_end_to_end.py")
