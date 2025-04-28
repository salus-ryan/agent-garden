"""
Base Skill Module for Agent Garden
----------------------------------
This module defines the base class for all skill modules.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BaseSkill(ABC):
    """Base class for all skill modules."""
    
    def __init__(self, name: str, description: str, version: str = "0.1.0"):
        """
        Initialize the skill.
        
        Args:
            name: Name of the skill
            description: Description of what the skill does
            version: Version of the skill
        """
        self.name = name
        self.description = description
        self.version = version
        self.enabled = True
        logger.info(f"Initialized skill: {self.name} v{self.version}")
    
    @abstractmethod
    def execute(self, task: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute the skill on a task.
        
        Args:
            task: The task to execute
            context: Additional context for the execution
            
        Returns:
            Dict containing the results of the execution
        """
        pass
    
    def validate_task(self, task: Dict[str, Any]) -> bool:
        """
        Validate that the task can be executed by this skill.
        
        Args:
            task: The task to validate
            
        Returns:
            True if the task can be executed, False otherwise
        """
        # Default implementation checks if the skill name is in the task's skill_required field
        return (
            "skill_required" in task and 
            (task["skill_required"] == self.name or task["skill_required"] in self.get_aliases())
        )
    
    def get_aliases(self) -> List[str]:
        """
        Get a list of alternative names for this skill.
        
        Returns:
            List of alias names
        """
        return []
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about the skill.
        
        Returns:
            Dict containing skill metadata
        """
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "enabled": self.enabled,
            "aliases": self.get_aliases()
        }
    
    def enable(self) -> None:
        """Enable the skill."""
        self.enabled = True
        logger.info(f"Enabled skill: {self.name}")
    
    def disable(self) -> None:
        """Disable the skill."""
        self.enabled = False
        logger.info(f"Disabled skill: {self.name}")
    
    def __str__(self) -> str:
        return f"{self.name} v{self.version} - {self.description}"
