"""
API Source for Agent Garden Perception
------------------------------------
This module provides a perception source for external APIs.
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

class ApiSource(PerceptionSource):
    """Perception source for external APIs."""
    
    def __init__(self, name: str = "api", description: str = "Monitors external APIs", frequency_minutes: int = 60):
        """Initialize the API source."""
        super().__init__(name, description, frequency_minutes)
        self.endpoints = self._load_endpoints()
        self.cache_file = os.path.join("perception", "cache", "api_cache.json")
        
        # Create cache directory if it doesn't exist
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
    
    def perceive(self) -> Dict[str, Any]:
        """
        Perceive data from external APIs.
        
        Returns:
            Dict containing API data
        """
        # Check if we have valid API endpoints configured
        if not self.endpoints:
            return self._simulate_api_data()
        
        # Otherwise, fetch real API data
        return self._fetch_real_api_data()
    
    def process_perception(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the perceived API data.
        
        Args:
            data: Raw API data
            
        Returns:
            Processed API data with additional metadata
        """
        api_data = data.get("api_data", {})
        
        # Add status indicators
        for endpoint, endpoint_data in api_data.items():
            # Add status based on response code or error
            if "error" in endpoint_data:
                endpoint_data["status"] = "error"
            elif "response_code" in endpoint_data:
                code = endpoint_data["response_code"]
                if 200 <= code < 300:
                    endpoint_data["status"] = "healthy"
                elif 300 <= code < 400:
                    endpoint_data["status"] = "redirect"
                elif 400 <= code < 500:
                    endpoint_data["status"] = "client_error"
                else:
                    endpoint_data["status"] = "server_error"
            else:
                endpoint_data["status"] = "unknown"
        
        # Add summary statistics
        healthy_count = sum(1 for _, data in api_data.items() if data.get("status") == "healthy")
        error_count = sum(1 for _, data in api_data.items() if data.get("status") in ["client_error", "server_error", "error"])
        
        # Generate insights
        insights = self._generate_insights(api_data)
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "api_data": api_data,
            "summary": {
                "total_endpoints": len(api_data),
                "healthy_endpoints": healthy_count,
                "error_endpoints": error_count,
                "health_percentage": round(healthy_count / len(api_data) * 100 if api_data else 0, 1)
            },
            "insights": insights
        }
    
    def _load_endpoints(self) -> List[Dict[str, Any]]:
        """
        Load API endpoints from configuration.
        
        Returns:
            List of API endpoint configurations
        """
        # Check if we have an endpoints configuration file
        endpoints_file = os.path.join("config", "api_endpoints.json")
        if os.path.exists(endpoints_file):
            try:
                with open(endpoints_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading API endpoints: {str(e)}")
        
        # Return empty list if no configuration found
        return []
    
    def _fetch_real_api_data(self) -> Dict[str, Any]:
        """
        Fetch data from real API endpoints.
        
        Returns:
            Dict containing API data
        """
        api_data = {}
        
        for endpoint in self.endpoints:
            name = endpoint.get("name", "unknown")
            url = endpoint.get("url", "")
            method = endpoint.get("method", "GET").upper()
            headers = endpoint.get("headers", {})
            params = endpoint.get("params", {})
            timeout = endpoint.get("timeout", 10)
            
            try:
                logger.info(f"Fetching API data from: {url}")
                
                if method == "GET":
                    response = requests.get(url, headers=headers, params=params, timeout=timeout)
                elif method == "POST":
                    data = endpoint.get("data", {})
                    response = requests.post(url, headers=headers, params=params, json=data, timeout=timeout)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                # Parse response based on content type
                content_type = response.headers.get("Content-Type", "")
                if "application/json" in content_type:
                    response_data = response.json()
                else:
                    response_data = {"text": response.text[:1000]}  # Limit text size
                
                api_data[name] = {
                    "response_code": response.status_code,
                    "response_time_ms": response.elapsed.total_seconds() * 1000,
                    "data": response_data,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error fetching API data from {url}: {str(e)}")
                api_data[name] = {
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }
        
        return {"api_data": api_data}
    
    def _simulate_api_data(self) -> Dict[str, Any]:
        """
        Simulate API data when no real endpoints are configured.
        
        Returns:
            Dict containing simulated API data
        """
        # Check if we have cached data
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    cached_data = json.load(f)
                    
                # Only use cache if it's less than an hour old
                cache_time = datetime.fromisoformat(cached_data.get("timestamp", "2000-01-01T00:00:00"))
                if datetime.utcnow() - cache_time < timedelta(hours=1):
                    return cached_data
            except Exception as e:
                logger.error(f"Error reading API cache: {str(e)}")
        
        # Generate simulated API data
        api_data = {}
        
        # Simulated financial API endpoints
        financial_endpoints = [
            {"name": "financial_inclusion_metrics", "url": "https://api.example.com/financial-inclusion"},
            {"name": "banking_access_index", "url": "https://api.example.com/banking-access"},
            {"name": "credit_availability", "url": "https://api.example.com/credit-availability"}
        ]
        
        # Simulated AI ethics API endpoints
        ai_ethics_endpoints = [
            {"name": "ai_bias_metrics", "url": "https://api.example.com/ai-bias"},
            {"name": "model_transparency_index", "url": "https://api.example.com/transparency"}
        ]
        
        # Simulated system monitoring endpoints
        system_endpoints = [
            {"name": "system_health", "url": "https://api.example.com/health"},
            {"name": "api_status", "url": "https://api.example.com/status"}
        ]
        
        # Combine all endpoints
        all_endpoints = financial_endpoints + ai_ethics_endpoints + system_endpoints
        
        for endpoint in all_endpoints:
            name = endpoint["name"]
            
            # Simulate success or failure (90% success rate)
            success = random.random() < 0.9
            
            if success:
                # Simulate successful response
                response_code = random.choice([200, 200, 200, 201, 204])  # Mostly 200 OK
                response_time = random.uniform(50, 500)  # 50-500ms
                
                # Generate simulated data based on endpoint type
                if "financial" in name or "banking" in name or "credit" in name:
                    data = self._simulate_financial_data()
                elif "ai" in name or "bias" in name or "model" in name:
                    data = self._simulate_ai_ethics_data()
                elif "system" in name or "health" in name or "status" in name:
                    data = self._simulate_system_data()
                else:
                    data = {"message": "Data available"}
                
                api_data[name] = {
                    "response_code": response_code,
                    "response_time_ms": response_time,
                    "data": data,
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                # Simulate error response
                error_code = random.choice([400, 401, 403, 404, 500, 502, 503])
                error_messages = {
                    400: "Bad Request",
                    401: "Unauthorized",
                    403: "Forbidden",
                    404: "Not Found",
                    500: "Internal Server Error",
                    502: "Bad Gateway",
                    503: "Service Unavailable"
                }
                
                api_data[name] = {
                    "response_code": error_code,
                    "error": error_messages.get(error_code, "Unknown Error"),
                    "timestamp": datetime.utcnow().isoformat()
                }
        
        result = {"api_data": api_data}
        
        # Cache the result
        try:
            result["timestamp"] = datetime.utcnow().isoformat()
            with open(self.cache_file, 'w') as f:
                json.dump(result, f)
        except Exception as e:
            logger.error(f"Error writing API cache: {str(e)}")
        
        return result
    
    def _simulate_financial_data(self) -> Dict[str, Any]:
        """
        Simulate financial API data.
        
        Returns:
            Dict containing simulated financial data
        """
        return {
            "financial_inclusion_index": round(random.uniform(0.5, 0.8), 2),
            "metrics": {
                "account_ownership": {
                    "overall": round(random.uniform(60, 80), 1),
                    "urban": round(random.uniform(70, 90), 1),
                    "rural": round(random.uniform(40, 70), 1),
                    "trend": random.choice(["increasing", "stable", "increasing"])
                },
                "digital_payments": {
                    "overall": round(random.uniform(50, 75), 1),
                    "urban": round(random.uniform(60, 85), 1),
                    "rural": round(random.uniform(30, 65), 1),
                    "trend": random.choice(["rapidly_increasing", "increasing", "stable"])
                },
                "credit_access": {
                    "overall": round(random.uniform(40, 65), 1),
                    "urban": round(random.uniform(50, 75), 1),
                    "rural": round(random.uniform(20, 55), 1),
                    "trend": random.choice(["increasing", "stable", "increasing"])
                }
            },
            "regional_data": {
                "north_america": round(random.uniform(0.8, 0.95), 2),
                "europe": round(random.uniform(0.75, 0.9), 2),
                "asia_pacific": round(random.uniform(0.5, 0.8), 2),
                "latin_america": round(random.uniform(0.4, 0.7), 2),
                "africa": round(random.uniform(0.3, 0.6), 2)
            }
        }
    
    def _simulate_ai_ethics_data(self) -> Dict[str, Any]:
        """
        Simulate AI ethics API data.
        
        Returns:
            Dict containing simulated AI ethics data
        """
        return {
            "bias_metrics": {
                "gender_bias_score": round(random.uniform(0.1, 0.4), 2),
                "racial_bias_score": round(random.uniform(0.15, 0.45), 2),
                "age_bias_score": round(random.uniform(0.1, 0.3), 2),
                "overall_bias_score": round(random.uniform(0.1, 0.4), 2)
            },
            "transparency_metrics": {
                "explainability_score": round(random.uniform(0.5, 0.9), 2),
                "documentation_score": round(random.uniform(0.6, 0.95), 2),
                "audit_readiness_score": round(random.uniform(0.4, 0.85), 2),
                "overall_transparency_score": round(random.uniform(0.5, 0.9), 2)
            },
            "industry_benchmarks": {
                "finance_sector": round(random.uniform(0.5, 0.8), 2),
                "healthcare_sector": round(random.uniform(0.6, 0.85), 2),
                "education_sector": round(random.uniform(0.55, 0.75), 2),
                "retail_sector": round(random.uniform(0.4, 0.7), 2)
            },
            "trend_data": {
                "bias_trend": random.choice(["improving", "stable", "improving"]),
                "transparency_trend": random.choice(["rapidly_improving", "improving", "stable"]),
                "industry_adoption_trend": random.choice(["increasing", "rapidly_increasing", "increasing"])
            }
        }
    
    def _simulate_system_data(self) -> Dict[str, Any]:
        """
        Simulate system API data.
        
        Returns:
            Dict containing simulated system data
        """
        return {
            "status": "healthy",
            "uptime": f"{random.randint(1, 30)} days, {random.randint(0, 23)} hours",
            "response_time": {
                "p50": round(random.uniform(50, 150), 1),
                "p90": round(random.uniform(150, 300), 1),
                "p99": round(random.uniform(300, 600), 1)
            },
            "error_rate": round(random.uniform(0.001, 0.01), 4),
            "resource_utilization": {
                "cpu": round(random.uniform(20, 70), 1),
                "memory": round(random.uniform(30, 80), 1),
                "disk": round(random.uniform(40, 75), 1)
            },
            "service_health": {
                "api_gateway": "healthy",
                "database": "healthy",
                "authentication": "healthy",
                "processing_engine": random.choice(["healthy", "healthy", "degraded"]),
                "notification_service": random.choice(["healthy", "healthy", "healthy", "degraded"])
            }
        }
    
    def _generate_insights(self, api_data: Dict[str, Any]) -> List[str]:
        """
        Generate insights from API data.
        
        Args:
            api_data: The API data to analyze
            
        Returns:
            List of insights
        """
        insights = []
        
        # Calculate health statistics
        total_endpoints = len(api_data)
        if total_endpoints == 0:
            return ["No API endpoints monitored"]
        
        healthy_endpoints = sum(1 for _, data in api_data.items() if data.get("status") == "healthy")
        health_percentage = healthy_endpoints / total_endpoints * 100
        
        # Add health insight
        if health_percentage == 100:
            insights.append("All monitored APIs are healthy")
        elif health_percentage >= 80:
            insights.append(f"Most APIs are healthy ({health_percentage:.1f}%)")
        elif health_percentage >= 50:
            insights.append(f"Some APIs are experiencing issues (only {health_percentage:.1f}% healthy)")
        else:
            insights.append(f"Critical: Most APIs are unhealthy (only {health_percentage:.1f}% healthy)")
        
        # Check for slow endpoints
        slow_endpoints = []
        for name, data in api_data.items():
            if "response_time_ms" in data and data["response_time_ms"] > 300:
                slow_endpoints.append(name)
        
        if slow_endpoints:
            if len(slow_endpoints) == 1:
                insights.append(f"The {slow_endpoints[0]} API is responding slowly")
            elif len(slow_endpoints) <= 3:
                insights.append(f"Several APIs are responding slowly: {', '.join(slow_endpoints)}")
            else:
                insights.append(f"Multiple APIs ({len(slow_endpoints)}) are experiencing performance issues")
        
        # Add insights from specific API types
        for name, data in api_data.items():
            if "data" not in data:
                continue
                
            api_data_content = data.get("data", {})
            
            # Financial insights
            if "financial_inclusion_index" in api_data_content:
                index = api_data_content.get("financial_inclusion_index", 0)
                if index > 0.7:
                    insights.append(f"Financial inclusion metrics show positive trends (index: {index:.2f})")
                elif index < 0.5:
                    insights.append(f"Financial inclusion metrics indicate challenges (index: {index:.2f})")
            
            # AI ethics insights
            if "bias_metrics" in api_data_content:
                bias_score = api_data_content.get("bias_metrics", {}).get("overall_bias_score", 0)
                if bias_score < 0.2:
                    insights.append("AI bias metrics are within acceptable thresholds")
                elif bias_score > 0.3:
                    insights.append("AI bias metrics require attention")
            
            # System insights
            if "error_rate" in api_data_content:
                error_rate = api_data_content.get("error_rate", 0)
                if error_rate > 0.005:
                    insights.append(f"System error rate is elevated ({error_rate:.4f})")
        
        # Limit to 5 most important insights
        return insights[:5]
