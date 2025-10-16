import time
import argparse
import logging
import sys
import os
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from agents.schema_guardian import SchemaGuardian

# Configure logging with UTF-8 encoding
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger(__name__)

# Disable emoji in logs for Windows compatibility
class SimpleFormatter(logging.Formatter):
    def format(self, record):
        # Remove emojis from message
        record.msg = str(record.msg).encode('ascii', 'ignore').decode('ascii')
        return super().format(record)

for handler in logger.handlers:
    handler.setFormatter(SimpleFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))


def monitor_loop(project_id: str, dataset_id: str, table_id: str, interval_seconds: int = 300, max_checks: int = None):
    """Run schema monitoring loop with local JSON storage"""
    guardian = SchemaGuardian(project_id, dataset_id, table_id)
    
    # Use local storage instead of Firestore
    storage_dir = Path("storage")
    storage_dir.mkdir(exist_ok=True)
    baseline_file = storage_dir / f"baseline_{table_id}.json"
    alerts_file = storage_dir / "alerts.json"
    
    logger.info(f"Schema Guardian starting for {table_id}")
    logger.info(f"Check interval: {interval_seconds} seconds")
    
    # Initial baseline capture
    try:
        if baseline_file.exists():
            logger.info("Loading existing baseline...")
            with open(baseline_file, 'r') as f:
                baseline_data = json.load(f)
            import pandas as pd
            baseline = pd.DataFrame(baseline_data['columns'])
            logger.info(f"Loaded baseline with {len(baseline)} columns")
        else:
            logger.info("No baseline found. Capturing initial baseline...")
            baseline = guardian.capture_baseline_schema()
            
            # Save to local file
            with open(baseline_file, 'w') as f:
                json.dump({
                    'table': table_id,
                    'columns': baseline.to_dict('records'),
                    'captured_at': time.time()
                }, f, indent=2)
            logger.info(f"Saved baseline with {len(baseline)} columns")
        
        guardian.baseline_schema = baseline
    except Exception as e:
        logger.error(f"Failed to initialize baseline: {e}")
        return
    
    # Load existing alerts
    alerts = []
    if alerts_file.exists():
        with open(alerts_file, 'r') as f:
            alerts = json.load(f)
    
    # Monitoring loop
    check_count = 0
    start_time = time.time()
    
    while True:
        try:
            check_count += 1
            logger.info(f"Running check #{check_count}...")
            
            # Check if we've reached max checks
            if max_checks and check_count > max_checks:
                logger.info(f"Completed {max_checks} checks. Stopping monitoring.")
                break
            
            changes = guardian.detect_schema_drift()
            
            # Check if any changes detected
            has_changes = any(
                len(v) > 0 if isinstance(v, list) else False 
                for v in changes.values() if v != "error"
            )
            
            if has_changes:
                alert = guardian.generate_alert(changes)
                logger.warning(f"Schema drift detected! Severity: {alert['severity']}")
                logger.warning(f"Changes: {alert['change_count']}")
                
                # Store alert locally
                alerts.append(alert)
                with open(alerts_file, 'w') as f:
                    json.dump(alerts, f, indent=2)
                
                # Log details
                for change_type, change_list in changes.items():
                    if change_list and isinstance(change_list, list):
                        logger.warning(f"  {change_type}: {change_list}")
            else:
                logger.info(f"Schema stable - no changes detected (uptime: {int(time.time() - start_time)}s)")
            
            # Display metrics
            metrics = guardian.get_metrics()
            logger.info(f"Metrics: Checks={check_count}, Alerts={len(alerts)}")
            
            if check_count < (max_checks or float('inf')):
                logger.info(f"Next check in {interval_seconds} seconds...")
                time.sleep(interval_seconds)
            
        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")
            break
        except Exception as e:
            logger.error(f"Error in monitoring loop: {e}", exc_info=True)
            time.sleep(60)  # Wait 1 min before retry
    
    logger.info(f"=== MONITORING COMPLETE ===")
    logger.info(f"Total checks: {check_count}")
    logger.info(f"Total alerts: {len(alerts)}")
    logger.info(f"Uptime: {int(time.time() - start_time)} seconds")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Schema Guardian - Monitor BigQuery schema changes (Local Storage)')
    parser.add_argument('--project', required=True, help='GCP Project ID')
    parser.add_argument('--dataset', required=True, help='BigQuery dataset')
    parser.add_argument('--table', required=True, help='Table to monitor')
    parser.add_argument('--interval', type=int, default=300, help='Check interval in seconds (default: 300)')
    parser.add_argument('--max-checks', type=int, default=None, help='Maximum number of checks before stopping (default: infinite)')
    
    args = parser.parse_args()
    
    monitor_loop(args.project, args.dataset, args.table, args.interval, args.max_checks)
