"""
Verify Schema Guardian setup and environment configuration
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=" * 80)
print("🔍 Schema Guardian Setup Verification")
print("=" * 80)

# Check environment variables
print("\n📋 Environment Variables:")
print("-" * 80)

project_id = os.getenv("PROJECT_ID")
dataset_id = os.getenv("DATASET_ID")
table_id = os.getenv("TABLE_ID")
creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

if project_id:
    print(f"✅ PROJECT_ID: {project_id}")
else:
    print("❌ PROJECT_ID not set")
    sys.exit(1)

if dataset_id:
    print(f"✅ DATASET_ID: {dataset_id}")
else:
    print("❌ DATASET_ID not set")

if table_id:
    print(f"✅ TABLE_ID: {table_id}")
else:
    print("❌ TABLE_ID not set")

if creds_path:
    print(f"✅ GOOGLE_APPLICATION_CREDENTIALS: {creds_path}")
    if Path(creds_path).exists():
        print(f"✅ Credentials file exists")
    else:
        print(f"❌ Credentials file NOT found at: {creds_path}")
        sys.exit(1)
else:
    print("❌ GOOGLE_APPLICATION_CREDENTIALS not set")
    sys.exit(1)

# Check Python packages
print("\n📦 Python Packages:")
print("-" * 80)

packages = {
    "google.cloud.bigquery": "BigQuery",
    "google.cloud.firestore": "Firestore",
    "pandas": "Pandas",
    "fastapi": "FastAPI",
    "pytest": "Pytest"
}

all_packages_ok = True
for module, name in packages.items():
    try:
        __import__(module)
        print(f"✅ {name}")
    except ImportError:
        print(f"❌ {name} not installed")
        all_packages_ok = False

if not all_packages_ok:
    print("\n❌ Some packages are missing. Run: uv sync")
    sys.exit(1)

# Check if Schema Guardian modules can be imported
print("\n🛡️  Schema Guardian Modules:")
print("-" * 80)

try:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from agents.schema_guardian import SchemaGuardian
    from agents.agent_memory import AgentMemory
    print("✅ schema_guardian.py")
    print("✅ agent_memory.py")
except ImportError as e:
    print(f"❌ Failed to import modules: {e}")
    sys.exit(1)

# Check GCP connectivity
print("\n☁️  GCP Connectivity:")
print("-" * 80)

try:
    from google.cloud import bigquery
    client = bigquery.Client(project=project_id)
    print(f"✅ BigQuery client initialized")
    
    # Try to check if dataset exists
    try:
        dataset_ref = client.dataset(dataset_id)
        dataset = client.get_dataset(dataset_ref)
        print(f"✅ Dataset '{dataset_id}' accessible")
        
        # Check if table exists
        try:
            table_ref = dataset_ref.table(table_id)
            table = client.get_table(table_ref)
            print(f"✅ Table '{table_id}' accessible ({table.num_rows} rows)")
        except Exception as e:
            print(f"⚠️  Table '{table_id}' not found or not accessible")
            print(f"   Error: {e}")
    except Exception as e:
        print(f"⚠️  Dataset '{dataset_id}' not found or not accessible")
        print(f"   Error: {e}")
        
except Exception as e:
    print(f"❌ BigQuery connection failed: {e}")
    print(f"   Check your credentials and project ID")
    sys.exit(1)

# Check Firestore connectivity
try:
    from google.cloud import firestore
    db = firestore.Client(project=project_id)
    print(f"✅ Firestore client initialized")
    
    # Try to list collections
    collections = list(db.collections())
    print(f"✅ Firestore accessible ({len(collections)} collections)")
    
except Exception as e:
    print(f"⚠️  Firestore connection: {e}")
    print(f"   (This is OK if you haven't used Firestore yet)")

# Check logs directory
print("\n📁 Directory Structure:")
print("-" * 80)

logs_dir = Path("logs")
if logs_dir.exists():
    print(f"✅ logs/ directory exists")
else:
    print(f"⚠️  logs/ directory missing (will be created on first run)")
    logs_dir.mkdir(exist_ok=True)
    print(f"✅ Created logs/ directory")

# Check if scripts exist
scripts = ["capture_baseline.py", "check_alerts.py"]
for script in scripts:
    script_path = Path("scripts") / script
    if script_path.exists():
        print(f"✅ scripts/{script}")
    else:
        print(f"⚠️  scripts/{script} missing")

# Summary
print("\n" + "=" * 80)
print("📊 Verification Summary")
print("=" * 80)

print("\n✅ All core components verified!")
print("\n🚀 Next Steps:")
print("   1. Capture baseline schema:")
print(f"      uv run python scripts/capture_baseline.py")
print("\n   2. Start Schema Guardian:")
print(f"      uv run python agents/run_schema_guardian.py --project {project_id} --dataset {dataset_id} --table {table_id}")
print("\n   3. Start API server (in another terminal):")
print(f"      uv run uvicorn agents.api:app --reload --port 8000")
print("\n" + "=" * 80)
