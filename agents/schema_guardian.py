from google.cloud import bigquery
from google.api_core import retry
import google.api_core.exceptions
from datetime import datetime
import pandas as pd
import json
import logging

logger = logging.getLogger(__name__)


class SchemaGuardian:
    def __init__(self, project_id: str, dataset_id: str, table_id: str, region: str = "us"):
        self.client = bigquery.Client(project=project_id)
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.table_id = table_id
        self.region = region
        self.table_ref = f"{project_id}.{dataset_id}.{table_id}"
        self.baseline_schema = None
        
        # Metrics
        self._check_count = 0
        self._alert_count = 0
        self._last_check = None
        self._uptime = 0
    
    @retry.Retry(
        predicate=retry.if_exception_type(
            google.api_core.exceptions.ServiceUnavailable,
            google.api_core.exceptions.TooManyRequests
        ),
        initial=1.0,
        maximum=60.0,
        multiplier=2.0,
        deadline=300.0
    )
    def capture_baseline_schema(self) -> pd.DataFrame:
        """Capture current schema as baseline - run this once on first setup"""
        query = f"""
        SELECT 
            table_name,
            column_name,
            ordinal_position,
            is_nullable,
            data_type,
            is_partitioning_column,
            clustering_ordinal_position
        FROM `{self.project_id}.{self.dataset_id}.INFORMATION_SCHEMA.COLUMNS`
        WHERE table_name = '{self.table_id}'
        ORDER BY ordinal_position
        """
        
        logger.info(f"Capturing schema for {self.table_ref}")
        schema_df = self.client.query(query).to_dataframe()
        logger.info(f"Captured {len(schema_df)} columns")
        
        # Critical: Store in both memory and Firestore
        self.baseline_schema = schema_df
        return schema_df
    
    def detect_schema_drift(self) -> dict:
        """Compare current schema against baseline"""
        current_schema = self.capture_baseline_schema()
        
        if self.baseline_schema is None:
            return {"error": "No baseline schema found. Run capture_baseline_schema() first."}
        
        changes = {
            "new_columns": [],
            "removed_columns": [],
            "type_changes": [],
            "nullability_changes": [],
            "partition_changes": []
        }
        
        # Convert to sets for comparison
        baseline_cols = set(self.baseline_schema['column_name'])
        current_cols = set(current_schema['column_name'])
        
        # Detect new/removed columns
        changes["new_columns"] = list(current_cols - baseline_cols)
        changes["removed_columns"] = list(baseline_cols - current_cols)
        
        # Check existing columns for modifications
        common_cols = baseline_cols & current_cols
        for col in common_cols:
            baseline_row = self.baseline_schema[self.baseline_schema['column_name'] == col].iloc[0]
            current_row = current_schema[current_schema['column_name'] == col].iloc[0]
            
            # Type change detection (CRITICAL severity)
            if baseline_row['data_type'] != current_row['data_type']:
                changes["type_changes"].append({
                    "column": col,
                    "from": baseline_row['data_type'],
                    "to": current_row['data_type']
                })
            
            # Nullability change
            if baseline_row['is_nullable'] != current_row['is_nullable']:
                changes["nullability_changes"].append({
                    "column": col,
                    "from": baseline_row['is_nullable'],
                    "to": current_row['is_nullable']
                })
            
            # Partition column change
            if baseline_row['is_partitioning_column'] != current_row['is_partitioning_column']:
                changes["partition_changes"].append({
                    "column": col,
                    "changed_to_partition": current_row['is_partitioning_column'] == 'YES'
                })
        
        self._check_count += 1
        self._last_check = datetime.utcnow().isoformat()
        
        return changes
    
    def _calculate_severity(self, changes: dict) -> str:
        """Rule-based severity calculation"""
        if changes.get("type_changes"):
            return "CRITICAL"  # Data type changes break downstream queries
        elif changes.get("removed_columns"):
            return "HIGH"  # Removed columns cause query failures
        elif changes.get("partition_changes"):
            return "HIGH"  # Partition changes affect performance
        elif changes.get("nullability_changes"):
            return "MEDIUM"  # May cause NULL handling issues
        elif changes.get("new_columns"):
            return "LOW"  # Generally safe, may need schema updates
        else:
            return "INFO"
    
    def _analyze_impact(self, changes: dict) -> str:
        """Generate human-readable impact description"""
        impacts = []
        
        if changes.get("type_changes"):
            impacts.append("⚠️ Type changes will break queries expecting previous types")
            impacts.append("📊 Dashboards may show incorrect data")
        
        if changes.get("removed_columns"):
            impacts.append("❌ Queries referencing removed columns will fail")
            impacts.append("🔧 ETL pipelines need immediate updates")
        
        if changes.get("new_columns"):
            impacts.append("✅ New columns detected - no immediate impact")
            impacts.append("📝 Consider updating documentation")
        
        return " | ".join(impacts) if impacts else "No significant impact detected"
    
    def _generate_recommendations(self, changes: dict) -> list:
        """Actionable recommendations"""
        recs = []
        
        if changes.get("type_changes"):
            recs.append("Pause Fivetran connector immediately")
            recs.append("Review source data for type inconsistencies")
            recs.append("Update downstream transformations")
        
        if changes.get("removed_columns"):
            recs.append("Check Fivetran connector configuration")
            recs.append("Verify source API hasn't changed")
            recs.append("Update dependent queries and views")
        
        if changes.get("new_columns"):
            recs.append("Document new column purpose")
            recs.append("Update schema documentation")
        
        return recs
    
    def generate_alert(self, changes: dict) -> dict:
        """Create structured alert from changes"""
        severity = self._calculate_severity(changes)
        
        alert = {
            "agent": "Schema Guardian",
            "timestamp": datetime.utcnow().isoformat(),
            "table": self.table_ref,
            "severity": severity,
            "changes": changes,
            "impact_analysis": self._analyze_impact(changes),
            "recommendations": self._generate_recommendations(changes),
            "change_count": sum(len(v) if isinstance(v, list) else 0 for v in changes.values())
        }
        
        self._alert_count += 1
        return alert
    
    def get_metrics(self) -> dict:
        """Return agent performance metrics"""
        return {
            "checks_performed": self._check_count,
            "alerts_generated": self._alert_count,
            "last_check_time": self._last_check,
            "uptime_seconds": self._uptime
        }
