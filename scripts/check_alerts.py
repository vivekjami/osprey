"""
Query and display recent alerts from Firestore
"""

from agents.agent_memory import AgentMemory
import sys
from datetime import datetime

try:
    memory = AgentMemory()

    # Get recent alerts
    print("🔍 Querying recent alerts from Firestore...\n")
    alerts = memory.get_alert_history(limit=10)

    if not alerts:
        print("ℹ️  No alerts found. This means:")
        print("   - Schema Guardian hasn't detected any changes yet")
        print("   - Or the monitoring agent hasn't been started")
        print("\n💡 To generate test alerts, manually alter your BigQuery table schema")
        sys.exit(0)

    print(f"📋 Found {len(alerts)} recent alerts:\n")
    print("=" * 100)

    for i, alert in enumerate(alerts, 1):
        severity = alert.get('severity', 'UNKNOWN')
        agent = alert.get('agent', 'Unknown')
        timestamp = alert.get('timestamp', 'Unknown')
        table = alert.get('table', 'Unknown')
        change_count = alert.get('change_count', 0)
        
        # Color code by severity
        severity_icon = {
            'CRITICAL': '🔴',
            'HIGH': '🟠',
            'MEDIUM': '🟡',
            'LOW': '🟢',
            'INFO': 'ℹ️'
        }.get(severity, '⚪')
        
        print(f"{i}. {severity_icon} {severity} - {agent}")
        print(f"   Time: {timestamp}")
        print(f"   Table: {table}")
        print(f"   Changes: {change_count}")
        
        # Show change details
        changes = alert.get('changes', {})
        if changes:
            if changes.get('type_changes'):
                print(f"   Type changes: {changes['type_changes']}")
            if changes.get('new_columns'):
                print(f"   New columns: {changes['new_columns']}")
            if changes.get('removed_columns'):
                print(f"   Removed columns: {changes['removed_columns']}")
        
        # Show impact and recommendations
        impact = alert.get('impact_analysis', '')
        if impact:
            print(f"   Impact: {impact}")
        
        recommendations = alert.get('recommendations', [])
        if recommendations:
            print(f"   Recommendations:")
            for rec in recommendations[:3]:  # Show first 3
                print(f"      - {rec}")
        
        print("-" * 100)

    print("\n📊 Alert Summary:")
    
    # Count by severity
    severity_counts = {}
    for alert in alerts:
        severity = alert.get('severity', 'UNKNOWN')
        severity_counts[severity] = severity_counts.get(severity, 0) + 1
    
    for severity, count in sorted(severity_counts.items()):
        print(f"   {severity}: {count}")

except Exception as e:
    print(f"❌ Error: {e}")
    print("\nTroubleshooting:")
    print("1. Verify GOOGLE_APPLICATION_CREDENTIALS is set")
    print("2. Check Firestore is enabled in GCP Console")
    print("3. Verify service account has Firestore permissions")
    sys.exit(1)
