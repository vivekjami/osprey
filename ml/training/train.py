"""
Training data pipeline for BigQuery ML anomaly detection model.

This module prepares labeled training data from raw_news and quarantined records.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import logging
from typing import Dict, Any, Optional
from google.cloud import bigquery
from google.cloud.exceptions import NotFound
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TrainingDataPipeline:
    """Pipeline for creating labeled training data for anomaly detection model."""
    
    def __init__(self, project_id: str, dataset_id: str = "osprey_data", table_id: str = "raw_news"):
        """
        Initialize the training data pipeline.
        
        Args:
            project_id: GCP project ID
            dataset_id: BigQuery dataset ID
            table_id: Source table name
        """
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.table_id = table_id
        self.client = bigquery.Client(project=project_id)
        self.training_table_id = "training_data"
        
        logger.info(f"Initialized TrainingDataPipeline for {project_id}.{dataset_id}.{table_id}")
    
    def prepare_training_data(self) -> Dict[str, Any]:
        """
        Create training data table with engineered features and labels.
        
        Creates a table with:
        - Engineered features (title_length, content_length, etc.)
        - Label (is_test_data) based on quarantine status or pattern matching
        - Train/test split ready data
        
        Returns:
            Dict with statistics about the created training data
        """
        logger.info("Starting training data preparation...")
        
        # SQL query to create training data with features
        query = f"""
        CREATE OR REPLACE TABLE `{self.project_id}.{self.dataset_id}.{self.training_table_id}` AS
        WITH labeled_data AS (
          SELECT
            article_id,
            -- Engineered features
            sentiment_score,
            LENGTH(title) as title_length,
            LENGTH(content) as content_length,
            ARRAY_LENGTH(SPLIT(stock_symbols, ',')) as num_stocks,
            TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), published_at, HOUR) as age_hours,
            EXTRACT(HOUR FROM published_at) as published_hour,
            
            -- Label: is this test data or anomaly?
            CASE
              -- Check if in quarantine (explicit label)
              WHEN article_id IN (
                SELECT article_id 
                FROM `{self.project_id}.{self.dataset_id}.quarantine` 
                WHERE reason LIKE '%test%'
              ) THEN TRUE
              
              -- Pattern-based labeling for test data
              WHEN REGEXP_CONTAINS(LOWER(title), r'test|dummy|fake|lorem|placeholder|qa_|dev_')
                OR REGEXP_CONTAINS(LOWER(author), r'test|dummy|fake|qa_|dev_|admin_test')
                OR stock_symbols LIKE '%TEST%'
                OR stock_symbols LIKE '%FAKE%'
                OR EXTRACT(YEAR FROM published_at) > 2030
                OR EXTRACT(YEAR FROM published_at) < 2000
              THEN TRUE
              
              -- Otherwise, assume it's clean data
              ELSE FALSE
            END as is_test_data
          
          FROM `{self.project_id}.{self.dataset_id}.{self.table_id}`
          
          -- Filter out rows with null critical fields
          WHERE published_at IS NOT NULL
            AND title IS NOT NULL
            AND content IS NOT NULL
            AND sentiment_score IS NOT NULL
        )
        
        SELECT 
          *,
          -- Add random split column for train/test
          RAND() as random_split
        FROM labeled_data
        """
        
        try:
            logger.info("Executing training data creation query...")
            query_job = self.client.query(query)
            query_job.result()  # Wait for completion
            
            logger.info(f"✅ Training data table created: {self.training_table_id}")
            
            # Get statistics
            stats = self.get_statistics()
            
            logger.info(f"Training data statistics: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"❌ Error creating training data: {e}")
            raise
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the training data.
        
        Returns:
            Dict with total rows, positive examples, negative examples, and class balance
        """
        query = f"""
        SELECT
          COUNT(*) as total_rows,
          COUNTIF(is_test_data = TRUE) as positive_examples,
          COUNTIF(is_test_data = FALSE) as negative_examples,
          ROUND(COUNTIF(is_test_data = TRUE) / COUNT(*) * 100, 2) as positive_percentage,
          
          -- Feature statistics
          AVG(sentiment_score) as avg_sentiment,
          AVG(title_length) as avg_title_length,
          AVG(content_length) as avg_content_length,
          AVG(num_stocks) as avg_num_stocks
          
        FROM `{self.project_id}.{self.dataset_id}.{self.training_table_id}`
        """
        
        try:
            result = self.client.query(query).result()
            row = list(result)[0]
            
            stats = {
                "total_rows": row.total_rows,
                "positive_examples": row.positive_examples,
                "negative_examples": row.negative_examples,
                "positive_percentage": row.positive_percentage,
                "avg_sentiment": float(row.avg_sentiment) if row.avg_sentiment else 0,
                "avg_title_length": float(row.avg_title_length) if row.avg_title_length else 0,
                "avg_content_length": float(row.avg_content_length) if row.avg_content_length else 0,
                "avg_num_stocks": float(row.avg_num_stocks) if row.avg_num_stocks else 0,
                "timestamp": datetime.now().isoformat()
            }
            
            # Check class balance
            if stats["positive_percentage"] < 5:
                logger.warning(f"⚠️  Low positive examples: {stats['positive_percentage']}% - may need more labeled data")
            elif stats["positive_percentage"] > 50:
                logger.warning(f"⚠️  High positive examples: {stats['positive_percentage']}% - dataset may be imbalanced")
            else:
                logger.info(f"✅ Good class balance: {stats['positive_percentage']}% positive examples")
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Error getting statistics: {e}")
            return {
                "total_rows": 0,
                "positive_examples": 0,
                "negative_examples": 0,
                "positive_percentage": 0,
                "error": str(e)
            }
    
    def validate_training_data(self) -> bool:
        """
        Validate that training data meets minimum requirements.
        
        Returns:
            True if data is valid for training, False otherwise
        """
        stats = self.get_statistics()
        
        # Validation criteria
        min_total_rows = 50
        min_positive_examples = 10
        min_positive_percentage = 5
        max_positive_percentage = 50
        
        is_valid = (
            stats["total_rows"] >= min_total_rows and
            stats["positive_examples"] >= min_positive_examples and
            min_positive_percentage <= stats["positive_percentage"] <= max_positive_percentage
        )
        
        if is_valid:
            logger.info("✅ Training data validation passed")
        else:
            logger.error(f"❌ Training data validation failed:")
            logger.error(f"   Total rows: {stats['total_rows']} (minimum: {min_total_rows})")
            logger.error(f"   Positive examples: {stats['positive_examples']} (minimum: {min_positive_examples})")
            logger.error(f"   Positive %: {stats['positive_percentage']}% (range: {min_positive_percentage}-{max_positive_percentage}%)")
        
        return is_valid
    
    def export_training_data(self, output_path: str) -> None:
        """
        Export training data to CSV for external analysis.
        
        Args:
            output_path: Local file path to save CSV
        """
        query = f"""
        SELECT 
          article_id,
          sentiment_score,
          title_length,
          content_length,
          num_stocks,
          age_hours,
          published_hour,
          is_test_data,
          random_split
        FROM `{self.project_id}.{self.dataset_id}.{self.training_table_id}`
        ORDER BY random_split
        """
        
        try:
            logger.info(f"Exporting training data to {output_path}...")
            df = self.client.query(query).to_dataframe()
            df.to_csv(output_path, index=False)
            logger.info(f"✅ Exported {len(df)} rows to {output_path}")
        except Exception as e:
            logger.error(f"❌ Error exporting training data: {e}")
            raise


def main():
    """Run training data pipeline."""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    project_id = os.getenv("PROJECT_ID", "osprey-hackathon-2025")
    
    pipeline = TrainingDataPipeline(project_id=project_id)
    
    # Create training data
    stats = pipeline.prepare_training_data()
    
    print("\n" + "="*60)
    print("TRAINING DATA STATISTICS")
    print("="*60)
    print(f"Total rows: {stats.get('total_rows', 0)}")
    print(f"Positive examples (anomalies): {stats.get('positive_examples', 0)}")
    print(f"Negative examples (clean): {stats.get('negative_examples', 0)}")
    print(f"Positive percentage: {stats.get('positive_percentage', 0)}%")
    print(f"\nFeature Averages:")
    print(f"  Sentiment score: {stats.get('avg_sentiment', 0):.3f}")
    print(f"  Title length: {stats.get('avg_title_length', 0):.1f} chars")
    print(f"  Content length: {stats.get('avg_content_length', 0):.1f} chars")
    print(f"  Num stocks: {stats.get('avg_num_stocks', 0):.1f}")
    print("="*60)
    
    # Validate
    if pipeline.validate_training_data():
        print("\n✅ Training data ready for model training!")
    else:
        print("\n❌ Training data needs more labeled examples")


if __name__ == "__main__":
    main()
