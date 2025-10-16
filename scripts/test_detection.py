"""
Test schema detection functionality
"""

import os
import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from agents.schema_guardian import SchemaGuardian
import pandas as pd

# Configuration
PROJECT_ID = os.getenv("PROJECT_ID")
DATASET_ID = os.getenv("DATASET_ID", "osprey_data")
TABLE_ID = os.getenv("TABLE_ID", "raw_news")

print("=" * 80)
print("🧪 Testing Schema Detection")
print("=" * 80)

# Initialize guardian
guardian = SchemaGuardian(PROJECT_ID, DATASET_ID, TABLE_ID)

# Load baseline from file
baseline_file = Path("baseline_schema.json")
if not baseline_file.exists():
    print(f"❌ Baseline file not found: {baseline_file}")
    print(f"   Run: uv run python scripts/capture_baseline_local.py")
    sys.exit(1)

with open(baseline_file) as f:
    baseline_data = json.load(f)
    guardian.baseline_schema = pd.DataFrame(baseline_data['columns'])

print(f"\n✅ Loaded baseline: {len(guardian.baseline_schema)} columns")

# Detect changes
print(f"\n🔍 Detecting schema changes...")
changes = guardian.detect_schema_drift()

print(f"\n📊 Detection Results:")
print("-" * 80)

has_changes = any(
    len(v) > 0 if isinstance(v, list) else False 
    for v in changes.values() if v != "error"
)

if has_changes:
    print("🚨 Changes detected!")
    for change_type, change_list in changes.items():
        if change_list and isinstance(change_list, list):
            print(f"\n{change_type}:")
            for item in change_list:
                print(f"  - {item}")
    
    # Generate alert
    alert = guardian.generate_alert(changes)
    print(f"\n📋 Alert Generated:")
    print(f"   Severity: {alert['severity']}")
    print(f"   Change Count: {alert['change_count']}")
    print(f"   Impact: {alert['impact_analysis']}")
    print(f"\n   Recommendations:")
    for rec in alert['recommendations']:
        print(f"     - {rec}")
else:
    print("✅ No changes detected - schema is stable!")

# Test metrics
metrics = guardian.get_metrics()
print(f"\n📈 Metrics:")
print(f"   Checks performed: {metrics['checks_performed']}")
print(f"   Alerts generated: {metrics['alerts_generated']}")

print("\n" + "=" * 80)
print("✅ Schema detection test complete!")
print("=" * 80)
