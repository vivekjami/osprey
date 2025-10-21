"""
Action Executor

Executes autonomous actions based on orchestrator decisions.
Handles connector control, data quarantine, rollback SQL generation, and alerting.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from google.cloud import bigquery
from dotenv import load_dotenv
import json

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.fivetran_client import FivetranClient

load_dotenv()


class ActionExecutor:
    """Executes autonomous pipeline actions"""
    
    def __init__(
        self,
        project_id: Optional[str] = None,
        dataset_id: Optional[str] = None,
        table_id: Optional[str] = None,
        connector_id: Optional[str] = None
    ):
        """
        Initialize action executor
        
        Args:
            project_id: GCP project ID (or from env)
            dataset_id: BigQuery dataset (or from env)
            table_id: BigQuery table (or from env)
            connector_id: Fivetran connector ID (or from env)
        """
        self.project_id = project_id or os.getenv("PROJECT_ID")
        self.dataset_id = dataset_id or os.getenv("DATASET_ID")
        self.table_id = table_id or os.getenv("TABLE_ID")
        self.connector_id = connector_id or os.getenv("FIVETRAN_CONNECTOR_ID")
        
        # Initialize clients
        self.bq_client = bigquery.Client(project=self.project_id)
        self.fivetran_client = FivetranClient()
        
        # Track actions
        self.action_history = []
    
    def execute_action(self, decision: Dict) -> Dict:
        """
        Execute action from decision
        
        Args:
            decision: Decision dict from DecisionEngine
        
        Returns:
            Execution result dict with:
                - action_id: Unique ID
                - decision_id: Original decision ID
                - timestamp: When executed
                - actions_taken: List of actions
                - success: bool
                - details: Execution details
        """
        action_type = decision.get("action")
        requirements = decision.get("requirements", {})
        
        result = {
            "action_id": f"act_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "decision_id": decision.get("decision_id"),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "action_type": action_type,
            "actions_taken": [],
            "success": True,
            "details": {},
            "errors": []
        }
        
        print(f"\n🎯 Executing action: {action_type}")
        print(f"   Decision ID: {decision.get('decision_id')[:8]}...")
        
        try:
            # Execute based on requirements
            if requirements.get("pause_connector"):
                pause_result = self.pause_connector()
                result["actions_taken"].append("pause_connector")
                result["details"]["pause_connector"] = pause_result
            
            if requirements.get("quarantine_data"):
                # Get affected rows from decision
                anomaly_alert = decision.get("inputs", {}).get("anomaly_alert", {})
                affected_ids = self._extract_affected_ids(anomaly_alert)
                
                quarantine_result = self.quarantine_data(affected_ids)
                result["actions_taken"].append("quarantine_data")
                result["details"]["quarantine_data"] = quarantine_result
            
            if requirements.get("generate_rollback"):
                anomaly_alert = decision.get("inputs", {}).get("anomaly_alert", {})
                affected_ids = self._extract_affected_ids(anomaly_alert)
                
                rollback_sql = self.generate_rollback_sql(affected_ids)
                result["actions_taken"].append("generate_rollback")
                result["details"]["rollback_sql"] = rollback_sql
            
            if requirements.get("send_alert"):
                alert_result = self.send_alert(decision)
                result["actions_taken"].append("send_alert")
                result["details"]["alert"] = alert_result
            
            # Log action
            self.log_action(result)
            
            print(f"✅ Action executed successfully")
            print(f"   Actions taken: {', '.join(result['actions_taken'])}")
        
        except Exception as e:
            result["success"] = False
            result["errors"].append(str(e))
            print(f"❌ Action execution failed: {e}")
        
        self.action_history.append(result)
        return result
    
    def pause_connector(self) -> Dict:
        """
        Pause Fivetran connector
        
        Returns:
            Result dict with status
        """
        try:
            response = self.fivetran_client.pause_connector(self.connector_id)
            return {
                "success": True,
                "connector_id": self.connector_id,
                "paused": response.get("paused"),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        except Exception as e:
            print(f"⚠️  Pause connector failed: {e}")
            return {
                "success": False,
                "connector_id": self.connector_id,
                "error": str(e)
            }
    
    def resume_connector(self) -> Dict:
        """
        Resume Fivetran connector
        
        Returns:
            Result dict with status
        """
        try:
            response = self.fivetran_client.resume_connector(self.connector_id)
            return {
                "success": True,
                "connector_id": self.connector_id,
                "paused": response.get("paused"),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        except Exception as e:
            print(f"⚠️  Resume connector failed: {e}")
            return {
                "success": False,
                "connector_id": self.connector_id,
                "error": str(e)
            }
    
    def quarantine_data(self, affected_ids: List[str]) -> Dict:
        """
        Move suspicious data to quarantine table
        
        Args:
            affected_ids: List of article IDs to quarantine
        
        Returns:
            Quarantine result dict
        """
        if not affected_ids:
            print("⚠️  No affected IDs provided for quarantine")
            return {
                "success": False,
                "reason": "No affected IDs",
                "rows_quarantined": 0
            }
        
        quarantine_table = f"{self.project_id}.{self.dataset_id}.quarantine"
        source_table = f"{self.project_id}.{self.dataset_id}.{self.table_id}"
        
        print(f"🔒 Quarantining {len(affected_ids)} rows...")
        
        try:
            # Create quarantine table if not exists
            create_query = f"""
            CREATE TABLE IF NOT EXISTS `{quarantine_table}` AS
            SELECT 
                *,
                CURRENT_TIMESTAMP() as quarantined_at,
                'initial' as quarantine_reason
            FROM `{source_table}`
            WHERE FALSE
            """
            
            self.bq_client.query(create_query).result()
            
            # Insert affected rows into quarantine
            # Using STRING type since article_id is STRING
            insert_query = f"""
            INSERT INTO `{quarantine_table}`
            SELECT 
                *,
                CURRENT_TIMESTAMP() as quarantined_at,
                'anomaly_detected' as quarantine_reason
            FROM `{source_table}`
            WHERE article_id IN UNNEST(@affected_ids)
            """
            
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ArrayQueryParameter("affected_ids", "STRING", affected_ids)
                ]
            )
            
            insert_job = self.bq_client.query(insert_query, job_config=job_config)
            insert_job.result()
            rows_inserted = insert_job.num_dml_affected_rows or 0
            
            print(f"   ✅ {rows_inserted} rows inserted into quarantine")
            
            # Note: Don't delete from source table for now (streaming buffer limitation)
            # In production, would delete after streaming buffer clears
            
            return {
                "success": True,
                "quarantine_table": quarantine_table,
                "rows_quarantined": rows_inserted,
                "affected_ids": affected_ids,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        
        except Exception as e:
            print(f"❌ Quarantine failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "rows_quarantined": 0
            }
    
    def generate_rollback_sql(self, affected_ids: List[str]) -> str:
        """
        Generate SQL to rollback quarantine action
        
        Args:
            affected_ids: List of quarantined IDs
        
        Returns:
            SQL script as string
        """
        if not affected_ids:
            return "-- No affected IDs to rollback"
        
        quarantine_table = f"{self.project_id}.{self.dataset_id}.quarantine"
        source_table = f"{self.project_id}.{self.dataset_id}.{self.table_id}"
        
        # Format IDs for SQL
        ids_str = ", ".join([f"'{id}'" for id in affected_ids])
        
        rollback_sql = f"""-- ROLLBACK SQL: Restore quarantined data
-- Generated: {datetime.utcnow().isoformat()}Z
-- Affected IDs: {len(affected_ids)}

-- Step 1: Restore data to main table
INSERT INTO `{source_table}`
SELECT * EXCEPT(quarantined_at, quarantine_reason)
FROM `{quarantine_table}`
WHERE article_id IN ({ids_str});

-- Step 2: Remove from quarantine
DELETE FROM `{quarantine_table}`
WHERE article_id IN ({ids_str});

-- Step 3: Verify restoration
SELECT 
    COUNT(*) as restored_count,
    MIN(published_at) as earliest_date,
    MAX(published_at) as latest_date
FROM `{source_table}`
WHERE article_id IN ({ids_str});
"""
        
        return rollback_sql
    
    def send_alert(self, decision: Dict) -> Dict:
        """
        Send alert (formatted output for now, can integrate Slack/email later)
        
        Args:
            decision: Decision dict
        
        Returns:
            Alert result
        """
        alert = {
            "alert_id": f"alert_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "decision_id": decision.get("decision_id"),
            "action": decision.get("action"),
            "priority": decision.get("priority"),
            "confidence": decision.get("confidence"),
            "reasoning": decision.get("reasoning"),
            "evidence": self._extract_evidence(decision)
        }
        
        print(f"\n📨 ALERT: {decision.get('action')}")
        print(f"   Priority: {decision.get('priority')}")
        print(f"   Confidence: {decision.get('confidence'):.0%}")
        print(f"   Reasoning:")
        for reason in decision.get("reasoning", []):
            print(f"      - {reason}")
        
        # In production: send to Slack, email, PagerDuty, etc.
        # For now, just log
        
        return {
            "success": True,
            "alert_sent": True,
            "channels": ["console"],  # Future: ["slack", "email"]
            "alert": alert
        }
    
    def log_action(self, action_result: Dict) -> None:
        """
        Log action execution (console + could store in Firestore)
        
        Args:
            action_result: Execution result dict
        """
        print(f"\n📝 Action Log:")
        print(f"   Action ID: {action_result['action_id']}")
        print(f"   Decision ID: {action_result['decision_id'][:8]}...")
        print(f"   Actions: {', '.join(action_result['actions_taken'])}")
        print(f"   Success: {'✅' if action_result['success'] else '❌'}")
        
        if action_result.get("errors"):
            print(f"   Errors: {action_result['errors']}")
    
    def _extract_affected_ids(self, anomaly_alert: Optional[Dict]) -> List[str]:
        """
        Extract affected row IDs from anomaly alert
        
        Args:
            anomaly_alert: Alert from Anomaly Detective
        
        Returns:
            List of article IDs
        """
        if not anomaly_alert or not anomaly_alert.get("has_anomalies"):
            return []
        
        affected_ids = []
        
        for anomaly in anomaly_alert.get("anomalies", []):
            evidence = anomaly.get("evidence", [])
            
            # Try to extract IDs from evidence
            for e in evidence:
                if "Article ID" in e or "article_id" in e.lower():
                    # Parse ID from evidence string
                    # Example: "Article ID 'TEST_001' contains..."
                    parts = e.split("'")
                    if len(parts) >= 2:
                        affected_ids.append(parts[1])
        
        # Remove duplicates
        return list(set(affected_ids))
    
    def _extract_evidence(self, decision: Dict) -> List[str]:
        """Extract evidence from decision inputs"""
        evidence = []
        
        # From schema alert
        schema_alert = decision.get("inputs", {}).get("schema_alert")
        if schema_alert:
            changes = schema_alert.get("changes", {})
            if changes.get("type_changes"):
                evidence.append(f"Schema type changes: {changes['type_changes']}")
            if changes.get("removed_columns"):
                evidence.append(f"Removed columns: {changes['removed_columns']}")
        
        # From anomaly alert
        anomaly_alert = decision.get("inputs", {}).get("anomaly_alert")
        if anomaly_alert and anomaly_alert.get("has_anomalies"):
            for anomaly in anomaly_alert.get("anomalies", []):
                evidence.extend(anomaly.get("evidence", []))
        
        return evidence
    
    def get_action_history(self, limit: int = 10) -> List[Dict]:
        """Get recent action history"""
        return sorted(
            self.action_history,
            key=lambda a: a["timestamp"],
            reverse=True
        )[:limit]


# Testing
if __name__ == "__main__":
    executor = ActionExecutor()
    
    print("=" * 60)
    print("ACTION EXECUTOR TEST")
    print("=" * 60)
    
    # Test 1: Pause connector
    print("\n1️⃣ Test: Pause connector")
    pause_result = executor.pause_connector()
    print(f"   Success: {pause_result.get('success')}")
    print(f"   Paused: {pause_result.get('paused')}")
    
    # Test 2: Generate rollback SQL
    print("\n2️⃣ Test: Generate rollback SQL")
    test_ids = ["TEST_001", "TEST_002"]
    rollback_sql = executor.generate_rollback_sql(test_ids)
    print(f"   SQL generated: {len(rollback_sql)} characters")
    print(f"   Preview: {rollback_sql[:100]}...")
    
    # Test 3: Send alert (mock)
    print("\n3️⃣ Test: Send alert")
    mock_decision = {
        "decision_id": "test-123",
        "action": "PAUSE_AND_ALERT",
        "priority": "CRITICAL",
        "confidence": 0.95,
        "reasoning": ["Test reason 1", "Test reason 2"]
    }
    alert_result = executor.send_alert(mock_decision)
    print(f"   Alert sent: {alert_result.get('alert_sent')}")
    
    # Test 4: Resume connector
    print("\n4️⃣ Test: Resume connector")
    resume_result = executor.resume_connector()
    print(f"   Success: {resume_result.get('success')}")
    print(f"   Paused: {resume_result.get('paused')}")
    
    print("\n✅ Action Executor tests completed!")
    print("=" * 60)
