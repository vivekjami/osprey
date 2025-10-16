# Schema Guardian Agent

## Overview
Autonomous agent monitoring BigQuery schema changes in real-time.

## Features
- ✅ **Detects**: Column additions/removals, type changes, partition changes, nullability modifications
- ✅ **Severity scoring**: CRITICAL → HIGH → MEDIUM → LOW → INFO
- ✅ **Stores alerts** in Firestore with full audit trail
- ✅ **REST API** for dashboard integration
- ✅ **Automatic retry** on transient failures
- ✅ **Metrics tracking**: checks performed, alerts generated, uptime

## Quick Start

### 1. Prerequisites

```bash
# Install dependencies
pip install google-cloud-bigquery google-cloud-firestore pandas

# Set GCP credentials
export GOOGLE_APPLICATION_CREDENTIALS="path/to/credentials.json"
export GCP_PROJECT_ID="your-project-id"
```

### 2. Capture Initial Baseline

```python
from agents.schema_guardian import SchemaGuardian
from agents.agent_memory import AgentMemory

# Initialize
guardian = SchemaGuardian("your-project-id", "osprey_data", "raw_news")
memory = AgentMemory()

# Capture and store baseline
baseline = guardian.capture_baseline_schema()
memory.store_schema_baseline("raw_news", baseline)

print(f"✅ Baseline captured: {len(baseline)} columns")
```

### 3. Run Monitoring

```bash
python agents/run_schema_guardian.py \
  --project your-project-id \
  --dataset osprey_data \
  --table raw_news \
  --interval 300
```

### 4. Start API Server

```bash
# Install FastAPI
pip install fastapi uvicorn

# Run API
uvicorn agents.api:app --reload --port 8000
```

### 5. Query Alerts

```python
# Get recent alerts
alerts = memory.get_alert_history(limit=5)
for alert in alerts:
    print(f"{alert['severity']}: {alert['change_count']} changes")
    print(f"  Table: {alert['table']}")
    print(f"  Impact: {alert['impact_analysis']}")
```

## Architecture

```
┌─────────────────┐
│   BigQuery      │
│  INFORMATION_   │
│    SCHEMA       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Schema Guardian │
│  - Capture      │
│  - Compare      │
│  - Analyze      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Agent Memory   │
│   (Firestore)   │
│  - Baselines    │
│  - Alerts       │
│  - Status       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   FastAPI       │
│   Dashboard     │
└─────────────────┘
```

## Alert Structure

```json
{
  "agent": "Schema Guardian",
  "timestamp": "2025-10-16T10:30:00Z",
  "table": "project.dataset.table",
  "severity": "CRITICAL",
  "changes": {
    "type_changes": [
      {
        "column": "sentiment_score",
        "from": "STRING",
        "to": "FLOAT"
      }
    ],
    "new_columns": [],
    "removed_columns": []
  },
  "impact_analysis": "⚠️ Type changes will break queries expecting previous types",
  "recommendations": [
    "Pause Fivetran connector immediately",
    "Review source data for type inconsistencies",
    "Update downstream transformations"
  ],
  "change_count": 1
}
```

## Severity Levels

| Severity | Triggers | Impact | Action Required |
|----------|----------|--------|-----------------|
| **CRITICAL** | Type changes | Breaking changes to queries | Immediate intervention |
| **HIGH** | Removed columns, partition changes | Query failures, performance impact | Urgent review |
| **MEDIUM** | Nullability changes | Potential NULL handling issues | Review within 24h |
| **LOW** | New columns | Documentation updates needed | Review at convenience |
| **INFO** | No changes | Informational only | None |

## API Endpoints

### Get Agent Status
```bash
curl http://localhost:8000/api/status
```

### Get Recent Alerts
```bash
curl http://localhost:8000/api/alerts?limit=10
```

### Get Agent Details
```bash
curl http://localhost:8000/api/agent/Schema%20Guardian
```

### Health Check
```bash
curl http://localhost:8000/api/health
```

## Testing

```bash
# Run all tests
pytest tests/test_schema_guardian.py -v

# Run specific test
pytest tests/test_schema_guardian.py::test_severity_calculation -v

# Run with coverage
pytest tests/test_schema_guardian.py --cov=agents --cov-report=html
```

## Configuration

### Environment Variables

```bash
# Required
export GOOGLE_APPLICATION_CREDENTIALS="credentials.json"
export GCP_PROJECT_ID="your-project-id"

# Optional
export SCHEMA_CHECK_INTERVAL=300  # seconds
export LOG_LEVEL="INFO"
```

### Firestore Collections

- `schema_baselines`: Stores table schema snapshots
- `alerts`: Stores all generated alerts
- `agent_status`: Stores current agent status

## Monitoring Commands

```bash
# Start monitoring (background)
nohup python agents/run_schema_guardian.py \
  --project your-project \
  --dataset osprey_data \
  --table raw_news \
  --interval 300 > logs/guardian.log 2>&1 &

# Check logs
tail -f logs/guardian.log

# Query recent alerts (Python)
python -c "
from agents.agent_memory import AgentMemory
m = AgentMemory()
alerts = m.get_alert_history(5)
for a in alerts:
    print(f\"{a['severity']}: {a['change_count']} changes\")
"

# Stop monitoring
pkill -f run_schema_guardian
```

## Troubleshooting

### Issue: "No baseline found"
**Solution**: Run baseline capture first:
```python
guardian.capture_baseline_schema()
memory.store_schema_baseline("table_name", baseline)
```

### Issue: "Permission denied on BigQuery"
**Solution**: Ensure service account has `bigquery.tables.get` permission

### Issue: "Firestore initialization failed"
**Solution**: 
1. Enable Firestore API in GCP Console
2. Set `GOOGLE_APPLICATION_CREDENTIALS` environment variable
3. Verify service account has Firestore permissions

### Issue: API returns 500 error
**Solution**: Check Firestore connectivity and credentials

## Performance

- **Schema check latency**: ~2-5 seconds (depends on table size)
- **Memory usage**: ~50-100 MB
- **BigQuery cost**: ~$0.00001 per check (10 MB minimum query)
- **Firestore cost**: ~$0.0001 per alert stored

## Next Steps

After completing Schema Guardian:
1. ✅ Verify all tests pass
2. ✅ Run monitoring for 1+ hours
3. ✅ Test API endpoints
4. ✅ Verify Firestore data storage
5. ➡️ **Move to Day 6: Anomaly Detective**

## Quick Verification Checklist

```bash
# 1. Check if guardian is running
ps aux | grep schema_guardian

# 2. Test imports
python -c "from agents.schema_guardian import SchemaGuardian; print('✅ Imports working')"

# 3. Check Firestore collections
gcloud firestore collections list

# 4. Test API
curl http://localhost:8000/api/health

# 5. Run tests
pytest tests/test_schema_guardian.py -v
```

---

**Status**: Day 3-5 Complete ✅  
**Next**: Day 6-8 Anomaly Detective Implementation
