import os
import time
from dotenv import load_dotenv
from anomaly_detective import AnomalyDetective
from agent_memory import AgentMemory

load_dotenv()

def monitor_loop(interval_seconds: int = 300):
    """Run anomaly checks every 5 minutes"""
    
    detective = AnomalyDetective(
        project_id=os.getenv("PROJECT_ID"),
        dataset_id=os.getenv("DATASET_ID"),
        table_id=os.getenv("TABLE_ID")
    )
    
    try:
        memory = AgentMemory()
    except Exception as e:
        print(f"Warning: Could not initialize Firestore: {e}")
        print("Running with local storage only")
        memory = None
    
    check_count = 0
    
    print(f"🔍 Anomaly Detective started (checking every {interval_seconds}s)")
    
    try:
        while True:
            check_count += 1
            print(f"\n[Check #{check_count}] {time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            result = detective.run_check()
            
            # Store if anomalies found
            if result.get("has_anomalies"):
                if memory:
                    memory.store_alert(result)
                    print(f"🚨 Alert stored: {result['confidence']:.0%} confidence")
                else:
                    print(f"🚨 Anomalies detected (not stored - Firestore unavailable)")
                    print(f"   Summary: {result.get('summary', 'N/A')}")
            
            time.sleep(interval_seconds)
            
    except KeyboardInterrupt:
        print(f"\n✅ Stopped after {check_count} checks")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--interval", type=int, default=300)
    args = parser.parse_args()
    
    monitor_loop(args.interval)
