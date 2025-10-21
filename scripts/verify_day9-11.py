"""
Day 9-11 Verification Script

Comprehensive 10-check verification that Pipeline Orchestrator is complete and working.
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()


def print_check(number, name, status, message=""):
    symbol = "✅" if status else "❌"
    print(f"{symbol} Check {number}: {name}")
    if message:
        print(f"   {message}")


def main():
    print("=" * 60)
    print("DAY 9-11 VERIFICATION")
    print("=" * 60)
    
    checks_passed = 0
    total_checks = 10
    
    # Check 1: Fivetran client
    print("\n1️⃣ Fivetran Client...")
    try:
        from agents.fivetran_client import FivetranClient
        client = FivetranClient()
        connector_id = os.getenv("FIVETRAN_CONNECTOR_ID")
        status = client.get_connector_status(connector_id)
        print_check(1, "Fivetran client operational", True, f"Connector: {status['status']}")
        checks_passed += 1
    except Exception as e:
        print_check(1, "Fivetran client", False, str(e))
    
    # Check 2: Decision Engine
    print("\n2️⃣ Decision Engine...")
    try:
        from agents.decision_engine import DecisionEngine
        engine = DecisionEngine()
        
        # Test decision
        anomaly_alert = {
            "has_anomalies": True,
            "confidence": 0.9,
            "anomalies": [{"type": "test_data"}]
        }
        decision = engine.evaluate(anomaly_alert=anomaly_alert)
        
        assert decision["action"] == "QUARANTINE_AND_PAUSE"
        print_check(2, "Decision engine makes correct decisions", True, f"Action: {decision['action']}")
        checks_passed += 1
    except Exception as e:
        print_check(2, "Decision engine", False, str(e))
    
    # Check 3: Action Executor
    print("\n3️⃣ Action Executor...")
    try:
        from agents.action_executor import ActionExecutor
        executor = ActionExecutor()
        
        # Test rollback SQL generation
        sql = executor.generate_rollback_sql(["TEST_001"])
        assert "ROLLBACK SQL" in sql
        assert "TEST_001" in sql
        
        print_check(3, "Action executor functional", True, "SQL generation works")
        checks_passed += 1
    except Exception as e:
        print_check(3, "Action executor", False, str(e))
    
    # Check 4: Pipeline Orchestrator
    print("\n4️⃣ Pipeline Orchestrator...")
    try:
        from agents.pipeline_orchestrator import PipelineOrchestrator
        orchestrator = PipelineOrchestrator()
        
        assert orchestrator.state == "IDLE"
        print_check(4, "Orchestrator initialized", True, f"State: {orchestrator.state}")
        checks_passed += 1
    except Exception as e:
        print_check(4, "Pipeline orchestrator", False, str(e))
    
    # Check 5: Orchestration run
    print("\n5️⃣ Orchestration Run...")
    try:
        from agents.pipeline_orchestrator import PipelineOrchestrator
        orchestrator = PipelineOrchestrator()
        
        result = orchestrator.orchestrate()
        
        assert result["success"]
        assert "decision" in result
        assert result["decision"]["action"] in ["CONTINUE", "QUARANTINE_AND_PAUSE", "PAUSE_AND_ALERT"]
        
        print_check(5, "Orchestration executes successfully", True, f"Action: {result['decision']['action']}")
        checks_passed += 1
    except Exception as e:
        print_check(5, "Orchestration run", False, str(e))
    
    # Check 6: API Endpoints
    print("\n6️⃣ API Endpoints...")
    try:
        import requests
        
        endpoints_to_test = [
            "/api/orchestrator/status",
            "/api/orchestrator/metrics",
            "/api/orchestrator/summary"
        ]
        
        all_ok = True
        for endpoint in endpoints_to_test:
            response = requests.get(f"http://localhost:8000{endpoint}")
            if response.status_code != 200:
                all_ok = False
                break
        
        if all_ok:
            print_check(6, "API endpoints operational", True, f"{len(endpoints_to_test)} endpoints working")
            checks_passed += 1
        else:
            print_check(6, "API endpoints", False, "Some endpoints failing")
    except Exception as e:
        print_check(6, "API endpoints", False, str(e))
    
    # Check 7: All 3 agents initialized
    print("\n7️⃣ All Agents...")
    try:
        from agents.schema_guardian import SchemaGuardian
        from agents.anomaly_detective import AnomalyDetective
        from agents.pipeline_orchestrator import PipelineOrchestrator
        
        sg = SchemaGuardian(os.getenv("PROJECT_ID"), os.getenv("DATASET_ID"), os.getenv("TABLE_ID"))
        ad = AnomalyDetective(os.getenv("PROJECT_ID"), os.getenv("DATASET_ID"), os.getenv("TABLE_ID"))
        po = PipelineOrchestrator()
        
        print_check(7, "All 3 agents initialized", True, "Schema Guardian + Anomaly Detective + Orchestrator")
        checks_passed += 1
    except Exception as e:
        print_check(7, "All agents", False, str(e))
    
    # Check 8: Decision history stored
    print("\n8️⃣ Decision History...")
    try:
        from agents.pipeline_orchestrator import PipelineOrchestrator
        orchestrator = PipelineOrchestrator()
        orchestrator.orchestrate()
        
        history = orchestrator.get_decision_history(limit=1)
        assert len(history) > 0
        
        print_check(8, "Decision history tracked", True, f"{len(history)} decisions stored")
        checks_passed += 1
    except Exception as e:
        print_check(8, "Decision history", False, str(e))
    
    # Check 9: Rollback SQL generation
    print("\n9️⃣ Rollback SQL...")
    try:
        from agents.action_executor import ActionExecutor
        executor = ActionExecutor()
        
        test_ids = ["TEST_001", "TEST_002", "TEST_003"]
        sql = executor.generate_rollback_sql(test_ids)
        
        assert "INSERT INTO" in sql
        assert "DELETE FROM" in sql
        assert all(id in sql for id in test_ids)
        
        print_check(9, "Rollback SQL correctly generated", True, f"{len(test_ids)} IDs handled")
        checks_passed += 1
    except Exception as e:
        print_check(9, "Rollback SQL", False, str(e))
    
    # Check 10: End-to-end test
    print("\n🔟 End-to-End Test...")
    try:
        from agents.pipeline_orchestrator import PipelineOrchestrator
        orchestrator = PipelineOrchestrator()
        
        # Run orchestration
        result = orchestrator.orchestrate()
        
        # Verify complete workflow
        assert result["success"]
        assert result["decision"] is not None
        assert result["state"] == "IDLE"
        
        # Verify status
        status = orchestrator.get_status()
        assert status["orchestrator_state"] == "IDLE"
        assert "agents" in status
        assert "metrics" in status
        
        print_check(10, "End-to-end workflow complete", True, "All components working together")
        checks_passed += 1
    except Exception as e:
        print_check(10, "End-to-end test", False, str(e))
    
    # Summary
    print("\n" + "=" * 60)
    print(f"VERIFICATION COMPLETE: {checks_passed}/{total_checks} checks passed")
    print("=" * 60)
    
    if checks_passed == total_checks:
        print("\n🎉 DAY 9-11 COMPLETE! Pipeline Orchestrator is fully operational!")
        print("\n✨ You now have:")
        print("   • 3 autonomous agents")
        print("   • Multi-agent coordination")
        print("   • Autonomous decision-making")
        print("   • Real action execution")
        print("   • 12 API endpoints")
        print("\n🏆 THIS IS 1ST PLACE MATERIAL!")
    elif checks_passed >= 8:
        print("\n✅ Most checks passed! Minor issues to fix.")
    else:
        print("\n⚠️  Several checks failed. Review errors above.")
    
    print("=" * 60)
    
    return checks_passed == total_checks


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
