"""
Provider capabilities module.

This module defines capability types, strength levels, and task mappings to enable
task-aware provider selection and capability-based model resolution.
"""

import re
from enum import IntEnum, Enum
from typing import Dict, Set, List, Optional, Any, Union, cast


class CapabilityLevel(IntEnum):
    """Enumeration of capability strength levels.
    
    These levels define how well a model performs with a particular capability,
    from none (0) to exceptional (4).
    """
    NONE = 0        # No capability
    BASIC = 1       # Has the capability but limited
    MODERATE = 2    # Average capability
    STRONG = 3      # Excellent at this capability 
    EXCEPTIONAL = 4 # Best-in-class for this capability
    
    def __str__(self) -> str:
        """Return the string representation of the strength level."""
        return self.name.lower()


# CapabilityStrength is kept for backward compatibility
CapabilityStrength = CapabilityLevel


class Capability(str, Enum):
    """Enumeration of capabilities supported by providers."""
    
    # Operational capabilities
    INEXPENSIVE = "inexpensive"  # Low cost per token
    EFFICIENT = "efficient"      # Good balance of performance and cost
    PREMIUM = "premium"          # High-end models with best quality
    STANDARD = "standard"        # Standard text completion
    STREAMING = "streaming"      # Efficient streaming support
    VISION = "vision"            # Visual content understanding
    
    # Task capabilities
    REASONING = "reasoning"       # General reasoning ability
    LOGIC = "logic"               # Logical reasoning and deduction
    MATH = "math"                 # Mathematical computation and reasoning
    ANALYSIS = "analysis"         # Detailed analytical thinking
    CODE = "code"                 # Code generation and understanding
    CREATIVE = "creative"         # Creative content generation
    SUMMARIZATION = "summarization" # Content summarization
    EXTRACTION = "extraction"      # Information extraction from text
    FORMATTING = "formatting"      # Structured output formatting
    TOOL_USE = "tool_use"          # Ability to use tools
    JSON_OUTPUT = "json_output"    # Ability to output well-formatted JSON
    
    # Domain capabilities
    SCIENCE = "science"           # Scientific knowledge
    FINANCE = "finance"           # Financial knowledge
    LEGAL = "legal"               # Legal knowledge
    MEDICAL = "medical"           # Medical knowledge
    TECHNICAL = "technical"       # Technical knowledge
    MULTILINGUAL = "multilingual" # Support for multiple languages


# Operational Capabilities
# These capabilities relate to operational characteristics like cost and performance

# Cost-related capabilities
CAPABILITY_INEXPENSIVE = "inexpensive"  # Low cost per token
CAPABILITY_EFFICIENT = "efficient"      # Good balance of performance and cost
CAPABILITY_PREMIUM = "premium"          # High-end models with best quality

# Mode-related capabilities
CAPABILITY_STANDARD = "standard"        # Standard text completion
CAPABILITY_STREAMING = "streaming"      # Efficient streaming support
CAPABILITY_VISION = "vision"            # Visual content understanding

# Task Capabilities
# These capabilities relate to specific tasks the model can perform

# Reasoning capabilities
CAPABILITY_REASONING = "reasoning"       # General reasoning ability
CAPABILITY_LOGIC = "logic"               # Logical reasoning and deduction
CAPABILITY_MATH = "math"                 # Mathematical computation and reasoning
CAPABILITY_ANALYSIS = "analysis"         # Detailed analytical thinking

# Generation capabilities
CAPABILITY_CODE = "code"                  # Code generation and understanding
CAPABILITY_CREATIVE = "creative"          # Creative content generation
CAPABILITY_SUMMARIZATION = "summarization" # Content summarization
CAPABILITY_EXTRACTION = "extraction"      # Information extraction from text
CAPABILITY_FORMATTING = "formatting"      # Structured output formatting

# Domain Capabilities
# These capabilities relate to specific knowledge domains

# Domain knowledge
CAPABILITY_SCIENCE = "science"           # Scientific knowledge
CAPABILITY_FINANCE = "finance"           # Financial knowledge
CAPABILITY_LEGAL = "legal"               # Legal knowledge
CAPABILITY_MEDICAL = "medical"           # Medical knowledge
CAPABILITY_TECHNICAL = "technical"       # Technical knowledge

# Language capabilities
CAPABILITY_MULTILINGUAL = "multilingual" # Support for multiple languages

# Collections of capabilities
ALL_OPERATIONAL_CAPABILITIES = {
    CAPABILITY_INEXPENSIVE,
    CAPABILITY_EFFICIENT,
    CAPABILITY_PREMIUM,
    CAPABILITY_STANDARD,
    CAPABILITY_STREAMING,
    CAPABILITY_VISION
}

ALL_TASK_CAPABILITIES = {
    CAPABILITY_REASONING,
    CAPABILITY_LOGIC,
    CAPABILITY_MATH,
    CAPABILITY_ANALYSIS,
    CAPABILITY_CODE,
    CAPABILITY_CREATIVE,
    CAPABILITY_SUMMARIZATION,
    CAPABILITY_EXTRACTION,
    CAPABILITY_FORMATTING
}

ALL_DOMAIN_CAPABILITIES = {
    CAPABILITY_SCIENCE,
    CAPABILITY_FINANCE,
    CAPABILITY_LEGAL,
    CAPABILITY_MEDICAL,
    CAPABILITY_TECHNICAL,
    CAPABILITY_MULTILINGUAL
}

# All capabilities combined
ALL_CAPABILITIES = ALL_OPERATIONAL_CAPABILITIES.union(
    ALL_TASK_CAPABILITIES, ALL_DOMAIN_CAPABILITIES
)

# Task Types
TASK_CONVERSATIONAL = "conversational"   # General conversation
TASK_CODE_GENERATION = "code_generation" # Writing code
TASK_SUMMARIZATION = "summarization"     # Summarizing content
TASK_CREATIVE_WRITING = "creative_writing" # Creative content generation
TASK_DATA_ANALYSIS = "data_analysis"     # Analyzing data and trends
TASK_INFORMATION_EXTRACTION = "information_extraction" # Extracting structured info
TASK_TRANSLATION = "translation"         # Language translation
TASK_MATH_PROBLEM_SOLVING = "math_problem_solving" # Solving math problems

# Task Capability Requirements
# Maps task types to required capabilities and their minimum strengths
TASK_CAPABILITY_REQUIREMENTS: Dict[str, Dict[str, CapabilityStrength]] = {
    TASK_CONVERSATIONAL: {
        CAPABILITY_REASONING: CapabilityStrength.MODERATE,
        CAPABILITY_STANDARD: CapabilityStrength.MODERATE
    },
    TASK_CODE_GENERATION: {
        CAPABILITY_CODE: CapabilityStrength.STRONG,
        CAPABILITY_REASONING: CapabilityStrength.MODERATE,
        CAPABILITY_TECHNICAL: CapabilityStrength.MODERATE
    },
    TASK_SUMMARIZATION: {
        CAPABILITY_SUMMARIZATION: CapabilityStrength.STRONG,
        CAPABILITY_REASONING: CapabilityStrength.MODERATE
    },
    TASK_CREATIVE_WRITING: {
        CAPABILITY_CREATIVE: CapabilityStrength.STRONG,
        CAPABILITY_REASONING: CapabilityStrength.MODERATE
    },
    TASK_DATA_ANALYSIS: {
        CAPABILITY_ANALYSIS: CapabilityStrength.STRONG,
        CAPABILITY_REASONING: CapabilityStrength.STRONG,
        CAPABILITY_MATH: CapabilityStrength.MODERATE
    },
    TASK_INFORMATION_EXTRACTION: {
        CAPABILITY_EXTRACTION: CapabilityStrength.STRONG,
        CAPABILITY_REASONING: CapabilityStrength.MODERATE
    },
    TASK_TRANSLATION: {
        CAPABILITY_MULTILINGUAL: CapabilityStrength.STRONG
    },
    TASK_MATH_PROBLEM_SOLVING: {
        CAPABILITY_MATH: CapabilityStrength.STRONG,
        CAPABILITY_REASONING: CapabilityStrength.STRONG
    }
}

# Task detection patterns
# Regex patterns used to detect task types from prompts
TASK_DETECTION_PATTERNS = {
    TASK_CODE_GENERATION: [
        r"(?i)(?:write|generate|create|implement|code)\s+(?:a|some|the)?\s*(?:code|function|class|implementation|program)",
        r"(?i)how\s+(?:do|would)\s+I\s+(?:code|program|implement|write)",
        r"(?i)(?:can|could)\s+you\s+(?:write|create|generate|code)\s+(?:a|some|the)\s+(?:code|implementation)"
    ],
    TASK_SUMMARIZATION: [
        r"(?i)(?:summarize|summarization|summary|tldr|tl;dr)",
        r"(?i)(?:can|could)\s+you\s+(?:summarize|provide\s+a\s+summary)",
        r"(?i)(?:give|provide)\s+(?:me|us)?\s+(?:a|the)\s+(?:brief|short|quick|concise)?\s*summary"
    ],
    TASK_CREATIVE_WRITING: [
        r"(?i)(?:write|compose|create)\s+(?:a|an|the)?\s*(?:story|poem|essay|article|blog|fiction)",
        r"(?i)(?:creative|imaginative|fictional|poetic|artistic)\s+(?:writing|composition|text|content)",
        r"(?i)(?:can|could)\s+you\s+(?:write|create|compose)\s+(?:something|anything)\s+(?:creative|imaginative)"
    ],
    TASK_DATA_ANALYSIS: [
        r"(?i)(?:analyze|analyse|analysis|evaluate|examine)\s+(?:this|the|these|that|my)?\s*(?:data|dataset|numbers|metrics|statistics)",
        r"(?i)(?:what|find|identify)\s+(?:patterns|trends|insights|conclusions|correlations|relationship)",
        r"(?i)(?:can|could)\s+you\s+(?:analyze|analyse|evaluate|interpret)\s+(?:this|the|these|that|my)"
    ],
    TASK_INFORMATION_EXTRACTION: [
        r"(?i)(?:extract|pull|identify|find|list)\s+(?:all|the|every|each)?\s*(?:entities|names|dates|information|values|facts)",
        r"(?i)(?:information|data)\s+extraction",
        r"(?i)(?:can|could)\s+you\s+(?:extract|identify|find|list)\s+(?:all|the)?\s*(?:key|important|relevant)?\s*(?:information|data|facts)"
    ],
    TASK_TRANSLATION: [
        r"(?i)(?:translate|translation|convert)\s+(?:this|the|following|these|that|my)?\s*(?:text|content|sentence|paragraph|document|phrase)",
        r"(?i)(?:from|in)\s+(?:[a-z]+)\s+(?:to|into)\s+(?:[a-z]+)",
        r"(?i)(?:can|could)\s+you\s+(?:translate|convert)\s+(?:this|the|following)"
    ],
    TASK_MATH_PROBLEM_SOLVING: [
        r"(?i)(?:solve|calculate|compute|evaluate|find)\s+(?:this|the|following|these)?\s*(?:math|mathematical|problem|equation|expression)",
        r"(?i)(?:what|find)\s+(?:is|the)\s+(?:value|solution|result|answer)",
        r"(?i)(?:can|could)\s+you\s+(?:solve|calculate|compute|evaluate|find)\s+(?:this|the)"
    ]
}


def get_capabilities_for_task(task_type: str) -> Dict[str, CapabilityStrength]:
    """Get the capability requirements for a specific task type.
    
    Args:
        task_type: The type of task
        
    Returns:
        Dictionary mapping capability names to required strength levels
        
    Raises:
        ValueError: If the task type is not recognized
    """
    requirements = TASK_CAPABILITY_REQUIREMENTS.get(task_type)
    if not requirements:
        raise ValueError(f"Unknown task type: {task_type}")
    return requirements.copy()


def detect_task_type_from_prompt(prompt: str) -> Optional[str]:
    """Detect the likely task type from a prompt using heuristics.
    
    Args:
        prompt: The user prompt text
        
    Returns:
        Detected task type, or None if no confident detection
    """
    # Default to conversational if prompt is too short
    if len(prompt) < 10:
        return TASK_CONVERSATIONAL
    
    # Check each task's patterns for matches
    task_matches = {}
    
    for task, patterns in TASK_DETECTION_PATTERNS.items():
        matches = 0
        for pattern in patterns:
            if re.search(pattern, prompt):
                matches += 1
        
        if matches > 0:
            # Calculate confidence score (matches / total patterns)
            confidence = matches / len(patterns)
            task_matches[task] = confidence
    
    # If no matches, default to conversational
    if not task_matches:
        return TASK_CONVERSATIONAL
    
    # Get task with highest confidence
    best_task = max(task_matches.items(), key=lambda x: x[1])
    
    # Require minimum confidence threshold of 0.5
    if best_task[1] >= 0.5:
        return best_task[0]
    
    # Default to conversational if confidence is too low
    return TASK_CONVERSATIONAL


def parse_capability_string(capability_str: str) -> Dict[str, CapabilityStrength]:
    """Parse a capability string in the format 'name:strength,name:strength'.
    
    Examples:
        "code:strong,reasoning:moderate" -> {CAPABILITY_CODE: CapabilityStrength.STRONG, ...}
        "inexpensive" -> {CAPABILITY_INEXPENSIVE: CapabilityStrength.MODERATE}
    
    Args:
        capability_str: Comma-separated capability string
        
    Returns:
        Dictionary mapping capability names to strength levels
    """
    capabilities = {}
    
    # Split by comma for multiple capabilities
    for part in capability_str.split(','):
        part = part.strip()
        if not part:
            continue
        
        # Check if there's a strength specified
        if ':' in part:
            name, strength = part.split(':', 1)
            name = name.strip().lower()
            strength = strength.strip().lower()
            
            # Convert name to capability constant if it exists
            capability = name
            for cap in ALL_CAPABILITIES:
                if cap.lower() == name:
                    capability = cap
                    break
            
            # Convert strength string to enum
            try:
                # Convert string to actual enum member using proper typing
                strength_level = cast(CapabilityStrength, getattr(CapabilityStrength, strength.upper()))
            except (AttributeError, KeyError):
                # Default to MODERATE if unrecognized
                strength_level = CapabilityStrength.MODERATE
            
            capabilities[capability] = strength_level
        else:
            # No strength specified, default to MODERATE
            name = part.lower()
            
            # Convert name to capability constant if it exists
            capability = name
            for cap in ALL_CAPABILITIES:
                if cap.lower() == name:
                    capability = cap
                    break
            
            capabilities[capability] = CapabilityStrength.MODERATE
    
    return capabilities