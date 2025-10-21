"""
Pipeline Orchestrator (Agent 3)

Coordinates Schema Guardian and Anomaly Detective to make autonomous decisions
and execute actions. This is the "brain" that brings multi-agent coordination to life.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.schema_guardian import SchemaGuardian
from agents.anomaly_detective import AnomalyDetective
from agents.decision_engine import DecisionEngine
from agents.action_executor import ActionExecutor
from agents.fivetran_client import FivetranClient

load_dotenv()


class PipelineOrchestrator:
    """
    Agent 3: Multi-Agent Coordinator
    
    Gathers intelligence from Agent 1 (Schema Guardian) and Agent 2 (Anomaly Detective),
    makes autonomous decisions using DecisionEngine, and executes actions via ActionExecutor.
    """
    
    def __init__(
        self,
        project_id: Optional[str] = None,
        dataset_id: Optional[str] = None,
        table_id: Optional[str] = None,
        connector_id: Optional[str] = None
    ):
        """
        Initialize Pipeline Orchestrator
        
        Args:
            project_id: GCP project ID (or from env)
            dataset_id: BigQuery dataset (or from env)
            table_id: BigQuery table (or from env)
            connector_id: Fivetran connector ID (or from env)
        """
        self.project_id = project_id or os.getenv("PROJECT_ID")
        self.dataset_id = dataset_id or os.getenv("DATASET_ID")
        self.table_id = table_id or os.getenv("TABLE_ID")
        self.connector_id = connector_id or os.getenv("FIVETRAN_CONNECTOR_ID")
        
        print("🦅 Initializing Pipeline Orchestrator...")
        
        # Initialize agents
        print("   Loading Agent 1 (Schema Guardian)...")
        self.schema_guardian = SchemaGuardian(
            self.project_id,
            self.dataset_id,
            self.table_id
        )
        
        print("   Loading Agent 2 (Anomaly Detective)...")
        self.anomaly_detective = AnomalyDetective(
            self.project_id,
            self.dataset_id,
            self.table_id
        )
        
        # Initialize decision and action systems
        print("   Loading Decision Engine...")
        self.decision_engine = DecisionEngine()
        
        print("   Loading Action Executor...")
        self.action_executor = ActionExecutor(
            self.project_id,
            self.dataset_id,
            self.table_id,
            self.connector_id
        )
        
        # Initialize Fivetran client
        self.fivetran_client = FivetranClient()
        
        # State tracking
        self.state = "IDLE"  # IDLE, EVALUATING, ACTING
        self.orchestration_history = []
        
        print("✅ Orchestrator initialized!\n")
    
    def orchestrate(self) -> Dict:
        """
        Main orchestration loop
        
        Coordinates agents, makes decisions, executes actions.
        
        Returns:
            Orchestration result dict with:
                - orchestration_id: Unique ID
                - timestamp: When run
                - schema_alert: Alert from Agent 1 (or None)
                - anomaly_alert: Alert from Agent 2 (or None)
                - decision: Decision made
                - action_result: Action execution result (or None)
                - state: Final state
        """
        orchestration_id = f"orch_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        print("=" * 60)
        print(f"🦅 ORCHESTRATION RUN: {orchestration_id}")
        print("=" * 60)
        
        result = {
            "orchestration_id": orchestration_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "schema_alert": None,
            "anomaly_alert": None,
            "decision": None,
            "action_result": None,
            "state": "IDLE",
            "success": True
        }
        
        try:
            # PHASE 1: Gather intelligence from agents
            self.state = "EVALUATING"
            print("\n📊 PHASE 1: Gathering intelligence from agents...\n")
            
            # Agent 1: Check schema
            print("1️⃣ Agent 1 (Schema Guardian): Checking schema drift...")
            try:
                schema_changes = self.schema_guardian.detect_schema_drift()
                
                if schema_changes and any(schema_changes.values()):
                    result["schema_alert"] = self.schema_guardian.generate_alert(schema_changes)
                    print(f"   🚨 Schema drift detected! Severity: {result['schema_alert']['severity']}")
                else:
                    print("   ✅ Schema stable")
            except Exception as e:
                print(f"   ⚠️  Schema check error: {e}")
            
            # Agent 2: Check anomalies
            print("\n2️⃣ Agent 2 (Anomaly Detective): Analyzing data quality...")
            try:
                anomaly_result = self.anomaly_detective.run_check()
                
                if anomaly_result and anomaly_result.get("has_anomalies"):
                    result["anomaly_alert"] = anomaly_result
                    print(f"   🚨 Anomalies detected! Confidence: {anomaly_result['confidence']:.0%}")
                else:
                    print("   ✅ Data quality clean")
            except Exception as e:
                print(f"   ⚠️  Anomaly check error: {e}")
            
            # PHASE 2: Make decision
            print("\n🧠 PHASE 2: Making autonomous decision...\n")
            
            decision = self.decision_engine.evaluate(
                schema_alert=result["schema_alert"],
                anomaly_alert=result["anomaly_alert"]
            )
            result["decision"] = decision
            
            print(f"Decision: {decision['action']}")
            print(f"Priority: {decision['priority']}")
            print(f"Confidence: {decision['confidence']:.0%}")
            print(f"Reasoning:")
            for reason in decision["reasoning"]:
                print(f"   • {reason}")
            
            # Get action requirements
            requirements = self.decision_engine.get_action_requirements(decision["action"])
            decision["requirements"] = requirements
            
            # PHASE 3: Execute action (if needed)
            if decision["action"] != DecisionEngine.ACTION_CONTINUE:
                self.state = "ACTING"
                print("\n⚡ PHASE 3: Executing autonomous actions...\n")
                
                action_result = self.action_executor.execute_action(decision)
                result["action_result"] = action_result
                
                if action_result["success"]:
                    print(f"\n✅ All actions completed successfully")
                else:
                    print(f"\n⚠️  Some actions failed: {action_result.get('errors')}")
            else:
                print("\n✅ PHASE 3: No action required - system healthy")
            
            # Return to IDLE
            self.state = "IDLE"
            result["state"] = self.state
            
            print("\n" + "=" * 60)
            print(f"🎯 ORCHESTRATION COMPLETE")
            print("=" * 60)
            
            # Store result
            self.orchestration_history.append(result)
            
            return result
        
        except Exception as e:
            print(f"\n❌ Orchestration failed: {e}")
            result["success"] = False
            result["error"] = str(e)
            result["state"] = "ERROR"
            self.state = "IDLE"
            
            self.orchestration_history.append(result)
            return result
    
    def get_status(self) -> Dict:
        """
        Get orchestrator status
        
        Returns:
            Status dict with agent states, last orchestration, etc.
        """
        last_orchestration = self.orchestration_history[-1] if self.orchestration_history else None
        
        # Get connector status
        try:
            connector_status = self.fivetran_client.get_connector_status(self.connector_id)
        except Exception:
            connector_status = {"status": "unknown", "error": "Failed to fetch"}
        
        return {
            "orchestrator_state": self.state,
            "agents": {
                "schema_guardian": {
                    "name": "Schema Guardian",
                    "status": "operational",
                    "last_check": last_orchestration.get("timestamp") if last_orchestration else None
                },
                "anomaly_detective": {
                    "name": "Anomaly Detective",
                    "status": "operational",
                    "model": "gemini-2.0-flash-exp",
                    "last_check": last_orchestration.get("timestamp") if last_orchestration else None
                }
            },
            "connector": {
                "connector_id": self.connector_id,
                "status": connector_status.get("status"),
                "paused": connector_status.get("paused", False)
            },
            "last_orchestration": {
                "id": last_orchestration.get("orchestration_id") if last_orchestration else None,
                "timestamp": last_orchestration.get("timestamp") if last_orchestration else None,
                "action_taken": last_orchestration.get("decision", {}).get("action") if last_orchestration else None
            },
            "metrics": {
                "total_orchestrations": len(self.orchestration_history),
                "decisions_made": len(self.decision_engine.decision_history),
                "actions_executed": len(self.action_executor.action_history)
            }
        }
    
    def get_orchestration_history(self, limit: int = 10) -> list:
        """Get recent orchestration history"""
        return sorted(
            self.orchestration_history,
            key=lambda o: o["timestamp"],
            reverse=True
        )[:limit]
    
    def get_decision_history(self, limit: int = 10) -> list:
        """Get recent decision history from engine"""
        return self.decision_engine.get_recent_decisions(limit)
    
    def get_action_history(self, limit: int = 10) -> list:
        """Get recent action history from executor"""
        return self.action_executor.get_action_history(limit)
    
    def generate_summary(self) -> str:
        """
        Generate executive summary of recent activity
        
        Returns:
            Formatted summary string
        """
        metrics = self.get_status()["metrics"]
        recent_orchestrations = self.get_orchestration_history(limit=5)
        
        summary = f"""
PIPELINE ORCHESTRATOR SUMMARY
{'=' * 60}

System Status: {self.state}
Connector: {'PAUSED' if self.get_status()['connector']['paused'] else 'RUNNING'}

Activity Metrics:
  • Total Orchestrations: {metrics['total_orchestrations']}
  • Decisions Made: {metrics['decisions_made']}
  • Actions Executed: {metrics['actions_executed']}

Recent Activity (last 5 runs):
"""
        
        for orch in recent_orchestrations:
            decision = orch.get("decision", {})
            timestamp = orch.get("timestamp", "")
            action = decision.get("action", "NONE")
            priority = decision.get("priority", "N/A")
            
            summary += f"\n  [{timestamp[:19]}] {action} (Priority: {priority})"
        
        summary += f"\n\n{'=' * 60}"
        
        return summary


# Testing
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("PIPELINE ORCHESTRATOR TEST")
    print("=" * 60 + "\n")
    
    try:
        # Initialize orchestrator
        orchestrator = PipelineOrchestrator()
        
        # Run one orchestration cycle
        print("\n🧪 Running test orchestration...\n")
        result = orchestrator.orchestrate()
        
        # Show status
        print("\n📊 Orchestrator Status:")
        status = orchestrator.get_status()
        print(f"   State: {status['orchestrator_state']}")
        print(f"   Connector: {status['connector']['status']}")
        print(f"   Orchestrations: {status['metrics']['total_orchestrations']}")
        print(f"   Decisions: {status['metrics']['decisions_made']}")
        print(f"   Actions: {status['metrics']['actions_executed']}")
        
        # Show summary
        print("\n📋 Executive Summary:")
        print(orchestrator.generate_summary())
        
        print("\n✅ Orchestrator test completed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
