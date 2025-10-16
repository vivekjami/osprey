# Day 3-5: Schema Guardian Setup Guide

## Prerequisites Installation

### 1. Install Required Packages

```powershell
# Ensure virtual environment is active
# If not: python -m venv venv; .\venv\Scripts\Activate.ps1

pip install google-cloud-bigquery google-cloud-firestore pandas fastapi uvicorn pytest pytest-cov
```

### 2. Set Environment Variables

```powershell
# Set GCP credentials (update path to your credentials file)
$env:GOOGLE_APPLICATION_CREDENTIALS="path\to\credentials.json"

# Set project ID
$env:GCP_PROJECT_ID="your-project-id"
```

### 3. Verify GCP Access

```powershell
# Test BigQuery access
python -c "from google.cloud import bigquery; client = bigquery.Client(); print('✅ BigQuery connected')"

# Test Firestore access
python -c "from google.cloud import firestore; db = firestore.Client(); print('✅ Firestore connected')"
```

## Step-by-Step Execution

### Step 1: Capture Initial Baseline (Run Once)

```python
# Save this as: scripts/capture_baseline.py

from agents.schema_guardian import SchemaGuardian
from agents.agent_memory import AgentMemory
import os

# Configuration
PROJECT_ID = os.getenv("GCP_PROJECT_ID", "your-project-id")
DATASET_ID = "osprey_data"
TABLE_ID = "raw_news"

# Initialize
guardian = SchemaGuardian(PROJECT_ID, DATASET_ID, TABLE_ID)
memory = AgentMemory(PROJECT_ID)

# Capture baseline
print(f"📊 Capturing baseline for {TABLE_ID}...")
baseline = guardian.capture_baseline_schema()
print(f"✅ Captured {len(baseline)} columns:")
print(baseline[['column_name', 'data_type', 'is_nullable']].to_string())

# Store in Firestore
print(f"\n💾 Storing baseline in Firestore...")
memory.store_schema_baseline(TABLE_ID, baseline)

# Verify storage
print(f"\n🔍 Verifying storage...")
retrieved = memory.get_schema_baseline(TABLE_ID)
if retrieved is not None and len(retrieved) == len(baseline):
    print(f"✅ Baseline stored and verified successfully!")
else:
    print(f"❌ Baseline verification failed")
```

Run it:
```powershell
python scripts/capture_baseline.py
```

### Step 2: Run Tests

```powershell
# Create logs directory
mkdir logs -Force

# Run tests
pytest tests/test_schema_guardian.py -v -s
```

Expected output:
```
test_capture_baseline PASSED
test_detect_no_changes PASSED
test_severity_calculation PASSED
test_alert_generation PASSED
test_impact_analysis PASSED
test_recommendations PASSED
test_metrics PASSED
test_agent_status_storage PASSED
```

### Step 3: Start Schema Guardian Monitor

```powershell
# Terminal 1: Start the monitoring agent
python agents/run_schema_guardian.py `
  --project your-project-id `
  --dataset osprey_data `
  --table raw_news `
  --interval 300
```

Expected output:
```
🛡️ Schema Guardian starting for raw_news
📊 Check interval: 300 seconds
✅ Loaded baseline with 10 columns
🔍 Running check #1...
✅ Schema stable - no changes detected
```

### Step 4: Start API Server

```powershell
# Terminal 2: Start the API server
uvicorn agents.api:app --reload --port 8000
```

Expected output:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

### Step 5: Test API Endpoints

```powershell
# Test health endpoint
curl http://localhost:8000/api/health

# Test status endpoint
curl http://localhost:8000/api/status

# Test alerts endpoint
curl http://localhost:8000/api/alerts?limit=5

# Test agent details
curl "http://localhost:8000/api/agent/Schema%20Guardian"
```

### Step 6: Simulate Schema Change (Optional - For Testing)

```sql
-- Run in BigQuery Console to test detection

-- Add a test column
ALTER TABLE `your-project.osprey_data.raw_news`
ADD COLUMN test_column STRING;

-- Wait for next check cycle (5 minutes)
-- Check logs - should show alert
```

Expected guardian output:
```
🚨 Schema drift detected! Severity: LOW
Changes: 1
  new_columns: ['test_column']
```

### Step 7: Query Alerts from Python

```python
# Save as: scripts/check_alerts.py

from agents.agent_memory import AgentMemory

memory = AgentMemory()

# Get recent alerts
alerts = memory.get_alert_history(limit=10)

print(f"📋 Found {len(alerts)} recent alerts:\n")

for i, alert in enumerate(alerts, 1):
    print(f"{i}. {alert.get('severity')} - {alert.get('agent')}")
    print(f"   Time: {alert.get('timestamp')}")
    print(f"   Table: {alert.get('table')}")
    print(f"   Changes: {alert.get('change_count')}")
    print(f"   Impact: {alert.get('impact_analysis')}")
    print()
```

Run it:
```powershell
python scripts/check_alerts.py
```

## Day 5 Checkpoint Verification

Run this verification script:

```powershell
# Save as: scripts/verify_checkpoint.ps1

Write-Host "`n🔍 Day 3-5 Checkpoint Verification" -ForegroundColor Cyan
Write-Host "================================`n" -ForegroundColor Cyan

# 1. Check Python imports
Write-Host "1. Testing Python imports..." -ForegroundColor Yellow
python -c "from agents.schema_guardian import SchemaGuardian; from agents.agent_memory import AgentMemory; print('   ✅ Imports working')"

# 2. Check if guardian is running
Write-Host "`n2. Checking if Schema Guardian is running..." -ForegroundColor Yellow
$process = Get-Process python -ErrorAction SilentlyContinue | Where-Object {$_.MainWindowTitle -like "*schema_guardian*"}
if ($process) {
    Write-Host "   ✅ Schema Guardian is running (PID: $($process.Id))" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  Schema Guardian not running" -ForegroundColor Red
}

# 3. Check API
Write-Host "`n3. Testing API health..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/health" -Method Get
    Write-Host "   ✅ API is responding: $($response.status)" -ForegroundColor Green
} catch {
    Write-Host "   ❌ API not responding" -ForegroundColor Red
}

# 4. Check Firestore collections
Write-Host "`n4. Checking Firestore collections..." -ForegroundColor Yellow
Write-Host "   Run manually: gcloud firestore collections list" -ForegroundColor Gray
Write-Host "   Expected: alerts, schema_baselines, agent_status" -ForegroundColor Gray

# 5. Run tests
Write-Host "`n5. Running test suite..." -ForegroundColor Yellow
pytest tests/test_schema_guardian.py -v --tb=short

Write-Host "`n✅ Checkpoint verification complete!" -ForegroundColor Green
Write-Host "If all checks passed, you're ready for Day 6-8 (Anomaly Detective)" -ForegroundColor Cyan
```

Run verification:
```powershell
.\scripts\verify_checkpoint.ps1
```

## Troubleshooting

### Issue: ImportError for google.cloud

**Solution:**
```powershell
pip install --upgrade google-cloud-bigquery google-cloud-firestore
```

### Issue: Authentication error

**Solution:**
```powershell
# Verify credentials file exists
Test-Path $env:GOOGLE_APPLICATION_CREDENTIALS

# Re-authenticate
gcloud auth application-default login
```

### Issue: Port 8000 already in use

**Solution:**
```powershell
# Find process using port 8000
netstat -ano | findstr :8000

# Kill the process (replace PID)
Stop-Process -Id PID -Force

# Or use different port
uvicorn agents.api:app --port 8001
```

### Issue: Firestore permission denied

**Solution:**
1. Go to GCP Console → Firestore
2. Enable Firestore API
3. Grant service account `Cloud Datastore User` role

### Issue: Tests fail with "No module named 'agents'"

**Solution:**
```powershell
# Add PYTHONPATH
$env:PYTHONPATH = "d:\osprey"

# Or install as package
pip install -e .
```

## Quick Commands Reference

```powershell
# Start monitoring (background)
Start-Process python -ArgumentList "agents/run_schema_guardian.py --project $env:GCP_PROJECT_ID --dataset osprey_data --table raw_news --interval 300" -NoNewWindow

# Start API
Start-Process python -ArgumentList "-m uvicorn agents.api:app --port 8000" -NoNewWindow

# Check logs
Get-Content logs/schema_guardian.log -Tail 20 -Wait

# Stop all
Get-Process python | Where-Object {$_.MainWindowTitle -like "*schema*"} | Stop-Process

# Query alerts
python -c "from agents.agent_memory import AgentMemory; m = AgentMemory(); alerts = m.get_alert_history(5); print(f'{len(alerts)} alerts found')"
```

## Success Criteria Checklist

- [ ] ✅ All dependencies installed
- [ ] ✅ GCP credentials configured
- [ ] ✅ Baseline captured and stored in Firestore
- [ ] ✅ All tests passing (8/8)
- [ ] ✅ Schema Guardian running autonomously
- [ ] ✅ API responding on port 8000
- [ ] ✅ Can query alerts from Firestore
- [ ] ✅ Schema changes detected correctly
- [ ] ✅ Severity calculation working
- [ ] ✅ Agent running for >1 hour without errors

**If all checked: Ready for Day 6 - Anomaly Detective! 🚀**

---

## Next Steps

After completing Day 3-5:

1. **Review the architecture diagram** in README.md
2. **Document any custom configurations** you made
3. **Take screenshots** of working system for demo
4. **Commit your code** to git
5. **Proceed to Day 6-8**: Anomaly Detective implementation

**Estimated Time**: 24 hours (3 days × 8 hours)  
**Actual Completion**: Track your time and blockers
