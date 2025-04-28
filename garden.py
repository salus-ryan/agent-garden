import os
import sys
import json
import time
import random
import argparse
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

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
    delegate_tasks_to_helpers(daily_plan, agent_mgr, message_bus)
    
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
    # Get recent memories
    memory_system = memory_helper.MemorySystem(os.path.join('agents', MAIN_AGENT_ID))
    memories = memory_system.get_recent_memories(limit=5)
    
    # Format the reflection
    reflection = """# Daily Reflection - {datetime.utcnow().date()}

## Perception Updates

"""
    
    # Add news updates if available
    if perceptions and 'news' in perceptions and perceptions['news']:
        reflection += "### News Updates\n\n"
        news_data = perceptions['news']
        if isinstance(news_data, list) and len(news_data) > 0:
            for article in news_data[:3]:  # Limit to 3 articles
                if isinstance(article, dict) and 'title' in article and 'description' in article:
                    reflection += f"- **{article['title']}**: {article['description']}\n"
            reflection += "\n"
        else:
            reflection += "No news articles available.\n\n"
    
    # Add API data if available
    if perceptions and 'api' in perceptions and perceptions['api']:
        reflection += "### API Data\n\n"
        api_data = perceptions['api']
        if isinstance(api_data, dict) and len(api_data) > 0:
            for endpoint, data in api_data.items():
                reflection += f"- **{endpoint}**: {json.dumps(data, indent=2)}\n"
            reflection += "\n"
        else:
            reflection += "No API data available.\n\n"
    
    # Add helper agent reports if available
    if helper_reports and len(helper_reports) > 0:
        reflection += "## Helper Agent Reports\n\n"
        for report in helper_reports:
            reflection += f"### {report['agent_name']} ({report['agent_id']})\n\n"
            reflection += f"**Specialization**: {report['specialization']}\n\n"
            reflection += f"**Tasks Completed**: {report['tasks_completed']}\n\n"
            if 'findings' in report and report['findings']:
                reflection += "**Key Findings**:\n\n"
                for finding in report['findings']:
                    reflection += f"- {finding}\n"
            reflection += "\n"
    
    # Add recent memories
    reflection += "## Recent Memories\n\n"
    if memories and len(memories) > 0:
        for memory in memories:
            if isinstance(memory, dict) and 'content' in memory:
                reflection += f"- {memory['content']}\n"
    else:
        reflection += "No recent memories available.\n"
    reflection += "\n"
    
    # Add proposed improvements or next steps
    reflection += "## Proposed Improvements\n\n"
    reflection += "- Continue monitoring financial inclusion metrics\n"
    reflection += "- Expand research into AI ethics frameworks\n"
    reflection += "- Develop more comprehensive content strategy\n"
    
    # Add helper agent recommendations if applicable
    if not helper_reports or len(helper_reports) == 0:
        reflection += "- Consider spawning helper agents for specialized tasks\n"
    
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
    
    # Get unread messages
    messages = message_bus.get_messages(MAIN_AGENT_ID, unread_only=True)
    
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

def delegate_tasks_to_helpers(tasks: List[Dict[str, Any]], 
                             agent_mgr: agent_framework.AgentManager,
                             message_bus: agent_communication.MessageBus) -> None:
    """Delegate appropriate tasks to helper agents."""
    
    # Get all helper agents
    helpers = agent_mgr.get_helpers(MAIN_AGENT_ID)
    
    if not helpers:
        return
    
    print(f"🤝 Evaluating {len(tasks)} tasks for delegation to {len(helpers)} helper agents")
    
    for task in tasks:
        # Skip tasks already delegated
        if task.get('delegated_to'):
            continue
        
        # Find a suitable helper based on specialization and skill required
        skill_required = task.get('skill_required', '')
        best_helper = None
        
        for helper in helpers:
            specialization = helper.get('specialization', '')
            
            # Check if this helper's specialization matches the task's required skill
            if specialization.lower() == skill_required.lower():
                best_helper = helper
                break
        
        # If we found a suitable helper, delegate the task
        if best_helper:
            helper_id = best_helper['agent_id']
            print(f"Delegating task '{task['description']}' to helper {best_helper['name']} ({helper_id})")
            
            # Mark the task as delegated
            task['delegated_to'] = helper_id
            
            # Send the task to the helper
            message_bus.assign_task(
                sender_id=MAIN_AGENT_ID,
                recipient_id=helper_id,
                task=task,
                instructions=f"Please complete this task using your {best_helper['specialization']} specialization."
            )

def get_helper_reports(agent_mgr: agent_framework.AgentManager,
                      message_bus: agent_communication.MessageBus) -> List[Dict[str, Any]]:
    """Get reports from all helper agents."""
    reports = []
    
    # Get all helper agents
    helpers = agent_mgr.get_helpers(MAIN_AGENT_ID)
    
    if not helpers:
        return reports
    
    print(f"📊 Collecting reports from {len(helpers)} helper agents")
    
    for helper in helpers:
        helper_id = helper['agent_id']
        helper_name = helper['name']
        specialization = helper.get('specialization', 'general')
        
        # Get all messages from this helper
        messages = message_bus.get_messages(MAIN_AGENT_ID)
        helper_messages = [m for m in messages if m.sender_id == helper_id]
        
        # Count completed tasks
        task_completion_messages = [m for m in helper_messages if m.message_type == "task_completion"]
        
        # Extract findings from messages
        findings = []
        for msg in helper_messages:
            if "finding:" in msg.content.lower():
                findings.append(msg.content)
        
        # Create the report
        report = {
            'agent_id': helper_id,
            'agent_name': helper_name,
            'specialization': specialization,
            'tasks_completed': len(task_completion_messages),
            'findings': findings
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
