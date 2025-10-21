"""
Decision Engine

Evaluates alerts from Schema Guardian and Anomaly Detective to make
autonomous decisions about pipeline actions.

Decision Matrix:
- CRITICAL schema + any anomaly → PAUSE_AND_ALERT
- Any schema + CRITICAL test data → QUARANTINE_AND_PAUSE  
- High confidence anomaly → QUARANTINE_AND_FLAG
- Medium confidence → FLAG_FOR_REVIEW
- Low severity → LOG_AND_CONTINUE
"""

from typing import Dict, Optional, List
from datetime import datetime
import uuid


class DecisionEngine:
    """Makes autonomous decisions based on multi-agent alerts"""
    
    # Decision action types
    ACTION_PAUSE_AND_ALERT = "PAUSE_AND_ALERT"
    ACTION_QUARANTINE_AND_PAUSE = "QUARANTINE_AND_PAUSE"
    ACTION_QUARANTINE_AND_FLAG = "QUARANTINE_AND_FLAG"
    ACTION_FLAG_FOR_REVIEW = "FLAG_FOR_REVIEW"
    ACTION_LOG_AND_CONTINUE = "LOG_AND_CONTINUE"
    ACTION_CONTINUE = "CONTINUE"
    ACTION_EMERGENCY_PAUSE = "EMERGENCY_PAUSE"
    
    # Priority levels
    PRIORITY_CRITICAL = "CRITICAL"
    PRIORITY_HIGH = "HIGH"
    PRIORITY_MEDIUM = "MEDIUM"
    PRIORITY_LOW = "LOW"
    
    def __init__(self):
        """Initialize decision engine"""
        self.decision_history = []
    
    def evaluate(
        self, 
        schema_alert: Optional[Dict] = None,
        anomaly_alert: Optional[Dict] = None
    ) -> Dict:
        """
        Evaluate alerts and make decision
        
        Args:
            schema_alert: Alert from Schema Guardian (can be None)
            anomaly_alert: Alert from Anomaly Detective (can be None)
        
        Returns:
            Decision dict with keys:
                - decision_id: Unique identifier
                - timestamp: ISO timestamp
                - action: Action to take
                - confidence: 0.0-1.0
                - reasoning: List of reasons
                - priority: CRITICAL/HIGH/MEDIUM/LOW
                - inputs: Original alerts
                - severity_score: Numeric score for sorting
        """
        decision = {
            "decision_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "action": self.ACTION_CONTINUE,
            "confidence": 1.0,
            "reasoning": [],
            "priority": self.PRIORITY_LOW,
            "inputs": {
                "schema_alert": schema_alert,
                "anomaly_alert": anomaly_alert
            },
            "severity_score": 0
        }
        
        # Extract severities and confidences
        schema_severity = schema_alert.get("severity") if schema_alert else None
        anomaly_confidence = anomaly_alert.get("confidence", 0) if anomaly_alert else 0
        anomaly_types = []
        
        if anomaly_alert and anomaly_alert.get("has_anomalies"):
            anomaly_types = [a.get("type") for a in anomaly_alert.get("anomalies", [])]
        
        # Decision logic (order matters - most critical first)
        
        # RULE 1: Multiple simultaneous critical issues = EMERGENCY
        if (schema_severity == "CRITICAL" and anomaly_confidence > 0.7):
            decision["action"] = self.ACTION_EMERGENCY_PAUSE
            decision["priority"] = self.PRIORITY_CRITICAL
            decision["confidence"] = 0.95
            decision["severity_score"] = 100
            decision["reasoning"].append(
                "EMERGENCY: Critical schema change + data quality issues detected simultaneously"
            )
            decision["reasoning"].append(
                f"Schema severity: {schema_severity}, Anomaly confidence: {anomaly_confidence:.0%}"
            )
        
        # RULE 2: Test data in production = QUARANTINE + PAUSE
        elif "test_data" in anomaly_types and anomaly_confidence >= 0.85:
            decision["action"] = self.ACTION_QUARANTINE_AND_PAUSE
            decision["priority"] = self.PRIORITY_CRITICAL
            decision["confidence"] = anomaly_confidence
            decision["severity_score"] = 90
            decision["reasoning"].append(
                f"Test data detected in production with {anomaly_confidence:.0%} confidence"
            )
            decision["reasoning"].append(
                "Action: Quarantine contaminated data and pause sync to prevent further pollution"
            )
        
        # RULE 3: Critical schema changes = PAUSE
        elif schema_severity == "CRITICAL":
            decision["action"] = self.ACTION_PAUSE_AND_ALERT
            decision["priority"] = self.PRIORITY_CRITICAL
            decision["confidence"] = 0.9
            decision["severity_score"] = 85
            decision["reasoning"].append(
                "Critical schema change detected - high risk of downstream breakage"
            )
            
            if schema_alert:
                changes = schema_alert.get("changes", {})
                if changes.get("type_changes"):
                    decision["reasoning"].append(
                        f"Column type changes: {len(changes['type_changes'])} detected"
                    )
                if changes.get("removed_columns"):
                    decision["reasoning"].append(
                        f"Removed columns: {len(changes['removed_columns'])} detected"
                    )
        
        # RULE 4: High removed columns + High anomaly = PAUSE
        elif (schema_severity == "HIGH" and 
              schema_alert and 
              len(schema_alert.get("changes", {}).get("removed_columns", [])) > 0 and
              anomaly_confidence > 0.8):
            decision["action"] = self.ACTION_PAUSE_AND_ALERT
            decision["priority"] = self.PRIORITY_HIGH
            decision["confidence"] = 0.85
            decision["severity_score"] = 80
            decision["reasoning"].append(
                "Data loss (removed columns) combined with quality issues"
            )
            decision["reasoning"].append(
                "Pausing to prevent cascading failures"
            )
        
        # RULE 5: High confidence anomalies = QUARANTINE
        elif anomaly_confidence > 0.80:
            decision["action"] = self.ACTION_QUARANTINE_AND_FLAG
            decision["priority"] = self.PRIORITY_HIGH
            decision["confidence"] = anomaly_confidence
            decision["severity_score"] = 70
            decision["reasoning"].append(
                f"High-confidence data anomalies detected ({anomaly_confidence:.0%})"
            )
            decision["reasoning"].append(
                "Action: Quarantine suspicious data for investigation"
            )
            
            # List anomaly types
            if anomaly_types:
                decision["reasoning"].append(
                    f"Anomaly types: {', '.join(set(anomaly_types))}"
                )
        
        # RULE 6: Medium confidence anomalies = FLAG
        elif anomaly_confidence > 0.70:
            decision["action"] = self.ACTION_FLAG_FOR_REVIEW
            decision["priority"] = self.PRIORITY_MEDIUM
            decision["confidence"] = anomaly_confidence
            decision["severity_score"] = 50
            decision["reasoning"].append(
                f"Moderate-confidence anomalies detected ({anomaly_confidence:.0%})"
            )
            decision["reasoning"].append(
                "Action: Flag for human review, continue monitoring"
            )
        
        # RULE 7: Schema changes (non-critical) = FLAG
        elif schema_severity in ["HIGH", "MEDIUM"]:
            decision["action"] = self.ACTION_FLAG_FOR_REVIEW
            decision["priority"] = self.PRIORITY_MEDIUM if schema_severity == "HIGH" else self.PRIORITY_LOW
            decision["confidence"] = 0.8
            decision["severity_score"] = 40 if schema_severity == "HIGH" else 30
            decision["reasoning"].append(
                f"{schema_severity} schema changes detected"
            )
            decision["reasoning"].append(
                "Action: Monitor and flag for review"
            )
        
        # RULE 8: Low confidence anomalies = LOG
        elif anomaly_confidence > 0.5:
            decision["action"] = self.ACTION_LOG_AND_CONTINUE
            decision["priority"] = self.PRIORITY_LOW
            decision["confidence"] = anomaly_confidence
            decision["severity_score"] = 20
            decision["reasoning"].append(
                f"Low-confidence anomalies ({anomaly_confidence:.0%}) - monitoring only"
            )
        
        # RULE 9: Everything clean = CONTINUE
        else:
            decision["action"] = self.ACTION_CONTINUE
            decision["priority"] = self.PRIORITY_LOW
            decision["confidence"] = 1.0
            decision["severity_score"] = 0
            decision["reasoning"].append(
                "All systems operational - no issues detected"
            )
        
        # Store decision
        self.decision_history.append(decision)
        
        return decision
    
    def get_action_requirements(self, action: str) -> Dict:
        """
        Get requirements for executing a specific action
        
        Args:
            action: Action type (e.g., PAUSE_AND_ALERT)
        
        Returns:
            Dict with keys:
                - pause_connector: bool
                - quarantine_data: bool
                - send_alert: bool
                - generate_rollback: bool
                - human_review: bool
        """
        requirements = {
            self.ACTION_EMERGENCY_PAUSE: {
                "pause_connector": True,
                "quarantine_data": False,
                "send_alert": True,
                "generate_rollback": False,
                "human_review": True,
                "urgent": True
            },
            self.ACTION_PAUSE_AND_ALERT: {
                "pause_connector": True,
                "quarantine_data": False,
                "send_alert": True,
                "generate_rollback": False,
                "human_review": True,
                "urgent": False
            },
            self.ACTION_QUARANTINE_AND_PAUSE: {
                "pause_connector": True,
                "quarantine_data": True,
                "send_alert": True,
                "generate_rollback": True,
                "human_review": True,
                "urgent": False
            },
            self.ACTION_QUARANTINE_AND_FLAG: {
                "pause_connector": False,
                "quarantine_data": True,
                "send_alert": True,
                "generate_rollback": True,
                "human_review": True,
                "urgent": False
            },
            self.ACTION_FLAG_FOR_REVIEW: {
                "pause_connector": False,
                "quarantine_data": False,
                "send_alert": True,
                "generate_rollback": False,
                "human_review": True,
                "urgent": False
            },
            self.ACTION_LOG_AND_CONTINUE: {
                "pause_connector": False,
                "quarantine_data": False,
                "send_alert": False,
                "generate_rollback": False,
                "human_review": False,
                "urgent": False
            },
            self.ACTION_CONTINUE: {
                "pause_connector": False,
                "quarantine_data": False,
                "send_alert": False,
                "generate_rollback": False,
                "human_review": False,
                "urgent": False
            }
        }
        
        return requirements.get(action, {})
    
    def get_recent_decisions(self, limit: int = 10) -> List[Dict]:
        """
        Get recent decision history
        
        Args:
            limit: Number of decisions to return
        
        Returns:
            List of recent decisions
        """
        return sorted(
            self.decision_history,
            key=lambda d: d["timestamp"],
            reverse=True
        )[:limit]
    
    def calculate_metrics(self) -> Dict:
        """
        Calculate decision metrics
        
        Returns:
            Metrics dict with counts by action and priority
        """
        if not self.decision_history:
            return {
                "total_decisions": 0,
                "by_action": {},
                "by_priority": {},
                "avg_confidence": 0.0
            }
        
        by_action = {}
        by_priority = {}
        total_confidence = 0.0
        
        for decision in self.decision_history:
            action = decision["action"]
            priority = decision["priority"]
            
            by_action[action] = by_action.get(action, 0) + 1
            by_priority[priority] = by_priority.get(priority, 0) + 1
            total_confidence += decision["confidence"]
        
        return {
            "total_decisions": len(self.decision_history),
            "by_action": by_action,
            "by_priority": by_priority,
            "avg_confidence": total_confidence / len(self.decision_history)
        }


# Testing
if __name__ == "__main__":
    engine = DecisionEngine()
    
    print("=" * 60)
    print("DECISION ENGINE TEST")
    print("=" * 60)
    
    # Test 1: Clean state
    print("\n1️⃣ Test: Clean state (no alerts)")
    decision = engine.evaluate()
    print(f"   Action: {decision['action']}")
    print(f"   Priority: {decision['priority']}")
    print(f"   Reasoning: {decision['reasoning'][0]}")
    
    # Test 2: Critical schema change
    print("\n2️⃣ Test: Critical schema change")
    schema_alert = {
        "severity": "CRITICAL",
        "changes": {"type_changes": [{"column": "price", "from": "STRING", "to": "FLOAT"}]}
    }
    decision = engine.evaluate(schema_alert=schema_alert)
    print(f"   Action: {decision['action']}")
    print(f"   Priority: {decision['priority']}")
    print(f"   Reasoning: {decision['reasoning'][0]}")
    
    # Test 3: Test data detected
    print("\n3️⃣ Test: Test data detected (90% confidence)")
    anomaly_alert = {
        "has_anomalies": True,
        "confidence": 0.92,
        "anomalies": [{"type": "test_data", "severity": "CRITICAL"}]
    }
    decision = engine.evaluate(anomaly_alert=anomaly_alert)
    print(f"   Action: {decision['action']}")
    print(f"   Priority: {decision['priority']}")
    print(f"   Confidence: {decision['confidence']:.0%}")
    
    # Test 4: Multiple issues (emergency)
    print("\n4️⃣ Test: Schema + Anomaly (emergency)")
    decision = engine.evaluate(schema_alert=schema_alert, anomaly_alert=anomaly_alert)
    print(f"   Action: {decision['action']}")
    print(f"   Priority: {decision['priority']}")
    print(f"   Reasoning: {decision['reasoning'][0]}")
    
    # Show metrics
    print("\n5️⃣ Decision metrics:")
    metrics = engine.calculate_metrics()
    print(f"   Total decisions: {metrics['total_decisions']}")
    print(f"   By action: {metrics['by_action']}")
    print(f"   By priority: {metrics['by_priority']}")
    print(f"   Avg confidence: {metrics['avg_confidence']:.0%}")
    
    print("\n✅ Decision Engine tests passed!")
    print("=" * 60)
