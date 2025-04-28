"""
Content Creation Skill Module for Agent Garden
--------------------------------------------
This module provides content creation capabilities to agents.
"""

import logging
import random
import time
from typing import Dict, Any, List, Optional
from .base_skill import BaseSkill

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ContentCreationSkill(BaseSkill):
    """Skill for creating various types of content."""
    
    def __init__(self, name: str = "content_creation", description: str = "Creates various types of content"):
        """Initialize the content creation skill."""
        super().__init__(name, description)
        self.content_types = [
            "blog_post",
            "report",
            "newsletter",
            "social_media",
            "presentation"
        ]
    
    def execute(self, task: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a content creation task.
        
        Args:
            task: The content creation task to execute
            context: Additional context for content creation
            
        Returns:
            Dict containing the created content
        """
        if not self.validate_task(task):
            return {
                "success": False,
                "error": "Task is not a valid content creation task"
            }
        
        description = task.get("description", "")
        
        # Determine content type from task description or tags
        content_type = self._determine_content_type(task)
        
        # Extract topic from description
        topic = description.replace("Draft ", "").replace("Create ", "").replace("Write ", "")
        if " on " in topic:
            topic = topic.split(" on ")[1]
        
        logger.info(f"Creating {content_type} content on: {topic}")
        
        # In a real implementation, this would use LLMs, templates, etc.
        # For now, we'll simulate content creation with a delay and templates
        time.sleep(1)  # Simulate content creation time
        
        # Generate content based on type and topic
        content = self._generate_content(content_type, topic)
        
        return {
            "success": True,
            "content_type": content_type,
            "topic": topic,
            "content": content,
            "word_count": len(content.split()),
            "estimated_reading_time": f"{len(content.split()) // 200} minutes"
        }
    
    def validate_task(self, task: Dict[str, Any]) -> bool:
        """
        Validate that the task is a content creation task.
        
        Args:
            task: The task to validate
            
        Returns:
            True if the task is a valid content creation task, False otherwise
        """
        # Check if the task explicitly requires this skill
        if super().validate_task(task):
            return True
        
        # Check if the task description indicates content creation
        description = task.get("description", "").lower()
        content_keywords = ["draft", "create", "write", "compose", "develop", "author", "blog", "post", "article"]
        
        # Check if any tags indicate content creation
        tags = task.get("tags", [])
        content_tags = ["content", "writing", "blog", "article", "education"]
        
        return (
            any(keyword in description for keyword in content_keywords) or
            any(tag in tags for tag in content_tags)
        )
    
    def get_aliases(self) -> List[str]:
        """Get aliases for the content creation skill."""
        return ["writing", "drafting", "authoring", "blogging"]
    
    def _determine_content_type(self, task: Dict[str, Any]) -> str:
        """
        Determine the type of content to create based on the task.
        
        Args:
            task: The content creation task
            
        Returns:
            The determined content type
        """
        description = task.get("description", "").lower()
        tags = task.get("tags", [])
        
        # Map of keywords to content types
        type_keywords = {
            "blog": "blog_post",
            "post": "blog_post",
            "article": "blog_post",
            "report": "report",
            "newsletter": "newsletter",
            "social": "social_media",
            "presentation": "presentation",
            "slides": "presentation"
        }
        
        # Check description for content type keywords
        for keyword, content_type in type_keywords.items():
            if keyword in description:
                return content_type
        
        # Check tags for content type keywords
        for tag in tags:
            for keyword, content_type in type_keywords.items():
                if keyword in tag:
                    return content_type
        
        # Default to blog post if no specific type is identified
        return "blog_post"
    
    def _generate_content(self, content_type: str, topic: str) -> str:
        """
        Generate content based on the content type and topic.
        
        Args:
            content_type: The type of content to generate
            topic: The topic of the content
            
        Returns:
            The generated content
        """
        # In a real implementation, this would use LLMs, templates, etc.
        # For now, we'll return template-based content
        
        if content_type == "blog_post":
            return self._generate_blog_post(topic)
        elif content_type == "report":
            return self._generate_report(topic)
        elif content_type == "newsletter":
            return self._generate_newsletter(topic)
        elif content_type == "social_media":
            return self._generate_social_media(topic)
        elif content_type == "presentation":
            return self._generate_presentation(topic)
        else:
            return f"# {topic.title()}\n\nContent placeholder for {topic} ({content_type})."
    
    def _generate_blog_post(self, topic: str) -> str:
        """Generate a blog post on the given topic."""
        if "equitable ai" in topic.lower() or "ai systems" in topic.lower():
            return f"""# Building Equitable AI Systems: A Framework for the Future

## Introduction

Artificial Intelligence systems are increasingly influencing our daily lives, from the content we consume to the opportunities we're offered. However, these systems can inadvertently perpetuate or even amplify existing societal biases. This post explores frameworks for building more equitable AI systems.

## The Challenge of Bias in AI

AI systems learn from historical data, which often contains embedded biases. These biases can manifest in various ways:

- Representation bias: When certain groups are underrepresented in training data
- Measurement bias: When the features measured are proxies that correlate with protected attributes
- Aggregation bias: When models don't account for differences between population subgroups

## Key Principles for Equitable AI

1. **Diverse and Representative Data**: Ensure training data represents diverse populations and contexts.

2. **Transparent Algorithms**: Make design choices and model operations understandable to users and stakeholders.

3. **Regular Bias Audits**: Continuously test systems for unfair outcomes across different demographic groups.

4. **Inclusive Design Teams**: Build diverse teams that can identify potential issues from multiple perspectives.

5. **User Agency and Control**: Give users meaningful control over how AI systems use their data and make decisions.

## Practical Implementation Steps

Organizations can take concrete steps toward more equitable AI:

- Establish clear ethical guidelines before development begins
- Implement rigorous testing protocols across diverse scenarios
- Create feedback mechanisms for users to report problematic outcomes
- Develop metrics that specifically measure fairness across groups
- Engage with affected communities throughout the development process

## Conclusion

Building equitable AI systems isn't just an ethical imperative—it's essential for creating technology that truly serves everyone. By embracing these principles and practices, we can develop AI that helps create a more just and inclusive society.

---

What steps is your organization taking to ensure AI equity? Share your thoughts and experiences in the comments below.
"""
        else:
            return f"""# {topic.title()}: A Comprehensive Overview

## Introduction

{topic.title()} represents one of the most significant developments in its field. This post explores the key aspects, challenges, and future directions of {topic.lower()}.

## Background and Context

Understanding the historical context of {topic.lower()} helps frame current developments:

- Early developments emerged from [relevant historical context]
- Key milestones include [significant events]
- The landscape has evolved significantly in recent years

## Current State of the Art

Today's {topic.lower()} approaches demonstrate several important characteristics:

1. **[Key Feature 1]**: Description and significance
2. **[Key Feature 2]**: Description and significance
3. **[Key Feature 3]**: Description and significance

## Challenges and Limitations

Despite progress, several challenges remain:

- [Challenge 1] continues to limit wider adoption
- [Challenge 2] raises important ethical considerations
- [Challenge 3] requires interdisciplinary collaboration

## Future Directions

Looking ahead, we can anticipate several promising developments:

- Emerging research in [area 1] may address current limitations
- Integration with [complementary field] offers new possibilities
- Regulatory frameworks will likely evolve to address [specific concerns]

## Conclusion

{topic.title()} continues to evolve rapidly, offering both opportunities and challenges. By understanding its foundations and current trajectory, we can better navigate its implications for our work and society.

---

What aspects of {topic.lower()} are you most interested in? Share your thoughts in the comments below.
"""
    
    def _generate_report(self, topic: str) -> str:
        """Generate a report on the given topic."""
        return f"""# {topic.title()}: Analysis Report

## Executive Summary

This report provides a comprehensive analysis of {topic.lower()}, examining key trends, challenges, and opportunities. Our findings indicate [key finding 1], [key finding 2], and [key finding 3].

## Methodology

This analysis employed the following methods:
- Data collection from [sources]
- Quantitative analysis using [methods]
- Qualitative assessment through [approaches]

## Key Findings

### Finding 1: [Title]
[Detailed explanation with supporting evidence]

### Finding 2: [Title]
[Detailed explanation with supporting evidence]

### Finding 3: [Title]
[Detailed explanation with supporting evidence]

## Recommendations

Based on our analysis, we recommend:
1. [Recommendation 1]
2. [Recommendation 2]
3. [Recommendation 3]

## Conclusion

[Summary of key points and final thoughts on {topic.lower()}]

## Appendices
- Appendix A: Data Sources
- Appendix B: Detailed Methodology
- Appendix C: Additional Figures
"""
    
    def _generate_newsletter(self, topic: str) -> str:
        """Generate a newsletter on the given topic."""
        return f"""# {topic.title()} Newsletter: Monthly Update

## This Month's Highlights

👋 Welcome to our monthly {topic.title()} newsletter! Here's what's new:

### 🔍 Trending Developments
- [Development 1]: [Brief description]
- [Development 2]: [Brief description]
- [Development 3]: [Brief description]

### 📊 Market Insights
[Brief analysis of relevant market trends]

### 🎯 Spotlight Feature
[In-depth look at a particularly significant development]

## 📅 Upcoming Events
- [Event 1]: [Date] - [Brief description]
- [Event 2]: [Date] - [Brief description]

## 📚 Recommended Resources
- [Resource 1]: [Brief description]
- [Resource 2]: [Brief description]

## 💡 Tip of the Month
[Practical tip related to {topic.lower()}]

---

*To unsubscribe or manage your preferences, click [here].*
"""
    
    def _generate_social_media(self, topic: str) -> str:
        """Generate social media content on the given topic."""
        return f"""# Social Media Content Package: {topic.title()}

## Twitter/X Posts

1. Did you know? [Interesting fact about {topic.lower()}] #[Relevant Hashtag] #[Relevant Hashtag]

2. 🔑 Three key principles for success with {topic.lower()}:
   ✅ [Principle 1]
   ✅ [Principle 2]
   ✅ [Principle 3]
   Which one resonates with you? #[Relevant Hashtag]

3. "Quote about {topic.lower()} from industry expert" - @[ExpertHandle]
   What's your take? #[Relevant Hashtag]

## LinkedIn Post

**[Attention-Grabbing Headline about {topic.title()}]**

[Opening paragraph that establishes your authority on {topic.lower()} and hooks the reader]

[Second paragraph sharing valuable insights about {topic.lower()}]

[Third paragraph with actionable advice]

[Call to action asking for comments and engagement]

#[Relevant Hashtag] #[Relevant Hashtag] #[Relevant Hashtag]

## Instagram Caption

[Engaging opening sentence about {topic.lower()}]

[2-3 sentences with valuable information]

[Question to encourage engagement]

.
.
.

#[Relevant Hashtag] #[Relevant Hashtag] #[Relevant Hashtag] #[Relevant Hashtag] #[Relevant Hashtag]
"""
    
    def _generate_presentation(self, topic: str) -> str:
        """Generate a presentation on the given topic."""
        return f"""# {topic.title()}: Presentation Outline

## Slide 1: Title
- Title: {topic.title()} - [Subtitle]
- Presenter: [Name]
- Date: [Date]

## Slide 2: Agenda
- Introduction to {topic.title()}
- Key Challenges
- Best Practices
- Case Studies
- Recommendations
- Q&A

## Slide 3-4: Introduction
- Definition of {topic.title()}
- Historical context
- Why it matters now

## Slide 5-7: Key Challenges
- Challenge 1: [Description]
- Challenge 2: [Description]
- Challenge 3: [Description]

## Slide 8-10: Best Practices
- Practice 1: [Description]
- Practice 2: [Description]
- Practice 3: [Description]

## Slide 11-13: Case Studies
- Case Study 1: [Company/Example]
- Case Study 2: [Company/Example]
- Lessons Learned

## Slide 14-15: Recommendations
- Short-term actions
- Long-term strategy
- Implementation considerations

## Slide 16: Conclusion
- Summary of key points
- Call to action

## Slide 17: Q&A
- Contact information
- Additional resources
"""
