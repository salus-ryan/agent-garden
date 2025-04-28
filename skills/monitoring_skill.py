"""
Monitoring Skill Module for Agent Garden
---------------------------------------
This module provides monitoring capabilities to agents.
"""

import logging
import random
import time
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from .base_skill import BaseSkill

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MonitoringSkill(BaseSkill):
    """Skill for monitoring metrics and systems."""
    
    def __init__(self, name: str = "monitoring", description: str = "Monitors metrics and systems"):
        """Initialize the monitoring skill."""
        super().__init__(name, description)
        self.metrics_categories = [
            "financial_inclusion",
            "system_performance",
            "user_engagement",
            "market_trends",
            "regulatory_compliance"
        ]
    
    def execute(self, task: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a monitoring task.
        
        Args:
            task: The monitoring task to execute
            context: Additional context for monitoring
            
        Returns:
            Dict containing the monitoring results
        """
        if not self.validate_task(task):
            return {
                "success": False,
                "error": "Task is not a valid monitoring task"
            }
        
        description = task.get("description", "")
        
        # Determine what to monitor from the task
        monitoring_category = self._determine_monitoring_category(task)
        
        # Extract specific metrics or systems to monitor
        metrics = self._extract_metrics_from_task(task)
        
        logger.info(f"Monitoring {monitoring_category}: {metrics}")
        
        # In a real implementation, this would connect to APIs, databases, etc.
        # For now, we'll simulate monitoring with a delay and random data
        time.sleep(1)  # Simulate monitoring time
        
        # Generate monitoring data based on category and metrics
        monitoring_data = self._generate_monitoring_data(monitoring_category, metrics)
        
        # Generate insights from the data
        insights = self._generate_insights(monitoring_category, monitoring_data)
        
        return {
            "success": True,
            "category": monitoring_category,
            "metrics": metrics,
            "data": monitoring_data,
            "insights": insights,
            "timestamp": datetime.utcnow().isoformat(),
            "next_scheduled_check": (datetime.utcnow() + timedelta(days=1)).isoformat()
        }
    
    def validate_task(self, task: Dict[str, Any]) -> bool:
        """
        Validate that the task is a monitoring task.
        
        Args:
            task: The task to validate
            
        Returns:
            True if the task is a valid monitoring task, False otherwise
        """
        # Check if the task explicitly requires this skill
        if super().validate_task(task):
            return True
        
        # Check if the task description indicates monitoring
        description = task.get("description", "").lower()
        monitoring_keywords = ["monitor", "track", "measure", "observe", "analyze", "metrics", "kpi"]
        
        # Check if any tags indicate monitoring
        tags = task.get("tags", [])
        monitoring_tags = ["monitoring", "metrics", "tracking", "analytics"]
        
        return (
            any(keyword in description for keyword in monitoring_keywords) or
            any(tag in tags for tag in monitoring_tags)
        )
    
    def get_aliases(self) -> List[str]:
        """Get aliases for the monitoring skill."""
        return ["tracking", "metrics", "analytics", "measurement"]
    
    def _determine_monitoring_category(self, task: Dict[str, Any]) -> str:
        """
        Determine the category of monitoring based on the task.
        
        Args:
            task: The monitoring task
            
        Returns:
            The determined monitoring category
        """
        description = task.get("description", "").lower()
        tags = task.get("tags", [])
        
        # Map of keywords to monitoring categories
        category_keywords = {
            "financial": "financial_inclusion",
            "inclusion": "financial_inclusion",
            "equity": "financial_inclusion",
            "performance": "system_performance",
            "system": "system_performance",
            "uptime": "system_performance",
            "user": "user_engagement",
            "engagement": "user_engagement",
            "market": "market_trends",
            "trend": "market_trends",
            "regulatory": "regulatory_compliance",
            "compliance": "regulatory_compliance",
            "regulation": "regulatory_compliance"
        }
        
        # Check description for category keywords
        for keyword, category in category_keywords.items():
            if keyword in description:
                return category
        
        # Check tags for category keywords
        for tag in tags:
            for keyword, category in category_keywords.items():
                if keyword in tag:
                    return category
        
        # Default to system performance if no specific category is identified
        return "system_performance"
    
    def _extract_metrics_from_task(self, task: Dict[str, Any]) -> List[str]:
        """
        Extract specific metrics to monitor from the task.
        
        Args:
            task: The monitoring task
            
        Returns:
            List of metrics to monitor
        """
        description = task.get("description", "").lower()
        
        # Financial inclusion metrics
        financial_metrics = [
            "account_access",
            "transaction_volume",
            "loan_approval_rates",
            "financial_literacy",
            "banking_penetration"
        ]
        
        # System performance metrics
        performance_metrics = [
            "response_time",
            "error_rate",
            "uptime",
            "resource_utilization",
            "throughput"
        ]
        
        # User engagement metrics
        engagement_metrics = [
            "active_users",
            "session_duration",
            "conversion_rate",
            "retention_rate",
            "feature_usage"
        ]
        
        # Market trends metrics
        market_metrics = [
            "competitor_activity",
            "industry_growth",
            "pricing_trends",
            "innovation_rate",
            "market_share"
        ]
        
        # Regulatory compliance metrics
        compliance_metrics = [
            "policy_adherence",
            "audit_results",
            "incident_reports",
            "compliance_training",
            "regulatory_changes"
        ]
        
        # Determine which set of metrics to use based on the description
        if "financial" in description or "inclusion" in description:
            return financial_metrics
        elif "performance" in description or "system" in description:
            return performance_metrics
        elif "user" in description or "engagement" in description:
            return engagement_metrics
        elif "market" in description or "trend" in description:
            return market_metrics
        elif "regulatory" in description or "compliance" in description:
            return compliance_metrics
        else:
            # Return a mix of metrics if no specific category is identified
            all_metrics = financial_metrics + performance_metrics + engagement_metrics + market_metrics + compliance_metrics
            return random.sample(all_metrics, min(5, len(all_metrics)))
    
    def _generate_monitoring_data(self, category: str, metrics: List[str]) -> Dict[str, Any]:
        """
        Generate monitoring data based on category and metrics.
        
        Args:
            category: The monitoring category
            metrics: The metrics to monitor
            
        Returns:
            Dict containing the monitoring data
        """
        data = {}
        
        # Generate time series data for each metric
        for metric in metrics:
            # Generate daily data points for the last 30 days
            time_series = []
            base_value = random.uniform(50, 100)
            trend = random.uniform(-0.1, 0.1)  # Slight trend up or down
            
            for i in range(30):
                date = (datetime.utcnow() - timedelta(days=29-i)).strftime("%Y-%m-%d")
                value = base_value * (1 + trend * i) + random.uniform(-5, 5)
                time_series.append({
                    "date": date,
                    "value": round(value, 2)
                })
            
            data[metric] = {
                "current_value": time_series[-1]["value"],
                "previous_value": time_series[-2]["value"],
                "change_percent": round((time_series[-1]["value"] - time_series[-2]["value"]) / time_series[-2]["value"] * 100, 2),
                "time_series": time_series
            }
        
        return data
    
    def _generate_insights(self, category: str, data: Dict[str, Any]) -> List[str]:
        """
        Generate insights from monitoring data.
        
        Args:
            category: The monitoring category
            data: The monitoring data
            
        Returns:
            List of insights
        """
        insights = []
        
        # Generate general category insights
        if category == "financial_inclusion":
            insights.append("Financial inclusion metrics show steady improvement in underserved regions")
            insights.append("Digital banking adoption continues to be a key driver of inclusion")
            insights.append("Gender gap in financial access is narrowing but still significant")
        elif category == "system_performance":
            insights.append("System performance remains stable with minor fluctuations")
            insights.append("Peak usage times are shifting to earlier in the day")
            insights.append("Error rates are within acceptable thresholds")
        elif category == "user_engagement":
            insights.append("User engagement shows seasonal patterns with higher activity mid-week")
            insights.append("New feature adoption is exceeding expectations")
            insights.append("Retention metrics indicate strong user loyalty")
        elif category == "market_trends":
            insights.append("Market competition is intensifying in the digital finance space")
            insights.append("Regulatory changes are creating new market opportunities")
            insights.append("Consumer preferences are shifting toward integrated financial services")
        elif category == "regulatory_compliance":
            insights.append("Compliance metrics are meeting or exceeding requirements")
            insights.append("Recent regulatory changes require attention in Q2")
            insights.append("Industry-wide compliance standards are becoming more stringent")
        
        # Generate metric-specific insights
        for metric, metric_data in data.items():
            change = metric_data["change_percent"]
            if change > 5:
                insights.append(f"{metric.replace('_', ' ').title()} has increased significantly by {change}%")
            elif change < -5:
                insights.append(f"{metric.replace('_', ' ').title()} has decreased significantly by {abs(change)}%")
            
            # Check for trends in time series
            time_series = metric_data["time_series"]
            if len(time_series) >= 7:
                recent_week = [point["value"] for point in time_series[-7:]]
                previous_week = [point["value"] for point in time_series[-14:-7]]
                
                recent_avg = sum(recent_week) / len(recent_week)
                previous_avg = sum(previous_week) / len(previous_week)
                
                week_change = (recent_avg - previous_avg) / previous_avg * 100
                
                if week_change > 10:
                    insights.append(f"{metric.replace('_', ' ').title()} shows strong positive trend over the past week (+{round(week_change, 1)}%)")
                elif week_change < -10:
                    insights.append(f"{metric.replace('_', ' ').title()} shows concerning negative trend over the past week ({round(week_change, 1)}%)")
        
        # Limit to 5 most important insights
        return insights[:5]
