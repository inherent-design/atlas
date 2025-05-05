# Multi-Provider Support in Atlas

This document explains how to use Atlas with different model providers beyond the default Anthropic Claude models.

## Available Model Providers

Atlas currently supports the following model providers:

1. **Anthropic (Default)** - Claude models with high-quality reasoning capabilities
2. **OpenAI** - GPT models for versatile applications
3. **Ollama** - Local models for privacy and no-cost operation

## Configuration

### Environment Variables

Set the appropriate API keys for your desired provider:

```bash
# For Anthropic (required for default operation)
export ANTHROPIC_API_KEY=your_anthropic_key_here

# For OpenAI
export OPENAI_API_KEY=your_openai_key_here

# For Ollama
# No API key required, but Ollama must be running locally
# Run: ollama run llama3 (or your preferred model)
```

### Command Line Arguments

Use the `--provider` flag to specify which model provider to use:

```bash
# Use OpenAI instead of Anthropic
uv run python main.py -m cli --provider openai

# Use Ollama with a specific model
uv run python main.py -m cli --provider ollama --model llama3
```

## Available Models

Each provider supports different models:

### Anthropic Models
- `claude-3-7-sonnet-20250219` (default)
- `claude-3-5-sonnet-20240620`
- `claude-3-opus-20240229`
- `claude-3-sonnet-20240229`
- `claude-3-haiku-20240307`

### OpenAI Models
- `gpt-4o` (default)
- `gpt-4-turbo`
- `gpt-4`
- `gpt-3.5-turbo`

### Ollama Models
- `llama3` (default)
- `mistral`
- `gemma`
- Any other model you've pulled to your Ollama installation

## Usage Examples

### Basic Usage

```bash
# Using Anthropic (default)
uv run python main.py -m cli

# Using OpenAI
uv run python main.py -m cli --provider openai

# Using Ollama
uv run python main.py -m cli --provider ollama
```

### Specifying Models

```bash
# Using a specific Anthropic model
uv run python main.py -m cli --model claude-3-opus-20240229

# Using a specific OpenAI model
uv run python main.py -m cli --provider openai --model gpt-4

# Using a specific Ollama model
uv run python main.py -m cli --provider ollama --model mistral
```

### Advanced Usage

```bash
# Running in controller mode with parallel processing using OpenAI
uv run python main.py -m controller --parallel --provider openai

# Ingesting documents and then querying with Ollama
uv run python main.py -m ingest -d ./my_documents
uv run python main.py -m query -q "What are the key concepts?" --provider ollama

# Using a custom system prompt with Anthropic
uv run python main.py -m cli -s path/to/custom_prompt.md --model claude-3-haiku-20240307
```

## Provider-Specific Features and Limitations

### Anthropic
- Highest quality reasoning for complex tasks
- Comprehensive token usage and cost tracking
- Requires API key and incurs usage costs

### OpenAI
- Fast response time
- Good for general-purpose applications
- Requires API key and incurs usage costs

### Ollama
- Free to use with local computation
- No data sent to external services
- Limited by your local hardware capabilities
- May have lower quality responses than cloud models
- Requires separate installation of Ollama

## Cost Considerations

The application tracks and displays token usage and estimated costs for API providers:

```
API Usage: 683 input tokens, 502 output tokens
Estimated Cost: $0.009579 (Input: $0.002049, Output: $0.007530)
```

- Anthropic and OpenAI have per-token costs (see their pricing pages for current rates)
- Ollama has no per-token costs as it runs locally

## Troubleshooting

### Provider Not Available

If you see an error like `Unsupported provider: [provider_name]`:
- Ensure you've typed the provider name correctly (should be `anthropic`, `openai`, or `ollama`)
- Check that you've installed all required dependencies (`uv add openai ollama`)

### API Key Issues

If you see authentication errors:
- Verify your API key is correctly set as an environment variable
- Try exporting the key again: `export OPENAI_API_KEY=your_key_here`

### Ollama Connection Problems

If you can't connect to Ollama:
- Ensure Ollama is installed and running (`ollama serve`)
- Check that it's accessible at `http://localhost:11434`
- Verify you have the specified model pulled (`ollama pull llama3`)
