# Schema Guardian Quick Start Guide

## 🚀 5-Minute Setup

### Step 1: Install Dependencies (2 minutes)

```powershell
# Make sure you're in the osprey directory
cd d:\osprey

# Install all dependencies
pip install -e .

# Or install manually
pip install google-cloud-bigquery google-cloud-firestore pandas fastapi uvicorn pytest pytest-cov
```

### Step 2: Configure GCP (1 minute)

```powershell
# Set your credentials file path
$env:GOOGLE_APPLICATION_CREDENTIALS="path\to\your\credentials.json"

# Set your project ID
$env:GCP_PROJECT_ID="your-gcp-project-id"

# Verify connection
python -c "from google.cloud import bigquery; client = bigquery.Client(); print('✅ Connected!')"
```

### Step 3: Capture Baseline (1 minute)

```powershell
# Run the baseline capture script
python scripts/capture_baseline.py
```

Expected output:
```
✅ Captured 10 columns
✅ Baseline stored and verified successfully!
```

### Step 4: Start Monitoring (1 minute)

Open **two terminal windows**:

**Terminal 1 - Schema Guardian:**
```powershell
python agents/run_schema_guardian.py `
  --project your-project-id `
  --dataset osprey_data `
  --table raw_news `
  --interval 300
```

**Terminal 2 - API Server:**
```powershell
uvicorn agents.api:app --reload --port 8000
```

### Step 5: Verify Everything Works

Open a **third terminal** and run:

```powershell
# Test API
curl http://localhost:8000/api/health

# Check status
curl http://localhost:8000/api/status

# Run verification
.\scripts\verify_checkpoint.ps1
```

---

## 🎯 What You Should See

### Terminal 1 (Schema Guardian):
```
🛡️ Schema Guardian starting for raw_news
📊 Check interval: 300 seconds
✅ Loaded baseline with 10 columns
🔍 Running check #1...
✅ Schema stable - no changes detected
```

### Terminal 2 (API):
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

### Browser (http://localhost:8000):
```json
{
  "name": "Osprey Agent API",
  "version": "1.0.0",
  "status": "operational"
}
```

---

## 🧪 Test Schema Detection

### Option 1: Add a Test Column (Safe)

In BigQuery Console, run:
```sql
ALTER TABLE `your-project.osprey_data.raw_news`
ADD COLUMN test_detection_column STRING;
```

Wait 5 minutes (or whatever interval you set), then check:
```powershell
python scripts/check_alerts.py
```

You should see:
```
🟢 LOW - Schema Guardian
   Changes: 1
   New columns: ['test_detection_column']
```

### Option 2: Simulate Type Change (Advanced)

This requires creating a new table with different types, which is more complex but tests CRITICAL alerts.

---

## 📊 Monitor in Real-Time

### View Logs:
```powershell
Get-Content logs\schema_guardian.log -Tail 20 -Wait
```

### Query Alerts:
```powershell
python scripts/check_alerts.py
```

### Check API:
```powershell
# Get agent status
curl http://localhost:8000/api/status | ConvertFrom-Json | ConvertTo-Json -Depth 10

# Get recent alerts
curl "http://localhost:8000/api/alerts?limit=5" | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

---

## 🛑 Stopping Everything

```powershell
# Stop all Python processes
Get-Process python | Stop-Process -Force

# Or stop individual terminals with Ctrl+C
```

---

## 🐛 Common Issues

### "Import error" or "Module not found"
```powershell
# Set Python path
$env:PYTHONPATH = "d:\osprey"

# Reinstall dependencies
pip install -e .
```

### "Permission denied" on BigQuery
- Ensure your service account has `BigQuery Data Viewer` role
- Check that the table exists: `your-project.osprey_data.raw_news`

### "Firestore not found"
- Enable Firestore API in GCP Console
- Grant `Cloud Datastore User` role to service account

### "Port 8000 already in use"
```powershell
# Find and kill process using port 8000
netstat -ano | findstr :8000
Stop-Process -Id <PID> -Force

# Or use different port
uvicorn agents.api:app --port 8001
```

---

## ✅ Success Checklist

Before moving to Day 6:

- [ ] All dependencies installed without errors
- [ ] GCP credentials configured and working
- [ ] Baseline captured (10+ columns)
- [ ] Schema Guardian running for 10+ minutes without crashes
- [ ] API responding to health checks
- [ ] Can query alerts from Firestore
- [ ] Test schema change detected correctly
- [ ] All tests passing: `pytest tests/test_schema_guardian.py -v`

---

## 🎓 Understanding the System

### What's Running:

1. **Schema Guardian** (Terminal 1):
   - Queries BigQuery INFORMATION_SCHEMA every 5 minutes
   - Compares current schema to baseline
   - Generates alerts on changes
   - Stores alerts in Firestore

2. **API Server** (Terminal 2):
   - Exposes REST endpoints for dashboard
   - Queries Firestore for alerts and status
   - Provides real-time system status

3. **Firestore Collections**:
   - `schema_baselines`: Stored schema snapshots
   - `alerts`: All generated alerts
   - `agent_status`: Current agent states

### Data Flow:

```
BigQuery Table
    ↓
INFORMATION_SCHEMA Query (every 5 min)
    ↓
Schema Comparison
    ↓
Change Detection
    ↓
Alert Generation
    ↓
Firestore Storage
    ↓
API Endpoints
    ↓
Dashboard (future)
```

---

## 📈 Next Steps

Once everything is working:

1. **Let it run for 1 hour** to ensure stability
2. **Create test scenarios** to verify detection
3. **Document your configuration** (project ID, table, etc.)
4. **Take screenshots** for your demo
5. **Commit to git**:
   ```powershell
   git add .
   git commit -m "Day 3-5: Schema Guardian implementation complete"
   ```
6. **Proceed to Day 6-8**: Anomaly Detective with Vertex AI

---

## 💡 Pro Tips

- **Background Running**: Use `Start-Process` to run in background
- **Auto-restart**: Consider using `supervisor` or Windows Task Scheduler
- **Logging**: Logs are in `logs/schema_guardian.log`
- **Debugging**: Add `--log-level DEBUG` for more verbose output
- **Performance**: 300s interval is good balance (cost vs freshness)

---

**Status**: Day 3-5 Implementation Complete ✅  
**Time Required**: ~24 hours (3 days × 8 hours)  
**Next**: Day 6-8 Anomaly Detective 🚀
