# Day 3-5 Checkpoint Verification Script
# Run this to verify all components are working correctly

Write-Host "`n🔍 Day 3-5 Checkpoint Verification" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Cyan

# Function to check if a command exists
function Test-CommandExists {
    param($command)
    $null -ne (Get-Command $command -ErrorAction SilentlyContinue)
}

# Check prerequisites
Write-Host "`n📋 Checking Prerequisites..." -ForegroundColor Yellow

# Check Python
if (Test-CommandExists python) {
    $pythonVersion = python --version
    Write-Host "   ✅ Python installed: $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "   ❌ Python not found" -ForegroundColor Red
    exit 1
}

# Check pip packages
Write-Host "`n📦 Checking Python packages..." -ForegroundColor Yellow
$packages = @("google-cloud-bigquery", "google-cloud-firestore", "pandas", "fastapi", "pytest")
foreach ($package in $packages) {
    $installed = pip show $package 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ $package installed" -ForegroundColor Green
    } else {
        Write-Host "   ❌ $package not installed" -ForegroundColor Red
    }
}

# Check environment variables
Write-Host "`n🔐 Checking Environment Variables..." -ForegroundColor Yellow
if ($env:GOOGLE_APPLICATION_CREDENTIALS) {
    if (Test-Path $env:GOOGLE_APPLICATION_CREDENTIALS) {
        Write-Host "   ✅ GOOGLE_APPLICATION_CREDENTIALS set and file exists" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  GOOGLE_APPLICATION_CREDENTIALS set but file not found" -ForegroundColor Red
        Write-Host "      Path: $env:GOOGLE_APPLICATION_CREDENTIALS" -ForegroundColor Gray
    }
} else {
    Write-Host "   ❌ GOOGLE_APPLICATION_CREDENTIALS not set" -ForegroundColor Red
}

if ($env:GCP_PROJECT_ID) {
    Write-Host "   ✅ GCP_PROJECT_ID set: $env:GCP_PROJECT_ID" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  GCP_PROJECT_ID not set" -ForegroundColor Yellow
}

# Test Python imports
Write-Host "`n🐍 Testing Python imports..." -ForegroundColor Yellow
$importTest = python -c "from agents.schema_guardian import SchemaGuardian; from agents.agent_memory import AgentMemory; print('OK')" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✅ Python imports working" -ForegroundColor Green
} else {
    Write-Host "   ❌ Python import error" -ForegroundColor Red
    Write-Host "      $importTest" -ForegroundColor Gray
}

# Check if Schema Guardian is running
Write-Host "`n🛡️  Checking if Schema Guardian is running..." -ForegroundColor Yellow
$guardianProcess = Get-Process python -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -like "*run_schema_guardian*"
}
if ($guardianProcess) {
    Write-Host "   ✅ Schema Guardian is running (PID: $($guardianProcess.Id))" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  Schema Guardian not running" -ForegroundColor Yellow
    Write-Host "      Start with: python agents/run_schema_guardian.py --project <PROJECT_ID> --dataset osprey_data --table raw_news" -ForegroundColor Gray
}

# Test API
Write-Host "`n🌐 Testing API..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/health" -Method Get -TimeoutSec 5
    Write-Host "   ✅ API is responding: $($response.status)" -ForegroundColor Green
    
    # Test status endpoint
    $statusResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/status" -Method Get -TimeoutSec 5
    Write-Host "   ✅ API status endpoint working" -ForegroundColor Green
} catch {
    Write-Host "   ⚠️  API not responding (may not be started)" -ForegroundColor Yellow
    Write-Host "      Start with: uvicorn agents.api:app --port 8000" -ForegroundColor Gray
}

# Check Firestore collections (if gcloud is available)
Write-Host "`n🔥 Checking Firestore..." -ForegroundColor Yellow
if (Test-CommandExists gcloud) {
    $collections = gcloud firestore collections list 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ Firestore accessible" -ForegroundColor Green
        Write-Host "      Collections: $collections" -ForegroundColor Gray
    } else {
        Write-Host "   ⚠️  Could not list Firestore collections" -ForegroundColor Yellow
    }
} else {
    Write-Host "   ℹ️  gcloud CLI not found - skipping Firestore check" -ForegroundColor Gray
    Write-Host "      You can manually verify in GCP Console" -ForegroundColor Gray
}

# Check logs directory
Write-Host "`n📁 Checking logs directory..." -ForegroundColor Yellow
if (Test-Path "logs") {
    $logFiles = Get-ChildItem "logs" -Filter "*.log" | Select-Object -First 5
    if ($logFiles) {
        Write-Host "   ✅ Logs directory exists with log files" -ForegroundColor Green
        foreach ($log in $logFiles) {
            Write-Host "      - $($log.Name) ($([math]::Round($log.Length / 1KB, 2)) KB)" -ForegroundColor Gray
        }
    } else {
        Write-Host "   ⚠️  Logs directory exists but no log files" -ForegroundColor Yellow
    }
} else {
    Write-Host "   ⚠️  Logs directory not found" -ForegroundColor Yellow
    Write-Host "      Creating logs directory..." -ForegroundColor Gray
    New-Item -ItemType Directory -Path "logs" -Force | Out-Null
    Write-Host "   ✅ Created logs directory" -ForegroundColor Green
}

# Run tests
Write-Host "`n🧪 Running tests..." -ForegroundColor Yellow
Write-Host "   Note: Tests require valid GCP credentials and BigQuery table" -ForegroundColor Gray

if (Test-Path "tests/test_schema_guardian.py") {
    Write-Host "`n   Running pytest..." -ForegroundColor Cyan
    pytest tests/test_schema_guardian.py -v --tb=short 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`n   ✅ All tests passed!" -ForegroundColor Green
    } else {
        Write-Host "`n   ⚠️  Some tests failed (may be due to missing GCP setup)" -ForegroundColor Yellow
    }
} else {
    Write-Host "   ⚠️  Test file not found" -ForegroundColor Yellow
}

# Summary
Write-Host "`n" + "=" * 80 -ForegroundColor Cyan
Write-Host "📊 Verification Summary" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Cyan

Write-Host "`nSuccess Criteria:" -ForegroundColor Yellow
Write-Host "  ✅ Dependencies installed: Check above" -ForegroundColor Gray
Write-Host "  ✅ GCP credentials configured: Check above" -ForegroundColor Gray
Write-Host "  ✅ Schema Guardian running: Check above" -ForegroundColor Gray
Write-Host "  ✅ API responding: Check above" -ForegroundColor Gray
Write-Host "  ✅ Tests passing: Check above" -ForegroundColor Gray

Write-Host "`n📚 Next Steps:" -ForegroundColor Cyan
Write-Host "  1. If Schema Guardian is not running, start it:" -ForegroundColor White
Write-Host "     python agents/run_schema_guardian.py --project YOUR_PROJECT --dataset osprey_data --table raw_news" -ForegroundColor Gray
Write-Host "`n  2. If API is not running, start it:" -ForegroundColor White
Write-Host "     uvicorn agents.api:app --port 8000" -ForegroundColor Gray
Write-Host "`n  3. Capture baseline if not done:" -ForegroundColor White
Write-Host "     python scripts/capture_baseline.py" -ForegroundColor Gray
Write-Host "`n  4. Check alerts:" -ForegroundColor White
Write-Host "     python scripts/check_alerts.py" -ForegroundColor Gray
Write-Host "`n  5. If all green, proceed to Day 6-8 (Anomaly Detective)!" -ForegroundColor White

Write-Host "`n✅ Verification complete!" -ForegroundColor Green
Write-Host "=" * 80 -ForegroundColor Cyan
