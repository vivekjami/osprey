"""
Test NewsAPI directly to verify API key and data quality
"""
import requests
import json
from datetime import datetime, timezone, timedelta

def test_newsapi(api_key: str):
    """Test NewsAPI endpoint"""
    
    print("=" * 70)
    print("NEWSAPI DIAGNOSTIC TEST")
    print("=" * 70)
    
    # Test configuration
    tickers = "AAPL,MSFT,GOOGL"
    query = f'(AAPL OR MSFT OR GOOGL) AND (stock OR shares OR trading)'
    
    url = "https://newsapi.org/v2/everything"
    
    to_date = datetime.now(timezone.utc)
    from_date = to_date - timedelta(days=7)
    
    params = {
        "q": query,
        "from": from_date.strftime("%Y-%m-%d"),
        "to": to_date.strftime("%Y-%m-%d"),
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": 10,
        "apiKey": api_key
    }
    
    print(f"\n[TEST 1] Testing API Key Validity...")
    print(f"Query: {query}")
    print(f"Date Range: {from_date.strftime('%Y-%m-%d')} to {to_date.strftime('%Y-%m-%d')}")
    
    try:
        response = requests.get(url, params=params, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 401:
            print("❌ FAILED: Invalid API key")
            print("Get your free API key at: https://newsapi.org/register")
            return False
        
        if response.status_code == 429:
            print("❌ FAILED: Rate limit exceeded (100 requests/day)")
            return False
        
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") != "ok":
            print(f"❌ FAILED: {data.get('message')}")
            return False
        
        articles = data.get("articles", [])
        total = data.get("totalResults", 0)
        
        print(f"✅ SUCCESS!")
        print(f"Total Results: {total}")
        print(f"Retrieved: {len(articles)} articles")
        
        if articles:
            print(f"\n[TEST 2] Sample Article:")
            print(f"Title: {articles[0].get('title')}")
            print(f"Source: {articles[0].get('source', {}).get('name')}")
            print(f"Published: {articles[0].get('publishedAt')}")
            print(f"URL: {articles[0].get('url')}")
            
            print(f"\n[TEST 3] All Articles:")
            for i, article in enumerate(articles, 1):
                print(f"{i}. {article.get('title')} - {article.get('source', {}).get('name')}")
        else:
            print("\n⚠️ WARNING: No articles found")
            print("This may be normal if there's no recent news for these tickers")
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False

if __name__ == "__main__":
    # Read API key from test_config.json
    try:
        with open("test_config.json", "r") as f:
            config = json.load(f)
            api_key = config.get("api_key")
            
            if not api_key or api_key == "YOUR_NEWSAPI_KEY_HERE":
                print("❌ Please update test_config.json with your NewsAPI key")
                print("Get free API key at: https://newsapi.org/register")
            else:
                test_newsapi(api_key)
    except FileNotFoundError:
        print("❌ test_config.json not found")
        print("Create it with: {\"api_key\": \"YOUR_KEY\", \"tickers\": \"AAPL,MSFT,GOOGL\", \"articles_per_sync\": \"50\"}")
