# OpenRouter Integration - LLM CLI Skill

## Overview

The LLM CLI Skill now includes **OpenRouter support**, providing unified access to 200+ LLM models from multiple providers through a single API.

## What is OpenRouter?

OpenRouter is a routing service that acts as a gateway to multiple LLM providers. Instead of managing separate API keys for OpenAI, Anthropic, Google, Mistral, etc., you can use OpenRouter's single API to access models from all these providers.

### Key Benefits

✅ **Unified API** - One API key for 200+ models
✅ **Model Routing** - Automatic routing to best available provider
✅ **Cost Optimization** - Compare prices across providers
✅ **Fallback Support** - Automatic fallback to alternative models
✅ **Single Billing** - Consolidated billing across providers
✅ **No Need for Multiple Keys** - One API key covers all providers

## Setup

### 1. Create OpenRouter Account (Free)

Visit: https://openrouter.ai/

Click "Sign in/Sign up" - choose your preferred auth method
(GitHub, Google, Discord, or email)

No credit card required for account creation!

### 2. Get API Key

1. Go to: https://openrouter.ai/keys
2. Click "Create Key"
3. Give it a name (e.g., "LLM CLI")
4. Copy the key

### 3. Set Environment Variable

```bash
export OPENROUTER_API_KEY='sk-or-...'
```

Or use llm CLI to store it:

```bash
llm keys set openrouter
```

### 4. Verify Setup

```bash
llm models | grep openrouter
```

Should show available OpenRouter models.

## Available Models

The skill includes popular models from multiple providers via OpenRouter:

### OpenAI Models
- `openrouter-gpt-4o` - Latest GPT-4o
- `openrouter-gpt-4-turbo` - GPT-4 Turbo

Aliases: `or-gpt-4o`, `openai/gpt-4o`

### Anthropic Models
- `openrouter-claude-opus` - Claude 3 Opus
- `openrouter-claude-sonnet` - Claude 3 Sonnet

Aliases: `or-claude-opus`, `anthropic/claude-opus`

### Meta Llama
- `openrouter-llama-3.3-70b` - Llama 3.3 70B

Aliases: `or-llama-3.3`, `meta-llama/llama-3.3-70b`

### Mistral
- `openrouter-mistral-large` - Mistral Large

Aliases: `or-mistral-large`, `mistralai/mistral-large`

### More Available

OpenRouter offers access to 200+ models including:
- Qwen, Grok, Llama, Cohere, Aleph Alpha, Baseten, and more
- See full list at: https://openrouter.ai/models

## Usage

### Direct llm CLI

```bash
# Use a specific model
llm -m openrouter-gpt-4o "Your prompt"

# Use via alias
llm -m or-gpt-4o "Your prompt"

# Use OpenRouter to access GPT-4o
llm -m openai/gpt-4o "Your prompt"
```

### With LLM Skill

```bash
# Specific model
/llm "Your prompt" --model openrouter-gpt-4o

# By alias
/llm "Your prompt" --model or-claude-opus

# By provider
/llm "Your prompt" --model openrouter
# Shows menu of available OpenRouter models
```

### File Processing

```bash
# Process a file with OpenRouter
cat document.txt | llm -m openrouter-gpt-4o "Summarize"

# Analyze code
llm -m or-gpt-4o "Review this code" < main.py
```

### Interactive Mode

```bash
# Interactive chat with OpenRouter model
llm -m openrouter-claude-opus --conversation
```

## Pricing

OpenRouter's pay-as-you-go pricing:

| Model | Input Cost | Output Cost |
|-------|-----------|------------|
| GPT-4o | $5/1M tokens | $15/1M tokens |
| Claude 3 Opus | $15/1M tokens | $75/1M tokens |
| Claude 3 Sonnet | $3/1M tokens | $15/1M tokens |
| Llama 3.3 70B | $0.31/1M tokens | $0.62/1M tokens |
| Mistral Large | $0.81/1M tokens | $2.43/1M tokens |

View latest pricing at: https://openrouter.ai/pricing

## Model Routing

### How OpenRouter Routes

1. **Direct Model**: You request a specific model → OpenRouter routes to that model
2. **Fallback**: If model unavailable → OpenRouter routes to configured fallback
3. **Cost Optimization**: Choose cheapest available model with similar capabilities

### Request Format

```bash
# Specify provider explicitly
llm -m openrouter-gpt-4o "prompt"

# Or use OpenRouter's routing
llm -m "openai/gpt-4o" "prompt"  # via OpenRouter
```

## Advanced Features

### 1. Model Fallbacks

OpenRouter supports requesting fallback models. When using via the skill, it handles this transparently.

Example: If you request GPT-4o but it's temporarily unavailable, OpenRouter will use a configured fallback.

### 2. Route-Based Requests

You can request by provider path:

```bash
# These all work via OpenRouter
llm -m "openai/gpt-4o" "prompt"
llm -m "anthropic/claude-opus" "prompt"
llm -m "meta-llama/llama-3.3-70b" "prompt"
llm -m "mistralai/mistral-large" "prompt"
```

### 3. Token Counting

OpenRouter provides token counting. Use it to estimate costs:

```bash
# Check tokens before making expensive calls
llm -m openrouter-gpt-4o "long prompt here" --dry-run
```

## Billing & Account Management

### View Usage

1. Log in to: https://openrouter.ai/account/usage
2. See real-time usage and costs
3. Track API calls, tokens, and spending

### Set Spending Limits

1. Go to: https://openrouter.ai/account/settings
2. Set monthly spending limit
3. Configure alerts

### Add Payment Method

1. Account Settings → Billing
2. Add credit card
3. OpenRouter charges based on usage

## Comparison: OpenRouter vs Direct APIs

| Feature | OpenRouter | Direct API |
|---------|-----------|-----------|
| API Keys | 1 | Multiple |
| Billing | Unified | Separate |
| Model Access | 200+ | Limited |
| Fallback Support | Yes | No |
| Setup Time | Quick | Complex |
| Cost | Competitive | Variable |

## Use Cases

### 1. Multi-Model Testing

```bash
# Test same prompt on different models
llm -m openrouter-gpt-4o "prompt"
llm -m openrouter-claude-opus "prompt"
llm -m openrouter-llama-3.3-70b "prompt"

# Compare results
```

### 2. Cost-Optimized Processing

```bash
# Use cheaper model for simple tasks
llm -m openrouter-llama-3.3-70b "Simple question"

# Use premium model for complex tasks
llm -m openrouter-gpt-4o "Complex analysis"
```

### 3. Reliability & Fallback

Use OpenRouter's routing for production workloads:

```bash
# Will use fallback if primary model unavailable
llm -m openai/gpt-4o "Critical task"
```

### 4. Research & Development

Access cutting-edge models:

```bash
# Test latest open models
llm -m openrouter-llama-3.3-70b "innovative prompt"

# Compare with proprietary models
llm -m openrouter-gpt-4o "same prompt"
```

## Examples

### Text Analysis

```bash
llm -m openrouter-claude-opus "Analyze sentiment" < review.txt
```

### Code Generation

```bash
llm -m or-gpt-4o "Generate Python function for" < requirements.txt
```

### Translation

```bash
echo "Hello world" | llm -m openrouter-mistral-large "Translate to Spanish"
```

### Research Summarization

```bash
llm -m or-claude-opus "Summarize key findings" < research_paper.txt
```

### Creative Writing

```bash
llm -m openrouter-gpt-4o "Write a short story about AI"
```

## Troubleshooting

### API Key Not Recognized

```bash
# Verify key is set
echo $OPENROUTER_API_KEY

# Should start with: sk-or-...

# If empty, set it again
export OPENROUTER_API_KEY='sk-or-...'

# Reload shell
source ~/.zshrc
```

### Model Not Found

```bash
# Check available OpenRouter models
llm models | grep openrouter

# Should list available models
```

### Rate Limiting

OpenRouter has rate limits. If exceeded:
- Wait a few minutes
- Use cheaper/lighter models
- Upgrade account for higher limits
- Contact support at: https://openrouter.ai/contact

### Authentication Error

1. Verify API key is correct
2. Ensure it starts with `sk-or-`
3. Check key isn't revoked at: https://openrouter.ai/keys
4. Try creating a new key

## FAQ

**Q: Do I need to pay upfront?**
A: No! OpenRouter uses pay-as-you-go pricing. You only pay for what you use.

**Q: Can I use free trial?**
A: Yes! OpenRouter offers free trial credits. Check your account for details.

**Q: What if a model is unavailable?**
A: OpenRouter handles fallback automatically. You can configure fallback preferences.

**Q: How fast is OpenRouter?**
A: OpenRouter adds minimal latency (<100ms). Actual latency depends on the underlying model.

**Q: Can I use my OpenRouter key with the regular llm CLI?**
A: Yes! OpenRouter is fully compatible with standard llm CLI. The skill just makes it easier to manage.

**Q: How many requests can I make?**
A: Depends on your plan. Free tier has reasonable limits. Upgrade for higher limits.

**Q: Can I switch between OpenRouter and direct APIs?**
A: Yes! You can use both simultaneously. Just set multiple API keys.

## Integration Details

### Files Modified

1. **models.py**
   - Added 6 OpenRouter models
   - Added `openrouter` and `or` provider aliases

2. **providers.py**
   - Added `OPENROUTER_API_KEY` detection
   - Updated setup suggestions

### Model IDs

OpenRouter uses these model ID formats:
- `openai/gpt-4o`
- `anthropic/claude-3-opus`
- `meta-llama/llama-3.3-70b-instruct`
- `mistralai/mistral-large`

The skill normalizes these to user-friendly names like `openrouter-gpt-4o`.

## Next Steps

1. **Get API Key**: https://openrouter.ai/keys
2. **Set Environment**: `export OPENROUTER_API_KEY='sk-or-...'`
3. **Verify**: `llm models | grep openrouter`
4. **Start Using**: `llm -m openrouter-gpt-4o "prompt"`

## Resources

- **OpenRouter Website**: https://openrouter.ai
- **Pricing**: https://openrouter.ai/pricing
- **Models**: https://openrouter.ai/models
- **Documentation**: https://openrouter.ai/docs
- **Account**: https://openrouter.ai/account
- **Status**: https://openrouter.io/status

## Summary

OpenRouter integration enables you to:
- ✅ Access 200+ models via single API
- ✅ Use unified billing and account management
- ✅ Easily switch between providers
- ✅ Benefit from fallback and routing features
- ✅ Optimize costs across models

**Recommended**: Start with OpenRouter for access to multiple providers, then add direct API keys for models you use frequently!

---

**Status**: ✅ Production Ready
**Last Updated**: November 3, 2025
**Version**: 1.0.0
