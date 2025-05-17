---
title: CLI
---

# CLI Planning - May 10, 2025

This document outlines the planning and tracking system for Atlas CLI improvements, including the architecture, logging enhancements, and command-line interface upgrades.

## Current Status

```
✅ Basic CLI functionality with query, ingest modes
🔄 Next focus: Improved logging system, verbosity controls, and CLI architecture
```

## CLI Architecture

```
atlas/
├── core/
│   ├── __init__.py
│   ├── config.py             # Existing - extend with CLI config
│   ├── env.py                # Existing - enhance environment integration
│   ├── errors.py             # Existing - extend with user-friendly messages
│   ├── logging.py            # NEW - Centralized logging system
│   ├── cli/                  # NEW - CLI framework
│   │   ├── __init__.py
│   │   ├── base.py           # NEW - Base CLI command structure
│   │   ├── commands/         # NEW - Command implementations
│   │   │   ├── __init__.py
│   │   │   ├── query.py      # NEW - Query command implementation
│   │   │   ├── ingest.py     # NEW - Ingest command implementation
│   │   │   ├── tool.py       # NEW - Tool command implementation
│   │   │   └── serve.py      # NEW - API server command
│   │   └── options.py        # NEW - Common CLI options
│   └── telemetry.py          # Existing - enhance with CLI events
└── bin/                      # NEW - Executable entry points
    ├── atlas                 # NEW - Main CLI entry point
    ├── atlas-query           # NEW - Direct query tool
    ├── atlas-ingest          # NEW - Direct ingest tool
    └── atlas-serve           # NEW - API server launcher
```

## Implementation Tasks

1. **Logging System Enhancement (High Priority)**
   - [ ] Create centralized logging configuration system
   - [ ] Implement structured logging with configurable formats
   - [ ] Add log level controls for different components
   - [ ] Integrate third-party library log suppression
   - [ ] Create custom log formatters for CLI and file output
   - [ ] Add telemetry controls for OpenTelemetry output
   - [ ] Implement log file rotation and management
   - [ ] Create user-friendly error reporting formats

2. **CLI Framework Implementation (High Priority)**
   - [ ] Design command architecture with subcommand pattern
   - [ ] Implement common option handling (verbosity, config, etc.)
   - [ ] Create consistent help text generation
   - [ ] Add shell completion support
   - [ ] Implement color output for better readability
   - [ ] Create progress indicators for long-running operations
   - [ ] Add configuration file support
   - [ ] Implement plugin architecture for extensibility

3. **Command Implementation (Medium Priority)**
   - [ ] Refactor existing query functionality to command pattern
   - [ ] Enhance ingest command with more options
   - [ ] Create tool command for local tool execution
   - [ ] Implement serve command for API endpoint
   - [ ] Add interactive mode for CLI operations
   - [ ] Create admin commands for system management
   - [ ] Add development utilities for debugging

## MVP Implementation Strategy

The Atlas CLI enhancement follows a **Progressive Improvement** approach that incrementally enhances the existing CLI capabilities while maintaining compatibility with current usage patterns.

### Phase 1: Logging Enhancement

**Critical Path [P0]:**
- [ ] Create core/logging.py with centralized configuration
- [ ] Implement structured logging with structlog
- [ ] Add verbosity controls via environment and CLI
- [ ] Create formatters for console and file output
- [ ] Implement ChromaDB and other library log suppression
- [ ] Add OpenTelemetry export controls
- [ ] Create consistent error reporting format

**Important [P1]:**
- [ ] Add log file configuration and rotation
- [ ] Implement component-specific log levels
- [ ] Create color-coded output for console logs
- [ ] Add trace context propagation
- [ ] Implement contextual logging with request IDs
- [ ] Create log filtering for sensitive information
- [ ] Add metrics collection for key operations

**Nice to Have [P2]:**
- [ ] Implement structured JSON logging option
- [ ] Add log aggregation capabilities
- [ ] Create dashboard visualization integration
- [ ] Implement advanced sampling for verbose logs
- [ ] Add automated log analysis tools
- [ ] Create performance logging middleware

### Phase 2: CLI Framework

**Critical Path [P0]:**
- [ ] Design modular command architecture
- [ ] Implement common option handling
- [ ] Create consistent help documentation
- [ ] Add environment variable integration
- [ ] Implement configuration file support
- [ ] Create progress indicators for operations
- [ ] Add color support for console output

**Important [P1]:**
- [ ] Implement shell completion
- [ ] Add plugin architecture for extensibility
- [ ] Create command aliasing system
- [ ] Implement interactive mode
- [ ] Add batch processing capabilities
- [ ] Create validation for command inputs
- [ ] Implement chaining of commands

### Phase 3: Executable Commands

**Critical Path [P0]:**
- [ ] Create executable entry points
- [ ] Implement command discovery mechanism
- [ ] Add version information and help commands
- [ ] Create consistent exit code convention
- [ ] Implement signal handling
- [ ] Add installation and packaging support
- [ ] Create user documentation for commands

**Important [P1]:**
- [ ] Add self-update mechanism
- [ ] Implement command caching for performance
- [ ] Create dependency validation
- [ ] Add command suggestions for errors
- [ ] Implement intelligent defaults
- [ ] Create profiles for different use cases
- [ ] Add environment detection and adaptation

## Key Implementation Components

### 1. Logging Configuration System

```python
# atlas/core/logging.py
import logging
import os
import sys
from typing import Optional, Literal, Dict, Any

import structlog
from structlog.types import Processor


def configure_logging(
    verbosity: int = 0,
    log_format: str = "text",
    log_file: Optional[str] = None,
    quiet: bool = False,
    component_levels: Optional[Dict[str, int]] = None,
):
    """Configure Atlas logging system with appropriate verbosity level.

    Args:
        verbosity: 0-3, where 0 is minimal and 3 is debug-level output
        log_format: "text", "json", or "colored" for output formatting
        log_file: Optional path to log file
        quiet: Suppress all non-error output
        component_levels: Optional dictionary of component-specific log levels
    """
    # Map verbosity to logging level
    level = {
        0: logging.WARNING,  # Default: warnings and errors only
        1: logging.INFO,     # -v: info level
        2: logging.DEBUG,    # -vv: debug level
        3: logging.NOTSET,   # -vvv: everything
    }.get(verbosity, logging.INFO)

    if quiet:
        level = logging.ERROR  # Override with quiet mode

    # Configure structlog processors
    processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    # Add formatter based on format
    if log_format == "json":
        processors.append(structlog.processors.JSONRenderer())
    elif log_format == "colored":
        processors.append(structlog.dev.ConsoleRenderer(colors=True))
    else:
        processors.append(structlog.dev.ConsoleRenderer(colors=False))

    # Configure structlog
    structlog.configure(
        processors=processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging
    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        level=level,
        stream=sys.stderr,
    )

    # Configure file logging if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        logging.getLogger().addHandler(file_handler)

    # Configure component-specific log levels
    if component_levels:
        for component, component_level in component_levels.items():
            logging.getLogger(component).setLevel(component_level)

    # Configure third-party libraries (always more restrictive)
    configure_library_loggers(level, verbosity)

    # Configure OpenTelemetry based on verbosity
    configure_otel_logging(verbosity)

    # Return a logger for the caller
    return structlog.get_logger()


def configure_library_loggers(level: int, verbosity: int) -> None:
    """Control third-party library logging.

    Args:
        level: Base log level for the application
        verbosity: Verbosity level (0-3)
    """
    # Make third-party logging more restrictive unless high verbosity
    third_party_level = level if verbosity >= 2 else logging.WARNING

    # ChromaDB logging (very verbose)
    chroma_level = level if verbosity >= 3 else logging.WARNING
    logging.getLogger("chromadb").setLevel(chroma_level)

    # Other libraries
    logging.getLogger("httpx").setLevel(third_party_level)
    logging.getLogger("httpcore").setLevel(third_party_level)
    logging.getLogger("opentelemetry").setLevel(third_party_level)
    logging.getLogger("anthropic").setLevel(third_party_level)
    logging.getLogger("openai").setLevel(third_party_level)


def configure_otel_logging(verbosity: int) -> None:
    """Configure OpenTelemetry based on verbosity level.

    Args:
        verbosity: Verbosity level (0-3)
    """
    if verbosity < 2:
        # Disable console export for OpenTelemetry
        os.environ["OTEL_SDK_DISABLED"] = "false"
        # Use file exporter or other non-console options
    else:
        # Enable full telemetry for debugging
        os.environ["OTEL_SDK_DISABLED"] = "false"
```

### 2. CLI Command Base Class

```python
# atlas/core/cli/base.py
import abc
import argparse
from typing import Any, Dict, List, Optional, Tuple

from atlas.core.logging import configure_logging


class Command(abc.ABC):
    """Base class for Atlas CLI commands."""

    name: str = ""
    help: str = ""
    description: str = ""

    def __init__(self) -> None:
        """Initialize the command."""
        self.parser: Optional[argparse.ArgumentParser] = None
        self.subparsers: Optional[argparse._SubParsersAction] = None
        self.logger = configure_logging()

    @abc.abstractmethod
    def configure_parser(self, parser: argparse.ArgumentParser) -> None:
        """Configure the argument parser for this command.

        Args:
            parser: The argument parser to configure
        """
        pass

    @abc.abstractmethod
    def run(self, args: argparse.Namespace) -> int:
        """Run the command with the parsed arguments.

        Args:
            args: The parsed command-line arguments

        Returns:
            Exit code (0 for success, non-zero for errors)
        """
        pass

    def add_common_options(self, parser: argparse.ArgumentParser) -> None:
        """Add common options to the parser.

        Args:
            parser: The argument parser to configure
        """
        # Verbosity controls
        verbosity_group = parser.add_mutually_exclusive_group()
        verbosity_group.add_argument(
            "-v", "--verbose",
            action="count",
            default=0,
            help="Increase verbosity (can be used multiple times)"
        )
        verbosity_group.add_argument(
            "-q", "--quiet",
            action="store_true",
            help="Suppress non-essential output"
        )

        # Logging options
        parser.add_argument(
            "--log-format",
            choices=["text", "json", "colored"],
            default="text",
            help="Log format (default: text)"
        )
        parser.add_argument(
            "--log-file",
            type=str,
            help="Write logs to file"
        )

        # Telemetry options
        parser.add_argument(
            "--telemetry",
            choices=["none", "console", "file"],
            default="none",
            help="Telemetry output mode"
        )

        # Config file
        parser.add_argument(
            "--config",
            type=str,
            help="Path to configuration file"
        )
```

### 3. Main CLI Entry Point

```python
# atlas/bin/atlas
#!/usr/bin/env python3
import argparse
import sys
from typing import Dict, Type

from atlas.core.cli.base import Command
from atlas.core.cli.commands.query import QueryCommand
from atlas.core.cli.commands.ingest import IngestCommand
from atlas.core.cli.commands.tool import ToolCommand
from atlas.core.cli.commands.serve import ServeCommand
from atlas.core.logging import configure_logging


def main() -> int:
    """Main entry point for the Atlas CLI.

    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    # Create main parser
    parser = argparse.ArgumentParser(
        description="Atlas AI Framework",
        prog="atlas"
    )

    # Register commands
    commands: Dict[str, Type[Command]] = {
        "query": QueryCommand,
        "ingest": IngestCommand,
        "tool": ToolCommand,
        "serve": ServeCommand,
    }

    # Add version argument
    parser.add_argument(
        "--version",
        action="store_true",
        help="Show version information and exit"
    )

    # Create subparsers
    subparsers = parser.add_subparsers(
        title="commands",
        dest="command",
        help="Command to execute"
    )

    # Add common options to main parser
    Command().add_common_options(parser)

    # Register all commands
    for cmd_name, cmd_class in commands.items():
        cmd = cmd_class()
        cmd_parser = subparsers.add_parser(
            cmd.name or cmd_name,
            help=cmd.help,
            description=cmd.description
        )
        cmd.configure_parser(cmd_parser)

    # Parse arguments
    args = parser.parse_args()

    # Configure logging based on arguments
    logger = configure_logging(
        verbosity=args.verbose,
        log_format=args.log_format,
        log_file=args.log_file,
        quiet=args.quiet
    )

    # Show version if requested
    if args.version:
        from atlas import __version__
        print(f"Atlas {__version__}")
        return 0

    # Execute the requested command
    if args.command is None:
        parser.print_help()
        return 1

    # Create and run the command
    cmd = commands[args.command]()
    return cmd.run(args)


if __name__ == "__main__":
    sys.exit(main())
```

## OpenTelemetry Integration

The logging system will provide better control over OpenTelemetry output with the following features:

1. **Telemetry Output Modes**
   - `none`: Disable all telemetry output (default)
   - `console`: Output formatted telemetry to console
   - `file`: Write telemetry data to file
   - `collector`: Send to OpenTelemetry collector

2. **Human-Readable Formatting**
   - Custom span formatting for console output
   - Event grouping and summarization
   - Visual indication of trace relationships

3. **Filtering Options**
   - Component-specific telemetry control
   - Duration-based filtering (skip fast operations)
   - Verbosity-based sampling rates

## CLI Documentation

Documentation for the CLI improvements will include:

1. **User Guides**
   - Command reference documentation
   - Common patterns and examples
   - Configuration and customization
   - Troubleshooting and debugging

2. **Developer Documentation**
   - CLI architecture and extension points
   - Adding new commands and options
   - Logging system integration
   - Testing CLI functionality

3. **Reference Materials**
   - Full command and option reference
   - Environment variable documentation
   - Configuration file format
   - Exit code conventions

## Development Principles

The CLI improvements will adhere to the following principles:

1. **Progressive Enhancement**: Improve existing functionality incrementally without breaking current usage patterns.
2. **Clarity Over Brevity**: Prioritize clear, descriptive output over terseness (but with verbosity controls).
3. **Consistent Pattern**: Maintain consistent command patterns, option naming, and behavior across all commands.
4. **Progressive Disclosure**: Essential information first, with details available through verbosity controls.
5. **Fail Gracefully**: Provide helpful error messages and recovery suggestions for failures.
6. **Predictable Behavior**: Ensure commands behave predictably and idempotently where possible.
7. **Documentation as First-Class**: Document all commands and options comprehensively as they are implemented.

## Timeline and Priorities

The CLI and logging improvements will be prioritized as follows:

1. **Immediate Priority**
   - Basic structlog integration
   - Verbosity controls via CLI and environment
   - Library log suppression
   - Initial CLI command framework

2. **Medium-Term Goals**
   - Complete command implementations
   - Executable entry points
   - Advanced formatting options
   - OpenTelemetry integration

3. **Longer-Term Goals**
   - Shell completion
   - Plugin architecture
   - Advanced visualization
   - Cross-platform packaging
