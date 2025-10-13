from google.cloud import bigquery
import os
from dotenv import load_dotenv

load_dotenv()

def create_bigquery_tables():
    """Create BigQuery tables for Osprey"""
    
    project_id = os.getenv("PROJECT_ID", "osprey-hackathon-2025")
    dataset_id = os.getenv("DATASET_ID", "osprey_data")
    
    client = bigquery.Client(project=project_id)
    
    # Table 1: raw_news (main data table)
    table_id = f"{project_id}.{dataset_id}.raw_news"
    
    schema = [
        bigquery.SchemaField("article_id", "STRING", mode="REQUIRED",
            description="Unique article identifier (MD5 hash of URL + timestamp)"),
        bigquery.SchemaField("url", "STRING", mode="REQUIRED",
            description="Article URL"),
        bigquery.SchemaField("title", "STRING", mode="REQUIRED",
            description="Article headline"),
        bigquery.SchemaField("summary", "STRING", mode="NULLABLE",
            description="Article summary/excerpt"),
        bigquery.SchemaField("source", "STRING", mode="REQUIRED",
            description="News source (Reuters, Bloomberg, etc.)"),
        bigquery.SchemaField("authors", "STRING", mode="NULLABLE",
            description="Comma-separated author names"),
        bigquery.SchemaField("category", "STRING", mode="NULLABLE",
            description="Article category"),
        bigquery.SchemaField("published_at", "TIMESTAMP", mode="REQUIRED",
            description="Publication timestamp"),
        bigquery.SchemaField("synced_at", "TIMESTAMP", mode="REQUIRED",
            description="Fivetran sync timestamp"),
        bigquery.SchemaField("stock_symbols", "STRING", mode="NULLABLE",
            description="Comma-separated stock tickers"),
        bigquery.SchemaField("topics", "STRING", mode="NULLABLE",
            description="JSON array of topic tags"),
        bigquery.SchemaField("sentiment_score", "FLOAT64", mode="NULLABLE",
            description="Overall sentiment score (-1 to 1)"),
        bigquery.SchemaField("sentiment_label", "STRING", mode="NULLABLE",
            description="Sentiment label (Bearish, Neutral, Bullish)"),
        bigquery.SchemaField("ticker_sentiments", "STRING", mode="NULLABLE",
            description="JSON array of per-ticker sentiment"),
    ]
    
    table = bigquery.Table(table_id, schema=schema)
    
    # Configure partitioning by day
    table.time_partitioning = bigquery.TimePartitioning(
        type_=bigquery.TimePartitioningType.DAY,
        field="published_at",
        require_partition_filter=True
    )
    
    # Configure clustering for better query performance
    table.clustering_fields = ["source", "sentiment_label"]
    
    # Add table description
    table.description = "Financial news articles from Alpha Vantage API"
    
    # Create table
    try:
        table = client.create_table(table, exists_ok=True)
        print(f"✅ Created table: {table.project}.{table.dataset_id}.{table.table_id}")
    except Exception as e:
        print(f"❌ Error creating table: {str(e)}")
        return False
    
    # Table 2: quarantine (for suspicious data)
    quarantine_schema = schema + [
        bigquery.SchemaField("quarantined_at", "TIMESTAMP", mode="REQUIRED",
            description="When the record was quarantined"),
        bigquery.SchemaField("quarantine_reason", "STRING", mode="REQUIRED",
            description="Why the record was quarantined"),
        bigquery.SchemaField("detected_by_agent", "STRING", mode="REQUIRED",
            description="Which agent flagged this record"),
    ]
    
    quarantine_table_id = f"{project_id}.{dataset_id}.quarantine"
    quarantine_table = bigquery.Table(quarantine_table_id, quarantine_schema)
    
    try:
        quarantine_table = client.create_table(quarantine_table, exists_ok=True)
        print(f"✅ Created quarantine table: {quarantine_table.project}.{quarantine_table.dataset_id}.{quarantine_table.table_id}")
    except Exception as e:
        print(f"❌ Error creating quarantine table: {str(e)}")
        return False
    
    # Table 3: agent_logs (for tracking agent activities)
    agent_logs_schema = [
        bigquery.SchemaField("log_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("agent_name", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("action", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("details", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("status", "STRING", mode="REQUIRED"),
    ]
    
    logs_table_id = f"{project_id}.{dataset_id}.agent_logs"
    logs_table = bigquery.Table(logs_table_id, agent_logs_schema)
    logs_table.time_partitioning = bigquery.TimePartitioning(
        type_=bigquery.TimePartitioningType.DAY,
        field="timestamp"
    )
    
    try:
        logs_table = client.create_table(logs_table, exists_ok=True)
        print(f"✅ Created agent_logs table: {logs_table.project}.{logs_table.dataset_id}.{logs_table.table_id}")
    except Exception as e:
        print(f"❌ Error creating logs table: {str(e)}")
        return False
    
    print("\n🎉 All tables created successfully!")
    return True

if __name__ == "__main__":
    create_bigquery_tables()