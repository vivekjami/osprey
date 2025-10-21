"""
Fivetran API Client

Handles interactions with Fivetran REST API for connector control.
Supports pausing, resuming, and querying connector status.

API Docs: https://fivetran.com/docs/rest-api/connectors
Rate Limit: 120 requests/hour
"""

import os
import requests
import time
from typing import Dict, Optional
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


class FivetranClient:
    """Client for Fivetran REST API v1"""
    
    BASE_URL = "https://api.fivetran.com/v1"
    RATE_LIMIT_REQUESTS_PER_HOUR = 120
    
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        """
        Initialize Fivetran client
        
        Args:
            api_key: Fivetran API key (or from env FIVETRAN_API_KEY)
            api_secret: Fivetran API secret (or from env FIVETRAN_API_SECRET)
        """
        self.api_key = api_key or os.getenv("FIVETRAN_API_KEY")
        self.api_secret = api_secret or os.getenv("FIVETRAN_API_SECRET")
        
        if not self.api_key or not self.api_secret:
            raise ValueError(
                "Fivetran API credentials not found. "
                "Set FIVETRAN_API_KEY and FIVETRAN_API_SECRET in .env"
            )
        
        self.auth = (self.api_key, self.api_secret)
        self._request_count = 0
        self._request_window_start = time.time()
    
    def _check_rate_limit(self):
        """Simple rate limit check"""
        elapsed = time.time() - self._request_window_start
        
        # Reset counter every hour
        if elapsed > 3600:
            self._request_count = 0
            self._request_window_start = time.time()
        
        # Warn if approaching limit
        if self._request_count >= self.RATE_LIMIT_REQUESTS_PER_HOUR - 10:
            print(f"⚠️  Approaching Fivetran rate limit ({self._request_count}/120 requests)")
    
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict] = None
    ) -> Dict:
        """
        Make authenticated request to Fivetran API
        
        Args:
            method: HTTP method (GET, POST, PATCH, DELETE)
            endpoint: API endpoint (e.g., "/connectors/{id}")
            data: Request body data (for POST/PATCH)
        
        Returns:
            Response JSON data
        
        Raises:
            requests.exceptions.RequestException: On API errors
        """
        self._check_rate_limit()
        
        url = f"{self.BASE_URL}{endpoint}"
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        
        try:
            response = requests.request(
                method=method,
                url=url,
                auth=self.auth,
                headers=headers,
                json=data,
                timeout=30
            )
            
            self._request_count += 1
            
            # Handle errors
            if response.status_code >= 400:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get("message", response.text)
                raise requests.exceptions.RequestException(
                    f"Fivetran API error ({response.status_code}): {error_msg}"
                )
            
            return response.json()
        
        except requests.exceptions.Timeout:
            raise requests.exceptions.RequestException("Fivetran API timeout (30s)")
        
        except requests.exceptions.RequestException as e:
            # Re-raise with context
            raise requests.exceptions.RequestException(f"Fivetran API request failed: {e}")
    
    def get_connector_details(self, connector_id: str) -> Dict:
        """
        Get detailed information about a connector
        
        Args:
            connector_id: Fivetran connector ID
        
        Returns:
            Connector details dict with keys:
                - id: connector ID
                - service: connector type
                - schema: destination schema
                - paused: bool
                - sync_frequency: minutes
                - succeeded_at: last successful sync timestamp
                - failed_at: last failed sync timestamp
        """
        response = self._make_request("GET", f"/connectors/{connector_id}")
        return response.get("data", {})
    
    def get_connector_status(self, connector_id: str) -> Dict:
        """
        Get connector status (simplified view)
        
        Args:
            connector_id: Fivetran connector ID
        
        Returns:
            Status dict with keys:
                - connector_id: str
                - paused: bool
                - status: "running" | "paused" | "error"
                - last_sync: ISO timestamp
                - sync_frequency_minutes: int
        """
        details = self.get_connector_details(connector_id)
        
        # Determine status
        if details.get("paused"):
            status = "paused"
        elif details.get("failed_at"):
            # Check if failure is recent
            failed_at = datetime.fromisoformat(details["failed_at"].replace("Z", "+00:00"))
            succeeded_at = details.get("succeeded_at")
            if succeeded_at:
                succeeded_at = datetime.fromisoformat(succeeded_at.replace("Z", "+00:00"))
                status = "error" if failed_at > succeeded_at else "running"
            else:
                status = "error"
        else:
            status = "running"
        
        return {
            "connector_id": details.get("id"),
            "service": details.get("service"),
            "schema": details.get("schema"),
            "paused": details.get("paused", False),
            "status": status,
            "last_sync": details.get("succeeded_at") or details.get("failed_at"),
            "sync_frequency_minutes": details.get("sync_frequency", 0),
            "setup_state": details.get("status", {}).get("setup_state"),
        }
    
    def pause_connector(self, connector_id: str) -> Dict:
        """
        Pause a Fivetran connector
        
        Args:
            connector_id: Fivetran connector ID
        
        Returns:
            Updated connector details
        """
        print(f"⏸️  Pausing Fivetran connector: {connector_id}")
        
        response = self._make_request(
            "PATCH",
            f"/connectors/{connector_id}",
            data={"paused": True}
        )
        
        result = response.get("data", {})
        
        if result.get("paused"):
            print(f"✅ Connector paused successfully")
        else:
            print(f"⚠️  Pause request sent but status unclear")
        
        return result
    
    def resume_connector(self, connector_id: str) -> Dict:
        """
        Resume a paused Fivetran connector
        
        Args:
            connector_id: Fivetran connector ID
        
        Returns:
            Updated connector details
        """
        print(f"▶️  Resuming Fivetran connector: {connector_id}")
        
        response = self._make_request(
            "PATCH",
            f"/connectors/{connector_id}",
            data={"paused": False}
        )
        
        result = response.get("data", {})
        
        if not result.get("paused"):
            print(f"✅ Connector resumed successfully")
        else:
            print(f"⚠️  Resume request sent but status unclear")
        
        return result
    
    def trigger_sync(self, connector_id: str) -> Dict:
        """
        Manually trigger a connector sync
        
        Args:
            connector_id: Fivetran connector ID
        
        Returns:
            Sync trigger response
        
        Note: Sync is asynchronous. Use get_connector_status to check progress.
        """
        print(f"🔄 Triggering manual sync for: {connector_id}")
        
        response = self._make_request(
            "POST",
            f"/connectors/{connector_id}/force"
        )
        
        print(f"✅ Sync triggered (async operation)")
        return response.get("data", {})
    
    def list_connectors(self) -> list:
        """
        List all connectors in your Fivetran account
        
        Returns:
            List of connector summary dicts
        """
        response = self._make_request("GET", "/connectors")
        return response.get("data", {}).get("items", [])


# Convenience function for quick testing
def test_client():
    """Test Fivetran client with connector from .env"""
    connector_id = os.getenv("FIVETRAN_CONNECTOR_ID")
    
    if not connector_id:
        print("❌ FIVETRAN_CONNECTOR_ID not set in .env")
        return
    
    try:
        client = FivetranClient()
        
        print("=" * 60)
        print("FIVETRAN CLIENT TEST")
        print("=" * 60)
        
        # Get status
        print("\n1️⃣ Getting connector status...")
        status = client.get_connector_status(connector_id)
        print(f"   Status: {status['status']}")
        print(f"   Paused: {status['paused']}")
        print(f"   Service: {status['service']}")
        print(f"   Last sync: {status['last_sync']}")
        
        # Get details
        print("\n2️⃣ Getting connector details...")
        details = client.get_connector_details(connector_id)
        print(f"   ID: {details['id']}")
        print(f"   Schema: {details['schema']}")
        print(f"   Frequency: {details['sync_frequency']} minutes")
        
        print("\n✅ Fivetran client working correctly!")
        print("=" * 60)
    
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        print("=" * 60)


if __name__ == "__main__":
    test_client()
