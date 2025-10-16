from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from agents.agent_memory import AgentMemory

app = FastAPI(
    title="Osprey Agent API",
    description="Multi-Agent Data Quality Guardian API",
    version="1.0.0"
)

# Enable CORS for React dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize memory (will return None if Firestore not set up)
try:
    memory = AgentMemory(project_id=os.getenv("PROJECT_ID"))
except Exception as e:
    print(f"Warning: Could not initialize Firestore: {e}")
    print("API will run with limited functionality until Firestore is set up")
    memory = None


@app.get("/")
def root():
    return {
        "name": "Osprey Agent API",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": ["/api/status", "/api/alerts", "/api/health", "/api/agent/{agent_name}"]
    }


@app.get("/api/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Osprey Multi-Agent System"
    }


@app.get("/api/status")
def get_agent_status():
    """Get status of all agents"""
    if not memory:
        return {
            "agents": [{
                "name": "Schema Guardian",
                "status": "firestore_not_configured",
                "message": "Firestore is not set up. Visit https://console.cloud.google.com/datastore/setup"
            }],
            "warning": "Firestore not configured - limited functionality",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    try:
        # Get Schema Guardian status
        sg_status = memory.get_agent_status('Schema Guardian')
        
        # Get recent alert count
        alerts = memory.get_alert_history(limit=100)
        alerts_today = len([a for a in alerts if a.get('agent') == 'Schema Guardian'])
        
        agents = []
        
        if sg_status:
            agents.append({
                "name": "Schema Guardian",
                "status": sg_status.get('status', 'unknown'),
                "last_check": sg_status.get('last_updated'),
                "checks_performed": sg_status.get('checks_performed', 0),
                "alerts_today": alerts_today,
                "table": sg_status.get('table', 'N/A'),
                "uptime_seconds": sg_status.get('uptime_seconds', 0)
            })
        else:
            agents.append({
                "name": "Schema Guardian",
                "status": "not_running",
                "message": "No status data found. Agent may not have started yet."
            })
        
        return {
            "agents": agents,
            "total_agents": len(agents),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        # Return graceful response even if Firestore fails
        return {
            "agents": [{
                "name": "Schema Guardian",
                "status": "error",
                "message": f"Error accessing status: {str(e)}"
            }],
            "error": "Could not retrieve full status",
            "timestamp": datetime.utcnow().isoformat()
        }


@app.get("/api/alerts")
def get_recent_alerts(
    limit: int = Query(default=10, ge=1, le=100),
    agent: str = Query(default=None)
):
    """Get recent alerts, optionally filtered by agent"""
    if not memory:
        return {
            "alerts": [],
            "count": 0,
            "warning": "Firestore not configured - no alerts available",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    try:
        alerts = memory.get_alert_history(limit=limit, agent=agent)
        
        return {
            "alerts": alerts,
            "count": len(alerts),
            "limit": limit,
            "filtered_by_agent": agent,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        # Return graceful response even if Firestore fails
        return {
            "alerts": [],
            "count": 0,
            "error": f"Could not retrieve alerts: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        }


@app.get("/api/agent/{agent_name}")
def get_agent_details(agent_name: str):
    """Get detailed information about a specific agent"""
    try:
        if not memory:
            raise HTTPException(status_code=503, detail="Firestore not configured")
        
        status = memory.get_agent_status(agent_name)
        
        if not status:
            raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")
        
        # Get agent-specific alerts
        alerts = memory.get_alert_history(limit=10, agent=agent_name)
        
        return {
            "agent": agent_name,
            "status": status,
            "recent_alerts": alerts,
            "alert_count": len(alerts),
            "timestamp": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving agent details: {str(e)}")


@app.get("/api/agent/{agent_name}/logs")
def get_agent_logs(agent_name: str, limit: int = Query(default=20, ge=1, le=100)):
    """Get recent activity logs for specific agent"""
    try:
        alerts = memory.get_alert_history(limit=limit, agent=agent_name)
        
        logs = []
        for alert in alerts:
            logs.append({
                "timestamp": alert.get('timestamp'),
                "severity": alert.get('severity'),
                "message": f"{alert.get('change_count', 0)} changes detected",
                "details": alert.get('changes', {})
            })
        
        return {
            "agent": agent_name,
            "logs": logs,
            "count": len(logs),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving logs: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
