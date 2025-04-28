"""
Agent Framework for the Agent Garden

This module provides the base classes and utilities for creating and managing
helper agents within the Agent Garden ecosystem.
"""

import os
import json
import uuid
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BaseAgent:
    """Base class for all agents in the Agent Garden."""
    
    def __init__(self, agent_id: str, name: str, mission: str, parent_id: Optional[str] = None):
        """
        Initialize a new agent.
        
        Args:
            agent_id: Unique identifier for the agent
            name: Human-readable name for the agent
            mission: The agent's primary mission statement
            parent_id: ID of the parent agent (if this is a helper agent)
        """
        self.agent_id = agent_id
        self.name = name
        self.mission = mission
        self.parent_id = parent_id
        self.created_at = datetime.utcnow().isoformat()
        self.skills = []
        self.tasks = []
        self.memory_path = None
        self.config_path = None
        
        # Set up agent directory structure if it doesn't exist
        self._setup_agent_directory()
        
    def _setup_agent_directory(self):
        """Set up the directory structure for this agent."""
        base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'agents')
        agent_dir = os.path.join(base_dir, self.agent_id)
        
        # Create directories
        os.makedirs(os.path.join(agent_dir, 'tasks'), exist_ok=True)
        os.makedirs(os.path.join(agent_dir, 'memories'), exist_ok=True)
        os.makedirs(os.path.join(agent_dir, 'reflections'), exist_ok=True)
        os.makedirs(os.path.join(agent_dir, 'outputs'), exist_ok=True)
        
        # Create initial task files
        open_tasks_path = os.path.join(agent_dir, 'tasks', 'open_tasks.json')
        completed_tasks_path = os.path.join(agent_dir, 'tasks', 'completed_tasks.json')
        
        if not os.path.exists(open_tasks_path):
            with open(open_tasks_path, 'w') as f:
                json.dump([], f, indent=2)
        
        if not os.path.exists(completed_tasks_path):
            with open(completed_tasks_path, 'w') as f:
                json.dump([], f, indent=2)
        
        # Set paths for future reference
        self.config_path = os.path.join(agent_dir, 'config.json')
        self.memory_path = os.path.join(agent_dir, 'memories')
        
        # Save agent configuration
        self._save_config()
    
    def _save_config(self):
        """Save the agent's configuration to disk."""
        config = {
            'agent_id': self.agent_id,
            'name': self.name,
            'mission': self.mission,
            'parent_id': self.parent_id,
            'created_at': self.created_at,
            'skills': self.skills
        }
        
        with open(self.config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"Saved configuration for agent {self.name} ({self.agent_id})")
    
    def add_skill(self, skill_name: str) -> bool:
        """
        Add a skill to this agent.
        
        Args:
            skill_name: Name of the skill to add
            
        Returns:
            bool: True if the skill was added, False if it was already present
        """
        if skill_name not in self.skills:
            self.skills.append(skill_name)
            self._save_config()
            return True
        return False
    
    def add_task(self, task: Dict[str, Any]) -> str:
        """
        Add a task to this agent's task list.
        
        Args:
            task: Dictionary containing task details
            
        Returns:
            str: ID of the added task
        """
        if 'id' not in task:
            task['id'] = f"task_{str(uuid.uuid4())[:8]}"
        
        agent_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'agents', self.agent_id)
        open_tasks_path = os.path.join(agent_dir, 'tasks', 'open_tasks.json')
        
        with open(open_tasks_path, 'r') as f:
            tasks = json.load(f)
        
        tasks.append(task)
        
        with open(open_tasks_path, 'w') as f:
            json.dump(tasks, f, indent=2)
        
        logger.info(f"Added task {task['id']} to agent {self.name} ({self.agent_id})")
        return task['id']
    
    def get_tasks(self) -> List[Dict[str, Any]]:
        """
        Get all open tasks for this agent.
        
        Returns:
            List[Dict[str, Any]]: List of open tasks
        """
        agent_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'agents', self.agent_id)
        open_tasks_path = os.path.join(agent_dir, 'tasks', 'open_tasks.json')
        
        with open(open_tasks_path, 'r') as f:
            return json.load(f)
    
    def get_completed_tasks(self) -> List[Dict[str, Any]]:
        """
        Get all completed tasks for this agent.
        
        Returns:
            List[Dict[str, Any]]: List of completed tasks
        """
        agent_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'agents', self.agent_id)
        completed_tasks_path = os.path.join(agent_dir, 'tasks', 'completed_tasks.json')
        
        with open(completed_tasks_path, 'r') as f:
            return json.load(f)
    
    def mark_task_completed(self, task_id: str) -> bool:
        """
        Mark a task as completed.
        
        Args:
            task_id: ID of the task to mark as completed
            
        Returns:
            bool: True if the task was found and marked as completed, False otherwise
        """
        agent_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'agents', self.agent_id)
        open_tasks_path = os.path.join(agent_dir, 'tasks', 'open_tasks.json')
        completed_tasks_path = os.path.join(agent_dir, 'tasks', 'completed_tasks.json')
        
        # Read open tasks
        with open(open_tasks_path, 'r') as f:
            open_tasks = json.load(f)
        
        # Find the task to complete
        task_to_complete = None
        remaining_tasks = []
        
        for task in open_tasks:
            if task['id'] == task_id:
                task_to_complete = task
                # Add completion timestamp
                task_to_complete['completed_at'] = datetime.utcnow().isoformat()
            else:
                remaining_tasks.append(task)
        
        if task_to_complete is None:
            logger.warning(f"Task {task_id} not found for agent {self.name} ({self.agent_id})")
            return False
        
        # Read completed tasks
        with open(completed_tasks_path, 'r') as f:
            completed_tasks = json.load(f)
        
        # Add the completed task
        completed_tasks.append(task_to_complete)
        
        # Write back both files
        with open(open_tasks_path, 'w') as f:
            json.dump(remaining_tasks, f, indent=2)
        
        with open(completed_tasks_path, 'w') as f:
            json.dump(completed_tasks, f, indent=2)
        
        logger.info(f"Marked task {task_id} as completed for agent {self.name} ({self.agent_id})")
        return True


class HelperAgent(BaseAgent):
    """Helper agent class for specialized tasks."""
    
    def __init__(self, name: str, mission: str, parent_id: str, specialization: str):
        """
        Initialize a new helper agent.
        
        Args:
            name: Human-readable name for the agent
            mission: The agent's primary mission statement
            parent_id: ID of the parent agent
            specialization: The helper's area of specialization
        """
        agent_id = f"helper_{str(uuid.uuid4())[:8]}"
        super().__init__(agent_id, name, mission, parent_id)
        self.specialization = specialization
        self._update_config_with_specialization()
    
    def _update_config_with_specialization(self):
        """Update the agent's configuration with specialization info."""
        with open(self.config_path, 'r') as f:
            config = json.load(f)
        
        config['specialization'] = self.specialization
        
        with open(self.config_path, 'w') as f:
            json.dump(config, f, indent=2)


class AgentManager:
    """Manager class for creating and coordinating agents."""
    
    def __init__(self):
        """Initialize the agent manager."""
        self.base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'agents')
        self.agents = self._load_agents()
    
    def _load_agents(self) -> Dict[str, Dict[str, Any]]:
        """
        Load all agents from disk.
        
        Returns:
            Dict[str, Dict[str, Any]]: Dictionary of agent configurations
        """
        agents = {}
        
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir, exist_ok=True)
            return agents
        
        for agent_id in os.listdir(self.base_dir):
            config_path = os.path.join(self.base_dir, agent_id, 'config.json')
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    agents[agent_id] = config
        
        return agents
    
    def create_helper_agent(self, name: str, mission: str, parent_id: str, 
                           specialization: str) -> Tuple[str, HelperAgent]:
        """
        Create a new helper agent.
        
        Args:
            name: Human-readable name for the agent
            mission: The agent's primary mission statement
            parent_id: ID of the parent agent
            specialization: The helper's area of specialization
            
        Returns:
            Tuple[str, HelperAgent]: The agent ID and the agent object
        """
        # Verify parent exists
        if parent_id not in self.agents:
            logger.error(f"Parent agent {parent_id} not found")
            raise ValueError(f"Parent agent {parent_id} not found")
        
        helper = HelperAgent(name, mission, parent_id, specialization)
        self.agents[helper.agent_id] = {
            'agent_id': helper.agent_id,
            'name': helper.name,
            'mission': helper.mission,
            'parent_id': helper.parent_id,
            'created_at': helper.created_at,
            'specialization': helper.specialization
        }
        
        logger.info(f"Created helper agent {helper.name} ({helper.agent_id}) for parent {parent_id}")
        return helper.agent_id, helper
    
    def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Get an agent's configuration.
        
        Args:
            agent_id: ID of the agent to get
            
        Returns:
            Optional[Dict[str, Any]]: The agent's configuration, or None if not found
        """
        return self.agents.get(agent_id)
    
    def get_helpers(self, parent_id: str) -> List[Dict[str, Any]]:
        """
        Get all helper agents for a parent agent.
        
        Args:
            parent_id: ID of the parent agent
            
        Returns:
            List[Dict[str, Any]]: List of helper agent configurations
        """
        return [agent for agent_id, agent in self.agents.items() 
                if agent.get('parent_id') == parent_id]
    
    def load_agent_instance(self, agent_id: str) -> Optional[BaseAgent]:
        """
        Load an agent as a BaseAgent or HelperAgent instance.
        
        Args:
            agent_id: ID of the agent to load
            
        Returns:
            Optional[BaseAgent]: The agent instance, or None if not found
        """
        config = self.get_agent(agent_id)
        if not config:
            return None
        
        if config.get('parent_id'):
            # This is a helper agent
            return HelperAgent(
                config['name'], 
                config['mission'], 
                config['parent_id'],
                config.get('specialization', 'general')
            )
        else:
            # This is a main agent
            return BaseAgent(
                config['agent_id'],
                config['name'],
                config['mission']
            )
