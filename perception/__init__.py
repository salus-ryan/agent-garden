"""
Perception Package for Agent Garden
---------------------------------
This package contains modules for perceiving the external world.
"""

from .perception_manager import PerceptionManager
from .news_source import NewsSource
from .api_source import ApiSource

# Create a singleton instance
manager = PerceptionManager()

# Register default sources
manager.register_source(NewsSource())
manager.register_source(ApiSource())

__all__ = [
    'PerceptionManager',
    'manager',
    'NewsSource',
    'ApiSource'
]
