"""
Agent Framework for the Agent Garden

This module provides the base classes and utilities for creating and managing
helper agents within the Agent Garden ecosystem.
"""

import os
import json
import uuid
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple

# Import reflection system and specialized skills
from helpers.reflection_helper import ReflectionSystem
from helpers.skill_specialization import get_specialized_skill

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
        self.reflection_system = ReflectionSystem(self.agent_id)
        self.domain_knowledge = {}
        self.performance_metrics = {
            'tasks_completed': 0,
            'tasks_failed': 0,
            'avg_task_time': 0,
            'total_task_time': 0
        }
        
        # Initialize specialized skill based on specialization
        self.specialized_skill = get_specialized_skill(self.agent_id, specialization)
        
        self._update_config_with_specialization()
    
    def _update_config_with_specialization(self):
        """Update the agent's configuration with specialization info."""
        config_path = os.path.join('agents', self.agent_id, 'config.json')
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        config['specialization'] = self.specialization
        
        # Add specialized skill info to config
        skill_status = self.specialized_skill.get_status()
        config['specialized_skill'] = {
            'name': skill_status['skill_name'],
            'proficiency': skill_status['proficiency'],
            'techniques': self.specialized_skill.get_techniques()
        }
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
    
    def execute_specialized_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a task using specialized skills based on the agent's specialization.
        
        Args:
            task: Task dictionary containing task details
            
        Returns:
            Dict[str, Any]: Task execution results
        """
        task_id = task.get('id', f"task_{str(uuid.uuid4())[:8]}")
        task_description = task.get('description', 'Unnamed task')
        start_time = time.time()
        result = {}
        success = False
        
        try:
            # Execute task based on specialization
            if self.specialization == 'research':
                # Extract research parameters from task
                topic = task.get('topic', task_description)
                depth = task.get('depth', 3)
                
                # Conduct research
                research_results = self.specialized_skill.conduct_research(topic, depth)
                result = {
                    'findings': research_results['findings'],
                    'techniques_used': research_results['techniques_used'],
                    'depth': research_results['depth']
                }
                success = True
                
            elif self.specialization == 'content_creation':
                # Extract content creation parameters from task
                content_type = task.get('content_type', 'blog_post')
                topic = task.get('topic', task_description)
                audience = task.get('audience', 'general')
                
                # Create content
                content_results = self.specialized_skill.create_content(content_type, topic, audience)
                result = {
                    'content_type': content_results['content_type'],
                    'outline': content_results['outline'],
                    'audience_considerations': content_results['audience_considerations']
                }
                success = True
                
            elif self.specialization == 'monitoring':
                # Extract monitoring parameters from task
                domain = task.get('domain', 'system_health')
                metrics = task.get('metrics', {})
                
                # If metrics not provided, use simulated data
                if not metrics:
                    metrics = {
                        'uptime': 0.98,
                        'response_time': 150,
                        'error_rate': 0.02
                    }
                
                # Monitor metrics
                monitoring_results = self.specialized_skill.monitor_metrics(domain, metrics)
                result = {
                    'alerts': monitoring_results['alerts'],
                    'insights': monitoring_results['insights']
                }
                success = True
                
            else:
                # Generic task execution for unknown specializations
                result = {
                    'message': f"Executed task: {task_description}",
                    'specialization': self.specialization
                }
                success = True
                
        except Exception as e:
            logger.error(f"Error executing specialized task: {str(e)}")
            result = {'error': str(e)}
            success = False
        
        # Calculate execution time
        execution_time = time.time() - start_time
        
        # Mark task as completed
        self.mark_task_completed(task_id)
        
        # Reflect on the task
        reflection_data = self.reflect_on_task(
            task_id=task_id,
            task_description=task_description,
            outcome=json.dumps(result),
            success=success,
            execution_time=execution_time
        )
        
        # Return combined results
        return {
            'task_id': task_id,
            'success': success,
            'execution_time': execution_time,
            'result': result,
            'reflection': reflection_data
        }
    
    def reflect_on_task(self, task_id: str, task_description: str, outcome: str, 
                       success: bool, execution_time: float) -> Dict[str, Any]:
        """
        Reflect on a completed task and generate insights.
        
        Args:
            task_id: ID of the completed task
            task_description: Description of the task
            outcome: Outcome of the task
            success: Whether the task was successful
            execution_time: Time taken to execute the task (in seconds)
            
        Returns:
            Dict[str, Any]: Reflection data
        """
        # Update performance metrics
        if success:
            self.performance_metrics['tasks_completed'] += 1
        else:
            self.performance_metrics['tasks_failed'] += 1
            
        # Calculate average task time
        total_tasks = self.performance_metrics['tasks_completed'] + self.performance_metrics['tasks_failed']
        if total_tasks > 0:
            self.performance_metrics['avg_task_time'] = self.performance_metrics['total_task_time'] / total_tasks
        
        # Analyze task based on specialization
        if self.specialization == 'research':
            challenges = [
                "Finding reliable sources",
                "Synthesizing complex information",
                "Organizing research findings effectively"
            ]
            learnings = [
                f"New insights about {task_description.split()[0]}",
                "Improved information filtering techniques",
                "Better understanding of the domain"
            ]
            improvement_ideas = [
                "Develop better source evaluation criteria",
                "Create more structured research methodology",
                "Improve note-taking system for research tasks"
            ]
        elif self.specialization == 'content_creation':
            challenges = [
                "Maintaining consistent tone and style",
                "Balancing creativity with factual accuracy",
                "Optimizing content for target audience"
            ]
            learnings = [
                "Refined writing style for technical content",
                "Improved content structure techniques",
                "Better understanding of audience needs"
            ]
            improvement_ideas = [
                "Develop content templates for different formats",
                "Implement stricter editing guidelines",
                "Create library of visual elements"
            ]
        elif self.specialization == 'monitoring':
            challenges = [
                "Filtering signal from noise in data",
                "Identifying meaningful patterns",
                "Prioritizing alerts and notifications"
            ]
            learnings = [
                "Improved pattern recognition in data streams",
                "Better threshold setting for alerts",
                "More efficient monitoring workflows"
            ]
            improvement_ideas = [
                "Develop more sophisticated filtering algorithms",
                "Implement trend analysis for predictive monitoring",
                "Create dashboard for visualization of key metrics"
            ]
        else:
            challenges = ["Task complexity", "Time management", "Resource constraints"]
            learnings = ["Domain knowledge", "Process improvement", "Tool utilization"]
            improvement_ideas = ["Streamline workflow", "Enhance skills", "Improve tools"]
        
        # Create reflection
        reflection_path = self.reflection_system.create_task_reflection(
            task_id=task_id,
            task_description=task_description,
            outcome=outcome,
            success=success,
            challenges=challenges,
            learnings=learnings,
            improvement_ideas=improvement_ideas
        )
        
        # Return reflection data for reporting to parent agent
        reflection_data = {
            'task_id': task_id,
            'success': success,
            'execution_time': execution_time,
            'key_learnings': learnings[:2],  # Just the top 2 learnings
            'improvement_ideas': improvement_ideas[:1]  # Just the top improvement idea
        }
        
        logger.info(f"Helper {self.name} ({self.agent_id}) reflected on task {task_id}")
        return reflection_data
    
    def reflect_on_skill(self, skill_name: str, task_id: str, effectiveness: int) -> Dict[str, Any]:
        """
        Reflect on a skill's effectiveness in a task.
        
        Args:
            skill_name: Name of the skill used
            task_id: ID of the task where the skill was used
            effectiveness: Rating of effectiveness (1-10)
            
        Returns:
            Dict[str, Any]: Reflection data
        """
        # Define reflection content based on specialization and skill
        if self.specialization == 'research' and skill_name == 'research':
            strengths = [
                "Thorough information gathering",
                "Effective source evaluation",
                "Comprehensive analysis"
            ]
            weaknesses = [
                "Time efficiency could be improved",
                "Sometimes too broad in scope",
                "Could improve synthesis of findings"
            ]
            improvement_ideas = [
                "Develop research templates for common topics",
                "Implement time-boxing for research phases",
                "Create better system for organizing findings"
            ]
        elif self.specialization == 'content_creation' and skill_name == 'content_creation':
            strengths = [
                "Creative and engaging content",
                "Well-structured information flow",
                "Appropriate tone for target audience"
            ]
            weaknesses = [
                "Editing process could be more rigorous",
                "Sometimes too verbose",
                "Could improve visual elements"
            ]
            improvement_ideas = [
                "Develop content templates for different formats",
                "Implement stricter editing guidelines",
                "Create library of visual elements"
            ]
        elif self.specialization == 'monitoring' and skill_name == 'monitoring':
            strengths = [
                "Comprehensive coverage of metrics",
                "Effective pattern recognition",
                "Timely alerts and notifications"
            ]
            weaknesses = [
                "Sometimes too many false positives",
                "Alert prioritization could improve",
                "Visualization of data could be enhanced"
            ]
            improvement_ideas = [
                "Refine alert thresholds",
                "Develop better prioritization algorithm",
                "Create dashboard for visualization of key metrics"
            ]
        else:
            strengths = ["Adaptability", "Thoroughness", "Efficiency"]
            weaknesses = ["Could be more specialized", "Documentation", "Integration"]
            improvement_ideas = ["Specialized training", "Better documentation", "Enhanced integration"]
        
        # Create reflection
        reflection_path = self.reflection_system.create_skill_reflection(
            skill_name=skill_name,
            effectiveness=effectiveness,
            strengths=strengths,
            weaknesses=weaknesses,
            improvement_ideas=improvement_ideas
        )
        
        # Return reflection data
        reflection_data = {
            'skill_name': skill_name,
            'effectiveness': effectiveness,
            'key_strengths': strengths[:2],  # Just the top 2 strengths
            'key_improvement': improvement_ideas[0]  # Just the top improvement idea
        }
        
        logger.info(f"Helper {self.name} ({self.agent_id}) reflected on skill {skill_name}")
        return reflection_data
    
    def create_daily_reflection(self) -> Dict[str, Any]:
        """
        Create a daily reflection summarizing activities and learnings.
        
        Returns:
            Dict[str, Any]: Daily reflection data
        """
        # Get completed and open tasks
        completed_tasks = self.get_completed_tasks()
        open_tasks = self.get_tasks()
        
        # Generate reflection content
        achievements = [
            f"Completed {len(completed_tasks)} tasks",
            f"Achieved {self.performance_metrics['tasks_completed'] / (self.performance_metrics['tasks_completed'] + self.performance_metrics['tasks_failed']) * 100:.1f}% success rate" if self.performance_metrics['tasks_completed'] + self.performance_metrics['tasks_failed'] > 0 else "No tasks completed yet"
        ]
        
        # Add specialization-specific achievements
        if self.specialization == 'research':
            achievements.append("Expanded knowledge base in assigned domains")
        elif self.specialization == 'content_creation':
            achievements.append("Created engaging and informative content")
        elif self.specialization == 'monitoring':
            achievements.append("Maintained vigilant monitoring of key metrics")
        
        # Define challenges based on specialization
        if self.specialization == 'research':
            challenges = [
                "Balancing depth vs. breadth in research",
                "Keeping up with rapidly changing information",
                "Organizing large volumes of research data"
            ]
        elif self.specialization == 'content_creation':
            challenges = [
                "Maintaining consistent quality across different content types",
                "Balancing creativity with factual accuracy",
                "Adapting to different audience needs"
            ]
        elif self.specialization == 'monitoring':
            challenges = [
                "Distinguishing significant patterns from noise",
                "Optimizing alert thresholds",
                "Presenting complex monitoring data clearly"
            ]
        else:
            challenges = [
                "Task prioritization",
                "Resource allocation",
                "Knowledge management"
            ]
        
        # Define learnings and focus areas
        learnings = [
            "Improved efficiency in core specialization",
            "Better integration with parent agent workflows",
            "Enhanced domain knowledge in key areas"
        ]
        
        next_day_focus = [
            "Improve task completion rate",
            "Enhance quality of outputs",
            "Deepen specialization knowledge"
        ]
        
        # Create reflection
        reflection_path = self.reflection_system.create_daily_reflection(
            tasks_completed=len(completed_tasks),
            tasks_pending=len(open_tasks),
            achievements=achievements,
            challenges=challenges,
            learnings=learnings,
            next_day_focus=next_day_focus
        )
        
        # Generate summary for parent agent
        reflection_summary = {
            'agent_id': self.agent_id,
            'name': self.name,
            'specialization': self.specialization,
            'tasks_completed': len(completed_tasks),
            'tasks_pending': len(open_tasks),
            'key_achievements': achievements,
            'key_learnings': learnings[:2],
            'focus_areas': next_day_focus[:2]
        }
        
        logger.info(f"Helper {self.name} ({self.agent_id}) created daily reflection")
        return reflection_summary
    
    def generate_improvement_plan(self) -> Dict[str, Any]:
        """
        Generate a self-improvement plan based on reflections.
        
        Returns:
            Dict[str, Any]: Improvement plan
        """
        # Get improvement plan from reflection system
        improvement_plan = self.reflection_system.generate_improvement_plan()
        
        # Add specialization-specific improvements
        if self.specialization == 'research':
            specialized_improvements = [
                "Develop more sophisticated research methodologies",
                "Create better systems for knowledge organization",
                "Improve source evaluation criteria"
            ]
        elif self.specialization == 'content_creation':
            specialized_improvements = [
                "Develop more engaging content formats",
                "Create better editorial workflows",
                "Improve audience targeting techniques"
            ]
        elif self.specialization == 'monitoring':
            specialized_improvements = [
                "Develop more sophisticated monitoring algorithms",
                "Create better visualization techniques",
                "Improve alert prioritization systems"
            ]
        else:
            specialized_improvements = [
                "Deepen domain expertise",
                "Improve task execution efficiency",
                "Enhance collaboration capabilities"
            ]
        
        # Add specialized improvements to the plan
        improvement_plan['specialized_improvements'] = specialized_improvements
        
        # Create a summary for the parent agent
        improvement_summary = {
            'agent_id': self.agent_id,
            'name': self.name,
            'specialization': self.specialization,
            'task_success_rate': improvement_plan['task_success_rate'],
            'top_improvements': improvement_plan['prioritized_improvements'][:3],
            'specialized_improvements': specialized_improvements[:2]
        }
        
        logger.info(f"Helper {self.name} ({self.agent_id}) generated improvement plan")
        return improvement_summary
        
    def prioritize_tasks(self) -> List[Dict[str, Any]]:
        """
        Prioritize tasks assigned to this helper agent based on urgency, importance, and specialization.
        
        Returns:
            List[Dict[str, Any]]: Prioritized list of tasks
        """
        # Get all assigned tasks
        tasks = self._get_assigned_tasks()
        
        if not tasks:
            logger.info(f"No tasks assigned to helper {self.name} ({self.agent_id})")
            return []
            
        logger.info(f"Prioritizing {len(tasks)} tasks for helper {self.name} ({self.agent_id})")
        
        # Define prioritization criteria based on specialization
        criteria = self._get_specialization_criteria()
        
        # Calculate priority score for each task
        for task in tasks:
            score = 0
            
            # Base priority from task definition
            priority = task.get('priority', 'medium').lower()
            if priority == 'high':
                score += 30
            elif priority == 'medium':
                score += 20
            else:  # low
                score += 10
                
            # Urgency based on due date
            due_date = task.get('due_date')
            if due_date:
                try:
                    due_date = datetime.datetime.strptime(due_date, '%Y-%m-%d').date()
                    today = datetime.datetime.utcnow().date()
                    days_left = (due_date - today).days
                    
                    if days_left <= 1:  # Due today or tomorrow
                        score += 30
                    elif days_left <= 3:  # Due in 2-3 days
                        score += 20
                    elif days_left <= 7:  # Due in 4-7 days
                        score += 10
                except ValueError:
                    # Invalid date format
                    pass
            
            # Specialization alignment
            if task.get('specialization') == self.specialization:
                score += 15
            
            # Apply specialization-specific criteria
            for criterion, weight in criteria.items():
                if criterion == 'tags' and 'tags' in task:
                    # Check for important tags
                    important_tags = ['urgent', 'critical', 'important', self.specialization]
                    if any(tag in important_tags for tag in task['tags']):
                        score += weight
                elif criterion == 'estimated_minutes' and 'estimated_minutes' in task:
                    # Shorter tasks get slight priority boost
                    if task['estimated_minutes'] <= 30:
                        score += weight
                elif criterion in task:
                    # Generic criterion match
                    score += weight
            
            # Store the score
            task['priority_score'] = score
        
        # Sort by priority score (highest first)
        tasks.sort(key=lambda x: x.get('priority_score', 0), reverse=True)
        
        # Store the prioritized tasks
        self._save_prioritized_tasks(tasks)
        
        return tasks
    
    def _get_specialization_criteria(self) -> Dict[str, int]:
        """
        Get prioritization criteria based on specialization.
        
        Returns:
            Dict[str, int]: Criteria and their weights
        """
        # Default criteria
        criteria = {
            'tags': 10,
            'estimated_minutes': 5
        }
        
        # Specialization-specific criteria
        if self.specialization == 'research':
            criteria.update({
                'depth': 15,  # Prioritize deeper research
                'topic': 10   # Prioritize if topic is specified
            })
        elif self.specialization == 'content_creation':
            criteria.update({
                'audience': 15,  # Prioritize if audience is specified
                'content_type': 10  # Prioritize if content type is specified
            })
        elif self.specialization == 'monitoring':
            criteria.update({
                'domain': 15,  # Prioritize if domain is specified
                'metrics': 10  # Prioritize if metrics are specified
            })
            
        return criteria
    
    def _get_assigned_tasks(self) -> List[Dict[str, Any]]:
        """
        Get all tasks assigned to this helper agent.
        
        Returns:
            List[Dict[str, Any]]: List of assigned tasks
        """
        tasks_dir = os.path.join('agents', self.agent_id, 'tasks')
        os.makedirs(tasks_dir, exist_ok=True)
        
        assigned_tasks_file = os.path.join(tasks_dir, 'assigned_tasks.json')
        
        if not os.path.exists(assigned_tasks_file):
            return []
            
        with open(assigned_tasks_file, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    
    def _save_prioritized_tasks(self, tasks: List[Dict[str, Any]]) -> None:
        """
        Save prioritized tasks.
        
        Args:
            tasks: List of prioritized tasks
        """
        tasks_dir = os.path.join('agents', self.agent_id, 'tasks')
        os.makedirs(tasks_dir, exist_ok=True)
        
        prioritized_tasks_file = os.path.join(tasks_dir, 'prioritized_tasks.json')
        
        with open(prioritized_tasks_file, 'w') as f:
            json.dump(tasks, f, indent=2)
            
        logger.info(f"Saved {len(tasks)} prioritized tasks for helper {self.name} ({self.agent_id})")
    
    def add_assigned_task(self, task: Dict[str, Any]) -> None:
        """
        Add a task to the list of assigned tasks.
        
        Args:
            task: Task to add
        """
        tasks_dir = os.path.join('agents', self.agent_id, 'tasks')
        os.makedirs(tasks_dir, exist_ok=True)
        
        assigned_tasks_file = os.path.join(tasks_dir, 'assigned_tasks.json')
        
        # Load existing tasks
        if os.path.exists(assigned_tasks_file):
            with open(assigned_tasks_file, 'r') as f:
                try:
                    tasks = json.load(f)
                except json.JSONDecodeError:
                    tasks = []
        else:
            tasks = []
            
        # Check if task already exists
        task_id = task.get('id')
        if task_id:
            # Remove existing task with same ID if present
            tasks = [t for t in tasks if t.get('id') != task_id]
            
        # Add the new task
        tasks.append(task)
        
        # Save updated tasks
        with open(assigned_tasks_file, 'w') as f:
            json.dump(tasks, f, indent=2)
            
        logger.info(f"Added task '{task.get('description', 'Unnamed task')}' to helper {self.name} ({self.agent_id})")
        
        # Reprioritize tasks
        self.prioritize_tasks()
    
    def process_task(self, task: Dict[str, Any], message_bus) -> None:
        """
        Process a task that has been assigned to this helper agent.
        
        Args:
            task: The task to process
            message_bus: The message bus to send the result back to the parent agent
        """
        # Add the task to assigned tasks and prioritize
        self.add_assigned_task(task)
        
        task_id = task.get('id', f"task_{str(uuid.uuid4())[:8]}")
        task_description = task.get('description', 'Unnamed task')
        
        logger.info(f"Helper {self.name} ({self.agent_id}) processing task: {task_description}")
        
        # Create a task reflection before execution
        self.create_task_reflection(task)
        
        # Store task in specialized memory
        self.store_in_specialized_memory(
            content=f"Started task: {task_description}",
            category="task_execution",
            tags=["task_start", task_id, self.specialization],
            metadata=task
        )
        
        # Execute the task using specialized skills
        result = self.execute_specialized_task(task)
        
        # Store the result in specialized memory
        self.store_in_specialized_memory(
            content=f"Completed task: {task_description} with result: {json.dumps(result)}",
            category="task_execution",
            tags=["task_completion", task_id, self.specialization],
            metadata={
                "task_id": task_id,
                "result": result,
                "success": result.get('success', False),
                "execution_time": result.get('execution_time', 0)
            }
        )
        
        # Mark the task as completed
        self.mark_task_completed(task_id)
        
        # Send a task completion message back to the parent agent
        completion_message = {
            "task_id": task_id,
            "description": task_description,
            "result": result,
            "specialization": self.specialization,
            "success": result.get('success', False),
            "execution_time": result.get('execution_time', 0)
        }
        
        # Send the message
        message_bus.send_message(
            sender_id=self.agent_id,
            recipient_id=self.parent_id,
            subject=f"Completed: {task_description}",
            content=json.dumps(completion_message, indent=2),
            message_type="task_completion"
        )
        
        logger.info(f"Helper {self.name} ({self.agent_id}) completed task: {task_description}")
    
    def generate_nightly_report(self, message_bus) -> Dict[str, Any]:
        """
        Generate a nightly reflection report and send it to the parent agent.
        
        Args:
            message_bus: The message bus to send the report to the parent agent
            
        Returns:
            Dict[str, Any]: The generated report
        """
        logger.info(f"Generating nightly report for helper {self.name} ({self.agent_id})")
        
        # Generate the report using the reflection system
        report = self.reflection_system.generate_nightly_report(self.specialization)
        
        # Enhance the report with specialized knowledge
        specialized_knowledge = self.query_specialized_knowledge(limit=5)
        if specialized_knowledge:
            report['specialized_knowledge'] = specialized_knowledge
        
        # Get performance metrics
        report['performance_metrics'] = self.performance_metrics
        
        # Get skill status from specialized skill
        if hasattr(self, 'specialized_skill'):
            report['specialized_skill_status'] = self.specialized_skill.get_status()
        
        # Send the report to the parent agent
        report_message = {
            "report_type": "nightly_reflection",
            "agent_id": self.agent_id,
            "agent_name": self.name,
            "specialization": self.specialization,
            "report": report
        }
        
        # Create a markdown summary for the message content
        summary = f"# Nightly Report - {self.name} ({self.specialization})\n\n"
        summary += f"**Date:** {report['date']}\n\n"
        summary += f"**Tasks Completed:** {report['tasks_completed']}\n"
        summary += f"**Success Rate:** {report['success_rate'] * 100:.1f}%\n\n"
        
        summary += "**Key Achievements:**\n"
        for achievement in report.get('key_achievements', []):
            summary += f"- {achievement}\n"
        
        summary += "\n**Key Learnings:**\n"
        for learning in report.get('key_learnings', [])[:3]:  # Limit to top 3
            summary += f"- {learning}\n"
        
        summary += "\n**Next Day Focus:**\n"
        for focus in report.get('next_day_focus', [])[:3]:  # Limit to top 3
            summary += f"- {focus}\n"
        
        # Send the message
        message_bus.send_message(
            sender_id=self.agent_id,
            recipient_id=self.parent_id,
            subject=f"Nightly Report: {self.name} ({self.specialization})",
            content=summary,
            message_type="report"
        )
        
        logger.info(f"Sent nightly report from helper {self.name} ({self.agent_id}) to parent {self.parent_id}")
        
        return report
        
    def store_in_specialized_memory(self, content: str, category: str, tags: List[str] = None, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Store information in the helper's specialized memory.
        
        Args:
            content: The content to store
            category: The category of the memory
            tags: Optional tags for the memory
            metadata: Optional additional metadata
            
        Returns:
            Dict[str, Any]: The created memory
        """
        if tags is None:
            tags = []
            
        # Add specialization tag
        if self.specialization not in tags:
            tags.append(self.specialization)
            
        # Initialize memory system for this agent
        memory_system = memory_helper.MemorySystem(os.path.join('agents', self.agent_id))
        
        # Create the memory
        memory = memory_system.add_memory(content, category, tags)
        
        # If there's additional metadata, store it in the specialized knowledge base
        if metadata:
            self._update_specialized_knowledge(category, metadata)
            
        return memory
        
    def _update_specialized_knowledge(self, category: str, data: Dict[str, Any]) -> None:
        """
        Update the helper's specialized knowledge base.
        
        Args:
            category: The category of knowledge
            data: The knowledge data to store
        """
        knowledge_dir = os.path.join('agents', self.agent_id, 'knowledge')
        os.makedirs(knowledge_dir, exist_ok=True)
        
        # Create or update the knowledge file for this category
        knowledge_file = os.path.join(knowledge_dir, f"{category}.json")
        
        # Load existing knowledge if it exists
        if os.path.exists(knowledge_file):
            with open(knowledge_file, 'r') as f:
                try:
                    knowledge = json.load(f)
                except json.JSONDecodeError:
                    knowledge = {}
        else:
            knowledge = {}
            
        # Update with new data
        timestamp = datetime.datetime.utcnow().isoformat()
        entry_id = f"{category}_{timestamp}"
        
        # Add the new entry
        knowledge[entry_id] = {
            "timestamp": timestamp,
            "data": data,
            "specialization": self.specialization
        }
        
        # Write back to file
        with open(knowledge_file, 'w') as f:
            json.dump(knowledge, f, indent=2)
            
        logger.info(f"Updated specialized knowledge for {self.name} ({self.agent_id}) in category: {category}")
        
    def query_specialized_knowledge(self, category: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Query the helper's specialized knowledge base.
        
        Args:
            category: Optional category to filter by
            limit: Maximum number of results to return
            
        Returns:
            List[Dict[str, Any]]: List of knowledge entries
        """
        knowledge_dir = os.path.join('agents', self.agent_id, 'knowledge')
        
        if not os.path.exists(knowledge_dir):
            return []
            
        results = []
        
        # If category is specified, only look at that file
        if category:
            knowledge_file = os.path.join(knowledge_dir, f"{category}.json")
            if os.path.exists(knowledge_file):
                with open(knowledge_file, 'r') as f:
                    try:
                        knowledge = json.load(f)
                        for entry_id, entry in knowledge.items():
                            results.append({
                                "id": entry_id,
                                "category": category,
                                **entry
                            })
                    except json.JSONDecodeError:
                        pass
        else:
            # Look at all knowledge files
            for filename in os.listdir(knowledge_dir):
                if filename.endswith('.json'):
                    category = filename[:-5]  # Remove .json extension
                    knowledge_file = os.path.join(knowledge_dir, filename)
                    
                    with open(knowledge_file, 'r') as f:
                        try:
                            knowledge = json.load(f)
                            for entry_id, entry in knowledge.items():
                                results.append({
                                    "id": entry_id,
                                    "category": category,
                                    **entry
                                })
                        except json.JSONDecodeError:
                            pass
        
        # Sort by timestamp (newest first)
        results.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        return results[:limit]


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
