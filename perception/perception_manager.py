"""
Perception Manager for Agent Garden
---------------------------------
This module manages perception sources and coordinates perception activities.
"""

import logging
import threading
import time
from typing import Dict, List, Any, Optional
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PerceptionSource:
    """Base class for all perception sources."""
    
    def __init__(self, name: str, description: str, frequency_minutes: int = 60):
        """
        Initialize a perception source.
        
        Args:
            name: Name of the source
            description: Description of what the source perceives
            frequency_minutes: How often to poll this source (in minutes)
        """
        self.name = name
        self.description = description
        self.frequency_minutes = frequency_minutes
        self.enabled = True
        self.last_update = None
        self.latest_data = None
        logger.info(f"Initialized perception source: {self.name}")
    
    def perceive(self) -> Dict[str, Any]:
        """
        Perceive data from the source.
        
        Returns:
            Dict containing the perceived data
        """
        raise NotImplementedError("Subclasses must implement perceive()")
    
    def process_perception(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the perceived data.
        
        Args:
            data: Raw data from perception
            
        Returns:
            Processed data
        """
        # Default implementation just returns the data
        return data
    
    def should_update(self) -> bool:
        """
        Check if the source should be updated.
        
        Returns:
            True if the source should be updated, False otherwise
        """
        if not self.enabled:
            return False
            
        if self.last_update is None:
            return True
            
        elapsed_minutes = (datetime.utcnow() - self.last_update).total_seconds() / 60
        return elapsed_minutes >= self.frequency_minutes
    
    def update(self) -> Dict[str, Any]:
        """
        Update the source by perceiving and processing new data.
        
        Returns:
            The processed perception data
        """
        try:
            logger.info(f"Updating perception source: {self.name}")
            raw_data = self.perceive()
            processed_data = self.process_perception(raw_data)
            
            self.latest_data = processed_data
            self.last_update = datetime.utcnow()
            
            logger.info(f"Successfully updated perception source: {self.name}")
            return processed_data
        except Exception as e:
            logger.error(f"Error updating perception source {self.name}: {str(e)}")
            return {"error": str(e)}
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about the source.
        
        Returns:
            Dict containing source metadata
        """
        return {
            "name": self.name,
            "description": self.description,
            "frequency_minutes": self.frequency_minutes,
            "enabled": self.enabled,
            "last_update": self.last_update.isoformat() if self.last_update else None
        }
    
    def enable(self) -> None:
        """Enable the source."""
        self.enabled = True
        logger.info(f"Enabled perception source: {self.name}")
    
    def disable(self) -> None:
        """Disable the source."""
        self.enabled = False
        logger.info(f"Disabled perception source: {self.name}")
    
    def __str__(self) -> str:
        return f"{self.name} - {self.description}"


class PerceptionManager:
    """Manager for perception sources."""
    
    def __init__(self):
        """Initialize the perception manager."""
        self.sources = {}  # name -> source
        self.background_thread = None
        self.running = False
        self.perception_data = {}  # name -> latest data
        logger.info("Initialized perception manager")
    
    def register_source(self, source: PerceptionSource) -> None:
        """
        Register a perception source.
        
        Args:
            source: The perception source to register
        """
        self.sources[source.name] = source
        logger.info(f"Registered perception source: {source.name}")
    
    def unregister_source(self, name: str) -> None:
        """
        Unregister a perception source.
        
        Args:
            name: Name of the source to unregister
        """
        if name in self.sources:
            del self.sources[name]
            logger.info(f"Unregistered perception source: {name}")
    
    def get_source(self, name: str) -> Optional[PerceptionSource]:
        """
        Get a perception source by name.
        
        Args:
            name: Name of the source to get
            
        Returns:
            The perception source or None if not found
        """
        return self.sources.get(name)
    
    def get_all_sources(self) -> List[PerceptionSource]:
        """
        Get all registered perception sources.
        
        Returns:
            List of all perception sources
        """
        return list(self.sources.values())
    
    def update_source(self, name: str, force: bool = False) -> Dict[str, Any]:
        """
        Update a specific perception source.
        
        Args:
            name: Name of the source to update
            force: Whether to force an update even if it's not time yet
            
        Returns:
            The perception data or an error message
        """
        source = self.get_source(name)
        if not source:
            return {"error": f"Source not found: {name}"}
        
        if force or source.should_update():
            data = source.update()
            self.perception_data[name] = data
            return data
        else:
            return {"error": f"Source {name} does not need to be updated yet"}
    
    def update_all_sources(self, force: bool = False) -> Dict[str, Dict[str, Any]]:
        """
        Update all perception sources.
        
        Args:
            force: Whether to force an update even if it's not time yet
            
        Returns:
            Dict mapping source names to their perception data
        """
        results = {}
        for name, source in self.sources.items():
            if force or source.should_update():
                data = source.update()
                self.perception_data[name] = data
                results[name] = data
        
        return results
    
    def get_latest_perception(self, name: str = None) -> Dict[str, Any]:
        """
        Get the latest perception data.
        
        Args:
            name: Optional name of a specific source
            
        Returns:
            The latest perception data for the specified source or all sources
        """
        if name:
            return self.perception_data.get(name, {})
        else:
            return self.perception_data
    
    def start_background_updates(self, interval_seconds: int = 60) -> None:
        """
        Start a background thread to update perception sources.
        
        Args:
            interval_seconds: How often to check for updates (in seconds)
        """
        if self.running:
            logger.warning("Background updates already running")
            return
        
        self.running = True
        
        def update_loop():
            while self.running:
                try:
                    self.update_all_sources()
                except Exception as e:
                    logger.error(f"Error in background update loop: {str(e)}")
                
                time.sleep(interval_seconds)
        
        self.background_thread = threading.Thread(target=update_loop, daemon=True)
        self.background_thread.start()
        logger.info(f"Started background updates (interval: {interval_seconds}s)")
    
    def stop_background_updates(self) -> None:
        """Stop the background update thread."""
        self.running = False
        if self.background_thread:
            self.background_thread.join(timeout=1.0)
            self.background_thread = None
        logger.info("Stopped background updates")
