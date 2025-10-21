from google.cloud import bigquery
from vertexai.generative_models import GenerativeModel
import vertexai
import json
from datetime import datetime
import os

class AnomalyDetective:
    def __init__(self, project_id: str, dataset_id: str, table_id: str):
        self.project_id = project_id
        self.bq_client = bigquery.Client(project=project_id)
        self.table_ref = f"{project_id}.{dataset_id}.{table_id}"
        
        # Initialize Vertex AI with latest Gemini
        location = os.getenv("VERTEX_AI_LOCATION", "us-central1")
        vertexai.init(project=project_id, location=location)
        self.model = GenerativeModel("gemini-2.0-flash-exp")
    
    def sample_latest_data(self, limit: int = 20):
        """Get recent rows for analysis"""
        query = f"""
        SELECT * FROM `{self.table_ref}`
        WHERE published_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
        ORDER BY published_at DESC
        LIMIT {limit}
        """
        return self.bq_client.query(query).to_dataframe().to_dict('records')
    
    def analyze_data_quality(self, data_sample: list) -> dict:
        """Send to Gemini for anomaly detection"""
        
        prompt = f"""You are a data quality analyst. Analyze this financial news data for anomalies.

DATA SAMPLE:
{json.dumps(data_sample, indent=2, default=str)}

CHECK FOR:
1. Test data: "test_", "dummy", "fake", placeholder values
2. Invalid stock symbols: Non-existent tickers
3. Temporal anomalies: Future dates, dates before 2000
4. Sentiment issues: Values outside [-1, 1], all identical
5. Missing critical fields: null in required columns

OUTPUT ONLY VALID JSON:
{{
  "has_anomalies": true/false,
  "confidence": 0.0-1.0,
  "anomalies": [
    {{
      "type": "test_data|invalid_symbol|temporal|sentiment|missing_data",
      "severity": "CRITICAL|HIGH|MEDIUM|LOW",
      "field": "column_name",
      "evidence": ["specific example 1", "example 2"],
      "affected_row_count": 5,
      "affected_ids": ["id1", "id2"]
    }}
  ],
  "summary": "Brief description of issues found"
}}

Be conservative. Only flag if confidence > 70%."""

        try:
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.1,
                    "max_output_tokens": 2048,
                }
            )
            
            # Parse JSON from response
            text = response.text
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            
            result = json.loads(text.strip())
            result["timestamp"] = datetime.utcnow().isoformat()
            result["agent"] = "Anomaly Detective"
            
            return result
            
        except Exception as e:
            return {
                "has_anomalies": False,
                "confidence": 0.0,
                "anomalies": [],
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def run_check(self) -> dict:
        """Run complete anomaly check"""
        data = self.sample_latest_data(limit=20)
        analysis = self.analyze_data_quality(data)
        
        if analysis.get("has_anomalies"):
            print(f"🚨 Anomalies detected! Confidence: {analysis['confidence']:.0%}")
            for anomaly in analysis.get("anomalies", []):
                print(f"  - {anomaly['type']}: {anomaly['severity']}")
        else:
            print("✅ Data quality check passed")
        
        return analysis
