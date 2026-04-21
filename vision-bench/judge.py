import base64
import json
import re
from pathlib import Path
import vault  # local secrets.py — renamed to avoid stdlib collision

SUPPORTED_FORMATS = {".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                     ".png": "image/png", ".gif": "image/gif", ".webp": "image/webp"}


def load_image_b64(path: str) -> tuple[str, str]:
    p = Path(path)
    suffix = p.suffix.lower()
    if suffix not in SUPPORTED_FORMATS:
        raise ValueError(f"Unsupported image format '{suffix}'. Supported: {', '.join(SUPPORTED_FORMATS)}")
    with open(p, "rb") as f:
        return base64.standard_b64encode(f.read()).decode(), SUPPORTED_FORMATS[suffix]


def _extract_json(text: str) -> dict:
    """Extract outermost JSON object robustly, handling model preamble."""
    start = text.find("{")
    if start == -1:
        raise ValueError("No JSON object found in response")
    depth, end = 0, -1
    for i, ch in enumerate(text[start:], start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end = i
                break
    if end == -1:
        raise ValueError("Unclosed JSON object in response")
    return json.loads(text[start:end + 1])


def build_criteria_details(criteria: dict) -> str:
    lines = []
    for name, cfg in criteria["criteria"].items():
        lines.append(f"\n**{name}** (weight: {cfg['weight']})")
        lines.append(f"  {cfg['description']}")
        if "rubric" in cfg:
            for score, desc in sorted(cfg["rubric"].items(), reverse=True):
                lines.append(f"  {score}: {desc}")
    return "\n".join(lines)


def build_judge_prompt(criteria: dict, original_prompt: str | None) -> str:
    prompt_context = f' generated from the prompt: "{original_prompt}"' if original_prompt else ""
    criteria_details = build_criteria_details(criteria)
    template = criteria.get("judge_prompt_template", DEFAULT_JUDGE_PROMPT)
    return template.format(prompt_context=prompt_context, criteria_details=criteria_details)


def call_openai(model: str, image_b64: str, media_type: str, prompt: str) -> dict:
    from openai import OpenAI
    client = OpenAI(api_key=vault.require("OPENAI_API_KEY"))
    resp = client.chat.completions.create(
        model=model,
        response_format={"type": "json_object"},
        messages=[{"role": "user", "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:{media_type};base64,{image_b64}"}}
        ]}]
    )
    return json.loads(resp.choices[0].message.content)


def call_anthropic(model: str, image_b64: str, media_type: str, prompt: str) -> dict:
    import anthropic
    client = anthropic.Anthropic(api_key=vault.require("ANTHROPIC_API_KEY"))
    resp = client.messages.create(
        model=model,
        max_tokens=1024,
        messages=[{"role": "user", "content": [
            {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": image_b64}},
            {"type": "text", "text": prompt}
        ]}]
    )
    return _extract_json(resp.content[0].text)


def call_gemini(model: str, image_b64: str, media_type: str, prompt: str) -> dict:
    from openai import OpenAI
    client = OpenAI(
        api_key=vault.require("GEMINI_API_KEY"),
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
    )
    resp = client.chat.completions.create(
        model=model,
        response_format={"type": "json_object"},
        messages=[{"role": "user", "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:{media_type};base64,{image_b64}"}}
        ]}]
    )
    return json.loads(resp.choices[0].message.content)


def call_openrouter(model: str, image_b64: str, media_type: str, prompt: str) -> dict:
    from openai import OpenAI
    or_model = model[len("openrouter/"):] if model.lower().startswith("openrouter/") else model
    client = OpenAI(
        api_key=vault.require("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1"
    )
    resp = client.chat.completions.create(
        model=or_model,
        response_format={"type": "json_object"},
        messages=[{"role": "user", "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:{media_type};base64,{image_b64}"}}
        ]}]
    )
    return json.loads(resp.choices[0].message.content)


def call_mistral(model: str, image_b64: str, media_type: str, prompt: str) -> dict:
    from mistralai import Mistral
    client = Mistral()
    resp = client.chat.complete(
        model=model,
        response_format={"type": "json_object"},
        messages=[{"role": "user", "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": f"data:{media_type};base64,{image_b64}"}
        ]}]
    )
    return json.loads(resp.choices[0].message.content)


# Ordered so longer/more-specific prefixes match before shorter ones
PROVIDERS = [
    ("claude",      call_anthropic),
    ("gemini",      call_gemini),
    ("openrouter/", call_openrouter),
    ("pixtral",     call_mistral),
    ("ministral",   call_mistral),
    ("mistral",     call_mistral),
    ("gpt",         call_openai),
    ("o1",          call_openai),
    ("o3",          call_openai),
    ("o4",          call_openai),
]


def call_judge(model: str, image_b64: str, media_type: str, prompt: str) -> dict:
    lower = model.lower()
    for prefix, fn in PROVIDERS:
        if lower.startswith(prefix):
            return fn(model, image_b64, media_type, prompt)
    return call_openai(model, image_b64, media_type, prompt)


def compute_weighted_score(scores: dict, criteria: dict) -> float:
    total = 0.0
    for name, cfg in criteria["criteria"].items():
        if name in scores:
            total += scores[name]["score"] * cfg["weight"]
    return round(total, 2)


def score_images(image_paths: list[str], criteria: dict, judge_models: list[str],
                 original_prompt: str | None = None) -> list[dict]:
    prompt = build_judge_prompt(criteria, original_prompt)
    results = []

    for img_path in image_paths:
        model_scores = {}

        try:
            b64, media_type = load_image_b64(img_path)
        except Exception as e:
            results.append({"image": img_path, "error": str(e), "judges": {}})
            continue

        for model in judge_models:
            try:
                raw = call_judge(model, b64, media_type, prompt)
                scores = raw.get("scores", {})
                model_scores[model] = {
                    "scores": scores,
                    "weighted_total": compute_weighted_score(scores, criteria),
                    "overall_impression": raw.get("overall_impression", "")
                }
            except Exception as e:
                model_scores[model] = {"error": str(e)}

        results.append({"image": img_path, "judges": model_scores})

    return results


DEFAULT_JUDGE_PROMPT = """You are evaluating an image{prompt_context}.

Score this image on each criterion using the rubric below.
Return ONLY a JSON object with this exact structure:
{{
  "scores": {{
    "<criterion_name>": {{
      "score": <integer 1-5>,
      "reasoning": "<one sentence>"
    }}
  }},
  "overall_impression": "<one sentence summary>"
}}

{criteria_details}"""
