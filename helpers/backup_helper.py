import os
import shutil
import json
import datetime
from typing import Dict, Any

def create_backup(agent_dir: str, backup_dir: str) -> Dict[str, Any]:
    """
    Create a backup of the agent's memory and configuration.
    
    Args:
        agent_dir: Path to the agent directory
        backup_dir: Path to the backup directory
        
    Returns:
        Dict with backup metadata
    """
    # Create timestamp for backup
    timestamp = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    
    # Create backup directory if it doesn't exist
    os.makedirs(backup_dir, exist_ok=True)
    
    # Create agent-specific backup directory
    agent_name = os.path.basename(agent_dir.rstrip('/'))
    agent_backup_dir = os.path.join(backup_dir, agent_name)
    os.makedirs(agent_backup_dir, exist_ok=True)
    
    # Create timestamp-specific backup directory
    backup_path = os.path.join(agent_backup_dir, timestamp)
    os.makedirs(backup_path, exist_ok=True)
    
    # Backup memory
    memory_dir = os.path.join(agent_dir, "memory")
    if os.path.exists(memory_dir):
        shutil.copytree(memory_dir, os.path.join(backup_path, "memory"))
    
    # Backup config
    config_file = os.path.join(agent_dir, "agent_config.json")
    if os.path.exists(config_file):
        shutil.copy2(config_file, os.path.join(backup_path, "agent_config.json"))
    
    # Backup tasks
    tasks_dir = os.path.join(agent_dir, "tasks")
    if os.path.exists(tasks_dir):
        shutil.copytree(tasks_dir, os.path.join(backup_path, "tasks"))
    
    # Backup reflections
    reflections_dir = os.path.join(agent_dir, "reflections")
    if os.path.exists(reflections_dir):
        shutil.copytree(reflections_dir, os.path.join(backup_path, "reflections"))
    
    # Create backup metadata
    metadata = {
        "timestamp": timestamp,
        "agent": agent_name,
        "backup_path": backup_path,
        "contents": ["memory", "config", "tasks", "reflections"]
    }
    
    # Save metadata
    with open(os.path.join(backup_path, "metadata.json"), 'w') as f:
        json.dump(metadata, f, indent=2)
    
    return metadata

def list_backups(backup_dir: str, agent_name: str = None):
    """
    List all backups for an agent or all agents.
    
    Args:
        backup_dir: Path to the backup directory
        agent_name: Optional agent name to filter backups
        
    Returns:
        List of backup metadata
    """
    backups = []
    
    if not os.path.exists(backup_dir):
        return backups
    
    # If agent_name is provided, only list backups for that agent
    if agent_name:
        agent_backup_dir = os.path.join(backup_dir, agent_name)
        if not os.path.exists(agent_backup_dir):
            return backups
        
        for backup_timestamp in os.listdir(agent_backup_dir):
            metadata_file = os.path.join(agent_backup_dir, backup_timestamp, "metadata.json")
            if os.path.exists(metadata_file):
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                    backups.append(metadata)
    else:
        # List backups for all agents
        for agent in os.listdir(backup_dir):
            agent_backup_dir = os.path.join(backup_dir, agent)
            if os.path.isdir(agent_backup_dir):
                for backup_timestamp in os.listdir(agent_backup_dir):
                    metadata_file = os.path.join(agent_backup_dir, backup_timestamp, "metadata.json")
                    if os.path.exists(metadata_file):
                        with open(metadata_file, 'r') as f:
                            metadata = json.load(f)
                            backups.append(metadata)
    
    # Sort backups by timestamp (newest first)
    backups.sort(key=lambda x: x["timestamp"], reverse=True)
    
    return backups

def restore_backup(backup_path: str, agent_dir: str):
    """
    Restore a backup to the agent directory.
    
    Args:
        backup_path: Path to the backup
        agent_dir: Path to the agent directory
        
    Returns:
        Dict with restore metadata
    """
    # Check if backup exists
    if not os.path.exists(backup_path):
        raise FileNotFoundError(f"Backup not found: {backup_path}")
    
    # Check if metadata exists
    metadata_file = os.path.join(backup_path, "metadata.json")
    if not os.path.exists(metadata_file):
        raise FileNotFoundError(f"Backup metadata not found: {metadata_file}")
    
    # Load metadata
    with open(metadata_file, 'r') as f:
        metadata = json.load(f)
    
    # Restore memory
    memory_backup = os.path.join(backup_path, "memory")
    if os.path.exists(memory_backup):
        memory_dir = os.path.join(agent_dir, "memory")
        if os.path.exists(memory_dir):
            shutil.rmtree(memory_dir)
        shutil.copytree(memory_backup, memory_dir)
    
    # Restore config
    config_backup = os.path.join(backup_path, "agent_config.json")
    if os.path.exists(config_backup):
        shutil.copy2(config_backup, os.path.join(agent_dir, "agent_config.json"))
    
    # Restore tasks
    tasks_backup = os.path.join(backup_path, "tasks")
    if os.path.exists(tasks_backup):
        tasks_dir = os.path.join(agent_dir, "tasks")
        if os.path.exists(tasks_dir):
            shutil.rmtree(tasks_dir)
        shutil.copytree(tasks_backup, tasks_dir)
    
    # Restore reflections
    reflections_backup = os.path.join(backup_path, "reflections")
    if os.path.exists(reflections_backup):
        reflections_dir = os.path.join(agent_dir, "reflections")
        if os.path.exists(reflections_dir):
            shutil.rmtree(reflections_dir)
        shutil.copytree(reflections_backup, reflections_dir)
    
    # Create restore metadata
    restore_metadata = {
        "timestamp": datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S"),
        "backup_timestamp": metadata["timestamp"],
        "agent": metadata["agent"],
        "restored_contents": metadata["contents"]
    }
    
    return restore_metadata

def cleanup_old_backups(backup_dir: str, retention_days: int = 7):
    """
    Clean up old backups, keeping only the most recent ones within the retention period.
    
    Args:
        backup_dir: Path to the backup directory
        retention_days: Number of days to retain backups (default: 7)
        
    Returns:
        Number of backups deleted
    """
    if not os.path.exists(backup_dir):
        return 0
    
    # Calculate cutoff date
    cutoff_date = datetime.datetime.utcnow() - datetime.timedelta(days=retention_days)
    cutoff_str = cutoff_date.strftime("%Y%m%d")
    
    deleted_count = 0
    
    # List all agent backup directories
    for agent in os.listdir(backup_dir):
        agent_backup_dir = os.path.join(backup_dir, agent)
        if not os.path.isdir(agent_backup_dir):
            continue
        
        # List all backups for this agent
        for backup_timestamp in os.listdir(agent_backup_dir):
            backup_path = os.path.join(agent_backup_dir, backup_timestamp)
            if not os.path.isdir(backup_path):
                continue
            
            # Check if backup is older than cutoff date
            # Timestamp format is YYYYMMDD_HHMMSS
            backup_date = backup_timestamp.split('_')[0]
            if backup_date < cutoff_str:
                # Delete old backup
                shutil.rmtree(backup_path)
                deleted_count += 1
                print(f"Deleted old backup: {backup_path}")
    
    return deleted_count
