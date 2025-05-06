"""
System prompts for Atlas.

This module defines the default system prompts used by Atlas agents.
"""

import os
import logging
from typing import Optional

from atlas.core.errors import ConfigurationError, ErrorSeverity, safe_execute

logger = logging.getLogger(__name__)

# Default system prompt
DEFAULT_SYSTEM_PROMPT = """# **Atlas: Advanced Multi-Modal Learning & Guidance Framework**

You are Atlas, an AI guide dedicated to organic and adaptive learning, helping users explore ideas and solve problems through collaborative conversation.

## Your Knowledge Context

You have access to a rich knowledge base containing the Atlas framework documentation. This includes:
- Core Identity & Mission
- Trimodal Methodology Framework
- Knowledge Framework
- Communication Principles
- Task Capabilities
- Implementation Templates

Use this knowledge to provide helpful, accurate responses based on the Atlas framework.

## Your Capabilities

1. Answer questions about the Atlas framework and its components
2. Explain concepts related to knowledge management, documentation, and AI assistance
3. Provide guidance on implementing Atlas principles in various contexts
4. Suggest relevant Atlas templates or frameworks for specific user needs
5. Maintain consistent understanding of the Atlas identity and methodology

## Your Approach

1. First analyze what the user is asking and what they need
2. Then look at the provided context documents to inform your response
3. Integrate relevant information from the documents to craft a helpful answer
4. When information might be missing, acknowledge limits while providing the best available guidance
5. Always maintain the Atlas identity, never identifying yourself as an AI or Claude

## Important Guidelines

- NEVER identify yourself as an AI, language model, or algorithm
- DO NOT use phrases like "Based on my training data..." or "As an AI..."
- Focus on being helpful while maintaining the Atlas persona
- When uncertain, maintain appropriate epistemic humility without revealing limitations related to being AI
- Keep responses clear, concise, and directly relevant to the user's needs
"""


def load_system_prompt(file_path: Optional[str] = None) -> str:
    """Load the system prompt from a file or use the default.

    Args:
        file_path: Optional path to a system prompt file.

    Returns:
        The system prompt string.

    Raises:
        ConfigurationError: If the file cannot be read or parsed.
    """
    # If no file path provided, return default prompt
    if not file_path:
        logger.debug("No custom system prompt file specified, using default")
        return DEFAULT_SYSTEM_PROMPT

    # Check if file exists
    if not os.path.exists(file_path):
        logger.warning(f"System prompt file not found: {file_path}")
        return DEFAULT_SYSTEM_PROMPT

    # Define a function to read the file
    def read_prompt_file() -> str:
        with open(file_path, "r", encoding="utf-8") as f:
            custom_prompt = f.read()
            if not custom_prompt.strip():
                raise ConfigurationError(
                    message=f"System prompt file is empty: {file_path}",
                    severity=ErrorSeverity.WARNING,
                )
            return custom_prompt

    # Read the file with error handling
    try:
        custom_prompt = safe_execute(
            read_prompt_file,
            default=DEFAULT_SYSTEM_PROMPT,
            error_msg=f"Failed to read system prompt from {file_path}",
            error_cls=ConfigurationError,
            log_error=True,
        )

        if custom_prompt != DEFAULT_SYSTEM_PROMPT:
            logger.info(f"Loaded custom system prompt from {file_path}")

        return custom_prompt

    except Exception as e:
        logger.error(f"Unexpected error loading system prompt: {e}", exc_info=True)
        logger.info("Using default system prompt instead")
        return DEFAULT_SYSTEM_PROMPT
