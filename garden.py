import os
import sys
import json
import time
import random
import argparse
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("garden.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("agent_garden")

from helpers import email_helper, memory_helper, backup_helper, task_prioritizer
from helpers import agent_framework, agent_communication
from skills import skill_registry
from perception import PerceptionManager, NewsSource, ApiSource

# Default paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.join(BASE_DIR, 'config')
AGENTS_DIR = os.path.join(BASE_DIR, 'agents')
MAIN_AGENT_ID = "agent_001"  # Aurora's ID
AGENT_DIR = os.path.join(AGENTS_DIR, MAIN_AGENT_ID)
BACKUP_DIR = os.path.join(BASE_DIR, 'backups')

def load_agent_config():
    with open(os.path.join(AGENT_DIR, "agent_config.json")) as f:
        return json.load(f)

def load_tasks():
    """Load tasks from the task file."""
    task_prioritizer = TaskPrioritizer(AGENT_DIR)
    return task_prioritizer.load_tasks()

def save_reflection(reflection: str) -> None:
    """Save the daily reflection to a file."""
    today = datetime.utcnow().strftime("%Y-%m-%d")
    reflection_dir = os.path.join('agents', MAIN_AGENT_ID, "reflections")
    os.makedirs(reflection_dir, exist_ok=True)
    
    reflection_file = os.path.join(reflection_dir, f"{today}_reflection.md")
    
    with open(reflection_file, 'w') as f:
        f.write(reflection)
    
    print(f"Saved reflection to {reflection_file}")

def send_email_report(config: Dict[str, Any], reflection: str) -> None:
    """Send the daily reflection as an email report."""
    # Get recipient from environment variable or fall back to config
    recipient = os.getenv("RECIPIENT_EMAIL") or "admin@example.com"
    
    # Send email
    email_helper.send_email(
        recipient=recipient,
        subject=f"Agent Garden Daily Report - {datetime.utcnow().date()}",
        body=reflection
    )
    
    print(f"Email sent to {recipient}")

def determine_phase(config):
    """Determine if it's day or night phase based on current time and config."""
    current_hour = datetime.utcnow().hour
    day_start = config.get("pulse_settings", {}).get("day_phase_start_hour", 8)
    night_start = config.get("pulse_settings", {}).get("night_phase_start_hour", 20)
    
    if day_start <= current_hour < night_start:
        return "day"
    else:
        return "night"

def execute_task_with_skill(task, memory_system):
    """Execute a task using the appropriate skill."""
    # Find the appropriate skill for the task
    skill = skill_registry.find_skill_for_task(task)
    
    if not skill:
        raise Exception(f"No suitable skill found for task: {task['description']}")
    
    print(f"Using skill '{skill.name}' to execute task: {task['description']}")
    
    # Execute the task with the skill
    result = skill.execute(task)
    
    if not result.get("success", False):
        raise Exception(f"Skill execution failed: {result.get('error', 'Unknown error')}")
    
    # Mark the task as completed
    task_prioritizer = TaskPrioritizer(AGENT_DIR)
    task_prioritizer.complete_task(task["id"], result)
    
    # Return the result
    return result

def prioritize_tasks(memory_system):
    """Prioritize tasks based on urgency and importance."""
    print("📌 Prioritizing tasks...")
    
    # Initialize task prioritizer
    task_prioritizer = TaskPrioritizer(AGENT_DIR)
    
    # Prioritize tasks
    prioritized_tasks = task_prioritizer.prioritize_tasks()
    
    # Generate a daily plan
    daily_plan = task_prioritizer.generate_daily_plan()
    
    # Log the prioritization
    plan_summary = f"Prioritized {len(prioritized_tasks)} tasks: "
    plan_summary += f"{len(daily_plan['high_priority_tasks'])} high, "
    plan_summary += f"{len(daily_plan['medium_priority_tasks'])} medium, "
    plan_summary += f"{len(daily_plan['low_priority_tasks'])} low priority. "
    plan_summary += f"Estimated completion time: {daily_plan['estimated_completion_time']}"
    
    print(plan_summary)
    
    # Store the plan in memory
    memory_system.add_memory(
        content=plan_summary,
        category="task_prioritization",
        tags=["planning", "prioritization", "daily_plan"]
    )
    
    # Store the full plan in memory
    memory_system.add_memory(
        content=json.dumps(daily_plan, indent=2),
        category="daily_plan",
        tags=["planning", "prioritization", "daily_plan"]
    )
    
    return prioritized_tasks

def day_phase(config, memory_system):
    """Execute the day phase of the pulse."""
    print("🌞 Starting DAY phase...")
    
    # Prioritize tasks
    tasks = prioritize_tasks(memory_system)
    
    completed_tasks = []
    failed_tasks = []
    task_results = []
    
    # Execute tasks
    for task in tasks:
        try:
            print(f"Executing task: {task['description']}")
            
            # Execute the task using the skill module system
            result = execute_task_with_skill(task, memory_system)
            
            # Add the result to the task
            task_with_result = task.copy()
            task_with_result["result"] = result
            
            completed_tasks.append(task_with_result)
            task_results.append(result)
            
            # Record success in memory
            memory_system.add_memory(
                content=f"Successfully completed task: {task['description']}",
                category="task_completion",
                tags=["success", "day_phase", task.get("skill_required", "unknown_skill")]
            )
            
            # Record detailed result in memory
            memory_system.add_memory(
                content=json.dumps(result, indent=2),
                category="task_result",
                tags=["result", "day_phase", task.get("skill_required", "unknown_skill")]
            )
                
        except Exception as e:
            print(f"Failed task: {task['description']} | Error: {e}")
            failed_tasks.append(task)
            memory_system.add_memory(
                content=f"Failed to complete task: {task['description']}. Error: {str(e)}",
                category="task_failure",
                tags=["failure", "day_phase"]
            )
    
    # Return results for the night phase
    return {
        "completed_tasks": completed_tasks,
        "failed_tasks": failed_tasks,
        "task_results": task_results
    }

def generate_improvement_suggestions(day_results, memory_system):
    """Generate improvement suggestions based on task results and memories."""
    completed_tasks = day_results.get("completed_tasks", [])
    failed_tasks = day_results.get("failed_tasks", [])
    task_results = day_results.get("task_results", [])
    
    # Get task prioritization memories
    prioritization_memories = memory_system.query_memories(
        category="task_prioritization",
        limit=5
    )
    
    suggestions = []
    
    # Analyze failed tasks
    if failed_tasks:
        suggestions.append("Improve error handling for failed tasks")
        
        # Check for patterns in failed tasks
        failed_skills = [task.get("skill_required", "unknown") for task in failed_tasks]
        if len(set(failed_skills)) < len(failed_skills):
            # There are duplicate skills in failed tasks
            for skill in set(failed_skills):
                if failed_skills.count(skill) > 1:
                    suggestions.append(f"Review and enhance the '{skill}' skill implementation")
    
    # Analyze task results for insights
    for result in task_results:
        if "insights" in result:
            for insight in result.get("insights", []):
                if "concerning" in insight or "negative" in insight or "decrease" in insight:
                    suggestions.append(f"Investigate: {insight}")
    
    # Analyze recent memories for patterns
    recent_failures = memory_system.query_memories(category="task_failure", limit=20)
    if len(recent_failures) > 3:  # If there are multiple recent failures
        suggestions.append("Review recent task failures for systemic issues")
    
    # Add general improvement suggestions
    general_suggestions = [
        "Refine task prioritization criteria based on mission impact",
        "Add more detailed analytics for task performance",
        "Consider creating specialized helper agents for repetitive tasks",
        "Enhance perception capabilities with additional data sources",
        "Improve memory querying efficiency for faster recall"
    ]
    
    # Add some general suggestions if we don't have enough specific ones
    while len(suggestions) < 3:
        suggestion = random.choice(general_suggestions)
        if suggestion not in suggestions:
            suggestions.append(suggestion)
    
    return suggestions

def update_perception(memory_system):
    """Update perception sources and store results in memory."""
    print("🔍 Updating perception sources...")
    
    # Update all perception sources
    perception_results = perception_manager.update_all_sources(force=True)
    
    if not perception_results:
        print("No perception sources updated")
        return {}
    
    # Store perception results in memory
    for source_name, data in perception_results.items():
        # Create a summary of the perception data
        summary = f"Perception update from {source_name}"
        
        if source_name == "news":
            # Summarize news perception
            articles_count = len(data.get("articles", []))
            trends = data.get("trends", [])
            
            summary = f"News perception: {articles_count} articles collected. "
            if trends:
                summary += f"Key trends: {', '.join(trends[:3])}"
        
        elif source_name == "api":
            # Summarize API perception
            api_summary = data.get("summary", {})
            insights = data.get("insights", [])
            
            summary = f"API perception: {api_summary.get('healthy_endpoints', 0)}/{api_summary.get('total_endpoints', 0)} endpoints healthy. "
            if insights:
                summary += f"Key insights: {', '.join(insights[:3])}"
        
        # Store the summary in memory
        memory_system.add_memory(
            content=summary,
            category="perception",
            tags=["perception", source_name]
        )
        
        # Store the full data in memory (as JSON string)
        memory_system.add_memory(
            content=json.dumps(data),
            category="perception_data",
            tags=["perception", source_name, "raw_data"]
        )
    
    print(f"Updated {len(perception_results)} perception sources")
    return perception_results

def night_phase(config, memory_system, day_results):
    """Execute the night phase of the pulse."""
    print("🌙 Starting NIGHT phase...")
    
    # Update perception sources
    perception_results = update_perception(memory_system)
    
    # Generate reflection based on the day's activities
    completed_tasks = day_results.get("completed_tasks", [])
    failed_tasks = day_results.get("failed_tasks", [])
    
    # Get recent memories for reflection
    recent_memories = memory_system.get_recent_memories(limit=10)
    
    # Generate improvement suggestions based on analysis
    suggestions = generate_improvement_suggestions(day_results, memory_system)
    
    # Format task results for the reflection
    task_results_text = ""
    for task in completed_tasks:
        if "result" in task:
            result = task["result"]
            result_summary = ""
            
            # Format the result based on the type of task/skill
            if "findings" in result:
                # Research skill
                result_summary = f"\n   Findings: {', '.join(result.get('findings', [])[:3])}\n   Confidence: {result.get('confidence', 0):.2f}"
            elif "content" in result and isinstance(result["content"], str) and len(result["content"]) > 100:
                # Content creation skill
                content_preview = result["content"][:100] + "..."
                result_summary = f"\n   Type: {result.get('content_type', 'unknown')}\n   Preview: {content_preview}"
            elif "insights" in result:
                # Monitoring skill
                result_summary = f"\n   Insights: {', '.join(result.get('insights', [])[:2])}"
            else:
                # Generic result
                result_summary = f"\n   Result: {str(result)[:100]}"
                
            task_results_text += f"- {task['description']}{result_summary}\n"
    
    # Format perception results for the reflection
    perception_text = ""
    if perception_results:
        for source_name, data in perception_results.items():
            if source_name == "news" and "trends" in data:
                perception_text += f"- News trends: {', '.join(data['trends'][:3])}\n"
            elif source_name == "api" and "insights" in data:
                perception_text += f"- API insights: {', '.join(data['insights'][:3])}\n"
    
    reflection = f"""
# Daily Reflection - {datetime.utcnow().date()}

## Completed Tasks with Results
{task_results_text if task_results_text else "No completed tasks."}

## Failed Tasks
{['- ' + task['description'] for task in failed_tasks] if failed_tasks else "No failed tasks."}

## Perception Updates
{perception_text if perception_text else "No perception updates."}

## Recent Memories
{['- ' + memory['content'][:100] + '...' if len(memory['content']) > 100 else '- ' + memory['content'] for memory in recent_memories]}

## Proposed Improvements
{['- ' + suggestion for suggestion in suggestions]}
"""
    
    # Save reflection
    save_reflection(reflection)
    
    # Add reflection to memory
    memory_system.add_memory(
        content=f"Created nightly reflection with {len(suggestions)} improvement suggestions",
        category="reflection",
        tags=["night_phase", "improvement"]
    )
    
    # Create backup
    backup_metadata = backup_helper.create_backup(AGENT_DIR, BACKUP_DIR)
    print(f"Created backup: {backup_metadata['backup_path']}")
    
    # Send daily report
    send_email_report(config, reflection)
    
    return {
        "reflection": reflection,
        "backup": backup_metadata
    }

def pulse(force_phase=None):
    """Execute a complete pulse cycle (day and night phases)."""
    config = load_agent_config()
    
    # Initialize memory system
    memory_system = memory_helper.MemorySystem(AGENT_DIR)
    
    # Determine current phase
    phase = force_phase or determine_phase(config)
    
    # Record pulse start
    memory_system.add_memory(
        content=f"Starting pulse cycle in {phase} phase",
        category="system",
        tags=["pulse_start", phase]
    )
    
    # Start the perception manager background updates
    perception_manager.start_background_updates(interval_seconds=300)  # Check every 5 minutes
    
    try:
        # Execute appropriate phase
        if phase == "day":
            day_results = day_phase(config, memory_system)
            # We don't do night phase immediately in normal operation
            # It will happen in the next pulse when it's night time
            results = day_results
        else:  # night phase
            # For night phase, we need day results, so we'll simulate them if not provided
            day_results = {
                "completed_tasks": [],
                "failed_tasks": []
            }
            night_results = night_phase(config, memory_system, day_results)
            results = night_results
        
        # Record pulse end
        memory_system.add_memory(
            content=f"Completed pulse cycle in {phase} phase",
            category="system",
            tags=["pulse_end", phase]
        )
        
        return results
    finally:
        # Stop the perception manager background updates
        perception_manager.stop_background_updates()

def run_day_phase(config: Dict[str, Any], perception_manager: PerceptionManager, 
                agent_mgr: agent_framework.AgentManager, 
                message_bus: agent_communication.MessageBus) -> None:
    """Run the day phase of the garden."""
    print("🌞 Starting DAY phase...")
    
    # Check for messages from helper agents
    process_messages(agent_mgr, message_bus)
    
    # Process messages for helper agents (including task assignments)
    process_helper_messages(agent_mgr, message_bus)
    
    # Prioritize tasks
    print("📌 Prioritizing tasks...")
    agent_dir = os.path.join('agents', MAIN_AGENT_ID)
    prioritizer = task_prioritizer.TaskPrioritizer(agent_dir)
    tasks = prioritizer.load_tasks()
    
    # Prioritize tasks with criteria based on agent's mission focus
    prioritized_tasks = prioritizer.prioritize_tasks({
        'urgency': 0.3,  # Higher weight for time-sensitive tasks
        'mission_alignment': 0.4,  # Higher weight for mission-critical tasks
        'skill_match': 0.2,  # Consider skill requirements
        'estimated_effort': 0.1  # Consider estimated effort
    })
    
    # Create a daily plan
    plan = prioritizer.generate_daily_plan()
    
    # Extract tasks from the plan
    daily_plan = []
    daily_plan.extend(plan.get('high_priority_tasks', []))
    daily_plan.extend(plan.get('medium_priority_tasks', []))
    daily_plan.extend(plan.get('low_priority_tasks', []))
    
    # Log the plan
    total_tasks = len(daily_plan)
    high_priority = len(plan.get('high_priority_tasks', []))
    medium_priority = len(plan.get('medium_priority_tasks', []))
    low_priority = len(plan.get('low_priority_tasks', []))
    
    # Use the estimated completion time from the plan
    estimated_time = plan.get('estimated_completion_time', '0 hours 0 minutes')
    
    print(f"Prioritized {total_tasks} tasks: {high_priority} high, {medium_priority} medium, {low_priority} low priority. Estimated completion time: {estimated_time}")
    
    # Check if we need to delegate any tasks to helper agents
    delegate_tasks_to_helpers(agent_mgr, message_bus, daily_plan)
    
    # Execute remaining tasks
    for task in daily_plan:
        # Skip tasks that have been delegated
        if task.get('delegated_to'):
            continue
            
        print(f"Executing task: {task['description']}")
        
        # Get the required skill for this task
        skill_name = task.get('skill_required')
        
        if skill_name:
            # Get the skill from the registry
            skill = skill_registry.get_skill(skill_name)
            
            if skill:
                print(f"Using skill '{skill_name}' to execute task: {task['description']}")
                # Execute the task using the skill
                result = skill.execute(task)
                
                # Mark task as completed
                prioritizer.complete_task(task['id'])
            else:
                print(f"Error: Skill '{skill_name}' not found for task: {task['description']}")
        else:
            print(f"Warning: No skill specified for task: {task['description']}")

def create_reflection(perceptions: Dict[str, Any], helper_reports: List[Dict[str, Any]] = None) -> str:
    """Create a daily reflection based on perceptions, memories, and helper reports."""
    today = datetime.utcnow().strftime("%Y-%m-%d")
    
    # Initialize the reflection
    reflection = f"# Daily Reflection - {today}\n\n"
    
    # Add perception insights
    reflection += "## Perception Insights\n\n"
    
    if 'news' in perceptions:
        reflection += "### News Insights\n\n"
        for insight in perceptions['news'].get('insights', []):
            reflection += f"- {insight}\n"
        reflection += "\n"
    
    if 'api' in perceptions:
        reflection += "### API Insights\n\n"
        for insight in perceptions['api'].get('insights', []):
            reflection += f"- {insight}\n"
        reflection += "\n"
    
    # Add memory insights
    reflection += "## Memory Insights\n\n"
    memory_system = memory_helper.MemorySystem(os.path.join('agents', MAIN_AGENT_ID))
    recent_memories = memory_system.get_recent_memories(10)
    
    # Group memories by category
    memory_by_category = {}
    for memory in recent_memories:
        category = memory.get('category', 'unknown')
        if category not in memory_by_category:
            memory_by_category[category] = []
        memory_by_category[category].append(memory)
    
    # Add insights for each category
    for category, memories in memory_by_category.items():
        reflection += f"### {category.title()} Memories\n\n"
        for memory in memories[:3]:  # Limit to 3 memories per category
            reflection += f"- {memory.get('content', 'No content')}\n"
        reflection += "\n"
    
    # Collect data from helper reports for later analysis
    all_helper_achievements = []
    all_helper_challenges = []
    all_helper_learnings = []
    all_helper_focus_areas = []
    all_helper_improvements = []
    
    # Add helper agent reports
    if helper_reports:
        reflection += "## Helper Agent Reports\n\n"
        
        for report in helper_reports:
            agent_name = report.get('agent_name', 'Unknown')
            agent_id = report.get('agent_id', 'unknown')
            specialization = report.get('specialization', 'general')
            
            # Extract information from the nightly report if available
            if 'report' in report and isinstance(report['report'], dict):
                nightly_report = report['report']
                tasks_completed = nightly_report.get('tasks_completed', 0)
                success_rate = nightly_report.get('success_rate', 0) * 100
                key_achievements = nightly_report.get('key_achievements', [])
                key_challenges = nightly_report.get('key_challenges', [])
                key_learnings = nightly_report.get('key_learnings', [])
                next_day_focus = nightly_report.get('next_day_focus', [])
                improvement_plan = nightly_report.get('improvement_plan', [])
                
                # Collect for later analysis
                all_helper_achievements.extend(key_achievements)
                all_helper_challenges.extend(key_challenges)
                all_helper_learnings.extend(key_learnings)
                all_helper_focus_areas.extend(next_day_focus)
                all_helper_improvements.extend(improvement_plan)
                
                reflection += f"### {agent_name} ({specialization})\n\n"
                reflection += f"- **Tasks Completed:** {tasks_completed}\n"
                reflection += f"- **Success Rate:** {success_rate:.1f}%\n\n"
                
                if key_achievements:
                    reflection += "**Key Achievements:**\n"
                    for achievement in key_achievements[:3]:  # Limit to top 3
                        reflection += f"- {achievement}\n"
                    reflection += "\n"
                
                if key_challenges:
                    reflection += "**Key Challenges:**\n"
                    for challenge in key_challenges[:3]:  # Limit to top 3
                        reflection += f"- {challenge}\n"
                    reflection += "\n"
                
                if key_learnings:
                    reflection += "**Key Learnings:**\n"
                    for learning in key_learnings[:3]:  # Limit to top 3
                        reflection += f"- {learning}\n"
                    reflection += "\n"
                
                if next_day_focus:
                    reflection += "**Next Day Focus:**\n"
                    for focus in next_day_focus[:3]:  # Limit to top 3
                        reflection += f"- {focus}\n"
                    reflection += "\n"
                
                if improvement_plan:
                    reflection += "**Improvement Plan:**\n"
                    for improvement in improvement_plan[:3]:  # Limit to top 3
                        reflection += f"- {improvement}\n"
                    reflection += "\n"
            else:
                # Fallback to old format if nightly report is not available
                tasks_completed = report.get('tasks_completed', 0)
                findings = report.get('findings', [])
                
                reflection += f"### {agent_name} ({specialization})\n\n"
                reflection += f"- **Tasks Completed:** {tasks_completed}\n\n"
                
                if findings:
                    reflection += "**Key Findings:**\n"
                    for finding in findings[:3]:  # Limit to top 3
                        reflection += f"- {finding}\n"
                    reflection += "\n"
            
            reflection += "---\n\n"
    
    # Add self-assessment
    reflection += "## Self-Assessment\n\n"
    
    # Calculate task completion rate
    tasks_dir = os.path.join('agents', MAIN_AGENT_ID, 'tasks')
    open_tasks_path = os.path.join(tasks_dir, 'open_tasks.json')
    completed_tasks_path = os.path.join(tasks_dir, 'completed_tasks.json')
    
    open_tasks = []
    completed_tasks = []
    
    if os.path.exists(open_tasks_path):
        with open(open_tasks_path, 'r') as f:
            open_tasks = json.load(f)
    
    if os.path.exists(completed_tasks_path):
        with open(completed_tasks_path, 'r') as f:
            completed_tasks = json.load(f)
    
    total_tasks = len(open_tasks) + len(completed_tasks)
    completion_rate = len(completed_tasks) / total_tasks if total_tasks > 0 else 0
    
    reflection += f"- **Task Completion Rate:** {completion_rate * 100:.1f}%\n"
    reflection += f"- **Open Tasks:** {len(open_tasks)}\n"
    reflection += f"- **Completed Tasks:** {len(completed_tasks)}\n\n"
    
    # Add system-wide insights from helper reports
    reflection += "## System-Wide Insights\n\n"
    
    # Function to extract most common items
    def extract_common_items(items, count=3):
        if not items:
            return []
        
        # Count occurrences
        item_counts = {}
        for item in items:
            item_counts[item] = item_counts.get(item, 0) + 1
        
        # Get most common items
        common_items = sorted(item_counts.items(), key=lambda x: x[1], reverse=True)[:count]
        return [item[0] for item in common_items]
    
    # Add common achievements across helpers
    common_achievements = extract_common_items(all_helper_achievements)
    if common_achievements:
        reflection += "### Common Achievements\n\n"
        for achievement in common_achievements:
            reflection += f"- {achievement}\n"
        reflection += "\n"
    
    # Add common challenges across helpers
    common_challenges = extract_common_items(all_helper_challenges)
    if common_challenges:
        reflection += "### Common Challenges\n\n"
        for challenge in common_challenges:
            reflection += f"- {challenge}\n"
        reflection += "\n"
    
    # Add common learnings across helpers
    common_learnings = extract_common_items(all_helper_learnings)
    if common_learnings:
        reflection += "### Common Learnings\n\n"
        for learning in common_learnings:
            reflection += f"- {learning}\n"
        reflection += "\n"
    
    # Add areas for improvement
    reflection += "## Areas for Improvement\n\n"
    
    # Default improvement areas
    improvement_areas = [
        "Develop more sophisticated task prioritization",
        "Improve coordination with helper agents",
        "Enhance perception analysis capabilities"
    ]
    
    # Add insights from helper reports
    if all_helper_challenges:
        # Get most common challenges as improvement areas
        for challenge in common_challenges:
            improvement_areas.append(f"Address common helper challenge: {challenge}")
    
    # Add common improvement plans from helpers
    common_improvements = extract_common_items(all_helper_improvements)
    if common_improvements:
        for improvement in common_improvements:
            improvement_areas.append(improvement)
    
    # Deduplicate and limit
    unique_improvements = list(set(improvement_areas))
    for area in unique_improvements[:5]:  # Limit to 5 areas
        reflection += f"- {area}\n"
    reflection += "\n"
    
    # Add consolidated focus for tomorrow
    reflection += "## Focus for Tomorrow\n\n"
    
    # Default focus areas
    focus_areas = [
        "Optimize task delegation to specialized helper agents",
        "Enhance coordination and knowledge sharing between agents"
    ]
    
    # Add insights from helper reports
    common_focus = extract_common_items(all_helper_focus_areas)
    if common_focus:
        for focus in common_focus:
            focus_areas.append(f"Support helper agents with: {focus}")
    
    # Deduplicate and limit
    unique_focus = list(set(focus_areas))
    for area in unique_focus[:5]:  # Limit to 5 areas
        reflection += f"- {area}\n"
    
    return reflection

def run_night_phase(config: Dict[str, Any], perception_manager: PerceptionManager,
                  agent_mgr: agent_framework.AgentManager,
                  message_bus: agent_communication.MessageBus) -> None:
    """Run the night phase of the garden."""
    print("🌙 Starting NIGHT phase...")
    
    # Check for messages from helper agents
    process_messages(agent_mgr, message_bus)
    
    # Update perception sources
    print("🔍 Updating perception sources...")
    perception_manager.update_all_sources()
    print(f"Updated {len(perception_manager.sources)} perception sources")
    
    # Get the latest perceptions
    perceptions = perception_manager.get_latest_perception()
    
    # Get helper agent reports
    helper_reports = get_helper_reports(agent_mgr, message_bus)
    
    # Create daily reflection
    reflection = create_reflection(perceptions, helper_reports)
    
    # Save reflection
    save_reflection(reflection)
    
    # Create backup
    agent_dir = os.path.join('agents', MAIN_AGENT_ID)
    backup_dir = os.path.join('backups', MAIN_AGENT_ID)
    backup_path = backup_helper.create_backup(agent_dir, backup_dir)
    print(f"Created backup: {backup_path}")
    
    # Send email report
    send_email_report(config, reflection)
    
    # Clean up old backups
    backup_dir = os.path.join('backups', MAIN_AGENT_ID)
    retention_days = int(os.getenv('BACKUP_RETENTION_DAYS', '7'))
    backup_helper.cleanup_old_backups(backup_dir, retention_days)
    
    # Evaluate if new helper agents are needed
    evaluate_helper_needs(agent_mgr, message_bus)

def main(phase: Optional[str] = None):
    """Main function to run the garden."""
    # Parse command line arguments if phase is not provided
    if phase is None:
        parser = argparse.ArgumentParser(description='Run the Agent Garden')
        parser.add_argument('--phase', choices=['day', 'night'], help='Specify which phase to run')
        parser.add_argument('--spawn-helper', action='store_true', help='Spawn a helper agent')
        parser.add_argument('--helper-name', type=str, help='Name for the helper agent')
        parser.add_argument('--helper-mission', type=str, help='Mission for the helper agent')
        parser.add_argument('--helper-specialization', type=str, help='Specialization for the helper agent')
        args = parser.parse_args()
        phase = args.phase
        
        # Check if we need to spawn a helper agent
        if args.spawn_helper:
            if not all([args.helper_name, args.helper_mission, args.helper_specialization]):
                print("Error: When spawning a helper, you must provide --helper-name, --helper-mission, and --helper-specialization")
                sys.exit(1)
            spawn_helper_agent(args.helper_name, args.helper_mission, args.helper_specialization)
            return

    # If phase is still None, determine it based on the current time
    if phase is None:
        phase = determine_phase()

    # Load configuration
    config = load_agent_config()

    # Initialize agent manager
    agent_mgr = initialize_agent_manager()
    
    # Initialize message bus
    message_bus = initialize_message_bus()

    # Initialize perception manager
    perception_manager = initialize_perception()

    # Run the appropriate phase
    if phase == "day":
        run_day_phase(config, perception_manager, agent_mgr, message_bus)
    elif phase == "night":
        run_night_phase(config, perception_manager, agent_mgr, message_bus)
    else:
        print(f"Unknown phase: {phase}")
        sys.exit(1)

def initialize_agent_manager() -> agent_framework.AgentManager:
    """Initialize the agent manager."""
    return agent_framework.AgentManager()

def initialize_message_bus() -> agent_communication.MessageBus:
    """Initialize the message bus."""
    return agent_communication.MessageBus()

def initialize_perception() -> PerceptionManager:
    """Initialize the perception manager and sources."""
    # Create perception manager
    perception_manager = PerceptionManager()
    
    # Add news source
    news_source = NewsSource()
    perception_manager.register_source(news_source)
    
    # Add API source
    api_source = ApiSource()
    perception_manager.register_source(api_source)
    
    # Start background updates
    perception_manager.start_background_updates()
    
    return perception_manager

def process_messages(agent_mgr: agent_framework.AgentManager, 
                    message_bus: agent_communication.MessageBus) -> None:
    """Process incoming messages for the main agent."""
    # Get all unread messages for the main agent
    messages = message_bus.get_unread_messages(MAIN_AGENT_ID)
    
    if not messages:
        return
    
    print(f"📬 Processing {len(messages)} new messages")
    
    for message in messages:
        print(f"Message from {message.sender_id}: {message.subject}")
        
        # Mark as read
        message_bus.mark_as_read(MAIN_AGENT_ID, message.message_id)
        
        # If it's a task completion message, log it
        if message.message_type == "task_completion":
            print(f"Helper agent {message.sender_id} completed task: {message.subject}")
            
            # Store this in memory
            memory_content = f"Helper agent {message.sender_id} reported: {message.content}"
            memory_system = memory_helper.MemorySystem(os.path.join('agents', MAIN_AGENT_ID))
            memory_system.add_memory(memory_content, "helper_report", ["helper_report", message.sender_id])

def process_helper_messages(agent_mgr: agent_framework.AgentManager,
                           message_bus: agent_communication.MessageBus) -> None:
    """Process incoming messages for helper agents, including task assignments."""
    # Get all helper agents
    helpers = agent_mgr.get_helpers(MAIN_AGENT_ID)
    
    if not helpers:
        return
    
    for helper in helpers:
        helper_id = helper['agent_id']
        
        # Get unread messages for this helper
        messages = message_bus.get_unread_messages(helper_id)
        
        if not messages:
            continue
        
        print(f"📬 Processing {len(messages)} messages for helper {helper['name']} ({helper_id})")
        
        # Load the helper agent instance
        helper_instance = agent_mgr.load_agent_instance(helper_id)
        
        for message in messages:
            print(f"Message to {helper['name']} from {message.sender_id}: {message.subject}")
            
            # Mark as read
            message_bus.mark_as_read(helper_id, message.message_id)
            
            # If it's a task assignment, process it
            if message.message_type == "task_assignment":
                print(f"Processing task assignment: {message.subject}")
                
                # Parse the task from the message
                try:
                    task = message.task
                    
                    # Process the task
                    helper_instance.process_task(task, message_bus)
                except Exception as e:
                    print(f"Error processing task: {str(e)}")
                    
                    # Send error message back to main agent
                    error_message = agent_communication.Message(
                        sender_id=helper_id,
                        recipient_id=MAIN_AGENT_ID,
                        subject=f"Error processing task: {message.subject}",
                        content=f"Error: {str(e)}",
                        message_type="error"
                    )
                    message_bus.send_message(error_message)

def enhance_task_for_specialization(task: Dict[str, Any], specialization: str) -> Dict[str, Any]:
    """Enhance a task with specialization-specific parameters."""
    # Create a copy of the task to avoid modifying the original
    enhanced_task = task.copy()
    
    # Add specialization to the task
    enhanced_task['specialization'] = specialization
    
    # Add specialization-specific parameters
    if specialization == 'research':
        # Add research-specific parameters if not already present
        if 'topic' not in enhanced_task:
            enhanced_task['topic'] = enhanced_task.get('description', 'General research')
        if 'depth' not in enhanced_task:
            enhanced_task['depth'] = 3  # Default research depth
    
    elif specialization == 'content_creation':
        # Add content creation-specific parameters if not already present
        if 'content_type' not in enhanced_task:
            # Try to infer content type from description
            desc = enhanced_task.get('description', '').lower()
            if 'blog' in desc:
                enhanced_task['content_type'] = 'blog_post'
            elif 'newsletter' in desc:
                enhanced_task['content_type'] = 'newsletter'
            elif 'social' in desc:
                enhanced_task['content_type'] = 'social_media'
            else:
                enhanced_task['content_type'] = 'blog_post'  # Default
        
        if 'topic' not in enhanced_task:
            enhanced_task['topic'] = enhanced_task.get('description', 'General content')
        
        if 'audience' not in enhanced_task:
            enhanced_task['audience'] = 'general'  # Default audience
    
    elif specialization == 'monitoring':
        # Add monitoring-specific parameters if not already present
        if 'domain' not in enhanced_task:
            # Try to infer domain from description
            desc = enhanced_task.get('description', '').lower()
            if 'financial' in desc or 'inclusion' in desc:
                enhanced_task['domain'] = 'financial_inclusion'
            elif 'ai' in desc or 'ethics' in desc:
                enhanced_task['domain'] = 'ai_ethics'
            else:
                enhanced_task['domain'] = 'system_health'  # Default
        
        if 'metrics' not in enhanced_task:
            # Add default metrics based on domain
            domain = enhanced_task.get('domain', 'system_health')
            if domain == 'financial_inclusion':
                enhanced_task['metrics'] = {
                    'access_rate': 0.78,
                    'usage_rate': 0.65,
                    'quality_index': 0.82
                }
            elif domain == 'ai_ethics':
                enhanced_task['metrics'] = {
                    'bias_score': 0.18,
                    'transparency_index': 0.72,
                    'accountability_measure': 0.81
                }
            else:  # system_health
                enhanced_task['metrics'] = {
                    'uptime': 0.98,
                    'response_time': 150,
                    'error_rate': 0.02
                }
    
    return enhanced_task

def delegate_tasks_to_helpers(agent_mgr: agent_framework.AgentManager, 
                              message_bus: agent_communication.MessageBus, 
                              tasks: List[Dict[str, Any]]) -> None:
    """Delegate tasks to helper agents based on their specializations."""
    # Get all helper agents
    helpers = agent_mgr.get_helpers(MAIN_AGENT_ID)
    
    if not helpers:
        return
    
    print(f"🤝 Evaluating {len(tasks)} tasks for delegation to {len(helpers)} helper agents")
    
    # Group helpers by specialization
    helpers_by_specialization = {}
    for helper in helpers:
        specialization = helper.get('specialization', 'general')
        if specialization not in helpers_by_specialization:
            helpers_by_specialization[specialization] = []
        helpers_by_specialization[specialization].append(helper)
    
    # Delegate tasks based on specialization
    for task in tasks:
        # Skip tasks already delegated
        if task.get('delegated_to'):
            continue
            
        task_description = task.get('description', '')
        
        # Determine task specialization based on task content
        task_specialization = task.get('specialization', 'general')
        
        # If no specialization is specified, try to infer it from the task description
        if task_specialization == 'general':
            if any(kw in task_description.lower() for kw in ['research', 'investigate', 'analyze', 'study']):
                task_specialization = 'research'
            elif any(kw in task_description.lower() for kw in ['create', 'write', 'draft', 'content', 'blog', 'newsletter']):
                task_specialization = 'content_creation'
            elif any(kw in task_description.lower() for kw in ['monitor', 'track', 'observe', 'metrics', 'alert']):
                task_specialization = 'monitoring'
        
        # Find helpers with matching specialization
        matching_helpers = helpers_by_specialization.get(task_specialization, [])
        
        if not matching_helpers:
            # If no exact match, try to find a general helper
            matching_helpers = helpers_by_specialization.get('general', [])
        
        if matching_helpers:
            # Choose the first available helper (could be more sophisticated)
            helper = matching_helpers[0]
            helper_id = helper['agent_id']
            helper_name = helper['name']
            
            # Enhance task with specialization-specific parameters
            enhanced_task = enhance_task_for_specialization(task, task_specialization)
            
            # Mark the task as delegated
            task['delegated_to'] = helper_id
            
            # Delegate the task
            print(f"Delegating task '{task_description}' to helper {helper_name} ({helper_id})")
            message_bus.assign_task(
                sender_id=MAIN_AGENT_ID,
                recipient_id=helper_id,
                task=enhanced_task,
                instructions=f"Please complete this task using your {helper['specialization']} specialization."
            )

def get_helper_reports(agent_mgr: agent_framework.AgentManager,
                      message_bus: agent_communication.MessageBus) -> List[Dict[str, Any]]:
    """Get reports from all helper agents, including their reflections."""
    reports = []
    
    # Get all helper agents
    helpers = agent_mgr.get_helpers(MAIN_AGENT_ID)
    
    if not helpers:
        return reports
    
    print(f"📊 Collecting reports from {len(helpers)} helper agents")
    
    # Generate nightly reports from each helper agent
    for helper in helpers:
        helper_id = helper['agent_id']
        helper_name = helper['name']
        specialization = helper.get('specialization', 'general')
        
        try:
            # Load the helper agent instance
            helper_instance = agent_mgr.load_agent_instance(helper_id)
            
            # Generate nightly report
            print(f"Generating nightly report for helper {helper_name} ({helper_id})")
            report = helper_instance.generate_nightly_report(message_bus)
            
            # Add to reports list
            reports.append({
                'agent_id': helper_id,
                'agent_name': helper_name,
                'specialization': specialization,
                'report': report
            })
            
            print(f"Received nightly report from helper {helper_name} ({helper_id})")
        except Exception as e:
            print(f"Error generating nightly report for helper {helper_id}: {str(e)}")
    
    for helper in helpers:
        helper_id = helper['agent_id']
        helper_name = helper['name']
        specialization = helper.get('specialization', 'general')
        
        # Load the helper agent instance to access reflection capabilities
        helper_instance = agent_mgr.load_agent_instance(helper_id)
        
        # Get messages from this helper
        helper_messages = message_bus.get_messages(MAIN_AGENT_ID)
        helper_messages = [msg for msg in helper_messages if msg.sender_id == helper_id]
        
        # Look for task completion messages
        task_completion_messages = [msg for msg in helper_messages 
                                  if "completed task" in msg.content.lower()]
        
        # Look for findings
        findings = []
        for msg in helper_messages:
            if "finding:" in msg.content.lower():
                findings.append(msg.content)
        
        # Generate reflections if helper instance is available
        reflections = {}
        improvement_plan = {}
        daily_summary = {}
        
        if helper_instance and isinstance(helper_instance, agent_framework.HelperAgent):
            try:
                # Generate daily reflection
                daily_summary = helper_instance.create_daily_reflection()
                
                # Generate improvement plan
                improvement_plan = helper_instance.generate_improvement_plan()
                
                # Get task and skill reflections if available
                reflection_system = helper_instance.reflection_system
                task_reflections = reflection_system.get_task_reflections(limit=3)
                skill_reflections = reflection_system.get_skill_reflections(limit=3)
                
                reflections = {
                    'task_reflections': task_reflections,
                    'skill_reflections': skill_reflections
                }
                
                # Mark messages as read
                for msg in helper_messages:
                    message_bus.mark_as_read(MAIN_AGENT_ID, msg.message_id)
                    
                logger.info(f"Generated reflections for helper {helper_name} ({helper_id})")
            except Exception as e:
                logger.error(f"Error generating reflections for helper {helper_id}: {str(e)}")
        
        # Create the report
        report = {
            'agent_id': helper_id,
            'agent_name': helper_name,
            'specialization': specialization,
            'tasks_completed': len(task_completion_messages),
            'findings': findings,
            'daily_summary': daily_summary,
            'improvement_plan': improvement_plan,
            'reflections': reflections
        }
        
        reports.append(report)
    
    return reports

def evaluate_helper_needs(agent_mgr: agent_framework.AgentManager,
                         message_bus: agent_communication.MessageBus) -> None:
    """Evaluate if new helper agents are needed based on task patterns."""
    
    # Load completed tasks
    completed_tasks_path = os.path.join('agents', MAIN_AGENT_ID, 'tasks', 'completed_tasks.json')
    with open(completed_tasks_path, 'r') as f:
        completed_tasks = json.load(f)
    
    # Count tasks by skill required
    skill_counts = {}
    for task in completed_tasks:
        skill = task.get('skill_required', 'unknown')
        if skill not in skill_counts:
            skill_counts[skill] = 0
        skill_counts[skill] += 1
    
    # Get existing helpers
    existing_helpers = agent_mgr.get_helpers(MAIN_AGENT_ID)
    existing_specializations = [h.get('specialization', '').lower() for h in existing_helpers]
    
    # Identify skills that might need dedicated helpers
    for skill, count in skill_counts.items():
        # If we have many tasks of a certain skill and no helper for it yet
        if count >= 3 and skill.lower() not in existing_specializations and skill != 'unknown':
            print(f"🤖 Recommending new helper agent for skill: {skill} (completed {count} tasks)")
            
            # Store this recommendation in memory
            memory_content = f"Recommended creating a helper agent specialized in {skill} based on task history analysis."
            memory_system = memory_helper.MemorySystem(os.path.join('agents', MAIN_AGENT_ID))
            memory_system.add_memory(memory_content, "recommendation", ["helper_recommendation", skill])

def spawn_helper_agent(name: str, mission: str, specialization: str) -> None:
    """Spawn a new helper agent with the given parameters."""
    
    # Initialize agent manager
    agent_mgr = initialize_agent_manager()
    
    # Create the helper agent
    helper_id, helper = agent_mgr.create_helper_agent(
        name=name,
        mission=mission,
        parent_id=MAIN_AGENT_ID,
        specialization=specialization
    )
    
    print(f"✨ Created helper agent: {name} ({helper_id})")
    print(f"   Mission: {mission}")
    print(f"   Specialization: {specialization}")
    print(f"   Parent: {MAIN_AGENT_ID}")
    
    # Initialize message bus
    message_bus = initialize_message_bus()
    
    # Send welcome message from Aurora to the helper
    welcome_message = agent_communication.Message(
        sender_id=MAIN_AGENT_ID,
        recipient_id=helper_id,
        subject="Welcome to the Agent Garden",
        content=f"Welcome {name}! You have been created to help with {specialization} tasks. Your mission is: {mission}",
        message_type="welcome"
    )
    message_bus.send_message(welcome_message)
    
    # Store this event in memory
    memory_content = f"Created helper agent {name} ({helper_id}) specialized in {specialization} with mission: {mission}"
    memory_system = memory_helper.MemorySystem(os.path.join('agents', MAIN_AGENT_ID))
    memory_system.add_memory(memory_content, "helper_agent", ["helper_creation", specialization])

if __name__ == "__main__":
    main()
