# Commit Message Style Guide

This guide outlines commit message format standards for consistent and informative version control history.

## Commit Message Structure

Each commit message consists of two parts:

1. **Subject Line**: A concise, descriptive header
2. **Body**: Optional detailed explanation (separated by a blank line)

```
action: concise description of changes

- bullet point details of what changed
- another important change detail
- additional context if needed
```

## Subject Line Format

The subject line should follow this format:

```
action: brief description
```

### Action Types

Choose the most appropriate action prefix:

| Action      | Purpose                                 | Example                                                    |
| ----------- | --------------------------------------- | ---------------------------------------------------------- |
| `add`       | New features or files                   | `add: MDX blog post component`                             |
| `update`    | Enhancements to existing features       | `update: MDX 2 -> 3 and API usage`                         |
| `fix`       | Bug fixes                               | `fix: MDX parsing for code blocks`                         |
| `refactor`  | Code changes that don't change behavior | `refactor: split Home component into smaller pieces`       |
| `style`     | Formatting, spacing, etc.               | `style: standardize indentation in stylesheet`             |
| `test`      | Adding or modifying tests               | `test: add unit tests for MDX components`                  |
| `docs`      | Documentation only changes              | `docs: update README with new installation steps`          |
| `chore`     | Changes to the build process, etc.      | `chore: update ESLint configuration`                       |
| `integrate` | Bringing systems together               | `integrate: MDX content with React component architecture` |

### Description Principles

The description should:
- Be no more than 50 characters
- Use present tense ("add" not "added")
- Not end with a period
- Be specific but concise

## Body Format

The commit body should:
- Consist of bullet points, each starting with a hyphen
- Begin each bullet point with lowercase text
- Have one blank line after the subject
- Focus on *what* changed and *why* (not how)
- Be concise and direct
- Use present tense consistently

## Examples

### Feature Addition

```
add: user authentication system

- implement JWT token-based auth
- create login/register forms
- add protected route middleware
- set up user persistence
```

### Bug Fix

```
fix: update husky configuration for v9/v10 compatibility

- remove deprecated shebang lines
- create husky compatibility shim
- add .gitignore for husky internals
```

### Dependency Update

```
update: MDX 2 -> 3 and API usage

- bump package.json dependencies
- convert to new MDXProvider interface
- adjust content loading mechanism for v3 compatibility
```

### Refactoring

```
refactor: ESLint configuration for modern plugins

- migrate from .eslintignore to config-based ignores
- configure proper JSX/React globals
- set up MDX linting with code block support
```

## Anti-Patterns to Avoid

Don't write commit messages like these:

- ❌ `"Fixed stuff"`
- ❌ `"WIP"`
- ❌ `"Updates"`
- ❌ `"Minor changes"`
- ❌ `"Addressing PR feedback"`

Instead, be specific about what changed and why.

## Notes for Larger Changes

For substantial changes:

1. Make smaller, logical commits rather than one massive change
2. Use detailed bullet points to explain the rationale
3. Reference issue numbers when applicable with `#123` syntax
4. If there are incomplete items, add a "TODO:" section at the end

## Workflow Recommendations

Use this workflow:

```bash
# Stage changes
git add .

# Create commit with proper formatting
git commit -m "action: concise description

- bullet point with details
- another bullet point"
```

## Final Thoughts

Good commit messages serve as both documentation and a change log. They help future contributors (including your future self) understand not just what changed, but why it changed.
