"""
Agent Communication Module for the Agent Garden

This module provides utilities for communication between agents in the Agent Garden.
"""

import os
import json
import uuid
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Message:
    """Class representing a message between agents."""
    
    def __init__(self, sender_id: str, recipient_id: str, subject: str, content: str, 
                 message_type: str = "general", reference_id: Optional[str] = None):
        """
        Initialize a new message.
        
        Args:
            sender_id: ID of the sending agent
            recipient_id: ID of the receiving agent
            subject: Message subject
            content: Message content
            message_type: Type of message (general, task, response, etc.)
            reference_id: Optional ID of a message this is in response to
        """
        self.message_id = str(uuid.uuid4())
        self.sender_id = sender_id
        self.recipient_id = recipient_id
        self.subject = subject
        self.content = content
        self.message_type = message_type
        self.reference_id = reference_id
        self.timestamp = datetime.utcnow().isoformat()
        self.read = False
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the message to a dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the message
        """
        return {
            'message_id': self.message_id,
            'sender_id': self.sender_id,
            'recipient_id': self.recipient_id,
            'subject': self.subject,
            'content': self.content,
            'message_type': self.message_type,
            'reference_id': self.reference_id,
            'timestamp': self.timestamp,
            'read': self.read
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """
        Create a message from a dictionary.
        
        Args:
            data: Dictionary containing message data
            
        Returns:
            Message: A message object
        """
        message = cls(
            sender_id=data['sender_id'],
            recipient_id=data['recipient_id'],
            subject=data['subject'],
            content=data['content'],
            message_type=data['message_type'],
            reference_id=data['reference_id']
        )
        message.message_id = data['message_id']
        message.timestamp = data['timestamp']
        message.read = data['read']
        return message


class TaskMessage(Message):
    """Class representing a task assignment message."""
    
    def __init__(self, sender_id: str, recipient_id: str, task: Dict[str, Any], 
                 instructions: Optional[str] = None, reference_id: Optional[str] = None):
        """
        Initialize a new task message.
        
        Args:
            sender_id: ID of the sending agent
            recipient_id: ID of the receiving agent
            task: Task dictionary
            instructions: Optional additional instructions
            reference_id: Optional ID of a message this is in response to
        """
        subject = f"Task Assignment: {task.get('description', 'New Task')}"
        content = instructions or f"Please complete the following task: {task.get('description', 'No description')}"
        super().__init__(sender_id, recipient_id, subject, content, "task", reference_id)
        self.task = task
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the task message to a dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the task message
        """
        data = super().to_dict()
        data['task'] = self.task
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskMessage':
        """
        Create a task message from a dictionary.
        
        Args:
            data: Dictionary containing task message data
            
        Returns:
            TaskMessage: A task message object
        """
        task_message = cls(
            sender_id=data['sender_id'],
            recipient_id=data['recipient_id'],
            task=data['task'],
            instructions=data['content'],
            reference_id=data['reference_id']
        )
        task_message.message_id = data['message_id']
        task_message.timestamp = data['timestamp']
        task_message.read = data['read']
        return task_message


class MessageBus:
    """Class for handling message passing between agents."""
    
    def __init__(self):
        """Initialize the message bus."""
        self.base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'messages')
        os.makedirs(self.base_dir, exist_ok=True)
    
    def _get_inbox_path(self, agent_id: str) -> str:
        """
        Get the path to an agent's inbox.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            str: Path to the agent's inbox
        """
        inbox_dir = os.path.join(self.base_dir, agent_id)
        os.makedirs(inbox_dir, exist_ok=True)
        return inbox_dir
    
    def _get_message_path(self, agent_id: str, message_id: str) -> str:
        """
        Get the path to a specific message.
        
        Args:
            agent_id: ID of the recipient agent
            message_id: ID of the message
            
        Returns:
            str: Path to the message file
        """
        return os.path.join(self._get_inbox_path(agent_id), f"{message_id}.json")
    
    def send_message(self, message: Message) -> str:
        """
        Send a message to an agent.
        
        Args:
            message: Message to send
            
        Returns:
            str: ID of the sent message
        """
        message_path = self._get_message_path(message.recipient_id, message.message_id)
        
        with open(message_path, 'w') as f:
            json.dump(message.to_dict(), f, indent=2)
        
        logger.info(f"Sent message from {message.sender_id} to {message.recipient_id}: {message.subject}")
        return message.message_id
    
    def get_messages(self, agent_id: str, unread_only: bool = False) -> List[Message]:
        """
        Get messages for an agent.
        
        Args:
            agent_id: ID of the agent
            unread_only: If True, only return unread messages
            
        Returns:
            List[Message]: List of messages
        """
        inbox_dir = self._get_inbox_path(agent_id)
        messages = []
        
        for filename in os.listdir(inbox_dir):
            if not filename.endswith('.json'):
                continue
            
            message_path = os.path.join(inbox_dir, filename)
            
            with open(message_path, 'r') as f:
                data = json.load(f)
            
            if unread_only and data.get('read', False):
                continue
            
            if data.get('message_type') == 'task':
                message = TaskMessage.from_dict(data)
            else:
                message = Message.from_dict(data)
            
            messages.append(message)
        
        # Sort by timestamp
        messages.sort(key=lambda m: m.timestamp)
        return messages
    
    def mark_as_read(self, agent_id: str, message_id: str) -> bool:
        """
        Mark a message as read.
        
        Args:
            agent_id: ID of the recipient agent
            message_id: ID of the message
            
        Returns:
            bool: True if the message was found and marked as read, False otherwise
        """
        message_path = self._get_message_path(agent_id, message_id)
        
        if not os.path.exists(message_path):
            logger.warning(f"Message {message_id} not found for agent {agent_id}")
            return False
        
        with open(message_path, 'r') as f:
            data = json.load(f)
        
        data['read'] = True
        
        with open(message_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Marked message {message_id} as read for agent {agent_id}")
        return True
    
    def delete_message(self, agent_id: str, message_id: str) -> bool:
        """
        Delete a message.
        
        Args:
            agent_id: ID of the recipient agent
            message_id: ID of the message
            
        Returns:
            bool: True if the message was found and deleted, False otherwise
        """
        message_path = self._get_message_path(agent_id, message_id)
        
        if not os.path.exists(message_path):
            logger.warning(f"Message {message_id} not found for agent {agent_id}")
            return False
        
        os.remove(message_path)
        logger.info(f"Deleted message {message_id} for agent {agent_id}")
        return True
    
    def reply_to_message(self, original_message: Message, content: str, 
                        message_type: str = "response") -> Message:
        """
        Create a reply to a message.
        
        Args:
            original_message: The message to reply to
            content: Content of the reply
            message_type: Type of the reply message
            
        Returns:
            Message: The reply message
        """
        reply = Message(
            sender_id=original_message.recipient_id,
            recipient_id=original_message.sender_id,
            subject=f"Re: {original_message.subject}",
            content=content,
            message_type=message_type,
            reference_id=original_message.message_id
        )
        
        self.send_message(reply)
        return reply
    
    def assign_task(self, sender_id: str, recipient_id: str, task: Dict[str, Any], 
                   instructions: Optional[str] = None) -> str:
        """
        Assign a task to an agent.
        
        Args:
            sender_id: ID of the sending agent
            recipient_id: ID of the receiving agent
            task: Task dictionary
            instructions: Optional additional instructions
            
        Returns:
            str: ID of the sent task message
        """
        task_message = TaskMessage(sender_id, recipient_id, task, instructions)
        return self.send_message(task_message)
