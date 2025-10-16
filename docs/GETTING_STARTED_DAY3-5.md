# 🚀 Getting Started with Day 3-5: Schema Guardian

## What You've Built

Congratulations! You now have a **fully functional autonomous Schema Guardian agent** that monitors BigQuery tables for schema changes in real-time. This is the first of three agents in your Osprey multi-agent system.

## Project Status

✅ **Day 1-2**: Fivetran Connector (Complete)  
✅ **Day 3-5**: Schema Guardian (Complete) ← **YOU ARE HERE**  
⏭️ **Day 6-8**: Anomaly Detective (Next)  
⏭️ **Day 9-11**: Pipeline Orchestrator  
⏭️ **Day 12-14**: Dashboard & ML  
⏭️ **Day 15**: Deployment

---

## Quick Start (Choose Your Path)

### Path A: Just Want to See it Work? (5 minutes)

1. **Install dependencies:**
   ```powershell
   pip install google-cloud-bigquery google-cloud-firestore pandas fastapi uvicorn
   ```

2. **Set credentials:**
   ```powershell
   $env:GOOGLE_APPLICATION_CREDENTIALS="path\to\credentials.json"
   $env:GCP_PROJECT_ID="your-project-id"
   ```

3. **Capture baseline:**
   ```powershell
   python scripts/capture_baseline.py
   ```

4. **Start monitoring:**
   ```powershell
   python agents/run_schema_guardian.py --project YOUR_PROJECT --dataset osprey_data --table raw_news
   ```

5. **In another terminal, start API:**
   ```powershell
   uvicorn agents.api:app --port 8000
   ```

6. **Test it:**
   ```powershell
   curl http://localhost:8000/api/health
   ```

**✅ Success!** Your Schema Guardian is now running autonomously.

---

### Path B: Want Full Setup with Testing? (15 minutes)

Follow the comprehensive guide: **[docs/QUICKSTART.md](QUICKSTART.md)**

---

### Path C: Developer Deep Dive? (1 hour)

Read the detailed implementation guide: **[docs/SETUP_DAY3-5.md](SETUP_DAY3-5.md)**

---

## What's Running?

### Terminal 1: Schema Guardian
```
🛡️ Schema Guardian starting for raw_news
📊 Check interval: 300 seconds
✅ Loaded baseline with 10 columns
🔍 Running check #1...
✅ Schema stable - no changes detected
```

**What it does:**
- Queries BigQuery INFORMATION_SCHEMA every 5 minutes
- Compares current schema to baseline
- Detects: new columns, type changes, nullability changes
- Generates alerts with severity levels
- Stores alerts in Firestore

### Terminal 2: FastAPI Server
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

**What it provides:**
- REST API for dashboard integration
- Agent status queries
- Alert history
- Health checks

---

## Testing Your Setup

### 1. Verify API is Working
```powershell
# Health check
curl http://localhost:8000/api/health

# Expected response:
# {"status": "healthy", "timestamp": "...", "service": "Osprey Multi-Agent System"}
```

### 2. Check Agent Status
```powershell
curl http://localhost:8000/api/status
```

Expected response:
```json
{
  "agents": [
    {
      "name": "Schema Guardian",
      "status": "running",
      "checks_performed": 5,
      "alerts_today": 0
    }
  ]
}
```

### 3. Simulate a Schema Change
In BigQuery Console, add a test column:
```sql
ALTER TABLE `your-project.osprey_data.raw_news`
ADD COLUMN test_column STRING;
```

Wait 5 minutes, then check alerts:
```powershell
python scripts/check_alerts.py
```

You should see:
```
🟢 LOW - Schema Guardian
   Time: 2025-10-16T...
   Changes: 1
   New columns: ['test_column']
   Recommendations:
      - Document new column purpose
      - Update schema documentation
```

### 4. Run Verification
```powershell
.\scripts\verify_checkpoint.ps1
```

This checks:
- ✅ Dependencies installed
- ✅ GCP credentials configured
- ✅ Schema Guardian running
- ✅ API responding
- ✅ Firestore accessible

---

## Understanding the System

### Architecture

```
┌─────────────────┐
│   BigQuery      │  Your data warehouse
│  raw_news table │
└────────┬────────┘
         │
         │ Query INFORMATION_SCHEMA
         ↓
┌─────────────────┐
│ Schema Guardian │  Autonomous agent
│  - Detects      │
│  - Analyzes     │
│  - Alerts       │
└────────┬────────┘
         │
         │ Store alerts
         ↓
┌─────────────────┐
│   Firestore     │  Persistent storage
│  - Baselines    │
│  - Alerts       │
│  - Status       │
└────────┬────────┘
         │
         │ Query for display
         ↓
┌─────────────────┐
│   FastAPI       │  REST API
│   Dashboard     │  (Future: React UI)
└─────────────────┘
```

### Data Flow

1. **Every 5 minutes:** Schema Guardian queries BigQuery
2. **Comparison:** Current schema vs stored baseline
3. **Detection:** Any changes? (new columns, type changes, etc.)
4. **Alert:** Generate structured alert with severity
5. **Storage:** Save to Firestore for history
6. **API:** Dashboard can query alerts in real-time

---

## Common Commands

### Start Everything
```powershell
# Terminal 1
python agents/run_schema_guardian.py --project YOUR_PROJECT --dataset osprey_data --table raw_news

# Terminal 2
uvicorn agents.api:app --port 8000
```

### Monitor Logs
```powershell
Get-Content logs\schema_guardian.log -Tail 20 -Wait
```

### Query Alerts
```powershell
python scripts/check_alerts.py
```

### Test API
```powershell
# Health
curl http://localhost:8000/api/health

# Status
curl http://localhost:8000/api/status

# Recent alerts
curl "http://localhost:8000/api/alerts?limit=5"
```

### Run Tests
```powershell
pytest tests/test_schema_guardian.py -v
```

### Stop Everything
```powershell
# Ctrl+C in each terminal
# Or kill all Python processes:
Get-Process python | Stop-Process -Force
```

---

## Troubleshooting

### "Import error: No module named 'agents'"
```powershell
$env:PYTHONPATH = "d:\osprey"
# Or: pip install -e .
```

### "Permission denied" on BigQuery
- Grant your service account `BigQuery Data Viewer` role
- Verify table exists: `your-project.osprey_data.raw_news`

### "Firestore not found"
- Enable Firestore API in GCP Console
- Grant service account `Cloud Datastore User` role

### "Port 8000 already in use"
```powershell
netstat -ano | findstr :8000
Stop-Process -Id <PID> -Force
```

### API returns 500 error
- Check Firestore connectivity
- Verify GOOGLE_APPLICATION_CREDENTIALS is set
- Check logs: `Get-Content logs\schema_guardian.log`

---

## Next Steps

### Before Moving to Day 6

**✅ Completion Checklist:**
- [ ] Schema Guardian running for 1+ hours without errors
- [ ] API responding to all endpoints
- [ ] Test schema change detected correctly
- [ ] All tests passing: `pytest tests/test_schema_guardian.py -v`
- [ ] Firestore has data (baseline, alerts, status)
- [ ] Can query alerts programmatically
- [ ] Documentation reviewed and understood

### When Ready for Day 6-8

**Anomaly Detective** will add:
- Vertex AI Gemini for semantic analysis
- Detection of: test data, invalid symbols, temporal anomalies
- BigQuery ML predictive model
- Multi-agent coordination

Start here: **[docs/DAY6-8_IMPLEMENTATION.md](DAY6-8_IMPLEMENTATION.md)** (to be created)

---

## Demo Preparation

### For Hackathon Demo

1. **Screenshot this:** Schema Guardian running with logs
2. **Screenshot this:** API response showing agent status
3. **Screenshot this:** Alert after schema change detection
4. **Prepare narrative:**
   - "Traditional monitoring: Did sync succeed?"
   - "Osprey: Is the data semantically valid?"
   - "Schema Guardian detects structural changes autonomously"

### Key Talking Points

- ✅ **Autonomous**: No manual intervention required
- ✅ **Real-time**: 5-minute detection latency
- ✅ **Intelligent**: Severity-based prioritization
- ✅ **Actionable**: Clear recommendations
- ✅ **Persistent**: Full audit trail in Firestore
- ✅ **API-first**: Dashboard-ready

---

## Files Reference

### Core Implementation
- `agents/schema_guardian.py` - Main agent logic
- `agents/agent_memory.py` - Firestore integration
- `agents/run_schema_guardian.py` - Monitoring loop
- `agents/api.py` - REST API endpoints

### Testing
- `tests/test_schema_guardian.py` - Test suite

### Helper Scripts
- `scripts/capture_baseline.py` - Initial baseline capture
- `scripts/check_alerts.py` - Query alerts
- `scripts/verify_checkpoint.ps1` - System verification

### Documentation
- `agents/README.md` - Agent documentation
- `docs/QUICKSTART.md` - 5-minute setup
- `docs/SETUP_DAY3-5.md` - Detailed setup guide
- `docs/DAY3-5_SUMMARY.md` - Implementation summary

---

## Need Help?

### Quick Checks
1. Is Python working? `python --version`
2. Are credentials set? `echo $env:GOOGLE_APPLICATION_CREDENTIALS`
3. Can you connect to BigQuery? `python -c "from google.cloud import bigquery; bigquery.Client()"`
4. Is Firestore enabled? Check GCP Console

### Review Documentation
- **Quick setup**: `docs/QUICKSTART.md`
- **Detailed guide**: `docs/SETUP_DAY3-5.md`
- **API docs**: `agents/README.md`
- **Summary**: `docs/DAY3-5_SUMMARY.md`

### Run Verification
```powershell
.\scripts\verify_checkpoint.ps1
```

This will show you exactly what's working and what needs fixing.

---

## Success!

If you can:
1. ✅ Start Schema Guardian
2. ✅ Start API server
3. ✅ Query agent status
4. ✅ Detect a schema change
5. ✅ Query alerts from Firestore

**Then you're 100% ready for Day 6-8!** 🎉

---

**Current Status**: Day 3-5 Complete ✅  
**Next Milestone**: Day 6-8 Anomaly Detective with Vertex AI  
**Final Goal**: Day 15 Deployment & Submission 🏆
