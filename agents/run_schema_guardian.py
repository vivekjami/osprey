import time
import argparse
import logging
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from agents.schema_guardian import SchemaGuardian
from agents.agent_memory import AgentMemory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/schema_guardian.log')
    ]
)
logger = logging.getLogger(__name__)


def monitor_loop(project_id: str, dataset_id: str, table_id: str, interval_seconds: int = 300, max_checks: int = None):
    """Run schema monitoring loop"""
    guardian = SchemaGuardian(project_id, dataset_id, table_id)
    memory = AgentMemory(project_id)
    
    logger.info(f"🛡️ Schema Guardian starting for {table_id}")
    logger.info(f"📊 Check interval: {interval_seconds} seconds")
    
    # Initial baseline capture
    try:
        baseline = memory.get_schema_baseline(table_id)
        if baseline is None:
            logger.info("No baseline found. Capturing initial baseline...")
            baseline = guardian.capture_baseline_schema()
            memory.store_schema_baseline(table_id, baseline)
        else:
            logger.info(f"✅ Loaded baseline with {len(baseline)} columns")
        
        guardian.baseline_schema = baseline
    except Exception as e:
        logger.error(f"Failed to initialize baseline: {e}")
        return
    
    # Update agent status
    memory.update_agent_status('Schema Guardian', {
        'status': 'running',
        'table': f"{project_id}.{dataset_id}.{table_id}",
        'interval_seconds': interval_seconds
    })
    
    # Monitoring loop
    check_count = 0
    start_time = time.time()
    
    while True:
        try:
            check_count += 1
            logger.info(f"🔍 Running check #{check_count}...")
            
            # Check if we've reached max checks
            if max_checks and check_count > max_checks:
                logger.info(f"✅ Completed {max_checks} checks. Stopping monitoring.")
                break
            
            changes = guardian.detect_schema_drift()
            
            # Check if any changes detected
            has_changes = any(
                len(v) > 0 if isinstance(v, list) else False 
                for v in changes.values() if not v == "error"
            )
            
            if has_changes:
                alert = guardian.generate_alert(changes)
                logger.warning(f"🚨 Schema drift detected! Severity: {alert['severity']}")
                logger.warning(f"Changes: {alert['change_count']}")
                
                # Store alert
                memory.store_alert(alert)
                
                # Log details
                for change_type, change_list in changes.items():
                    if change_list and isinstance(change_list, list):
                        logger.warning(f"  {change_type}: {change_list}")
                
                # Update agent status with alert
                memory.update_agent_status('Schema Guardian', {
                    'status': 'alert',
                    'last_alert': alert,
                    'checks_performed': check_count
                })
            else:
                logger.info("✅ Schema stable - no changes detected")
                
                # Update agent status
                memory.update_agent_status('Schema Guardian', {
                    'status': 'running',
                    'checks_performed': check_count,
                    'uptime_seconds': int(time.time() - start_time)
                })
            
            guardian._uptime = int(time.time() - start_time)
            
            time.sleep(interval_seconds)
            
        except KeyboardInterrupt:
            logger.info("🛑 Monitoring stopped by user")
            memory.update_agent_status('Schema Guardian', {'status': 'stopped'})
            break
        except Exception as e:
            logger.error(f"Error in monitoring loop: {e}", exc_info=True)
            memory.update_agent_status('Schema Guardian', {
                'status': 'error',
                'last_error': str(e)
            })
            time.sleep(60)  # Wait 1 min before retry


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Schema Guardian - Monitor BigQuery schema changes')
    parser.add_argument('--project', required=True, help='GCP Project ID')
    parser.add_argument('--dataset', required=True, help='BigQuery dataset')
    parser.add_argument('--table', required=True, help='Table to monitor')
    parser.add_argument('--interval', type=int, default=300, help='Check interval in seconds (default: 300)')
    parser.add_argument('--max-checks', type=int, default=None, help='Maximum number of checks before stopping (default: infinite)')
    
    args = parser.parse_args()
    
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    monitor_loop(args.project, args.dataset, args.table, args.interval, args.max_checks)
