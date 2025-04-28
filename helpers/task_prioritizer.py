"""
Task Prioritization Engine for Agent Garden
-----------------------------------------
This module provides task prioritization capabilities.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TaskPrioritizer:
    """Engine for prioritizing agent tasks."""
    
    def __init__(self, agent_dir: str):
        """
        Initialize the task prioritizer.
        
        Args:
            agent_dir: Path to the agent directory
        """
        self.agent_dir = agent_dir
        self.tasks_dir = os.path.join(agent_dir, "tasks")
        self.open_tasks_file = os.path.join(self.tasks_dir, "open_tasks.json")
        self.completed_tasks_file = os.path.join(self.tasks_dir, "completed_tasks.json")
        
        # Create tasks directory if it doesn't exist
        os.makedirs(self.tasks_dir, exist_ok=True)
        
        # Create completed tasks file if it doesn't exist
        if not os.path.exists(self.completed_tasks_file):
            with open(self.completed_tasks_file, 'w') as f:
                json.dump([], f)
    
    def load_tasks(self) -> List[Dict[str, Any]]:
        """
        Load open tasks from the tasks file.
        
        Returns:
            List of tasks
        """
        if os.path.exists(self.open_tasks_file):
            with open(self.open_tasks_file, 'r') as f:
                return json.load(f)
        else:
            return []
    
    def save_tasks(self, tasks: List[Dict[str, Any]]) -> None:
        """
        Save tasks to the tasks file.
        
        Args:
            tasks: List of tasks to save
        """
        with open(self.open_tasks_file, 'w') as f:
            json.dump(tasks, f, indent=2)
    
    def load_completed_tasks(self) -> List[Dict[str, Any]]:
        """
        Load completed tasks from the completed tasks file.
        
        Returns:
            List of completed tasks
        """
        if os.path.exists(self.completed_tasks_file):
            with open(self.completed_tasks_file, 'r') as f:
                return json.load(f)
        else:
            return []
    
    def save_completed_tasks(self, tasks: List[Dict[str, Any]]) -> None:
        """
        Save completed tasks to the completed tasks file.
        
        Args:
            tasks: List of completed tasks to save
        """
        with open(self.completed_tasks_file, 'w') as f:
            json.dump(tasks, f, indent=2)
    
    def add_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add a new task to the task queue.
        
        Args:
            task: The task to add
            
        Returns:
            The added task with a generated ID
        """
        tasks = self.load_tasks()
        
        # Generate a task ID if not provided
        if "id" not in task:
            task["id"] = self._generate_task_id(tasks)
        
        # Set default priority if not provided
        if "priority" not in task:
            task["priority"] = "medium"
        
        # Set creation timestamp
        task["created_at"] = datetime.utcnow().isoformat()
        
        # Add the task to the list
        tasks.append(task)
        
        # Save the updated tasks
        self.save_tasks(tasks)
        
        logger.info(f"Added task: {task['description']} (ID: {task['id']})")
        return task
    
    def complete_task(self, task_id: str, result: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Mark a task as completed and move it to the completed tasks file.
        
        Args:
            task_id: ID of the task to complete
            result: Optional result of the task execution
            
        Returns:
            The completed task or None if not found
        """
        tasks = self.load_tasks()
        completed_tasks = self.load_completed_tasks()
        
        # Find the task
        task_index = None
        for i, task in enumerate(tasks):
            if task.get("id") == task_id:
                task_index = i
                break
        
        if task_index is None:
            logger.warning(f"Task not found: {task_id}")
            return None
        
        # Remove the task from the open tasks
        task = tasks.pop(task_index)
        
        # Add completion metadata
        task["completed_at"] = datetime.utcnow().isoformat()
        if result:
            task["result"] = result
        
        # Add the task to the completed tasks
        completed_tasks.append(task)
        
        # Save both files
        self.save_tasks(tasks)
        self.save_completed_tasks(completed_tasks)
        
        logger.info(f"Completed task: {task['description']} (ID: {task['id']})")
        return task
    
    def prioritize_tasks(self, criteria: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Prioritize tasks based on specified criteria.
        
        Args:
            criteria: Optional criteria for prioritization
            
        Returns:
            List of prioritized tasks
        """
        tasks = self.load_tasks()
        
        if not tasks:
            return []
        
        # Default criteria
        default_criteria = {
            "priority_weights": {
                "high": 10,
                "medium": 5,
                "low": 1
            },
            "due_date_weight": 8,
            "creation_date_weight": 2,
            "tag_weights": {}
        }
        
        # Merge with provided criteria
        if criteria:
            for key, value in criteria.items():
                if key in default_criteria and isinstance(default_criteria[key], dict):
                    default_criteria[key].update(value)
                else:
                    default_criteria[key] = value
        
        criteria = default_criteria
        
        # Calculate scores for each task
        for task in tasks:
            score = 0
            
            # Priority score
            priority = task.get("priority", "medium").lower()
            score += criteria["priority_weights"].get(priority, 5)
            
            # Due date score
            if "due_date" in task and task["due_date"]:
                try:
                    due_date = datetime.fromisoformat(task["due_date"])
                    now = datetime.utcnow()
                    days_until_due = (due_date - now).days
                    
                    if days_until_due < 0:
                        # Overdue tasks get maximum score
                        score += criteria["due_date_weight"] * 10
                    elif days_until_due == 0:
                        # Due today
                        score += criteria["due_date_weight"] * 8
                    elif days_until_due <= 2:
                        # Due in next 2 days
                        score += criteria["due_date_weight"] * 6
                    elif days_until_due <= 7:
                        # Due in next week
                        score += criteria["due_date_weight"] * 4
                    else:
                        # Due later
                        score += criteria["due_date_weight"] * 2
                except (ValueError, TypeError):
                    # Invalid date format
                    pass
            
            # Creation date score
            if "created_at" in task:
                try:
                    created_at = datetime.fromisoformat(task["created_at"])
                    now = datetime.utcnow()
                    days_since_creation = (now - created_at).days
                    
                    # Older tasks get higher scores
                    age_score = min(days_since_creation, 10)  # Cap at 10 days
                    score += criteria["creation_date_weight"] * age_score / 10
                except (ValueError, TypeError):
                    # Invalid date format
                    pass
            
            # Tag scores
            for tag in task.get("tags", []):
                score += criteria["tag_weights"].get(tag, 0)
            
            # Store the score in the task
            task["_priority_score"] = score
        
        # Sort tasks by score (descending)
        tasks.sort(key=lambda x: x.get("_priority_score", 0), reverse=True)
        
        # Remove temporary score field
        for task in tasks:
            if "_priority_score" in task:
                del task["_priority_score"]
        
        # Save the prioritized tasks
        self.save_tasks(tasks)
        
        logger.info(f"Prioritized {len(tasks)} tasks")
        return tasks
    
    def get_task_by_id(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a task by its ID.
        
        Args:
            task_id: ID of the task to get
            
        Returns:
            The task or None if not found
        """
        tasks = self.load_tasks()
        
        for task in tasks:
            if task.get("id") == task_id:
                return task
        
        return None
    
    def update_task(self, task_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update a task.
        
        Args:
            task_id: ID of the task to update
            updates: Dict of fields to update
            
        Returns:
            The updated task or None if not found
        """
        tasks = self.load_tasks()
        
        # Find the task
        task_index = None
        for i, task in enumerate(tasks):
            if task.get("id") == task_id:
                task_index = i
                break
        
        if task_index is None:
            logger.warning(f"Task not found: {task_id}")
            return None
        
        # Update the task
        for key, value in updates.items():
            tasks[task_index][key] = value
        
        # Save the updated tasks
        self.save_tasks(tasks)
        
        logger.info(f"Updated task: {tasks[task_index]['description']} (ID: {task_id})")
        return tasks[task_index]
    
    def delete_task(self, task_id: str) -> bool:
        """
        Delete a task.
        
        Args:
            task_id: ID of the task to delete
            
        Returns:
            True if the task was deleted, False otherwise
        """
        tasks = self.load_tasks()
        
        # Find the task
        task_index = None
        for i, task in enumerate(tasks):
            if task.get("id") == task_id:
                task_index = i
                break
        
        if task_index is None:
            logger.warning(f"Task not found: {task_id}")
            return False
        
        # Remove the task
        task = tasks.pop(task_index)
        
        # Save the updated tasks
        self.save_tasks(tasks)
        
        logger.info(f"Deleted task: {task['description']} (ID: {task_id})")
        return True
    
    def generate_daily_plan(self) -> Dict[str, Any]:
        """
        Generate a daily plan based on prioritized tasks.
        
        Returns:
            Dict containing the daily plan
        """
        tasks = self.prioritize_tasks()
        
        # Group tasks by priority
        high_priority = []
        medium_priority = []
        low_priority = []
        
        for task in tasks:
            priority = task.get("priority", "medium").lower()
            if priority == "high":
                high_priority.append(task)
            elif priority == "medium":
                medium_priority.append(task)
            else:
                low_priority.append(task)
        
        # Create the plan
        plan = {
            "date": datetime.utcnow().date().isoformat(),
            "high_priority_tasks": high_priority,
            "medium_priority_tasks": medium_priority,
            "low_priority_tasks": low_priority,
            "total_tasks": len(tasks),
            "estimated_completion_time": self._estimate_completion_time(tasks)
        }
        
        logger.info(f"Generated daily plan with {len(tasks)} tasks")
        return plan
    
    def _generate_task_id(self, existing_tasks: List[Dict[str, Any]]) -> str:
        """
        Generate a unique task ID.
        
        Args:
            existing_tasks: List of existing tasks
            
        Returns:
            A unique task ID
        """
        # Find the highest existing task ID
        highest_id = 0
        for task in existing_tasks:
            if "id" in task and task["id"].startswith("task_"):
                try:
                    task_num = int(task["id"].split("_")[1])
                    highest_id = max(highest_id, task_num)
                except (ValueError, IndexError):
                    pass
        
        # Generate a new ID
        return f"task_{highest_id + 1:03d}"
    
    def _estimate_completion_time(self, tasks: List[Dict[str, Any]]) -> str:
        """
        Estimate the time required to complete a list of tasks.
        
        Args:
            tasks: List of tasks
            
        Returns:
            Estimated completion time as a string
        """
        # Default time estimates in minutes
        default_estimates = {
            "high": 60,
            "medium": 30,
            "low": 15
        }
        
        total_minutes = 0
        for task in tasks:
            priority = task.get("priority", "medium").lower()
            estimate = task.get("estimated_minutes", default_estimates.get(priority, 30))
            total_minutes += estimate
        
        # Format the estimate
        hours = total_minutes // 60
        minutes = total_minutes % 60
        
        if hours > 0:
            return f"{hours} hours {minutes} minutes"
        else:
            return f"{minutes} minutes"
