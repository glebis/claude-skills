# GPT Image 2 API Reference

## Endpoint

**Generation:** `POST https://api.openai.com/v1/images/generations`
**Editing:** `POST https://api.openai.com/v1/images/edits`

## Authentication

```
Authorization: Bearer <OPENAI_API_KEY>
Content-Type: application/json
```

## Generation Request Body

```json
{
  "model": "gpt-image-2",
  "prompt": "a cat wearing a space suit",
  "n": 1,
  "size": "1024x1024",
  "quality": "high",
  "thinking": "off",
  "response_format": "b64_json"
}
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | string | required | `gpt-image-2` |
| `prompt` | string | required | Text description of desired image |
| `n` | integer | 1 | Number of images to generate (1-10) |
| `size` | string | `1024x1024` | Image size. Options: `1024x1024`, `1536x1024`, `1024x1536`, `2000x1024`, `1024x2000`, `auto` |
| `quality` | string | `high` | `low`, `medium`, `high` |
| `thinking` | string | `off` | `off`, `low`, `medium`, `high` — reasoning before rendering |
| `response_format` | string | `url` | `url` or `b64_json` |

## Edit Request Body

```json
{
  "model": "gpt-image-2",
  "image": "<base64-encoded-image>",
  "prompt": "make the background blue",
  "size": "1024x1024",
  "quality": "high",
  "response_format": "b64_json"
}
```

## Response

```json
{
  "created": 1714000000,
  "data": [
    {
      "b64_json": "<base64-encoded-png>",
      "revised_prompt": "..."
    }
  ],
  "usage": {
    "input_tokens": 150,
    "output_tokens": 4096,
    "input_tokens_details": {
      "text_tokens": 50,
      "image_tokens": 100
    },
    "output_tokens_details": {
      "text_tokens": 0,
      "image_tokens": 4096
    }
  }
}
```

## Pricing (per million tokens)

| Token Type | Cost |
|-----------|------|
| Input text | $5 |
| Output text (thinking) | $10 |
| Input image | $8 |
| Output image | $30 |

### Approximate per-image costs

| Thinking | ~1024x1024 High |
|----------|----------------|
| off | ~$0.19 |
| low | ~$0.23 |
| medium | ~$0.29 |
| high | ~$0.38 |

## OpenRouter

Same request format, different base URL:
- **Generation:** `POST https://openrouter.ai/api/v1/images/generations`
- **Editing:** `POST https://openrouter.ai/api/v1/images/edits`
- Extra headers: `HTTP-Referer`, `X-Title`

## Error Codes

| Code | Meaning | Retry? |
|------|---------|--------|
| 400 | Bad request / invalid params | No |
| 401 | Invalid API key | No |
| 403 | Safety filter / content policy | No |
| 429 | Rate limit exceeded | Yes (backoff) |
| 500 | Server error | Yes (backoff) |
| 502 | Bad gateway | Yes (backoff) |
