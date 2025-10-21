"""
BigQuery ML wrapper for anomaly detection model.

This module provides a Python interface to BigQuery ML models for anomaly detection.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import logging
from typing import Dict, Any, List, Optional
from google.cloud import bigquery
from datetime import datetime, timedelta
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BigQueryML:
    """Wrapper for BigQuery ML anomaly detection model."""
    
    def __init__(self, project_id: str, dataset_id: str = "osprey_data"):
        """
        Initialize BigQuery ML client.
        
        Args:
            project_id: GCP project ID
            dataset_id: BigQuery dataset ID
        """
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.client = bigquery.Client(project=project_id)
        self.model_id = "anomaly_predictor_v1"
        
        logger.info(f"Initialized BigQueryML for {project_id}.{dataset_id}")
    
    def create_model(self) -> Dict[str, Any]:
        """
        Create and train the BigQuery ML model.
        
        Returns:
            Dict with model creation status and info
        """
        logger.info("Creating BigQuery ML model...")
        
        query = f"""
        CREATE OR REPLACE MODEL `{self.project_id}.{self.dataset_id}.{self.model_id}`
        OPTIONS(
          model_type='LOGISTIC_REG',
          input_label_cols=['is_test_data'],
          data_split_method='AUTO_SPLIT',
          data_split_eval_fraction=0.3,
          max_iterations=20,
          learn_rate_strategy='line_search',
          early_stop=TRUE,
          min_rel_progress=0.01
        ) AS
        SELECT 
          sentiment_score,
          title_length,
          content_length,
          num_stocks,
          age_hours,
          published_hour,
          is_test_data
        FROM `{self.project_id}.{self.dataset_id}.training_data`
        WHERE is_test_data IS NOT NULL
        """
        
        try:
            query_job = self.client.query(query)
            query_job.result()  # Wait for completion
            
            logger.info(f"✅ Model created: {self.model_id}")
            
            # Get evaluation metrics immediately
            metrics = self.evaluate_model()
            
            return {
                "status": "success",
                "model_id": self.model_id,
                "timestamp": datetime.now().isoformat(),
                "metrics": metrics
            }
            
        except Exception as e:
            logger.error(f"❌ Error creating model: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def evaluate_model(self) -> Dict[str, Any]:
        """
        Evaluate the trained model performance.
        
        Returns:
            Dict with accuracy, precision, recall, AUC-ROC metrics
        """
        query = f"""
        SELECT
          precision,
          recall,
          accuracy,
          f1_score,
          log_loss,
          roc_auc
        FROM ML.EVALUATE(
          MODEL `{self.project_id}.{self.dataset_id}.{self.model_id}`
        )
        """
        
        try:
            result = self.client.query(query).result()
            row = list(result)[0]
            
            metrics = {
                "precision": float(row.precision) if row.precision else 0,
                "recall": float(row.recall) if row.recall else 0,
                "accuracy": float(row.accuracy) if row.accuracy else 0,
                "f1_score": float(row.f1_score) if row.f1_score else 0,
                "log_loss": float(row.log_loss) if row.log_loss else 0,
                "roc_auc": float(row.roc_auc) if row.roc_auc else 0,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Model Metrics: Accuracy={metrics['accuracy']:.2%}, Precision={metrics['precision']:.2%}, Recall={metrics['recall']:.2%}")
            
            return metrics
            
        except Exception as e:
            logger.error(f"❌ Error evaluating model: {e}")
            return {
                "error": str(e)
            }
    
    def get_feature_importance(self) -> List[Dict[str, Any]]:
        """
        Get feature importance from the model.
        
        Returns:
            List of features with their importance scores
        """
        query = f"""
        SELECT
          feature,
          importance_weight,
          importance_gain
        FROM ML.FEATURE_IMPORTANCE(
          MODEL `{self.project_id}.{self.dataset_id}.{self.model_id}`
        )
        ORDER BY ABS(importance_weight) DESC
        """
        
        try:
            result = self.client.query(query).result()
            
            features = []
            for row in result:
                features.append({
                    "feature": row.feature,
                    "importance_weight": float(row.importance_weight) if row.importance_weight else 0,
                    "importance_gain": float(row.importance_gain) if row.importance_gain else 0
                })
            
            logger.info(f"Top 3 features: {[f['feature'] for f in features[:3]]}")
            
            return features
            
        except Exception as e:
            logger.error(f"❌ Error getting feature importance: {e}")
            return []
    
    def predict_on_new_data(self, days_back: int = 7, confidence_threshold: float = 0.70) -> List[Dict[str, Any]]:
        """
        Make predictions on recent data.
        
        Args:
            days_back: Number of days back to analyze
            confidence_threshold: Minimum probability to consider as anomaly
        
        Returns:
            List of predicted anomalies with probabilities
        """
        logger.info(f"Making predictions on data from last {days_back} days...")
        
        query = f"""
        SELECT
          article_id,
          predicted_is_test_data,
          predicted_is_test_data_probs[OFFSET(1)].prob as anomaly_probability,
          title,
          author,
          published_at,
          sentiment_score,
          title_length,
          content_length
        FROM ML.PREDICT(
          MODEL `{self.project_id}.{self.dataset_id}.{self.model_id}`,
          (
            SELECT
              article_id,
              sentiment_score,
              LENGTH(title) as title_length,
              LENGTH(content) as content_length,
              ARRAY_LENGTH(SPLIT(stock_symbols, ',')) as num_stocks,
              TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), published_at, HOUR) as age_hours,
              EXTRACT(HOUR FROM published_at) as published_hour,
              title,
              author,
              published_at
            FROM `{self.project_id}.{self.dataset_id}.raw_news`
            WHERE published_at > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days_back} DAY)
          )
        )
        WHERE predicted_is_test_data = TRUE
          AND predicted_is_test_data_probs[OFFSET(1)].prob > {confidence_threshold}
        ORDER BY anomaly_probability DESC
        LIMIT 100
        """
        
        try:
            result = self.client.query(query).result()
            
            predictions = []
            for row in result:
                predictions.append({
                    "article_id": row.article_id,
                    "anomaly_probability": float(row.anomaly_probability),
                    "title": row.title,
                    "author": row.author,
                    "published_at": row.published_at.isoformat() if row.published_at else None,
                    "sentiment_score": float(row.sentiment_score) if row.sentiment_score else 0,
                    "title_length": int(row.title_length) if row.title_length else 0,
                    "content_length": int(row.content_length) if row.content_length else 0
                })
            
            logger.info(f"Found {len(predictions)} anomalies with confidence > {confidence_threshold}")
            
            return predictions
            
        except Exception as e:
            logger.error(f"❌ Error making predictions: {e}")
            return []
    
    def get_model_metrics(self) -> Dict[str, Any]:
        """
        Get comprehensive model metrics for dashboard.
        
        Returns:
            Dict with all model information and performance metrics
        """
        try:
            metrics = self.evaluate_model()
            features = self.get_feature_importance()
            
            # Get prediction statistics
            pred_stats_query = f"""
            SELECT
              COUNT(*) as total_predictions,
              COUNTIF(predicted_is_test_data = TRUE) as positive_predictions,
              AVG(predicted_is_test_data_probs[OFFSET(1)].prob) as avg_confidence
            FROM ML.PREDICT(
              MODEL `{self.project_id}.{self.dataset_id}.{self.model_id}`,
              (
                SELECT
                  sentiment_score,
                  LENGTH(title) as title_length,
                  LENGTH(content) as content_length,
                  ARRAY_LENGTH(SPLIT(stock_symbols, ',')) as num_stocks,
                  TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), published_at, HOUR) as age_hours,
                  EXTRACT(HOUR FROM published_at) as published_hour
                FROM `{self.project_id}.{self.dataset_id}.raw_news`
                WHERE published_at > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY)
              )
            )
            """
            
            pred_result = self.client.query(pred_stats_query).result()
            pred_row = list(pred_result)[0]
            
            return {
                "model_id": self.model_id,
                "status": "operational",
                "metrics": metrics,
                "feature_importance": features[:5],  # Top 5 features
                "recent_predictions": {
                    "total": pred_row.total_predictions,
                    "positive": pred_row.positive_predictions,
                    "avg_confidence": float(pred_row.avg_confidence) if pred_row.avg_confidence else 0
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting model metrics: {e}")
            return {
                "model_id": self.model_id,
                "status": "error",
                "error": str(e)
            }
    
    def model_exists(self) -> bool:
        """
        Check if the model exists in BigQuery.
        
        Returns:
            True if model exists, False otherwise
        """
        try:
            model_ref = f"{self.project_id}.{self.dataset_id}.{self.model_id}"
            self.client.get_model(model_ref)
            return True
        except Exception:
            return False


def main():
    """Test BigQuery ML functionality."""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    project_id = os.getenv("PROJECT_ID", "osprey-hackathon-2025")
    
    ml = BigQueryML(project_id=project_id)
    
    print("\n" + "="*60)
    print("BIGQUERY ML - ANOMALY DETECTION MODEL")
    print("="*60)
    
    # Check if model exists
    if ml.model_exists():
        print("\n✅ Model exists")
        
        # Get metrics
        metrics = ml.get_model_metrics()
        
        print(f"\nModel Status: {metrics.get('status', 'unknown')}")
        print(f"\nPerformance Metrics:")
        model_metrics = metrics.get('metrics', {})
        print(f"  Accuracy: {model_metrics.get('accuracy', 0):.2%}")
        print(f"  Precision: {model_metrics.get('precision', 0):.2%}")
        print(f"  Recall: {model_metrics.get('recall', 0):.2%}")
        print(f"  F1 Score: {model_metrics.get('f1_score', 0):.2%}")
        print(f"  ROC-AUC: {model_metrics.get('roc_auc', 0):.3f}")
        
        print(f"\nTop Features:")
        for feat in metrics.get('feature_importance', [])[:5]:
            print(f"  {feat['feature']}: {feat['importance_weight']:.4f}")
        
        # Get predictions
        predictions = ml.predict_on_new_data(days_back=7, confidence_threshold=0.70)
        
        print(f"\nRecent Predictions (confidence > 70%):")
        print(f"  Found {len(predictions)} potential anomalies")
        
        if predictions:
            print(f"\n  Top 3 Anomalies:")
            for i, pred in enumerate(predictions[:3], 1):
                print(f"    {i}. {pred['title'][:50]}...")
                print(f"       Confidence: {pred['anomaly_probability']:.1%}")
                print(f"       Author: {pred['author']}")
    else:
        print("\n⚠️  Model does not exist")
        print("   Run: python ml/training/train.py")
        print("   Then create model with this module")
    
    print("="*60)


if __name__ == "__main__":
    main()
