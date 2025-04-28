#!/usr/bin/env python3
"""
Agent Garden Lifecycle Manager
------------------------------
This module manages the lifecycle of helper agents, including retirement,
memory compression, and population control.
"""

import os
import json
import shutil
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("agent_garden.lifecycle_manager")

class LifecycleManager:
    """Manages the lifecycle of helper agents in the Agent Garden."""
    
    def __init__(self, 
                 agents_dir: str, 
                 archive_dir: str, 
                 max_active_helpers: int = 20,
                 max_tasks_threshold: int = 50,
                 max_days_threshold: int = 30):
        """
        Initialize the lifecycle manager.
        
        Args:
            agents_dir: Directory containing agent data
            archive_dir: Directory for archived agents
            max_active_helpers: Maximum number of active helper agents
            max_tasks_threshold: Number of tasks after which an agent should retire
            max_days_threshold: Number of days after which an agent should retire
        """
        self.agents_dir = agents_dir
        self.archive_dir = archive_dir
        self.max_active_helpers = max_active_helpers
        self.max_tasks_threshold = max_tasks_threshold
        self.max_days_threshold = max_days_threshold
        
        # Ensure archive directory exists
        os.makedirs(self.archive_dir, exist_ok=True)
    
    def get_helper_agents(self, parent_id: str = None) -> List[Dict[str, Any]]:
        """
        Get all helper agents, optionally filtered by parent.
        
        Args:
            parent_id: Optional parent agent ID to filter by
            
        Returns:
            List of helper agent metadata
        """
        helpers = []
        
        # List all directories in the agents directory
        for agent_dir in os.listdir(self.agents_dir):
            # Skip if not a directory or doesn't start with "helper_"
            if not os.path.isdir(os.path.join(self.agents_dir, agent_dir)) or not agent_dir.startswith("helper_"):
                continue
            
            # Load agent config
            config_path = os.path.join(self.agents_dir, agent_dir, "config.json")
            if not os.path.exists(config_path):
                continue
                
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                
                # Filter by parent if specified
                if parent_id and config.get('parent_id') != parent_id:
                    continue
                
                # Add agent ID to config
                config['agent_id'] = agent_dir
                helpers.append(config)
            except Exception as e:
                logger.error(f"Error loading config for agent {agent_dir}: {str(e)}")
        
        return helpers
    
    def get_active_helper_count(self, parent_id: str = None) -> int:
        """
        Get the number of active helper agents.
        
        Args:
            parent_id: Optional parent agent ID to filter by
            
        Returns:
            Number of active helper agents
        """
        return len(self.get_helper_agents(parent_id))
    
    def check_retirement_conditions(self, agent_id: str) -> Tuple[bool, str]:
        """
        Check if an agent should be retired based on tasks completed and age.
        
        Args:
            agent_id: ID of the agent to check
            
        Returns:
            Tuple of (should_retire, reason)
        """
        agent_dir = os.path.join(self.agents_dir, agent_id)
        
        # Skip if agent directory doesn't exist
        if not os.path.isdir(agent_dir):
            return False, "Agent directory not found"
        
        # Load agent config
        config_path = os.path.join(agent_dir, "config.json")
        if not os.path.exists(config_path):
            return False, "Agent config not found"
            
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Check creation date
            creation_date = datetime.fromisoformat(config.get('creation_date', datetime.utcnow().isoformat()))
            age_days = (datetime.utcnow() - creation_date).days
            
            if age_days >= self.max_days_threshold:
                return True, f"Agent has reached maximum age of {self.max_days_threshold} days"
            
            # Check tasks completed
            tasks_completed = 0
            completed_tasks_path = os.path.join(agent_dir, "tasks", "completed_tasks.json")
            if os.path.exists(completed_tasks_path):
                try:
                    with open(completed_tasks_path, 'r') as f:
                        completed_tasks = json.load(f)
                    tasks_completed = len(completed_tasks)
                except Exception as e:
                    logger.error(f"Error loading completed tasks for agent {agent_id}: {str(e)}")
            
            if tasks_completed >= self.max_tasks_threshold:
                return True, f"Agent has completed {tasks_completed} tasks (threshold: {self.max_tasks_threshold})"
            
            return False, "Agent is still active"
        except Exception as e:
            logger.error(f"Error checking retirement conditions for agent {agent_id}: {str(e)}")
            return False, f"Error: {str(e)}"
    
    def compress_agent_memory(self, agent_id: str) -> Dict[str, Any]:
        """
        Compress an agent's memory into a summarized format.
        
        Args:
            agent_id: ID of the agent to compress memory for
            
        Returns:
            Dictionary containing compressed memory
        """
        agent_dir = os.path.join(self.agents_dir, agent_id)
        memories_dir = os.path.join(agent_dir, "memories")
        
        # Initialize compressed memory
        compressed_memory = {
            "agent_id": agent_id,
            "compression_date": datetime.utcnow().isoformat(),
            "knowledge_areas": {},
            "key_learnings": [],
            "specialization_insights": [],
            "task_patterns": {}
        }
        
        # Skip if memories directory doesn't exist
        if not os.path.isdir(memories_dir):
            return compressed_memory
        
        # Load all memory files
        memory_files = [f for f in os.listdir(memories_dir) if f.endswith('.jsonl')]
        all_memories = []
        
        for memory_file in memory_files:
            memory_path = os.path.join(memories_dir, memory_file)
            try:
                with open(memory_path, 'r') as f:
                    for line in f:
                        memory = json.loads(line.strip())
                        all_memories.append(memory)
            except Exception as e:
                logger.error(f"Error loading memory file {memory_file} for agent {agent_id}: {str(e)}")
        
        # Group memories by category
        memories_by_category = {}
        for memory in all_memories:
            category = memory.get('category', 'unknown')
            if category not in memories_by_category:
                memories_by_category[category] = []
            memories_by_category[category].append(memory)
        
        # Process each category
        for category, memories in memories_by_category.items():
            # Extract key insights based on category
            if category == "knowledge":
                # Group by tags
                knowledge_by_tag = {}
                for memory in memories:
                    tags = memory.get('tags', [])
                    content = memory.get('content', '')
                    for tag in tags:
                        if tag not in knowledge_by_tag:
                            knowledge_by_tag[tag] = []
                        knowledge_by_tag[tag].append(content)
                
                # Summarize knowledge by tag
                for tag, contents in knowledge_by_tag.items():
                    compressed_memory["knowledge_areas"][tag] = {
                        "count": len(contents),
                        "summary": f"Knowledge about {tag} based on {len(contents)} memories",
                        "samples": contents[:3]  # Include a few samples
                    }
            
            elif category == "task":
                # Group by task type
                tasks_by_type = {}
                for memory in memories:
                    task_type = memory.get('metadata', {}).get('task_type', 'unknown')
                    if task_type not in tasks_by_type:
                        tasks_by_type[task_type] = []
                    tasks_by_type[task_type].append(memory)
                
                # Summarize tasks by type
                for task_type, task_memories in tasks_by_type.items():
                    success_count = sum(1 for m in task_memories if m.get('metadata', {}).get('success', False))
                    compressed_memory["task_patterns"][task_type] = {
                        "count": len(task_memories),
                        "success_rate": success_count / len(task_memories) if task_memories else 0,
                        "common_challenges": self._extract_common_patterns([m.get('metadata', {}).get('challenges', []) for m in task_memories], 3)
                    }
            
            elif category == "reflection":
                # Extract key learnings from reflections
                learnings = []
                for memory in memories:
                    if 'content' in memory and isinstance(memory['content'], dict) and 'learnings' in memory['content']:
                        learnings.extend(memory['content']['learnings'])
                
                # Find most common learnings
                compressed_memory["key_learnings"] = self._extract_common_patterns(learnings, 5)
        
        # Load agent config to get specialization
        config_path = os.path.join(agent_dir, "config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                specialization = config.get('specialization', 'general')
                
                # Add specialization-specific insights
                if specialization == "research":
                    compressed_memory["specialization_insights"] = [
                        "Research methodology patterns",
                        "Source evaluation techniques",
                        "Information synthesis approaches"
                    ]
                elif specialization == "content_creation":
                    compressed_memory["specialization_insights"] = [
                        "Content structure patterns",
                        "Audience engagement techniques",
                        "Narrative development approaches"
                    ]
                elif specialization == "monitoring":
                    compressed_memory["specialization_insights"] = [
                        "Metric tracking patterns",
                        "Anomaly detection techniques",
                        "Trend analysis approaches"
                    ]
            except Exception as e:
                logger.error(f"Error loading config for agent {agent_id}: {str(e)}")
        
        return compressed_memory
    
    def _extract_common_patterns(self, items_list: List[Any], count: int = 3) -> List[str]:
        """
        Extract common patterns from a list of items.
        
        Args:
            items_list: List of items or lists of items
            count: Number of common patterns to extract
            
        Returns:
            List of common patterns
        """
        # Flatten the list if it contains lists
        flat_items = []
        for items in items_list:
            if isinstance(items, list):
                flat_items.extend(items)
            else:
                flat_items.append(items)
        
        # Count occurrences
        item_counts = {}
        for item in flat_items:
            if not item:
                continue
            item_str = str(item)
            item_counts[item_str] = item_counts.get(item_str, 0) + 1
        
        # Sort by count and return top items
        sorted_items = sorted(item_counts.items(), key=lambda x: x[1], reverse=True)
        return [item for item, _ in sorted_items[:count]]
    
    def retire_agent(self, agent_id: str) -> Dict[str, Any]:
        """
        Retire an agent by compressing its memory and archiving it.
        
        Args:
            agent_id: ID of the agent to retire
            
        Returns:
            Dictionary containing retirement metadata
        """
        agent_dir = os.path.join(self.agents_dir, agent_id)
        archive_agent_dir = os.path.join(self.archive_dir, agent_id)
        
        # Skip if agent directory doesn't exist
        if not os.path.isdir(agent_dir):
            return {"success": False, "error": "Agent directory not found"}
        
        try:
            # Compress agent memory
            compressed_memory = self.compress_agent_memory(agent_id)
            
            # Create archive directory
            os.makedirs(archive_agent_dir, exist_ok=True)
            
            # Save compressed memory
            compressed_memory_path = os.path.join(archive_agent_dir, "compressed_memory.json")
            with open(compressed_memory_path, 'w') as f:
                json.dump(compressed_memory, f, indent=2)
            
            # Copy config and other important files
            for item in ["config.json", "reflections"]:
                source_path = os.path.join(agent_dir, item)
                target_path = os.path.join(archive_agent_dir, item)
                if os.path.exists(source_path):
                    if os.path.isdir(source_path):
                        shutil.copytree(source_path, target_path, dirs_exist_ok=True)
                    else:
                        shutil.copy2(source_path, target_path)
            
            # Create retirement metadata
            retirement_metadata = {
                "agent_id": agent_id,
                "retirement_date": datetime.utcnow().isoformat(),
                "compressed_memory_size": os.path.getsize(compressed_memory_path),
                "reason": "Lifecycle management"
            }
            
            # Save retirement metadata
            metadata_path = os.path.join(archive_agent_dir, "retirement_metadata.json")
            with open(metadata_path, 'w') as f:
                json.dump(retirement_metadata, f, indent=2)
            
            # Remove agent directory
            shutil.rmtree(agent_dir)
            
            logger.info(f"Successfully retired agent {agent_id}")
            return {"success": True, "metadata": retirement_metadata}
        except Exception as e:
            logger.error(f"Error retiring agent {agent_id}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def manage_helper_population(self, parent_id: str = None) -> Dict[str, Any]:
        """
        Manage the helper agent population by retiring agents as needed.
        
        Args:
            parent_id: Optional parent agent ID to filter by
            
        Returns:
            Dictionary containing management results
        """
        results = {
            "active_helpers_before": 0,
            "active_helpers_after": 0,
            "retired_agents": [],
            "retirement_reasons": {}
        }
        
        # Get all helper agents
        helpers = self.get_helper_agents(parent_id)
        results["active_helpers_before"] = len(helpers)
        
        # Check each agent for retirement conditions
        retirement_candidates = []
        for helper in helpers:
            agent_id = helper.get('agent_id')
            should_retire, reason = self.check_retirement_conditions(agent_id)
            if should_retire:
                retirement_candidates.append((agent_id, reason))
        
        # Sort candidates by priority (age first, then tasks completed)
        retirement_candidates.sort(key=lambda x: "age" in x[1], reverse=True)
        
        # Retire agents as needed
        for agent_id, reason in retirement_candidates:
            # Stop if we're below the maximum
            if len(helpers) - len(results["retired_agents"]) <= self.max_active_helpers:
                break
            
            # Retire the agent
            retirement_result = self.retire_agent(agent_id)
            if retirement_result.get("success", False):
                results["retired_agents"].append(agent_id)
                results["retirement_reasons"][agent_id] = reason
        
        # Update active helpers count
        results["active_helpers_after"] = results["active_helpers_before"] - len(results["retired_agents"])
        
        return results
