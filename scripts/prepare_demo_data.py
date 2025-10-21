"""
Demo data generator for Osprey presentation.

Creates clean data, obvious test data, and subtle anomalies for reliable demos.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import argparse
import logging
from datetime import datetime, timedelta
import random
from typing import List, Dict, Any
from google.cloud import bigquery
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()


class DemoDataGenerator:
    """Generate demo data for presentations and testing."""
    
    # Real stock symbols for clean data
    REAL_STOCKS = [
        "AAPL", "GOOGL", "MSFT", "TSLA", "AMZN",
        "NVDA", "META", "NFLX", "AMD", "INTC",
        "PYPL", "DIS", "BA", "JPM", "V"
    ]
    
    # Real news sources
    REAL_AUTHORS = [
        "Reuters", "Bloomberg", "CNBC", "MarketWatch",
        "Financial Times", "WSJ", "Barrons", "Seeking Alpha"
    ]
    
    # Test patterns for obvious anomalies
    TEST_STOCKS = ["TEST_STOCK", "FAKE_TICKER", "QA_TEST", "DEV_SYMBOL", "DUMMY_STOCK"]
    TEST_AUTHORS = ["test_user_42", "qa_account", "admin_test", "dev_user", "test_automation"]
    
    def __init__(self, project_id: str, dataset_id: str = "osprey_data", table_id: str = "raw_news"):
        """
        Initialize demo data generator.
        
        Args:
            project_id: GCP project ID
            dataset_id: BigQuery dataset ID
            table_id: Target table name
        """
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.table_id = table_id
        self.client = bigquery.Client(project=project_id)
        
        logger.info(f"Initialized DemoDataGenerator for {project_id}.{dataset_id}.{table_id}")
    
    def insert_clean_data(self, count: int = 100) -> int:
        """
        Insert clean, realistic financial news data.
        
        Args:
            count: Number of articles to insert
        
        Returns:
            Number of rows inserted
        """
        logger.info(f"Inserting {count} clean articles...")
        
        # Title templates for realistic news
        title_templates = [
            "{stock} shares surge {pct}% on strong earnings report",
            "Tech giant {stock} announces new product lineup",
            "{stock} stock drops {pct}% amid market concerns",
            "Analysts upgrade {stock} with bullish forecast",
            "Breaking: {stock} reaches all-time high",
            "{stock} Q{q} earnings beat expectations",
            "Market analysis: Why {stock} is trending today",
            "{stock} announces major acquisition deal",
            "Investors eye {stock} ahead of earnings call",
            "{stock} stock rallies on positive news"
        ]
        
        rows_to_insert = []
        base_time = datetime.now() - timedelta(days=7)
        
        for i in range(count):
            stock = random.choice(self.REAL_STOCKS)
            author = random.choice(self.REAL_AUTHORS)
            
            # Generate realistic title
            template = random.choice(title_templates)
            title = template.format(
                stock=stock,
                pct=random.randint(2, 15),
                q=random.randint(1, 4)
            )
            
            # Generate content
            content = f"In financial news today, {stock} has shown significant movement in the market. "
            content += f"Analysts from {author} are closely monitoring the situation. "
            content += "Industry experts suggest this trend may continue as market conditions evolve."
            
            # Realistic timestamp (spread across 7 days)
            published_at = base_time + timedelta(
                days=random.randint(0, 7),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )
            
            # Realistic sentiment (normal distribution around 0, range -0.8 to 0.8)
            sentiment = random.gauss(0, 0.3)
            sentiment = max(-0.8, min(0.8, sentiment))  # Clamp to realistic range
            
            row = {
                "article_id": f"clean_{i}_{int(datetime.now().timestamp())}",
                "title": title,
                "content": content,
                "author": author,
                "source": author,
                "published_at": published_at.isoformat(),
                "url": f"https://example.com/article/{i}",
                "stock_symbols": ",".join(random.sample(self.REAL_STOCKS, random.randint(1, 3))),
                "sentiment_score": round(sentiment, 3),
                "category": "financial_news"
            }
            
            rows_to_insert.append(row)
        
        # Insert into BigQuery
        table_ref = f"{self.project_id}.{self.dataset_id}.{self.table_id}"
        errors = self.client.insert_rows_json(table_ref, rows_to_insert)
        
        if errors:
            logger.error(f"❌ Errors inserting clean data: {errors}")
            return 0
        else:
            logger.info(f"✅ Inserted {count} clean articles")
            return count
    
    def insert_test_data(self, count: int = 50) -> int:
        """
        Insert obvious test data with clear patterns.
        
        Args:
            count: Number of test articles to insert
        
        Returns:
            Number of rows inserted
        """
        logger.info(f"Inserting {count} obvious test articles...")
        
        test_title_patterns = [
            "TEST: {stock} article for QA verification",
            "SANDBOX: Market analysis for {stock}",
            "QA TEST - {stock} news validation",
            "[DEV] {stock} test data entry",
            "PLACEHOLDER: {stock} article content",
            "DUMMY article about {stock} for testing"
        ]
        
        rows_to_insert = []
        
        for i in range(count):
            test_stock = random.choice(self.TEST_STOCKS)
            test_author = random.choice(self.TEST_AUTHORS)
            
            # Obvious test title
            title = random.choice(test_title_patterns).format(stock=test_stock)
            
            # Test content
            content = "This is test data. Lorem ipsum dolor sit amet. "
            content += "QA validation placeholder text. This should be filtered out."
            
            # Obvious anomalies:
            # 1. Future date (2099)
            # 2. Exactly 0.5 sentiment (suspicious)
            # 3. Test author
            # 4. Test stock symbol
            
            published_at = datetime(2099, 1, 1, 12, 0, 0) if i % 3 == 0 else datetime.now()
            
            row = {
                "article_id": f"test_{i}_{int(datetime.now().timestamp())}",
                "title": title,
                "content": content,
                "author": test_author,
                "source": "test_source",
                "published_at": published_at.isoformat(),
                "url": f"https://test.example.com/article/{i}",
                "stock_symbols": ",".join([test_stock, random.choice(self.TEST_STOCKS)]),
                "sentiment_score": 0.5,  # Suspiciously exact
                "category": "test_data"
            }
            
            rows_to_insert.append(row)
        
        # Insert into BigQuery
        table_ref = f"{self.project_id}.{self.dataset_id}.{self.table_id}"
        errors = self.client.insert_rows_json(table_ref, rows_to_insert)
        
        if errors:
            logger.error(f"❌ Errors inserting test data: {errors}")
            return 0
        else:
            logger.info(f"✅ Inserted {count} test articles (will trigger anomaly detection)")
            return count
    
    def insert_subtle_anomalies(self, count: int = 30) -> int:
        """
        Insert subtle statistical anomalies that AI/ML should catch.
        
        Args:
            count: Number of subtle anomalies to insert
        
        Returns:
            Number of rows inserted
        """
        logger.info(f"Inserting {count} subtle anomalies...")
        
        rows_to_insert = []
        
        # All articles at exactly midnight (temporal pattern)
        published_at = datetime.now().replace(hour=0, minute=0, second=0)
        
        # Single author for all articles (suspicious)
        single_author = "SuspiciousBot"
        
        for i in range(count):
            stock = random.choice(self.REAL_STOCKS)
            
            # Titles sound normal but have subtle issues
            title = f"Market update on {stock} performance today"
            
            # Content has negative words but high positive sentiment (mismatch)
            content = "Disappointing earnings. Stock plummets. Investors worried. "
            content += "Losses mounting. Crisis deepens. Future uncertain."
            
            row = {
                "article_id": f"subtle_{i}_{int(datetime.now().timestamp())}",
                "title": title,
                "content": content,
                "author": single_author,  # Same author for all
                "source": single_author,
                "published_at": published_at.isoformat(),  # All at midnight
                "url": f"https://example.com/subtle/{i}",
                "stock_symbols": stock,
                "sentiment_score": 0.75,  # High positive despite negative content
                "category": "financial_news"
            }
            
            rows_to_insert.append(row)
        
        # Insert into BigQuery
        table_ref = f"{self.project_id}.{self.dataset_id}.{self.table_id}"
        errors = self.client.insert_rows_json(table_ref, rows_to_insert)
        
        if errors:
            logger.error(f"❌ Errors inserting subtle anomalies: {errors}")
            return 0
        else:
            logger.info(f"✅ Inserted {count} subtle anomalies (statistical patterns)")
            return count
    
    def clear_demo_data(self) -> int:
        """
        Clear all demo data (articles with demo prefixes).
        
        Returns:
            Number of rows deleted
        """
        logger.info("Clearing demo data...")
        
        query = f"""
        DELETE FROM `{self.project_id}.{self.dataset_id}.{self.table_id}`
        WHERE article_id LIKE 'clean_%'
           OR article_id LIKE 'test_%'
           OR article_id LIKE 'subtle_%'
        """
        
        try:
            query_job = self.client.query(query)
            query_job.result()
            
            # Count deleted rows
            count_query = f"""
            SELECT COUNT(*) as deleted_count
            FROM `{self.project_id}.{self.dataset_id}.{self.table_id}`
            WHERE FALSE  -- This is a hack to get 0 rows but valid query
            """
            
            logger.info("✅ Demo data cleared")
            return 0  # Can't easily get deleted count in BigQuery
            
        except Exception as e:
            logger.error(f"❌ Error clearing demo data: {e}")
            return 0
    
    def get_demo_stats(self) -> Dict[str, Any]:
        """
        Get statistics about demo data in the table.
        
        Returns:
            Dict with counts of each demo data type
        """
        query = f"""
        SELECT
          COUNTIF(article_id LIKE 'clean_%') as clean_count,
          COUNTIF(article_id LIKE 'test_%') as test_count,
          COUNTIF(article_id LIKE 'subtle_%') as subtle_count,
          COUNT(*) as total_count
        FROM `{self.project_id}.{self.dataset_id}.{self.table_id}`
        """
        
        try:
            result = self.client.query(query).result()
            row = list(result)[0]
            
            return {
                "clean": row.clean_count,
                "test": row.test_count,
                "subtle": row.subtle_count,
                "total": row.total_count
            }
        except Exception as e:
            logger.error(f"❌ Error getting stats: {e}")
            return {}


def main():
    """CLI interface for demo data generator."""
    parser = argparse.ArgumentParser(description="Generate demo data for Osprey")
    parser.add_argument("--mode", choices=["clean", "test", "subtle", "clear", "stats"],
                       required=True, help="Data generation mode")
    parser.add_argument("--count", type=int, default=100,
                       help="Number of articles to generate")
    
    args = parser.parse_args()
    
    project_id = os.getenv("PROJECT_ID", "osprey-hackathon-2025")
    
    generator = DemoDataGenerator(project_id=project_id)
    
    print("\n" + "="*60)
    print("OSPREY DEMO DATA GENERATOR")
    print("="*60)
    
    if args.mode == "clean":
        count = generator.insert_clean_data(count=args.count)
        print(f"\n✅ Inserted {count} clean articles")
        
    elif args.mode == "test":
        count = generator.insert_test_data(count=args.count)
        print(f"\n✅ Inserted {count} test articles")
        print("   These will trigger anomaly detection!")
        
    elif args.mode == "subtle":
        count = generator.insert_subtle_anomalies(count=args.count)
        print(f"\n✅ Inserted {count} subtle anomalies")
        print("   These require AI/ML to detect")
        
    elif args.mode == "clear":
        generator.clear_demo_data()
        print("\n✅ Demo data cleared")
        
    elif args.mode == "stats":
        stats = generator.get_demo_stats()
        print(f"\nCurrent Demo Data:")
        print(f"  Clean articles: {stats.get('clean', 0)}")
        print(f"  Test articles: {stats.get('test', 0)}")
        print(f"  Subtle anomalies: {stats.get('subtle', 0)}")
        print(f"  Total in table: {stats.get('total', 0)}")
    
    print("="*60)


if __name__ == "__main__":
    main()
