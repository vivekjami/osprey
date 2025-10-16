"""
Capture initial baseline schema and store in Firestore
Run this script once before starting the monitoring agent
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from agents.schema_guardian import SchemaGuardian
from agents.agent_memory import AgentMemory

# Configuration
PROJECT_ID = os.getenv("PROJECT_ID")
DATASET_ID = os.getenv("DATASET_ID", "osprey_data")
TABLE_ID = os.getenv("TABLE_ID", "raw_news")

if not PROJECT_ID:
    print("❌ Error: PROJECT_ID environment variable not set")
    print("Make sure .env file exists with PROJECT_ID set")
    sys.exit(1)

try:
    # Initialize
    print(f"🔧 Initializing Schema Guardian...")
    print(f"   Project: {PROJECT_ID}")
    print(f"   Table: {DATASET_ID}.{TABLE_ID}")
    
    guardian = SchemaGuardian(PROJECT_ID, DATASET_ID, TABLE_ID)
    memory = AgentMemory(PROJECT_ID)

    # Capture baseline
    print(f"\n📊 Capturing baseline schema...")
    baseline = guardian.capture_baseline_schema()
    
    print(f"\n✅ Captured {len(baseline)} columns:")
    print("=" * 80)
    print(baseline[['column_name', 'data_type', 'is_nullable', 'ordinal_position']].to_string())
    print("=" * 80)

    # Store in Firestore
    print(f"\n💾 Storing baseline in Firestore...")
    memory.store_schema_baseline(TABLE_ID, baseline)

    # Verify storage
    print(f"\n🔍 Verifying storage...")
    retrieved = memory.get_schema_baseline(TABLE_ID)
    
    if retrieved is not None and len(retrieved) == len(baseline):
        print(f"✅ Baseline stored and verified successfully!")
        print(f"\n📝 Summary:")
        print(f"   - Columns: {len(baseline)}")
        print(f"   - Table: {PROJECT_ID}.{DATASET_ID}.{TABLE_ID}")
        print(f"   - Stored in: Firestore collection 'schema_baselines'")
        print(f"\n🚀 You can now start the monitoring agent with:")
        print(f"   python agents/run_schema_guardian.py --project {PROJECT_ID} --dataset {DATASET_ID} --table {TABLE_ID}")
    else:
        print(f"❌ Baseline verification failed")
        sys.exit(1)

except Exception as e:
    print(f"\n❌ Error: {e}")
    print(f"\nTroubleshooting:")
    print(f"1. Verify GOOGLE_APPLICATION_CREDENTIALS is set")
    print(f"2. Ensure table {PROJECT_ID}.{DATASET_ID}.{TABLE_ID} exists")
    print(f"3. Check service account has BigQuery and Firestore permissions")
    sys.exit(1)
