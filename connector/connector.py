"""
Osprey Financial News Connector for Fivetran
Syncs financial news from NewsAPI to BigQuery
Production-ready with comprehensive error handling
"""
from fivetran_connector_sdk import Connector, Logging as log, Operations as op
import requests
import hashlib
from datetime import datetime, timezone, timedelta
import json

def schema(configuration: dict):
    """Define BigQuery schema for raw_news table"""
    return [
        {
            "table": "raw_news",
            "primary_key": ["article_id"],
            "columns": {
                "article_id": "STRING",
                "url": "STRING",
                "title": "STRING",
                "summary": "STRING",
                "source": "STRING",
                "authors": "STRING",
                "category": "STRING",
                "published_at": "UTC_DATETIME",
                "synced_at": "UTC_DATETIME",
                "stock_symbols": "STRING",
                "topics": "STRING",
                "sentiment_score": "DOUBLE",
                "sentiment_label": "STRING",
                "ticker_sentiments": "STRING"
            }
        }
    ]

def update(configuration: dict, state: dict):
    """Main sync function called by Fivetran"""
    log.warning("🚀 Starting Financial News Sync")
    
    # Get configuration (all values are strings from Fivetran)
    api_key = configuration.get("api_key")
    tickers = configuration.get("tickers", "AAPL,MSFT,GOOGL")
    articles_limit = int(configuration.get("articles_per_sync", "50"))
    
    if not api_key:
        log.severe("❌ API key is required in configuration")
        raise ValueError("api_key is required in configuration")
    
    log.info(f"📊 Fetching news for tickers: {tickers}")
    log.info(f"📈 Request limit: {articles_limit} articles")
    
    try:
        # Fetch news from NewsAPI
        articles = fetch_newsapi_data(api_key, tickers, articles_limit)
        
        if not articles:
            log.warning("⚠️ No articles returned from API")
            # Still checkpoint even with no data
            new_state = {
                "last_sync": datetime.now(timezone.utc).isoformat(),
                "total_synced": state.get("total_synced", 0),
                "last_article_count": 0
            }
            op.checkpoint(new_state)
            return
        
        log.info(f"✅ Fetched {len(articles)} articles from API")
        
        # Process and upsert each article
        synced_count = 0
        errors_count = 0
        
        for article in articles:
            try:
                record = transform_article(article, tickers)
                
                # Upsert to raw_news table
                op.upsert(
                    table="raw_news",
                    data=record
                )
                synced_count += 1
                
            except Exception as e:
                errors_count += 1
                log.warning(f"⚠️ Failed to process article: {str(e)}")
                continue
        
        log.info(f"✅ Successfully synced {synced_count} articles")
        
        if errors_count > 0:
            log.warning(f"⚠️ {errors_count} articles failed to process")
        
        # Update state with metrics
        new_state = {
            "last_sync": datetime.now(timezone.utc).isoformat(),
            "total_synced": state.get("total_synced", 0) + synced_count,
            "last_article_count": synced_count,
            "last_error_count": errors_count
        }
        
        # Checkpoint state (critical for incremental syncs)
        op.checkpoint(new_state)
        
        log.warning(f"🎉 Sync completed: {synced_count} articles synced")
        
    except Exception as e:
        log.severe(f"❌ Sync failed with error: {str(e)}")
        raise

def fetch_newsapi_data(api_key: str, tickers: str, limit: int):
    """Fetch financial news from NewsAPI"""
    
    # Build search query for financial news about tickers
    # NewsAPI supports OR operators
    ticker_list = [t.strip() for t in tickers.split(",")]
    query_parts = []
    
    for ticker in ticker_list:
        # Search for ticker symbol and company-related terms
        query_parts.append(f'"{ticker}"')
    
    query = f"({' OR '.join(query_parts)}) AND (stock OR shares OR trading OR earnings OR market)"
    
    # NewsAPI endpoint for everything (last 30 days)
    url = "https://newsapi.org/v2/everything"
    
    # Calculate date range (last 7 days for more relevant news)
    to_date = datetime.now(timezone.utc)
    from_date = to_date - timedelta(days=7)
    
    params = {
        "q": query,
        "from": from_date.strftime("%Y-%m-%d"),
        "to": to_date.strftime("%Y-%m-%d"),
        "language": "en",
        "sortBy": "publishedAt",  # Most recent first
        "pageSize": min(limit, 100),  # NewsAPI max is 100
        "apiKey": api_key
    }
    
    log.info(f"🔍 Query: {query[:100]}...")
    
    response = requests.get(url, params=params, timeout=30)
    
    if response.status_code == 429:
        log.severe("❌ Rate limit exceeded - max 100 requests/day on free tier")
        raise Exception("NewsAPI rate limit exceeded")
    
    if response.status_code == 401:
        log.severe("❌ Invalid API key")
        raise Exception("Invalid NewsAPI key")
    
    response.raise_for_status()
    data = response.json()
    
    # Check response status
    if data.get("status") != "ok":
        error_msg = data.get("message", "Unknown error")
        log.severe(f"❌ NewsAPI Error: {error_msg}")
        raise Exception(f"NewsAPI Error: {error_msg}")
    
    articles = data.get("articles", [])
    total_results = data.get("totalResults", 0)
    
    log.info(f"📰 Total matching articles: {total_results}")
    log.info(f"📥 Returning {len(articles)} articles")
    
    return articles

def transform_article(article, tickers: str):
    """Transform NewsAPI article to BigQuery schema"""
    
    # Generate unique article ID from URL
    url = article.get("url", "")
    article_id = hashlib.md5(url.encode()).hexdigest()
    
    # Parse published timestamp
    published_str = article.get("publishedAt", "")
    try:
        # NewsAPI format: 2025-10-15T06:30:00Z
        published_at = datetime.fromisoformat(published_str.replace("Z", "+00:00"))
        published_at = published_at.isoformat()
    except:
        published_at = datetime.now(timezone.utc).isoformat()
    
    # Extract author(s)
    author = article.get("author", "")
    authors = author if author else None
    
    # Extract source
    source_obj = article.get("source", {})
    source_name = source_obj.get("name", "Unknown")
    
    # Determine which tickers are mentioned in title/description
    title = article.get("title", "")
    description = article.get("description", "")
    content = article.get("content", "")
    
    full_text = f"{title} {description} {content}".upper()
    
    ticker_list = [t.strip() for t in tickers.split(",")]
    mentioned_tickers = [t for t in ticker_list if t.upper() in full_text]
    stock_symbols = ", ".join(mentioned_tickers) if mentioned_tickers else tickers.split(",")[0]
    
    # Simple sentiment analysis based on keywords (basic implementation)
    sentiment_score, sentiment_label = analyze_sentiment(title, description)
    
    # Build topics from category
    topics = [{"topic": "Financial Markets", "relevance": "0.9"}]
    
    return {
        "article_id": article_id,
        "url": url,
        "title": title,
        "summary": description,
        "source": source_name,
        "authors": authors,
        "category": "financial",
        "published_at": published_at,
        "synced_at": datetime.now(timezone.utc).isoformat(),
        "stock_symbols": stock_symbols,
        "topics": json.dumps(topics),
        "sentiment_score": sentiment_score,
        "sentiment_label": sentiment_label,
        "ticker_sentiments": json.dumps([])  # NewsAPI doesn't provide this
    }

def analyze_sentiment(title: str, description: str):
    """Basic sentiment analysis using keyword matching"""
    
    if not title and not description:
        return 0.0, "Neutral"
    
    text = f"{title} {description}".lower()
    
    # Positive keywords
    positive_keywords = [
        "surge", "gain", "rise", "rally", "profit", "beat", "exceed",
        "growth", "strong", "record", "upgrade", "bullish", "optimistic",
        "boost", "soar", "jump", "positive", "advance"
    ]
    
    # Negative keywords
    negative_keywords = [
        "fall", "drop", "decline", "loss", "miss", "plunge", "crash",
        "weak", "disappointing", "downgrade", "bearish", "pessimistic",
        "concern", "worry", "risk", "threat", "negative", "struggle"
    ]
    
    positive_count = sum(1 for keyword in positive_keywords if keyword in text)
    negative_count = sum(1 for keyword in negative_keywords if keyword in text)
    
    # Calculate sentiment score (-1 to 1 range)
    total_keywords = positive_count + negative_count
    
    if total_keywords == 0:
        return 0.0, "Neutral"
    
    sentiment_score = (positive_count - negative_count) / max(total_keywords, 1)
    
    # Normalize to -0.35 to 0.35 range (similar to Alpha Vantage)
    sentiment_score = sentiment_score * 0.35
    
    # Determine label
    if sentiment_score > 0.15:
        sentiment_label = "Bullish"
    elif sentiment_score > 0.05:
        sentiment_label = "Somewhat-Bullish"
    elif sentiment_score < -0.15:
        sentiment_label = "Bearish"
    elif sentiment_score < -0.05:
        sentiment_label = "Somewhat-Bearish"
    else:
        sentiment_label = "Neutral"
    
    return round(sentiment_score, 6), sentiment_label

# Create connector instance
connector = Connector(update=update, schema=schema)

# For local testing
if __name__ == "__main__":
    # Load test configuration
    with open("test_config.json", "r") as f:
        configuration = json.load(f)
    
    # Run debug
    connector.debug(configuration=configuration)
