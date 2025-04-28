"""
Skill Registry for Agent Garden
------------------------------
This module manages the registration and discovery of skills.
"""

import os
import importlib
import inspect
import logging
from typing import Dict, List, Any, Type, Optional
from .base_skill import BaseSkill

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SkillRegistry:
    """Registry for managing and discovering skills."""
    
    def __init__(self):
        """Initialize the skill registry."""
        self.skills = {}  # name -> skill instance
        self.skill_classes = {}  # name -> skill class
    
    def register_skill(self, skill_class: Type[BaseSkill]) -> None:
        """
        Register a skill class.
        
        Args:
            skill_class: The skill class to register
        """
        # Create a temporary instance to get metadata
        temp_instance = skill_class("temp", "temp")
        name = temp_instance.name
        
        self.skill_classes[name] = skill_class
        logger.info(f"Registered skill class: {name}")
    
    def instantiate_skill(self, name: str, *args, **kwargs) -> Optional[BaseSkill]:
        """
        Instantiate a registered skill.
        
        Args:
            name: Name of the skill to instantiate
            *args, **kwargs: Arguments to pass to the skill constructor
            
        Returns:
            Instantiated skill or None if not found
        """
        if name in self.skill_classes:
            skill = self.skill_classes[name](*args, **kwargs)
            self.skills[name] = skill
            logger.info(f"Instantiated skill: {name}")
            return skill
        else:
            logger.warning(f"Skill not found: {name}")
            return None
    
    def get_skill(self, name: str) -> Optional[BaseSkill]:
        """
        Get an instantiated skill by name.
        
        Args:
            name: Name of the skill to get
            
        Returns:
            The skill instance or None if not found
        """
        return self.skills.get(name)
    
    def get_all_skills(self) -> List[BaseSkill]:
        """
        Get all instantiated skills.
        
        Returns:
            List of all skill instances
        """
        return list(self.skills.values())
    
    def discover_skills(self, skills_dir: str = None) -> List[str]:
        """
        Discover and register skills from a directory.
        
        Args:
            skills_dir: Directory to search for skills, defaults to the 'skills' directory
            
        Returns:
            List of discovered skill names
        """
        if skills_dir is None:
            # Default to the 'skills' directory in the same directory as this file
            skills_dir = os.path.dirname(os.path.abspath(__file__))
        
        discovered_skills = []
        
        # Get all Python files in the directory
        for filename in os.listdir(skills_dir):
            if filename.endswith('.py') and filename != '__init__.py' and filename != 'base_skill.py' and filename != 'skill_registry.py':
                module_name = filename[:-3]  # Remove .py extension
                
                try:
                    # Import the module
                    module_path = f"skills.{module_name}"
                    module = importlib.import_module(module_path)
                    
                    # Find all classes in the module that are subclasses of BaseSkill
                    for name, obj in inspect.getmembers(module):
                        if (inspect.isclass(obj) and 
                            issubclass(obj, BaseSkill) and 
                            obj != BaseSkill):
                            
                            # Register the skill
                            self.register_skill(obj)
                            discovered_skills.append(name)
                            
                except Exception as e:
                    logger.error(f"Error discovering skill in {filename}: {str(e)}")
        
        return discovered_skills
    
    def find_skill_for_task(self, task: Dict[str, Any]) -> Optional[BaseSkill]:
        """
        Find a skill that can execute the given task.
        
        Args:
            task: The task to find a skill for
            
        Returns:
            A skill that can execute the task, or None if no suitable skill is found
        """
        if "skill_required" in task:
            # If the task specifies a required skill, try to use that
            skill_name = task["skill_required"]
            skill = self.get_skill(skill_name)
            
            if skill and skill.validate_task(task):
                return skill
            
            # If the specified skill doesn't exist or can't handle the task,
            # try to find a skill with a matching alias
            for skill in self.get_all_skills():
                if skill_name in skill.get_aliases() and skill.validate_task(task):
                    return skill
        
        # If no skill is specified or the specified skill isn't suitable,
        # try all skills to see if any can handle the task
        for skill in self.get_all_skills():
            if skill.validate_task(task):
                return skill
        
        return None

# Create a singleton instance
registry = SkillRegistry()
