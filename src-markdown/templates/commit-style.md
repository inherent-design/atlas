# Commit Message Style Guide

## Subject Line Format

```
action: brief description
```

### Action Types

| Action      | Purpose                                 | Example                                      |
| ----------- | --------------------------------------- | -------------------------------------------- |
| `add`       | New features or files                   | `add: MDX blog post component`               |
| `update`    | Enhancements to existing features       | `update: MDX 2 -> 3 and API usage`           |
| `fix`       | Bug fixes                               | `fix: MDX parsing for code blocks`           |
| `refactor`  | Code changes that don't change behavior | `refactor: split Home component into pieces` |
| `style`     | Formatting, spacing, etc.               | `style: standardize indentation`             |
| `test`      | Adding or modifying tests               | `test: add unit tests for MDX components`    |
| `docs`      | Documentation only changes              | `docs: update README with install steps`     |
| `chore`     | Changes to the build process, etc.      | `chore: update ESLint configuration`         |
| `integrate` | Bringing systems together               | `integrate: MDX content with React system`   |

## Body Format

```
action: concise description of changes

- bullet point details of what changed
- another important change detail
- additional context if needed
```

## Description Principles

- No more than 50 characters
- Use present tense ("add" not "added")
- No period at end
- Specific but concise
- Focus on "what" and "why", not "how"

## Body Format Guidelines

- Use bullet points starting with hyphens
- Begin each bullet with lowercase
- One blank line after the subject
- Focus on what changed and why
- Use present tense consistently