"""
News Source for Agent Garden Perception
-------------------------------------
This module provides a perception source for news articles.
"""

import os
import logging
import random
import requests
import json
from typing import Dict, List, Any
from datetime import datetime, timedelta
from .perception_manager import PerceptionSource

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NewsSource(PerceptionSource):
    """Perception source for news articles."""
    
    def __init__(self, name: str = "news", description: str = "Monitors news articles", frequency_minutes: int = 120):
        """Initialize the news source."""
        super().__init__(name, description, frequency_minutes)
        self.categories = ["technology", "business", "finance", "ai", "ethics"]
        self.api_key = os.getenv("NEWS_API_KEY", "")
        self.cache_file = os.path.join("perception", "cache", "news_cache.json")
        
        # Create cache directory if it doesn't exist
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
    
    def perceive(self) -> Dict[str, Any]:
        """
        Perceive news articles.
        
        Returns:
            Dict containing news articles
        """
        # If we have a real API key, use the actual news API
        if self.api_key and self.api_key != "":
            return self._fetch_real_news()
        else:
            # Otherwise, use simulated news
            return self._simulate_news()
    
    def process_perception(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the perceived news data.
        
        Args:
            data: Raw news data
            
        Returns:
            Processed news data with additional metadata
        """
        articles = data.get("articles", [])
        
        # Add categories and sentiment analysis (simulated)
        for article in articles:
            # Assign categories
            article["categories"] = self._categorize_article(article)
            
            # Simulate sentiment analysis
            article["sentiment"] = self._analyze_sentiment(article)
            
            # Add relevance score (simulated)
            article["relevance_score"] = round(random.uniform(0.1, 1.0), 2)
        
        # Sort by relevance
        articles.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        
        # Add summary of key trends
        trends = self._identify_trends(articles)
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "articles": articles,
            "trends": trends,
            "total_articles": len(articles)
        }
    
    def _fetch_real_news(self) -> Dict[str, Any]:
        """
        Fetch real news from a news API.
        
        Returns:
            Dict containing news articles
        """
        try:
            # Example using NewsAPI.org
            url = "https://newsapi.org/v2/everything"
            
            # Create a query for AI and finance related news
            params = {
                "q": "artificial intelligence OR financial inclusion OR ethics",
                "sortBy": "publishedAt",
                "language": "en",
                "apiKey": self.api_key,
                "pageSize": 10
            }
            
            response = requests.get(url, params=params)
            data = response.json()
            
            if response.status_code == 200:
                return data
            else:
                logger.error(f"Error fetching news: {data.get('message', 'Unknown error')}")
                return {"articles": [], "error": data.get("message", "Unknown error")}
                
        except Exception as e:
            logger.error(f"Error fetching news: {str(e)}")
            return {"articles": [], "error": str(e)}
    
    def _simulate_news(self) -> Dict[str, Any]:
        """
        Simulate news articles when no API key is available.
        
        Returns:
            Dict containing simulated news articles
        """
        # Check if we have cached news
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    cached_data = json.load(f)
                    
                # Only use cache if it's less than a day old
                cache_time = datetime.fromisoformat(cached_data.get("timestamp", "2000-01-01T00:00:00"))
                if datetime.utcnow() - cache_time < timedelta(days=1):
                    return cached_data
            except Exception as e:
                logger.error(f"Error reading news cache: {str(e)}")
        
        # Generate simulated news
        current_date = datetime.utcnow()
        
        ai_titles = [
            "New AI Ethics Framework Proposed by Leading Tech Companies",
            "Study Shows Bias in AI Financial Systems Affecting Minority Groups",
            "Open Source AI Models Gain Traction in Financial Sector",
            "AI Regulation Bill Advances in Senate Committee",
            "Tech Giants Pledge $1B for Responsible AI Development"
        ]
        
        finance_titles = [
            "Financial Inclusion Index Shows Progress in Developing Regions",
            "Mobile Banking Adoption Reaches Record Levels in Rural Areas",
            "New Microlending Platform Targets Underbanked Communities",
            "Central Banks Explore Digital Currencies for Financial Inclusion",
            "Report: Alternative Credit Scoring Improves Loan Access"
        ]
        
        ethics_titles = [
            "Ethics in Technology: A New Framework for the Digital Age",
            "Survey Reveals Growing Consumer Concern Over Data Privacy",
            "Financial Institutions Adopt New Ethical Guidelines",
            "Transparency in AI Decision-Making Becomes Industry Standard",
            "Ethics Committees Now Required for AI Development in Healthcare"
        ]
        
        # Combine all titles and generate articles
        all_titles = ai_titles + finance_titles + ethics_titles
        random.shuffle(all_titles)
        
        articles = []
        for i, title in enumerate(all_titles[:10]):  # Limit to 10 articles
            # Generate a random date within the last week
            days_ago = random.randint(0, 6)
            hours_ago = random.randint(0, 23)
            published_date = current_date - timedelta(days=days_ago, hours=hours_ago)
            
            # Determine source based on title
            if any(term in title.lower() for term in ["ai", "artificial intelligence"]):
                source = random.choice(["TechCrunch", "Wired", "MIT Technology Review", "The Verge"])
            elif any(term in title.lower() for term in ["financial", "banking", "loan"]):
                source = random.choice(["Financial Times", "Bloomberg", "The Economist", "Wall Street Journal"])
            else:
                source = random.choice(["The Guardian", "New York Times", "Washington Post", "BBC"])
            
            # Generate article
            article = {
                "title": title,
                "source": {"name": source},
                "publishedAt": published_date.isoformat(),
                "url": f"https://example.com/article/{i}",
                "description": self._generate_description(title)
            }
            
            articles.append(article)
        
        result = {"articles": articles}
        
        # Cache the result
        try:
            result["timestamp"] = datetime.utcnow().isoformat()
            with open(self.cache_file, 'w') as f:
                json.dump(result, f)
        except Exception as e:
            logger.error(f"Error writing news cache: {str(e)}")
        
        return result
    
    def _generate_description(self, title: str) -> str:
        """
        Generate a description for a simulated news article.
        
        Args:
            title: The article title
            
        Returns:
            A simulated article description
        """
        ai_descriptions = [
            "Researchers have developed a new framework for ensuring AI systems operate ethically and transparently.",
            "A recent study highlights concerning biases in AI algorithms used for financial decision-making.",
            "Open source AI models are gaining popularity as financial institutions seek more transparent solutions.",
            "Lawmakers are advancing legislation to regulate artificial intelligence applications in sensitive domains.",
            "Major technology companies have announced a joint initiative to promote responsible AI development."
        ]
        
        finance_descriptions = [
            "The latest Financial Inclusion Index shows significant progress in expanding banking access globally.",
            "Mobile banking adoption has reached unprecedented levels in previously underserved rural communities.",
            "A new platform aims to connect underbanked individuals with microloans to build credit history.",
            "Central banks worldwide are exploring digital currencies as a means to improve financial inclusion.",
            "Alternative approaches to credit scoring are helping more people qualify for financial services."
        ]
        
        ethics_descriptions = [
            "Industry leaders have collaborated on a new ethical framework for technology development and deployment.",
            "A comprehensive survey reveals growing public concern regarding data privacy and algorithmic decision-making.",
            "Financial institutions are implementing new ethical guidelines to ensure fair treatment of all customers.",
            "Transparency in AI decision-making processes is becoming the expected standard across industries.",
            "Healthcare organizations will now require ethics committee approval for AI implementation."
        ]
        
        # Select description based on title keywords
        if any(term in title.lower() for term in ["ai", "artificial intelligence"]):
            return random.choice(ai_descriptions)
        elif any(term in title.lower() for term in ["financial", "banking", "loan"]):
            return random.choice(finance_descriptions)
        else:
            return random.choice(ethics_descriptions)
    
    def _categorize_article(self, article: Dict[str, Any]) -> List[str]:
        """
        Categorize an article based on its content.
        
        Args:
            article: The article to categorize
            
        Returns:
            List of categories
        """
        title = article.get("title", "").lower()
        description = article.get("description", "").lower()
        content = title + " " + description
        
        categories = []
        
        # Simple keyword-based categorization
        category_keywords = {
            "technology": ["technology", "tech", "digital", "software", "hardware", "app"],
            "business": ["business", "company", "industry", "market", "economic", "economy"],
            "finance": ["finance", "banking", "loan", "credit", "investment", "financial"],
            "ai": ["ai", "artificial intelligence", "machine learning", "algorithm", "neural", "model"],
            "ethics": ["ethics", "ethical", "bias", "fairness", "responsible", "transparency"]
        }
        
        for category, keywords in category_keywords.items():
            if any(keyword in content for keyword in keywords):
                categories.append(category)
        
        # Ensure at least one category
        if not categories:
            categories.append(random.choice(list(category_keywords.keys())))
        
        return categories
    
    def _analyze_sentiment(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform sentiment analysis on an article (simulated).
        
        Args:
            article: The article to analyze
            
        Returns:
            Dict with sentiment analysis results
        """
        # In a real implementation, this would use NLP models
        # For now, we'll simulate sentiment analysis
        
        # Generate random sentiment scores
        positive = round(random.uniform(0, 1), 2)
        negative = round(random.uniform(0, 1 - positive), 2)
        neutral = round(1 - positive - negative, 2)
        
        # Determine overall sentiment
        if positive > 0.6:
            overall = "positive"
        elif negative > 0.6:
            overall = "negative"
        else:
            overall = "neutral"
        
        return {
            "positive": positive,
            "negative": negative,
            "neutral": neutral,
            "overall": overall
        }
    
    def _identify_trends(self, articles: List[Dict[str, Any]]) -> List[str]:
        """
        Identify trends from a collection of articles.
        
        Args:
            articles: List of articles to analyze
            
        Returns:
            List of identified trends
        """
        # In a real implementation, this would use more sophisticated analysis
        # For now, we'll use a simple approach based on categories and sentiment
        
        # Count categories
        category_counts = {}
        for article in articles:
            for category in article.get("categories", []):
                category_counts[category] = category_counts.get(category, 0) + 1
        
        # Count sentiment by category
        sentiment_by_category = {}
        for article in articles:
            sentiment = article.get("sentiment", {}).get("overall", "neutral")
            for category in article.get("categories", []):
                if category not in sentiment_by_category:
                    sentiment_by_category[category] = {"positive": 0, "negative": 0, "neutral": 0}
                sentiment_by_category[category][sentiment] += 1
        
        # Generate trend statements
        trends = []
        
        # Add category prevalence trends
        sorted_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
        if sorted_categories:
            top_category = sorted_categories[0][0]
            trends.append(f"Increased coverage of {top_category}-related news")
        
        # Add sentiment trends
        for category, sentiments in sentiment_by_category.items():
            total = sum(sentiments.values())
            if total >= 3:  # Only consider categories with enough articles
                if sentiments["positive"] / total > 0.6:
                    trends.append(f"Positive sentiment trend in {category} news")
                elif sentiments["negative"] / total > 0.6:
                    trends.append(f"Negative sentiment trend in {category} news")
        
        # Add some general trends
        general_trends = [
            "Growing focus on ethical AI development",
            "Increasing regulatory attention to financial technology",
            "Rising interest in financial inclusion initiatives",
            "Expanding adoption of AI in financial services",
            "Heightened concern about algorithmic bias"
        ]
        
        # Add 1-3 general trends
        num_general = min(3, 5 - len(trends))
        if num_general > 0:
            trends.extend(random.sample(general_trends, num_general))
        
        return trends
