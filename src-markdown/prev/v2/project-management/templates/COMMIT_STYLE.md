# Commit Message Style Guide

This guide outlines commit message format standards for ensuring a consistent, informative, and useful version control history.

## Commit Message Structure

Each commit message consists of two essential parts:

1. **Subject Line**: A concise, descriptive header
2. **Body**: Optional detailed explanation (separated by a blank line)

```
action: concise description of changes

- bullet point details of what changed
- another important change detail
- additional context if needed
```

## Subject Line Format

The subject line should follow this specific format:

```
action: brief description
```

### Action Types

Choose the most appropriate action prefix from this standardized list:

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
- Focus on the "what" and "why", not the "how"

## Body Format

The commit body should:
- Consist of bullet points, each starting with a hyphen
- Begin each bullet point with lowercase text
- Have one blank line after the subject
- Focus on *what* changed and *why* (not how)
- Be concise and direct
- Use present tense consistently

## Extended Examples

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

## Guidelines for Larger Changes

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

## Common Situations and Examples

### Documentation Update

```
docs: improve API reference documentation

- add missing parameters to getUserData method
- include response examples for all endpoints
- fix incorrect return type descriptions
```

### Configuration Change

```
chore: adjust build optimization settings

- enable tree-shaking for production builds
- configure code splitting for dynamic imports
- reduce bundle size by 35% in production
```

### Multiple Related Changes

```
update: enhance form validation system

- implement client-side validation with Zod
- add custom error message support
- create reusable validation hooks
- improve accessibility of error states
```

### Addressing Code Review Feedback

```
fix: address PR feedback on user profile feature

- improve form validation error handling
- add missing unit tests for edge cases
- fix responsive layout issues on mobile
```

## Integration with Issue Tracking

When commits relate to tracked issues:

```
fix: resolve intermittent test failures on CI #123

- increase timeout for async operations
- add retry logic for flaky network tests
- improve error logging for failed assertions
```

## Final Thoughts

Good commit messages serve as both documentation and a change log. They help future contributors (including your future self) understand not just what changed, but why it changed. Taking the time to write good commit messages is an investment in the project's long-term maintainability and team collaboration.
