"""
Skills Package for Agent Garden
------------------------------
This package contains skill modules that agents can use to perform various tasks.
"""

from .base_skill import BaseSkill
from .skill_registry import registry, SkillRegistry
from .research_skill import ResearchSkill
from .content_creation_skill import ContentCreationSkill
from .monitoring_skill import MonitoringSkill

# Initialize default skills
registry.register_skill(ResearchSkill)
registry.register_skill(ContentCreationSkill)
registry.register_skill(MonitoringSkill)

# Instantiate default skills
research_skill = ResearchSkill()
registry.skills["research"] = research_skill

content_creation_skill = ContentCreationSkill()
registry.skills["content_creation"] = content_creation_skill

monitoring_skill = MonitoringSkill()
registry.skills["monitoring"] = monitoring_skill

__all__ = [
    'BaseSkill',
    'SkillRegistry',
    'registry',
    'ResearchSkill',
    'ContentCreationSkill',
    'MonitoringSkill'
]
