# Atlas Examples

This document serves as the central reference for Atlas examples, covering their organization, implementation standards, and developer guidelines.

## 1. Organization & Structure

Examples are organized by feature area with a numeric prefix to indicate a logical learning progression:

### Basic Usage (00-09)

- `01_query_simple.py` - Basic querying using the Atlas framework
  - Demonstrates simple query, retrieve-only, and query-with-context
  - Shows integration with different providers

- `02_query_streaming.py` - Streaming responses from language models
  - Shows basic streaming with character-by-character output
  - Implements custom streaming callbacks
  - Demonstrates graceful degradation for non-streaming providers

- `03_provider_selection.py` - Provider and model selection
  - Shows automatic provider resolution
  - Demonstrates capability-based model selection
  - Verifies correct interface between providers and clients

### Knowledge & Retrieval (10-19)

- `10_document_ingestion.py` - Ingesting documents into the knowledge base
  - Demonstrates loading documents from a directory
  - Shows chunking and embedding generation
  - Verifies ingestion through simple retrieval

- `11_basic_retrieval.py` - Document retrieval and relevance scoring
  - Shows basic document retrieval
  - Implements threshold-based filtering
  - Demonstrates metadata filtering
  - Integrates with query client

### Advanced Features (20-29)

- `20_tool_agent.py.todo` - Tool usage with agents
- `21_multi_agent.py.todo` - Multi-agent communication
- `22_agent_workflows.py.todo` - LangGraph integration

## 2. Standardization

All examples follow a consistent structure and implementation pattern:

### Common Utilities (`common.py`)

We've created shared utilities that all examples use:

- `configure_example_logging()`: Sets up Atlas's centralized logging
- `get_base_argument_parser()`: Creates standard CLI parser
- `setup_example()`: One-step example initialization
- `create_provider_from_args()`: Consistent provider creation
- `print_example_footer()`: Standardized footer

### Standard Example Structure

```python
"""
Brief description of the example.

This should explain what the example demonstrates and key concepts.
"""

# Imports from standard library
import sys
from typing import Dict, Any, List

# Import common utilities
from common import setup_example, create_provider_from_args, print_example_footer
from atlas.core import logging

# Import Atlas modules
from atlas import relevant_modules

def add_example_arguments(parser):
    """Add example-specific arguments to the parser."""
    # Add custom arguments beyond the standard ones
    parser.add_argument(
        "--custom-arg",
        help="Description of custom argument"
    )

def main():
    """Run the example."""
    # Set up the example (logging, CLI parsing)
    args = setup_example("Example Title", add_example_arguments)
    logger = logging.get_logger(__name__)

    # Example implementation
    # ...

    # Print standardized footer
    print_example_footer()

if __name__ == "__main__":
    main()
```

### CLI Interface

All examples support a standard set of CLI arguments:

```
# Standard arguments
-h, --help            Show help message
--provider PROVIDER   Provider to use (e.g., anthropic, openai, mock)
--model MODEL         Model to use
--capability {inexpensive,efficient,premium,vision,standard}
-v, --verbose         Enable verbose (DEBUG) logging

# Example-specific arguments vary by example
```

### Logging System

Examples use Atlas's centralized logging system:

- Configurable through environment variables
- Integrates with Rich for better formatting
- Quiets noisy third-party loggers
- Supports verbose mode with `-v` flag

## 3. Implementation Status

| Example                      | Status      | Notes                                       |
|------------------------------|-------------|---------------------------------------------|
| 01_query_simple.py           | ✅ Complete | Uses standardized utilities                 |
| 02_query_streaming.py        | ✅ Complete | Uses standardized utilities                 |
| 03_provider_selection.py     | ✅ Complete | Uses standardized utilities                 |
| 10_document_ingestion.py     | ✅ Complete | Fixed to use DocumentProcessor correctly    |
| 11_basic_retrieval.py        | ✅ Complete | Updated for correct exception handling      |
| 12_hybrid_retrieval.py.todo  | 🔄 Planned  | To be implemented with keyword search       |
| 20_tool_agent.py.todo        | 🔄 Planned  | Needs tool system implementation            |
| 21_multi_agent.py.todo       | 🔄 Planned  | Needs agent controller implementation       |
| 22_agent_workflows.py.todo   | 🔄 Planned  | Needs LangGraph workflow implementation     |

## 4. Running Examples

All examples can be run directly from the command line with sensible defaults:

### Basic Setup

```bash
# Ensure you're in the Atlas project root directory
cd /path/to/atlas

# Create and activate a virtual environment (if needed)
uv venv
source .venv/bin/activate

# Install Atlas in development mode
uv pip install -e .
```

### Running Examples

```bash
# Run with default settings (uses mock provider)
python examples/01_query_simple.py

# Run with a specific provider
python examples/01_query_simple.py --provider anthropic
python examples/01_query_simple.py --provider openai

# Use capability-based model selection
python examples/01_query_simple.py --provider anthropic --capability premium

# Use a specific model
python examples/02_query_streaming.py --model claude-3-sonnet-20240229

# Enable verbose logging
python examples/01_query_simple.py -v
```

### Example Dependencies

Some examples depend on others for setup:

- `10_document_ingestion.py` should be run before retrieval examples
- `11_basic_retrieval.py` requires documents to have been ingested

## 5. Environment Configuration

All examples respect the following environment variables:

```bash
# Log level configuration
export ATLAS_LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR

# Provider API keys
export ANTHROPIC_API_KEY=sk-ant-...
export OPENAI_API_KEY=sk-...

# Default provider and model
export ATLAS_DEFAULT_PROVIDER=anthropic
export ATLAS_DEFAULT_MODEL=claude-3-sonnet-20240229

# Database configuration
export ATLAS_DB_PATH=/custom/path/to/db
export ATLAS_COLLECTION_NAME=my_custom_collection
```

## 6. Developer Guidelines

When creating or updating examples:

### Creating New Examples

1. Use existing examples as templates
2. Follow the numeric prefix convention for organizing examples
3. Include detailed docstrings explaining what the example demonstrates
4. Use the common utilities for consistent CLI and logging
5. Test with both mock provider and real providers

### Updating Existing Examples

1. Maintain backward compatibility where possible
2. Update examples to use latest API patterns
3. Ensure all examples pass with mock provider
4. Keep CLI interfaces consistent between examples

### Testing Examples

Before committing changes:

1. Run with default settings (`python examples/example.py`)
2. Run with verbose flag (`python examples/example.py -v`)
3. Run with mock provider (`python examples/example.py --provider mock`)
4. Verify proper error handling with invalid inputs

## 7. Future Work

Planned improvements to examples:

1. Add hybrid retrieval example combining semantic and keyword search
2. Implement tool agent example with the toolkit interface
3. Create multi-agent example with controller/worker pattern
4. Add LangGraph workflow examples
5. Develop comprehensive testing for all examples
6. Expand documentation with more in-line comments
7. Add Jupyter notebook versions of examples

## 8. Bug Fixes Implemented

Issues fixed during standardization:

1. Fixed provider selection example to use ModelRequest/ModelMessage
2. Corrected document ingestion to use DocumentProcessor correctly
3. Fixed error handling in retrieval examples
4. Standardized metadata extraction in retrieval examples
5. Improved robustness of streaming examples
6. Fixed centralized logging setup to quiet ChromaDB and other noisy loggers

## 9. Future Improvements & Known Issues

1. Metadata filtering in RetrievalFilter needs update for newer ChromaDB versions
2. Document content handling in query_with_context needs better standardization
3. Logger name consistency needs better enforcement
4. Examples with Todo extensions need implementation
5. More comprehensive error handling for external API failures
