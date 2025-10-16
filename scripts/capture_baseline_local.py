"""
Capture baseline schema (without Firestore)
This version just captures and displays the schema
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from agents.schema_guardian import SchemaGuardian

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

    # Capture baseline
    print(f"\n📊 Capturing baseline schema...")
    baseline = guardian.capture_baseline_schema()
    
    print(f"\n✅ Captured {len(baseline)} columns:")
    print("=" * 80)
    print(baseline[['column_name', 'data_type', 'is_nullable', 'ordinal_position']].to_string())
    print("=" * 80)

    # Save to local JSON file
    import json
    baseline_file = Path("baseline_schema.json")
    baseline_data = {
        'table': f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}",
        'columns': baseline.to_dict('records'),
        'captured_at': baseline.iloc[0]['table_name'] if len(baseline) > 0 else None
    }
    
    with open(baseline_file, 'w') as f:
        json.dump(baseline_data, f, indent=2)
    
    print(f"\n💾 Baseline saved to: {baseline_file.absolute()}")
    
    # Store in memory for immediate use
    guardian.baseline_schema = baseline
    
    print(f"\n📝 Summary:")
    print(f"   - Columns: {len(baseline)}")
    print(f"   - Table: {PROJECT_ID}.{DATASET_ID}.{TABLE_ID}")
    print(f"   - Baseline file: {baseline_file.absolute()}")
    
    print(f"\n⚠️  Note: Firestore is not set up yet.")
    print(f"   To enable Firestore storage:")
    print(f"   1. Go to: https://console.cloud.google.com/datastore/setup?project={PROJECT_ID}")
    print(f"   2. Choose 'Firestore Native Mode'")
    print(f"   3. Select a region (e.g., us-central1)")
    print(f"   4. Then run: uv run python scripts/capture_baseline.py")
    
    print(f"\n🚀 You can now test schema detection with:")
    print(f"   uv run python -c \"")
    print(f"import sys; sys.path.insert(0, '.')")
    print(f"from agents.schema_guardian import SchemaGuardian")
    print(f"import json")
    print(f"guardian = SchemaGuardian('{PROJECT_ID}', '{DATASET_ID}', '{TABLE_ID}')")
    print(f"with open('baseline_schema.json') as f:")
    print(f"    import pandas as pd")
    print(f"    baseline = json.load(f)")
    print(f"    guardian.baseline_schema = pd.DataFrame(baseline['columns'])")
    print(f"changes = guardian.detect_schema_drift()")
    print(f"print('Changes detected:', changes)")
    print(f"\"")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    print(f"\nTroubleshooting:")
    print(f"1. Verify GOOGLE_APPLICATION_CREDENTIALS is set correctly")
    print(f"2. Ensure table {PROJECT_ID}.{DATASET_ID}.{TABLE_ID} exists")
    print(f"3. Check service account has BigQuery permissions")
    sys.exit(1)
