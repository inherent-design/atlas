# Contributing to Atlas

First off, thank you for considering contributing to Atlas! It's people like you that make Atlas such a great tool for building advanced AI agent systems.

Following these guidelines helps to communicate that you respect the time of the developers managing and developing this open source project. In return, they should reciprocate that respect in addressing your issue, assessing changes, and helping you finalize your pull requests.

## Quick Navigation

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Workflow](#development-workflow)
- [Pull Request Process](#pull-request-process)
- [Style Guides](#style-guides)
- [Community](#community)

## Code of Conduct

This project and everyone participating in it is governed by the [Atlas Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to [conduct@inherent.design](mailto:conduct@inherent.design).

## Getting Started

### Project Setup

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR-USERNAME/atlas.git
   cd atlas
   ```
3. **Set up the development environment**:
   ```bash
   # Create a virtual environment
   uv venv
   source .venv/bin/activate  # On Windows, use `.venv\Scripts\activate`
   
   # Install dependencies in development mode
   uv pip install -e ".[dev]"
   ```
4. **Create a branch** for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

### Understanding the Project Structure

- `/atlas`: Core library code
  - `/agents`: Agent framework components
  - `/core`: Core functionality and utilities
  - `/graph`: LangGraph integration
  - `/knowledge`: Knowledge management
  - `/models`: Provider integrations
  - `/orchestration`: Multi-agent orchestration
  - `/tools`: Tool integrations
- `/examples`: Example implementations
- `/docs`: Documentation
- `/tests`: Test suite

## How Can I Contribute?

### Reporting Bugs

Before creating a bug report:

1. **Check the issue tracker** to see if the problem has already been reported
2. **Try the latest version** to see if the problem has already been fixed
3. **Collect information** about the bug:
   - Steps to reproduce
   - Expected behavior
   - Actual behavior
   - Screenshots if applicable
   - Environment details (OS, Python version, etc.)

When creating a bug report:

1. **Use the bug report template**
2. **Use a clear and descriptive title**
3. **Describe the exact steps to reproduce the problem**
4. **Explain the behavior you expected**
5. **Include relevant details** about your configuration

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion:

1. **Use the feature request template**
2. **Use a clear and descriptive title**
3. **Provide a step-by-step description** of the suggested enhancement
4. **Explain why this enhancement would be useful**
5. **List some other applications where this enhancement exists**, if applicable

### Your First Code Contribution

Unsure where to begin contributing to Atlas? You can start by looking through these `beginner` and `help-wanted` issues:

- **Beginner issues** - issues that should only require a few lines of code and minimal testing
- **Help wanted issues** - issues that are more involved than beginner issues

### Documentation

Documentation improvements are always welcome! This could be:

- Fixing typos or grammar errors
- Improving existing documentation
- Adding missing documentation
- Creating tutorials or examples

## Development Workflow

### Setting Up Your Development Environment

We recommend using the following tools:

- **uv** for package management
- **Visual Studio Code** with the following extensions:
  - Python
  - Pylance
  - Python Docstring Generator
  - Markdown All in One
- **pre-commit** for maintaining code quality

### Development Process

1. **Choose an issue** to work on or create a new one
2. **Create a branch** with a descriptive name
3. **Make your changes** and write tests
4. **Run the tests** locally
5. **Push your changes** to your fork
6. **Create a pull request**

### Testing

Run the test suite with:

```bash
python -m atlas.scripts.testing.run_tests.py
```

Different test types can be run with:

```bash
# Run unit tests
python -m atlas.scripts.testing.run_tests.py --test-type unit

# Run mock tests (no API calls)
python -m atlas.scripts.testing.run_tests.py --test-type mock

# Run integration tests (requires API keys)
python -m atlas.scripts.testing.run_tests.py --test-type integration
```

### Type Checking

Run type checking with:

```bash
mypy atlas
```

### Development Tips

- **Use feature flags** for experimental features
- **Write tests** for all new features
- **Keep changes focused** - one pull request per feature or bug fix
- **Update documentation** alongside code changes
- **Follow the style guides**

## Pull Request Process

1. **Create your pull request** from your forked repository
2. **Use the pull request template**
3. **Ensure all tests pass**
4. **Update documentation** if necessary
5. **Add your changes to the CHANGELOG** under the Unreleased section
6. **Respond to feedback** from maintainers

The PR will be merged once it:
- Passes all tests
- Follows the style guidelines
- Has at least one approval from a maintainer
- Includes appropriate documentation
- Addresses all review comments

## Style Guides

### Git Commit Messages

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters or less
- Reference issues and pull requests after the first line
- Consider using the [Conventional Commits](https://www.conventionalcommits.org/) format:
  - `feat:` for new features
  - `fix:` for bug fixes
  - `docs:` for documentation changes
  - `style:` for formatting changes
  - `refactor:` for code refactoring
  - `test:` for test-related changes
  - `chore:` for maintenance tasks

### Python Style Guide

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- Use [Google-style docstrings](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings)
- Use type hints according to [PEP 484](https://www.python.org/dev/peps/pep-0484/)
- Maximum line length of 88 characters
- Use [black](https://black.readthedocs.io/) for code formatting
- Use [isort](https://pycqa.github.io/isort/) for import sorting

### Documentation Style Guide

- Use [Markdown](https://www.markdownguide.org/) for documentation
- Follow the [VitePress](https://vitepress.dev/) conventions for documentation
- Use [Mermaid](https://mermaid-js.github.io/mermaid/#/) for diagrams
- Keep sentences concise and clear
- Use code examples liberally

## Community

### Communication Channels

- **GitHub Discussions** - For feature ideas and general questions
- **Discord Server** - For real-time discussion and community building
- **Mailing List** - For important announcements and discussions

### Recognition

We recognize contributions in several ways:

- **CONTRIBUTORS.md** file with an acknowledgment of all contributors
- **Release Notes** mentioning significant contributions
- **Maintainer Status** for regular and substantial contributors

### Governance

The project is currently governed by the core team at inherent.design. As the community grows, we plan to establish:

- A **Technical Steering Committee** for major decisions
- An **RFC Process** for significant changes
- **Special Interest Groups** for specific areas of the project

## Questions?

If you have any questions about contributing, please feel free to ask in GitHub Discussions or reach out to the maintainers directly.

Thank you for contributing to Atlas! 🙌