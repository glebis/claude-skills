# Gemini Image Generation API Reference

## Endpoint

```
POST https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent
```

## Authentication

Pass the API key via header:
```
x-goog-api-key: YOUR_GEMINI_API_KEY
```

## Models

| Model | Speed | Quality | Text Rendering | Best For |
|-------|-------|---------|----------------|----------|
| `gemini-2.5-flash-image` | Fast | Good | Basic | Iteration, bulk generation |
| `gemini-3-pro-image-preview` | Slower | Excellent | Accurate | Final assets, text-heavy images |

## Request Format

### Text-to-Image (Generation)

```json
{
  "contents": [{
    "parts": [{"text": "prompt describing the image"}]
  }],
  "generationConfig": {
    "responseModalities": ["TEXT", "IMAGE"]
  }
}
```

### Image Editing (with Input Image)

```json
{
  "contents": [{
    "parts": [
      {"text": "edit instruction"},
      {
        "inlineData": {
          "mimeType": "image/png",
          "data": "BASE64_ENCODED_IMAGE"
        }
      }
    ]
  }],
  "generationConfig": {
    "responseModalities": ["TEXT", "IMAGE"]
  }
}
```

## Response Format

```json
{
  "candidates": [{
    "content": {
      "parts": [
        {"text": "Description of the generated image"},
        {
          "inlineData": {
            "mimeType": "image/png",
            "data": "BASE64_ENCODED_IMAGE_DATA"
          }
        }
      ]
    }
  }]
}
```

The response may contain:
- Text parts describing what was generated
- Image parts with base64-encoded PNG data
- Both text and image parts in a single response

## Prompt Engineering Tips

### Style Control Keywords

- **Photography**: "photograph", "DSLR", "35mm film", "studio lighting", "natural light"
- **Illustration**: "flat illustration", "vector art", "line drawing", "watercolor"
- **Design**: "minimalist", "isometric", "3D render", "UI mockup", "infographic"
- **Art styles**: "oil painting", "sketch", "pixel art", "comic book style"

### Composition Keywords

- "centered composition", "rule of thirds", "wide shot", "close-up"
- "white background", "transparent background", "gradient background"
- "top-down view", "bird's eye view", "eye level", "low angle"

### Quality Boosters

- "high quality", "detailed", "sharp focus", "professional"
- "4K", "high resolution", "crisp"
- Specify color palette: "blue and white color scheme", "warm earth tones"

### Text in Images

For images containing text (diagrams, logos, labels):
- Use `gemini-3-pro-image-preview` for accurate text rendering
- Specify exact text in quotes: 'with the text "Hello World"'
- Specify font style: "bold sans-serif text", "handwritten text"

## Error Codes

| HTTP Code | Meaning | Fix |
|-----------|---------|-----|
| 400 | Bad request / invalid model | Check model name |
| 401 | Invalid API key | Verify GEMINI_API_KEY |
| 429 | Rate limited | Wait and retry |
| 500 | Server error | Retry after a moment |

## Rate Limits

- Free tier: ~15 requests per minute
- Paid tier: Higher limits based on plan
- Each image generation counts as one request
