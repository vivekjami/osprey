import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def test_alpha_vantage():
    """Test Alpha Vantage News API"""
    api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
    
    if not api_key or api_key == "YOUR_API_KEY_HERE":
        print("❌ Please set ALPHA_VANTAGE_API_KEY in .env file")
        return
    
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "NEWS_SENTIMENT",
        "tickers": "AAPL,MSFT",
        "limit": 5,
        "apikey": api_key
    }
    
    print("🔍 Testing Alpha Vantage API...")
    response = requests.get(url, params=params)
    
    if response.status_code != 200:
        print(f"❌ Error: {response.status_code}")
        return
    
    data = response.json()
    
    if "Error Message" in data:
        print(f"❌ API Error: {data['Error Message']}")
        return
    
    if "Note" in data:
        print(f"⚠️ Rate limit: {data['Note']}")
        return
    
    feed = data.get("feed", [])
    print(f"✅ API working! Received {len(feed)} articles")
    
    if feed:
        print("\n📰 Sample Article:")
        article = feed[0]
        print(f"  Title: {article.get('title', 'N/A')}")
        print(f"  Source: {article.get('source', 'N/A')}")
        print(f"  Sentiment: {article.get('overall_sentiment_label', 'N/A')}")
        print(f"  Published: {article.get('time_published', 'N/A')}")

if __name__ == "__main__":
    test_alpha_vantage()