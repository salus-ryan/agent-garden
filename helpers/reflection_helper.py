"""
Reflection Helper Module for the Agent Garden

This module provides utilities for agent reflection and self-improvement.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ReflectionSystem:
    """Class for managing agent reflections."""
    
    def __init__(self, agent_id: str):
        """
        Initialize the reflection system for an agent.
        
        Args:
            agent_id: ID of the agent
        """
        self.agent_id = agent_id
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.agent_dir = os.path.join(self.base_dir, 'agents', agent_id)
        self.reflections_dir = os.path.join(self.agent_dir, 'reflections')
        
        # Create reflections directory if it doesn't exist
        os.makedirs(self.reflections_dir, exist_ok=True)
    
    def create_reflection(self, reflection_type: str, content: Dict[str, Any]) -> str:
        """
        Create a new reflection.
        
        Args:
            reflection_type: Type of reflection (e.g., 'task', 'daily', 'skill')
            content: Dictionary containing reflection content
            
        Returns:
            str: Path to the saved reflection file
        """
        timestamp = datetime.utcnow()
        date_str = timestamp.strftime("%Y-%m-%d")
        time_str = timestamp.strftime("%H%M%S")
        
        # Create a structured reflection with metadata
        reflection = {
            'type': reflection_type,
            'timestamp': timestamp.isoformat(),
            'agent_id': self.agent_id,
            'content': content
        }
        
        # Save the reflection
        filename = f"{date_str}_{reflection_type}_{time_str}.json"
        reflection_path = os.path.join(self.reflections_dir, filename)
        
        with open(reflection_path, 'w') as f:
            json.dump(reflection, f, indent=2)
        
        logger.info(f"Created {reflection_type} reflection for agent {self.agent_id}")
        return reflection_path
    
    def create_task_reflection(self, task_id: str, task_description: str, 
                              outcome: str, success: bool, 
                              challenges: List[str], learnings: List[str],
                              improvement_ideas: List[str]) -> str:
        """
        Create a reflection on a completed task.
        
        Args:
            task_id: ID of the task
            task_description: Description of the task
            outcome: Outcome of the task
            success: Whether the task was successful
            challenges: List of challenges encountered
            learnings: List of things learned
            improvement_ideas: List of ideas for improvement
            
        Returns:
            str: Path to the saved reflection file
        """
        content = {
            'task_id': task_id,
            'task_description': task_description,
            'outcome': outcome,
            'success': success,
            'challenges': challenges,
            'learnings': learnings,
            'improvement_ideas': improvement_ideas
        }
        
        return self.create_reflection('task', content)
    
    def create_skill_reflection(self, skill_name: str, effectiveness: int,
                               strengths: List[str], weaknesses: List[str],
                               improvement_ideas: List[str]) -> str:
        """
        Create a reflection on a skill's effectiveness.
        
        Args:
            skill_name: Name of the skill
            effectiveness: Rating of effectiveness (1-10)
            strengths: List of strengths in using this skill
            weaknesses: List of weaknesses in using this skill
            improvement_ideas: List of ideas for improving this skill
            
        Returns:
            str: Path to the saved reflection file
        """
        content = {
            'skill_name': skill_name,
            'effectiveness': effectiveness,
            'strengths': strengths,
            'weaknesses': weaknesses,
            'improvement_ideas': improvement_ideas
        }
        
        return self.create_reflection('skill', content)
    
    def create_daily_reflection(self, tasks_completed: int, tasks_pending: int,
                               achievements: List[str], challenges: List[str],
                               learnings: List[str], next_day_focus: List[str]) -> str:
        """
        Create a daily reflection.
        
        Args:
            tasks_completed: Number of tasks completed
            tasks_pending: Number of tasks still pending
            achievements: List of achievements for the day
            challenges: List of challenges encountered
            learnings: List of things learned
            next_day_focus: List of focus areas for the next day
            
        Returns:
            str: Path to the saved reflection file
        """
        content = {
            'tasks_completed': tasks_completed,
            'tasks_pending': tasks_pending,
            'achievements': achievements,
            'challenges': challenges,
            'learnings': learnings,
            'next_day_focus': next_day_focus
        }
        
        return self.create_reflection('daily', content)
    
    def get_reflections(self, reflection_type: Optional[str] = None, 
                       limit: int = 10, skip: int = 0) -> List[Dict[str, Any]]:
        """
        Get reflections for this agent.
        
        Args:
            reflection_type: Optional type of reflections to retrieve
            limit: Maximum number of reflections to return
            skip: Number of reflections to skip (for pagination)
            
        Returns:
            List[Dict[str, Any]]: List of reflection dictionaries
        """
        reflections = []
        
        for filename in os.listdir(self.reflections_dir):
            if not filename.endswith('.json'):
                continue
                
            # Skip non-matching reflection types if specified
            if reflection_type and not filename.split('_')[1] == reflection_type:
                continue
                
            reflection_path = os.path.join(self.reflections_dir, filename)
            
            with open(reflection_path, 'r') as f:
                reflection = json.load(f)
                reflections.append(reflection)
        
        # Sort by timestamp (newest first)
        reflections.sort(key=lambda r: r['timestamp'], reverse=True)
        
        # Apply pagination
        return reflections[skip:skip+limit]
    
    def get_task_reflections(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get task reflections for this agent.
        
        Args:
            limit: Maximum number of reflections to return
            
        Returns:
            List[Dict[str, Any]]: List of task reflection dictionaries
        """
        return self.get_reflections('task', limit)
    
    def get_skill_reflections(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get skill reflections for this agent.
        
        Args:
            limit: Maximum number of reflections to return
            
        Returns:
            List[Dict[str, Any]]: List of skill reflection dictionaries
        """
        return self.get_reflections('skill', limit)
    
    def get_daily_reflections(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get daily reflections for this agent.
        
        Args:
            limit: Maximum number of reflections to return
            
        Returns:
            List[Dict[str, Any]]: List of daily reflection dictionaries
        """
        return self.get_reflections('daily', limit)
    
    def analyze_task_performance(self) -> Dict[str, Any]:
        """
        Analyze task performance based on reflections.
        
        Returns:
            Dict[str, Any]: Analysis of task performance
        """
        task_reflections = self.get_task_reflections(limit=50)
        
        if not task_reflections:
            return {
                'total_tasks': 0,
                'success_rate': 0,
                'common_challenges': [],
                'key_learnings': [],
                'improvement_areas': []
            }
        
        # Calculate success rate
        total_tasks = len(task_reflections)
        successful_tasks = sum(1 for r in task_reflections if r['content']['success'])
        success_rate = (successful_tasks / total_tasks) * 100 if total_tasks > 0 else 0
        
        # Aggregate challenges, learnings, and improvement ideas
        all_challenges = []
        all_learnings = []
        all_improvements = []
        
        for reflection in task_reflections:
            all_challenges.extend(reflection['content']['challenges'])
            all_learnings.extend(reflection['content']['learnings'])
            all_improvements.extend(reflection['content']['improvement_ideas'])
        
        # Count occurrences
        challenge_counts = {}
        learning_counts = {}
        improvement_counts = {}
        
        for challenge in all_challenges:
            challenge_counts[challenge] = challenge_counts.get(challenge, 0) + 1
            
        for learning in all_learnings:
            learning_counts[learning] = learning_counts.get(learning, 0) + 1
            
        for improvement in all_improvements:
            improvement_counts[improvement] = improvement_counts.get(improvement, 0) + 1
        
        # Get most common items
        common_challenges = sorted(challenge_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        key_learnings = sorted(learning_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        improvement_areas = sorted(improvement_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'total_tasks': total_tasks,
            'success_rate': success_rate,
            'common_challenges': [c[0] for c in common_challenges],
            'key_learnings': [l[0] for l in key_learnings],
            'improvement_areas': [i[0] for i in improvement_areas]
        }
    
    def analyze_skill_effectiveness(self) -> Dict[str, Dict[str, Any]]:
        """
        Analyze skill effectiveness based on reflections.
        
        Returns:
            Dict[str, Dict[str, Any]]: Analysis of skill effectiveness by skill name
        """
        skill_reflections = self.get_skill_reflections(limit=50)
        skill_analysis = {}
        
        for reflection in skill_reflections:
            content = reflection['content']
            skill_name = content['skill_name']
            
            if skill_name not in skill_analysis:
                skill_analysis[skill_name] = {
                    'effectiveness_ratings': [],
                    'strengths': [],
                    'weaknesses': [],
                    'improvement_ideas': []
                }
            
            skill_analysis[skill_name]['effectiveness_ratings'].append(content['effectiveness'])
            skill_analysis[skill_name]['strengths'].extend(content['strengths'])
            skill_analysis[skill_name]['weaknesses'].extend(content['weaknesses'])
            skill_analysis[skill_name]['improvement_ideas'].extend(content['improvement_ideas'])
        
        # Calculate averages and find most common items
        for skill_name, data in skill_analysis.items():
            ratings = data['effectiveness_ratings']
            avg_rating = sum(ratings) / len(ratings) if ratings else 0
            
            # Count occurrences
            strength_counts = {}
            weakness_counts = {}
            improvement_counts = {}
            
            for strength in data['strengths']:
                strength_counts[strength] = strength_counts.get(strength, 0) + 1
                
            for weakness in data['weaknesses']:
                weakness_counts[weakness] = weakness_counts.get(weakness, 0) + 1
                
            for improvement in data['improvement_ideas']:
                improvement_counts[improvement] = improvement_counts.get(improvement, 0) + 1
            
            # Get most common items
            common_strengths = sorted(strength_counts.items(), key=lambda x: x[1], reverse=True)[:3]
            common_weaknesses = sorted(weakness_counts.items(), key=lambda x: x[1], reverse=True)[:3]
            common_improvements = sorted(improvement_counts.items(), key=lambda x: x[1], reverse=True)[:3]
            
            skill_analysis[skill_name] = {
                'average_effectiveness': avg_rating,
                'common_strengths': [s[0] for s in common_strengths],
                'common_weaknesses': [w[0] for w in common_weaknesses],
                'common_improvement_ideas': [i[0] for i in common_improvements]
            }
        
        return skill_analysis
    
    def generate_improvement_plan(self) -> Dict[str, Any]:
        """
        Generate an improvement plan based on reflections.
        
        Returns:
            Dict[str, Any]: Improvement plan
        """
        task_analysis = self.analyze_task_performance()
        skill_analysis = self.analyze_skill_effectiveness()
        
        # Identify areas for improvement
        improvement_areas = []
        
        # Add task-based improvements
        improvement_areas.extend(task_analysis['improvement_areas'])
        
        # Add skill-based improvements
        for skill_name, data in skill_analysis.items():
            if data['average_effectiveness'] < 7:  # Threshold for improvement
                for idea in data['common_improvement_ideas']:
                    improvement_areas.append(f"Improve {skill_name}: {idea}")
        
        # Prioritize improvements (simple approach - could be more sophisticated)
        prioritized_improvements = improvement_areas[:5]  # Top 5 improvements
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'agent_id': self.agent_id,
            'task_success_rate': task_analysis['success_rate'],
            'skill_effectiveness': {k: v['average_effectiveness'] for k, v in skill_analysis.items()},
            'prioritized_improvements': prioritized_improvements,
            'implementation_steps': [f"Implement {improvement}" for improvement in prioritized_improvements]
        }
        
    def generate_nightly_report(self, specialization: str = None) -> Dict[str, Any]:
        """
        Generate a comprehensive nightly report for the agent.
        
        Args:
            specialization: Optional specialization of the agent
            
        Returns:
            Dict[str, Any]: Nightly report data
        """
        # Get today's date
        today = datetime.utcnow().strftime("%Y-%m-%d")
        
        # Get task reflections from today
        task_reflections = []
        for reflection in self.get_reflections('task', limit=50):
            if reflection['timestamp'].startswith(today):
                task_reflections.append(reflection)
        
        # Calculate task statistics
        tasks_completed = len(task_reflections)
        successful_tasks = sum(1 for r in task_reflections if r['content']['success'])
        success_rate = successful_tasks / tasks_completed if tasks_completed > 0 else 0
        
        # Collect learnings and challenges
        all_learnings = []
        all_challenges = []
        all_improvements = []
        
        for reflection in task_reflections:
            content = reflection['content']
            all_learnings.extend(content.get('learnings', []))
            all_challenges.extend(content.get('challenges', []))
            all_improvements.extend(content.get('improvement_ideas', []))
        
        # Get skill analysis
        skill_analysis = self.analyze_skill_effectiveness()
        
        # Generate improvement plan
        improvement_plan = self.generate_improvement_plan()
        
        # Create the report
        report = {
            'date': today,
            'agent_id': self.agent_id,
            'specialization': specialization,
            'tasks_completed': tasks_completed,
            'success_rate': success_rate,
            'key_achievements': self._extract_key_points(all_learnings, 3),
            'key_challenges': self._extract_key_points(all_challenges, 3),
            'key_learnings': self._extract_key_points(all_learnings, 5),
            'improvement_ideas': self._extract_key_points(all_improvements, 3),
            'skill_effectiveness': {k: v['average_effectiveness'] for k, v in skill_analysis.items()},
            'improvement_plan': improvement_plan['prioritized_improvements'],
            'next_day_focus': self._generate_next_day_focus(improvement_plan, specialization)
        }
        
        # Save the report
        report_path = os.path.join(self.reflections_dir, f"{today}_nightly_report.json")
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Also create a markdown version for human readability
        markdown_report = self._generate_markdown_report(report)
        markdown_path = os.path.join(self.reflections_dir, f"{today}_nightly_report.md")
        with open(markdown_path, 'w') as f:
            f.write(markdown_report)
        
        logger.info(f"Generated nightly report for agent {self.agent_id}")
        return report
    
    def _extract_key_points(self, items: List[str], count: int = 3) -> List[str]:
        """
        Extract key points from a list of items based on frequency.
        
        Args:
            items: List of items
            count: Number of key points to extract
            
        Returns:
            List[str]: Key points
        """
        if not items:
            return []
            
        # Count occurrences
        item_counts = {}
        for item in items:
            item_counts[item] = item_counts.get(item, 0) + 1
            
        # Get most common items
        common_items = sorted(item_counts.items(), key=lambda x: x[1], reverse=True)[:count]
        return [item[0] for item in common_items]
    
    def _generate_next_day_focus(self, improvement_plan: Dict[str, Any], specialization: str = None) -> List[str]:
        """
        Generate focus areas for the next day based on the improvement plan and specialization.
        
        Args:
            improvement_plan: Improvement plan dictionary
            specialization: Optional specialization of the agent
            
        Returns:
            List[str]: Next day focus areas
        """
        focus_areas = []
        
        # Add top 2 improvement areas
        if 'prioritized_improvements' in improvement_plan and improvement_plan['prioritized_improvements']:
            focus_areas.extend(improvement_plan['prioritized_improvements'][:2])
        
        # Add specialization-specific focus
        if specialization == 'research':
            focus_areas.append("Deepen research methodology and source evaluation")
        elif specialization == 'content_creation':
            focus_areas.append("Improve content structure and engagement techniques")
        elif specialization == 'monitoring':
            focus_areas.append("Enhance pattern recognition and anomaly detection")
        else:
            focus_areas.append("Develop core skills and knowledge base")
        
        # Add general improvement focus
        focus_areas.append("Optimize task execution efficiency")
        
        return focus_areas
    
    def _generate_markdown_report(self, report: Dict[str, Any]) -> str:
        """
        Generate a markdown version of the nightly report.
        
        Args:
            report: Report dictionary
            
        Returns:
            str: Markdown report
        """
        specialization = report.get('specialization', 'General')
        date = report.get('date', datetime.utcnow().strftime("%Y-%m-%d"))
        
        markdown = f"# Nightly Report - {specialization} Agent\n\n"
        markdown += f"**Date:** {date}\n\n"
        markdown += f"**Agent ID:** {report['agent_id']}\n\n"
        
        markdown += f"## Performance Summary\n\n"
        markdown += f"- **Tasks Completed:** {report['tasks_completed']}\n"
        markdown += f"- **Success Rate:** {report['success_rate'] * 100:.1f}%\n\n"
        
        markdown += f"## Key Achievements\n\n"
        for achievement in report.get('key_achievements', []):
            markdown += f"- {achievement}\n"
        markdown += "\n"
        
        markdown += f"## Key Challenges\n\n"
        for challenge in report.get('key_challenges', []):
            markdown += f"- {challenge}\n"
        markdown += "\n"
        
        markdown += f"## Key Learnings\n\n"
        for learning in report.get('key_learnings', []):
            markdown += f"- {learning}\n"
        markdown += "\n"
        
        markdown += f"## Skill Effectiveness\n\n"
        for skill, effectiveness in report.get('skill_effectiveness', {}).items():
            markdown += f"- **{skill}:** {effectiveness:.1f}/10\n"
        markdown += "\n"
        
        markdown += f"## Improvement Plan\n\n"
        for improvement in report.get('improvement_plan', []):
            markdown += f"- {improvement}\n"
        markdown += "\n"
        
        markdown += f"## Next Day Focus\n\n"
        for focus in report.get('next_day_focus', []):
            markdown += f"- {focus}\n"
        
        return markdown
