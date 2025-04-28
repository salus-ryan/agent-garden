import os
import json
import datetime
from typing import List, Dict, Any, Optional

class MemorySystem:
    def __init__(self, agent_dir: str):
        self.agent_dir = agent_dir
        self.memory_dir = os.path.join(agent_dir, "memory")
        self.memory_file = os.path.join(self.memory_dir, "memory.jsonl")
        
        # Create memory directory if it doesn't exist
        os.makedirs(self.memory_dir, exist_ok=True)
        
        # Create memory file if it doesn't exist
        if not os.path.exists(self.memory_file):
            with open(self.memory_file, 'w') as f:
                pass  # Create empty file
    
    def add_memory(self, content: str, category: str, tags: List[str] = None) -> Dict[str, Any]:
        """Add a new memory to the memory store."""
        if tags is None:
            tags = []
            
        memory = {
            "id": self._generate_id(),
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "content": content,
            "category": category,
            "tags": tags
        }
        
        with open(self.memory_file, 'a') as f:
            f.write(json.dumps(memory) + '\n')
            
        return memory
    
    def query_memories(self, 
                      category: Optional[str] = None, 
                      tags: Optional[List[str]] = None, 
                      start_date: Optional[str] = None,
                      end_date: Optional[str] = None,
                      limit: int = 100) -> List[Dict[str, Any]]:
        """Query memories based on category, tags, and date range."""
        results = []
        
        with open(self.memory_file, 'r') as f:
            for line in f:
                if not line.strip():
                    continue
                    
                memory = json.loads(line)
                
                # Apply filters
                if category and memory["category"] != category:
                    continue
                    
                if tags and not all(tag in memory["tags"] for tag in tags):
                    continue
                    
                if start_date and memory["timestamp"] < start_date:
                    continue
                    
                if end_date and memory["timestamp"] > end_date:
                    continue
                
                results.append(memory)
                
                if len(results) >= limit:
                    break
                    
        return results
    
    def get_recent_memories(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get the most recent memories."""
        memories = []
        
        with open(self.memory_file, 'r') as f:
            for line in f:
                if not line.strip():
                    continue
                memories.append(json.loads(line))
        
        # Sort by timestamp (newest first)
        memories.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return memories[:limit]
    
    def _generate_id(self) -> str:
        """Generate a unique ID for a memory."""
        return f"mem_{datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{os.urandom(4).hex()}"
