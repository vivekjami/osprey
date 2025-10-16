from google.cloud import firestore
from datetime import datetime
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class AgentMemory:
    def __init__(self, project_id: str = None):
        """Initialize Firestore client with auto-detection in GCP environments"""
        try:
            self.db = firestore.Client(project=project_id) if project_id else firestore.Client()
            logger.info("✅ Firestore client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Firestore: {e}")
            raise
    
    def store_schema_baseline(self, table_id: str, schema_df: pd.DataFrame):
        """Store schema baseline with timestamp"""
        doc_ref = self.db.collection('schema_baselines').document(table_id)
        
        # Convert DataFrame to Firestore-compatible format
        schema_data = {
            'columns': schema_df.to_dict('records'),
            'captured_at': firestore.SERVER_TIMESTAMP,
            'column_count': len(schema_df)
        }
        
        doc_ref.set(schema_data)
        logger.info(f"✅ Stored baseline for {table_id} with {len(schema_df)} columns")
    
    def get_schema_baseline(self, table_id: str) -> pd.DataFrame:
        """Retrieve schema baseline"""
        doc_ref = self.db.collection('schema_baselines').document(table_id)
        doc = doc_ref.get()
        
        if doc.exists:
            data = doc.to_dict()
            logger.info(f"✅ Retrieved baseline for {table_id}")
            return pd.DataFrame(data['columns'])
        
        logger.warning(f"No baseline found for {table_id}")
        return None
    
    def store_alert(self, alert: dict):
        """Store alert with auto-generated ID"""
        # Add server timestamp if not present
        if 'timestamp' not in alert:
            alert['timestamp'] = firestore.SERVER_TIMESTAMP
        
        doc_ref = self.db.collection('alerts').add(alert)
        logger.info(f"🚨 Alert stored: {alert.get('severity', 'UNKNOWN')} - ID: {doc_ref[1].id}")
        return doc_ref[1].id
    
    def get_alert_history(self, limit: int = 10, agent: str = None) -> list:
        """Get recent alerts, optionally filtered by agent"""
        alerts_ref = self.db.collection('alerts')
        
        # Filter by agent if specified
        if agent:
            alerts_ref = alerts_ref.where('agent', '==', agent)
        
        alerts_ref = alerts_ref.order_by('timestamp', direction=firestore.Query.DESCENDING).limit(limit)
        
        alerts = []
        for doc in alerts_ref.stream():
            alert_data = {'id': doc.id, **doc.to_dict()}
            alerts.append(alert_data)
        
        logger.info(f"Retrieved {len(alerts)} alerts")
        return alerts
    
    def get_agent_status(self, agent_name: str) -> dict:
        """Get current status for a specific agent"""
        doc_ref = self.db.collection('agent_status').document(agent_name)
        doc = doc_ref.get()
        
        if doc.exists:
            return doc.to_dict()
        return None
    
    def update_agent_status(self, agent_name: str, status: dict):
        """Update agent status"""
        doc_ref = self.db.collection('agent_status').document(agent_name)
        status['last_updated'] = firestore.SERVER_TIMESTAMP
        doc_ref.set(status, merge=True)
        logger.info(f"Updated status for {agent_name}")
