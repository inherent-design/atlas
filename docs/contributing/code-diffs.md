# Colored Diffs in Code Blocks

When documenting code changes, updates, or comparing different implementations, colored diffs make it easy to highlight what has changed. This guide explains how to effectively use colored diffs in Atlas documentation.

## Basic Syntax

VitePress provides syntax for adding colored diffs to code blocks using inline comments. The syntax is as follows:

```
def hello_world():
    print("Hello, World!") # [!code --]
    print("Hello, Atlas!") # [!code ++]
```

This renders as:

```python
def hello_world():
    print("Hello, World!") # [!code --]
    print("Hello, Atlas!") # [!code ++]
```

## How It Works

- Lines marked with the appropriate comment syntax followed by `[!code --]` are highlighted in red (indicating removal)
- Lines marked with the appropriate comment syntax followed by `[!code ++]` are highlighted in green (indicating addition)
- The rest of the code block maintains its syntax highlighting

**Important:** The comment syntax must match the language of your code block:
- Python: `# [!code --]` and `# [!code ++]` (with hash symbol)
- JavaScript/TypeScript: `// [!code --]` and `// [!code ++]` (with double slashes)
- CSS: `/* [!code --] */` and `/* [!code ++] */` (CSS comment style)
- HTML: `<!-- [!code --] -->` and `<!-- [!code ++] -->` (HTML comment style)
- Other languages: Use the appropriate comment syntax for that language

## When to Use Colored Diffs

Use colored diffs in documentation when:

1. **API Changes**: Showing how an API has evolved between versions
2. **Code Improvements**: Demonstrating refactoring or optimization
3. **Bug Fixes**: Highlighting the specific lines that fix a bug
4. **Best Practices**: Showing the difference between problematic and recommended code
5. **Subtle Changes**: Making small but important changes more visible

## Example: API Evolution

```python
# Old API (v0.8)
provider = Provider( # [!code --]
    provider_type="anthropic", # [!code --]
    model="claude-2.0", # [!code --]
    api_key=os.environ.get("ANTHROPIC_API_KEY") # [!code --]
) # [!code --]

# New API (v1.0)
from atlas.providers import AnthropicProvider # [!code ++]
 # [!code ++]
provider = AnthropicProvider( # [!code ++]
    model_name="claude-3-7-sonnet-20250219", # [!code ++]
    api_key=os.environ.get("ANTHROPIC_API_KEY") # [!code ++]
) # [!code ++]
```

## Example: Security Enhancement

```python
# Insecure implementation
api_key = config["api_key"] # [!code --]
headers = {"Authorization": f"Bearer {api_key}"} # [!code --]
response = requests.post(url, headers=headers, json=payload) # [!code --]

# Secure implementation
import validators # [!code ++]
from atlas.core.security import sanitize_headers # [!code ++]
 # [!code ++]
api_key = config["api_key"] # [!code ++]
if not api_key or len(api_key) < 32: # [!code ++]
    raise ValueError("Invalid API key format") # [!code ++]
     # [!code ++]
if not validators.url(url): # [!code ++]
    raise ValueError("Invalid URL format") # [!code ++]
 # [!code ++]
headers = sanitize_headers({"Authorization": f"Bearer {api_key}"}) # [!code ++]
response = requests.post(url, headers=headers, json=payload, timeout=30) # [!code ++]
```

## Guidelines for Effective Diffs

To create clear and helpful diffs:

1. **Focus on the Changes**: Only mark the specific lines that have changed
2. **Include Context**: Provide enough surrounding code for understanding
3. **Clear Comments**: Add explanatory comments as needed
4. **Group Related Changes**: Keep related changes together
5. **Stay Concise**: Avoid showing unnecessary code

### Bad Example (Too Little Context)

```python
max_tokens=1024 # [!code --]
max_tokens=2048 # [!code ++]
```

### Good Example (Appropriate Context)

```python
provider = AnthropicProvider(
    model_name="claude-3-7-sonnet-20250219",
    max_tokens=1024,  # Limited token count for efficiency // [!code --]
    max_tokens=2048,  # Increased for complex reasoning tasks // [!code ++]
    temperature=0.7
)
```

## Combining With Code Groups

You can combine colored diffs with code groups to show "before" and "after" versions alongside the diff:

::: code-group

```python [Before]
from atlas.providers import AnthropicProvider

provider = AnthropicProvider(model_name="claude-2.0")
response = provider.generate("What is Atlas?")
print(response)
```

```python [After]
from atlas.providers import AnthropicProvider

provider = AnthropicProvider(
    model_name="claude-3-7-sonnet-20250219",
    temperature=0.7,
    max_tokens=2000
)
response = provider.generate(
    "What is Atlas?",
    system_prompt="You are a helpful assistant focused on explaining software frameworks."
)
print(response)
```

```python [Diff]
from atlas.providers import AnthropicProvider

provider = AnthropicProvider(model_name="claude-2.0") # [!code --]
provider = AnthropicProvider( # [!code ++]
    model_name="claude-3-7-sonnet-20250219", # [!code ++]
    temperature=0.7, # [!code ++]
    max_tokens=2000 # [!code ++]
) # [!code ++]
response = provider.generate("What is Atlas?") # [!code --]
response = provider.generate( # [!code ++]
    "What is Atlas?", # [!code ++]
    system_prompt="You are a helpful assistant focused on explaining software frameworks." # [!code ++]
) # [!code ++]
print(response)
```

:::

## Best Practices

When using colored diffs in Atlas documentation:

1. **Be Specific**: Only mark the exact changes, not entire blocks
2. **Add Comments**: Explain the rationale for changes
3. **Show Context**: Include enough surrounding code for clarity
4. **Combine with Text**: Use explanatory text before and after diffs
5. **Version Information**: Specify which Atlas versions the diff applies to
6. **Migration Guidance**: Include diffs in migration guides to help users update their code

By effectively using colored diffs, you can make code changes more visible and easier to understand in Atlas documentation.
