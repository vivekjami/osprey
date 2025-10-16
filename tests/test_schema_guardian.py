import pytest
import pandas as pd
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.schema_guardian import SchemaGuardian
from agents.agent_memory import AgentMemory


# Note: These tests require GCP credentials and an actual BigQuery table
# Run with: pytest tests/test_schema_guardian.py -v
# Set environment variable: GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json


@pytest.fixture
def test_config():
    """Test configuration - UPDATE THESE WITH YOUR PROJECT DETAILS"""
    return {
        "project_id": os.getenv("GCP_PROJECT_ID", "your-project-id"),
        "dataset_id": "osprey_data",
        "table_id": "raw_news"
    }


@pytest.fixture
def guardian(test_config):
    """Create SchemaGuardian instance"""
    return SchemaGuardian(
        test_config["project_id"],
        test_config["dataset_id"],
        test_config["table_id"]
    )


@pytest.fixture
def memory(test_config):
    """Create AgentMemory instance"""
    return AgentMemory(test_config["project_id"])


def test_capture_baseline(guardian, memory, test_config):
    """Test baseline capture and storage"""
    # Capture baseline
    baseline = guardian.capture_baseline_schema()
    
    # Assertions
    assert len(baseline) > 0, "No columns captured"
    assert 'column_name' in baseline.columns
    assert 'data_type' in baseline.columns
    assert 'is_nullable' in baseline.columns
    
    print(f"✅ Captured {len(baseline)} columns")
    print(f"Columns: {baseline['column_name'].tolist()}")
    
    # Store in Firestore
    memory.store_schema_baseline(test_config["table_id"], baseline)
    
    # Verify retrieval
    retrieved = memory.get_schema_baseline(test_config["table_id"])
    assert retrieved is not None
    assert len(retrieved) == len(baseline)
    
    print(f"✅ Stored and retrieved baseline successfully")


def test_detect_no_changes(guardian, memory, test_config):
    """Test when schema hasn't changed"""
    # Capture baseline
    baseline = guardian.capture_baseline_schema()
    memory.store_schema_baseline(test_config["table_id"], baseline)
    
    # Load baseline and detect
    guardian.baseline_schema = memory.get_schema_baseline(test_config["table_id"])
    changes = guardian.detect_schema_drift()
    
    # Should be no changes
    assert len(changes["new_columns"]) == 0
    assert len(changes["removed_columns"]) == 0
    assert len(changes["type_changes"]) == 0
    
    print("✅ No false positives - schema correctly identified as stable")


def test_severity_calculation(guardian):
    """Test severity logic"""
    # Type change = CRITICAL
    changes = {
        "type_changes": [{"column": "test", "from": "STRING", "to": "INT"}],
        "new_columns": [],
        "removed_columns": [],
        "nullability_changes": [],
        "partition_changes": []
    }
    severity = guardian._calculate_severity(changes)
    assert severity == "CRITICAL", f"Expected CRITICAL, got {severity}"
    print("✅ Type change correctly identified as CRITICAL")
    
    # Removed column = HIGH
    changes = {
        "removed_columns": ["test_col"],
        "type_changes": [],
        "new_columns": [],
        "nullability_changes": [],
        "partition_changes": []
    }
    severity = guardian._calculate_severity(changes)
    assert severity == "HIGH", f"Expected HIGH, got {severity}"
    print("✅ Removed column correctly identified as HIGH")
    
    # New column = LOW
    changes = {
        "new_columns": ["new_col"],
        "type_changes": [],
        "removed_columns": [],
        "nullability_changes": [],
        "partition_changes": []
    }
    severity = guardian._calculate_severity(changes)
    assert severity == "LOW", f"Expected LOW, got {severity}"
    print("✅ New column correctly identified as LOW")


def test_alert_generation(guardian, memory):
    """Test full alert flow"""
    # Simulate type change
    changes = {
        "type_changes": [{"column": "sentiment_score", "from": "STRING", "to": "FLOAT"}],
        "new_columns": [],
        "removed_columns": [],
        "nullability_changes": [],
        "partition_changes": []
    }
    
    alert = guardian.generate_alert(changes)
    
    # Assertions
    assert alert["severity"] == "CRITICAL"
    assert alert["agent"] == "Schema Guardian"
    assert "sentiment_score" in str(alert["changes"])
    assert len(alert["recommendations"]) > 0
    assert alert["change_count"] == 1
    
    print(f"✅ Alert generated: {alert['severity']}")
    print(f"Recommendations: {alert['recommendations']}")
    
    # Store alert
    alert_id = memory.store_alert(alert)
    assert alert_id is not None
    print(f"✅ Alert stored with ID: {alert_id}")
    
    # Verify storage
    alerts = memory.get_alert_history(limit=1)
    assert len(alerts) > 0
    assert alerts[0]["severity"] == "CRITICAL"
    
    print("✅ Alert successfully retrieved from Firestore")


def test_impact_analysis(guardian):
    """Test impact analysis generation"""
    changes = {
        "type_changes": [{"column": "price", "from": "STRING", "to": "FLOAT"}],
        "new_columns": ["new_field"],
        "removed_columns": [],
        "nullability_changes": [],
        "partition_changes": []
    }
    
    impact = guardian._analyze_impact(changes)
    
    assert "Type changes" in impact
    assert "New columns" in impact
    
    print(f"✅ Impact analysis: {impact}")


def test_recommendations(guardian):
    """Test recommendation generation"""
    changes = {
        "type_changes": [{"column": "price", "from": "STRING", "to": "FLOAT"}],
        "new_columns": [],
        "removed_columns": [],
        "nullability_changes": [],
        "partition_changes": []
    }
    
    recs = guardian._generate_recommendations(changes)
    
    assert len(recs) > 0
    assert any("Pause" in rec for rec in recs)
    assert any("Review" in rec for rec in recs)
    
    print(f"✅ Generated {len(recs)} recommendations")
    for rec in recs:
        print(f"  - {rec}")


def test_metrics(guardian):
    """Test metrics tracking"""
    initial_metrics = guardian.get_metrics()
    assert initial_metrics["checks_performed"] == 0
    assert initial_metrics["alerts_generated"] == 0
    
    # Simulate a check
    guardian._check_count = 5
    guardian._alert_count = 2
    
    metrics = guardian.get_metrics()
    assert metrics["checks_performed"] == 5
    assert metrics["alerts_generated"] == 2
    
    print(f"✅ Metrics tracking working: {metrics}")


def test_agent_status_storage(memory):
    """Test agent status in Firestore"""
    status = {
        "status": "running",
        "checks_performed": 10,
        "uptime_seconds": 3600
    }
    
    memory.update_agent_status("Schema Guardian", status)
    
    retrieved = memory.get_agent_status("Schema Guardian")
    assert retrieved is not None
    assert retrieved["status"] == "running"
    assert retrieved["checks_performed"] == 10
    
    print(f"✅ Agent status stored and retrieved: {retrieved}")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s"])
