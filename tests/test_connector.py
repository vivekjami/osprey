"""
Simple test script without Fivetran SDK complications
Run this from the connector directory
"""
import os
import sys
import requests
import json
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment
load_dotenv()

def test_api_direct():
    """Test Alpha Vantage API directly"""
    print("\n" + "="*70)
    print("TEST 1: Direct API Test")
    print("="*70)
    
    api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
    if not api_key:
        print("❌ API key not found in .env")
        return False
    
    print(f"✅ API Key: {api_key[:8]}...")
    
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "NEWS_SENTIMENT",
        "tickers": "AAPL,MSFT",
        "limit": 5,
        "apikey": api_key,
        "sort": "LATEST"
    }
    
    print("📡 Calling API...")
    response = requests.get(url, params=params, timeout=30)
    
    if response.status_code != 200:
        print(f"❌ HTTP {response.status_code}")
        return False
    
    data = response.json()
    
    if "Error Message" in data:
        print(f"❌ API Error: {data['Error Message']}")
        return False
    
    if "Note" in data:
        print(f"⚠️  Rate limit: {data['Note']}")
        return False
    
    articles = data.get("feed", [])
    print(f"✅ Fetched {len(articles)} articles\n")
    
    if articles:
        article = articles[0]
        print("📰 Sample Article:")
        print(f"   Title: {article.get('title', 'N/A')[:60]}...")
        print(f"   Source: {article.get('source', 'N/A')}")
        print(f"   Published: {article.get('time_published', 'N/A')}")
        print(f"   Sentiment: {article.get('overall_sentiment_label', 'N/A')}")
        print(f"   Score: {article.get('overall_sentiment_score', 'N/A')}")
    
    return True


def test_transformation():
    """Test article transformation logic"""
    print("\n" + "="*70)
    print("TEST 2: Article Transformation")
    print("="*70)
    
    # Sample article from API
    sample_article = {
        "title": "Apple Announces New Products",
        "url": "https://example.com/article",
        "summary": "Apple unveiled new iPhone models...",
        "source": "Reuters",
        "authors": ["John Doe", "Jane Smith"],
        "category_within_source": "Technology",
        "time_published": "20241014T120000",
        "overall_sentiment_score": 0.45,
        "overall_sentiment_label": "Bullish",
        "topics": [
            {"topic": "Technology", "relevance_score": "0.9"},
            {"topic": "Retail", "relevance_score": "0.3"}
        ],
        "ticker_sentiment": [
            {
                "ticker": "AAPL",
                "relevance_score": "0.95",
                "ticker_sentiment_score": "0.42",
                "ticker_sentiment_label": "Bullish"
            }
        ]
    }
    
    print("📋 Transforming sample article...")
    
    # Import transformation function
    sys.path.insert(0, os.path.dirname(__file__))
    from connector import transform_article
    
    try:
        record = transform_article(sample_article)
        
        print("✅ Transformation successful\n")
        print("🔍 Transformed Record:")
        print(f"   article_id: {record['article_id'][:16]}...")
        print(f"   title: {record['title']}")
        print(f"   source: {record['source']}")
        print(f"   authors: {record['authors']}")
        print(f"   published_at: {record['published_at']}")
        print(f"   stock_symbols: {record['stock_symbols']}")
        print(f"   sentiment_score: {record['sentiment_score']}")
        print(f"   sentiment_label: {record['sentiment_label']}")
        
        # Validate required fields
        required = ['article_id', 'url', 'title', 'source', 'published_at', 'synced_at']
        missing = [f for f in required if not record.get(f)]
        
        if missing:
            print(f"\n❌ Missing required fields: {missing}")
            return False
        
        print("\n✅ All required fields present")
        return True
        
    except Exception as e:
        print(f"❌ Transformation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_full_flow():
    """Test complete flow: fetch + transform"""
    print("\n" + "="*70)
    print("TEST 3: Complete Flow (Fetch + Transform)")
    print("="*70)
    
    api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
    if not api_key:
        print("❌ API key not found")
        return False
    
    # Import connector functions
    sys.path.insert(0, os.path.dirname(__file__))
    from connector import fetch_news_from_api, transform_article
    
    try:
        print("📡 Fetching real articles...")
        articles = fetch_news_from_api(api_key, "AAPL,MSFT", 5)
        
        if not articles:
            print("⚠️  No articles returned (may be rate limited)")
            return False
        
        print(f"✅ Fetched {len(articles)} articles")
        
        print("\n📋 Transforming articles...")
        records = []
        
        for i, article in enumerate(articles[:3], 1):
            record = transform_article(article)
            records.append(record)
            
            print(f"\n📰 Article {i}:")
            print(f"   ID: {record['article_id'][:12]}...")
            print(f"   Title: {record['title'][:50]}...")
            print(f"   Source: {record['source']}")
            print(f"   Stocks: {record['stock_symbols']}")
            print(f"   Sentiment: {record['sentiment_label']} ({record['sentiment_score']:.2f})")
        
        print(f"\n✅ Successfully processed {len(records)} articles")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "█"*70)
    print("OSPREY CONNECTOR - SIMPLE TEST SUITE")
    print("█"*70)
    
    tests = [
        ("Direct API Test", test_api_direct),
        ("Transformation Logic", test_transformation),
        ("Complete Flow", test_full_flow)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n❌ {test_name} crashed: {str(e)}")
            results[test_name] = False
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    passed_count = sum(1 for v in results.values() if v)
    total_count = len(results)
    
    print(f"\n📊 {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("\n🎉 All tests PASSED!")
        print("\n📦 Ready to deploy:")
        print("   1. Create ZIP:")
        print("      Compress-Archive -Path connector.py, configuration_schema.json, requirements.txt")
        print("                       -DestinationPath osprey-connector.zip -Force")
        print("   2. Upload to Fivetran UI")
        print("   3. Configure and sync")
        return True
    else:
        print(f"\n⚠️  {total_count - passed_count} test(s) failed")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)