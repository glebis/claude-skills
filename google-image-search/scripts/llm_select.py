"""LLM-based image selection and term extraction."""

import json
import os
import subprocess
import textwrap
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

DEFAULT_LLM_EXECUTABLE = Path("/opt/homebrew/bin/llm")
DEFAULT_LLM_MODEL = "openrouter/openai/gpt-4o-mini"
DEFAULT_LLM_PROVIDER = "openrouter"

DEFAULT_SELECTION_PROMPT = textwrap.dedent(
    """
    You are an expert fact-checking researcher picking the single best real-world image or
    research figure for a technical presentation. Prioritize authenticity, clarity, and
    alignment with the provided selection criteria. Prefer reputable sources, avoid stock
    art, concept renders, diagrams (unless the criteria call for figures), and low-quality
    or suspicious images. When in doubt, choose the option that best illustrates the topic
    for a skeptical technical audience.
    Respond strictly with JSON: {"chosen_index": <integer>, "explanation": "<short reason>"}.
    """
).strip()

DEFAULT_TERM_EXTRACTION_PROMPT = textwrap.dedent(
    """
    You are an expert at identifying concepts in text that would benefit from visual illustration.
    Analyze the provided note and extract terms/concepts that:
    1. Would be clearer with an image (technical diagrams, physical devices, people, places)
    2. Are concrete enough to find relevant images for
    3. Are significant to the document's content

    For each term, provide:
    - term: the search query
    - heading: which section heading it belongs under (or null if general)
    - description: brief context for what kind of image would be helpful
    - criteria: what makes a good image for this term

    Respond with JSON array: [{"term": "...", "heading": "...", "description": "...", "criteria": "..."}, ...]
    Extract 3-8 terms maximum, focusing on the most visually impactful concepts.
    """
).strip()


def parse_json_from_response(text: str) -> Optional[Dict[str, Any]]:
    """Parse JSON from LLM response, handling markdown code blocks."""
    text = text.strip()
    if not text:
        return None

    # Try direct parse
    if text.startswith("{") and text.endswith("}"):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

    # Try to find JSON object in response
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        snippet = text[start : end + 1]
        try:
            return json.loads(snippet)
        except json.JSONDecodeError:
            pass

    return None


def parse_json_array_from_response(text: str) -> Optional[List[Dict[str, Any]]]:
    """Parse JSON array from LLM response."""
    text = text.strip()
    if not text:
        return None

    # Remove markdown code blocks if present
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()

    # Try direct parse
    if text.startswith("[") and text.endswith("]"):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

    # Try to find JSON array in response
    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end != -1 and end > start:
        snippet = text[start : end + 1]
        try:
            return json.loads(snippet)
        except json.JSONDecodeError:
            pass

    return None


def run_llm(
    prompt: str,
    system_prompt: str,
    llm_executable: Path = DEFAULT_LLM_EXECUTABLE,
    model: str = DEFAULT_LLM_MODEL,
    provider: Optional[str] = DEFAULT_LLM_PROVIDER,
    openrouter_key: Optional[str] = None,
) -> tuple[bool, str]:
    """Run LLM with prompt and return (success, output)."""
    if not llm_executable.exists():
        return False, f"LLM executable not found: {llm_executable}"

    cmd = [
        str(llm_executable),
        "prompt",
        prompt,
        "-m",
        model,
        "-n",
        "--no-stream",
        "-s",
        system_prompt,
    ]
    # Only add provider if model doesn't already include provider prefix
    if provider and "/" not in model:
        cmd.extend(["-o", f"provider={provider}"])

    llm_env = os.environ.copy()
    if openrouter_key:
        llm_env.setdefault("OPENROUTER_API_KEY", openrouter_key)

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            env=llm_env,
            timeout=120,
        )
    except subprocess.TimeoutExpired:
        return False, "LLM request timed out"

    if proc.returncode != 0:
        return False, proc.stderr.strip() or "Unknown LLM error"

    return True, proc.stdout


def run_llm_selection(
    *,
    results: Iterable[Dict[str, Any]],
    llm_executable: Path = DEFAULT_LLM_EXECUTABLE,
    model: str = DEFAULT_LLM_MODEL,
    system_prompt: str = DEFAULT_SELECTION_PROMPT,
    openrouter_key: Optional[str] = None,
    provider: Optional[str] = DEFAULT_LLM_PROVIDER,
) -> None:
    """Use LLM to select best image from candidates for each entry."""
    for bundle in results:
        entry = bundle["entry"]
        candidates = sorted(
            bundle["results"],
            key=lambda item: item.get("evaluation", {}).get("score", float("-inf")),
            reverse=True,
        )
        selection_count = entry.get("selectionCount", 2)
        if selection_count <= 0:
            continue
        candidates = candidates[: max(selection_count, 1)]
        if not candidates:
            continue

        # Build prompt
        prompt_lines = [
            f"Topic: {entry.get('heading') or entry.get('id', 'Unnamed')}",
        ]
        criteria = entry.get("selectionCriteria") or entry.get("description")
        if criteria:
            prompt_lines.append(f"Selection criteria: {criteria}")
        prompt_lines.append("Candidates:")

        for idx, item in enumerate(candidates, start=1):
            eval_data = item.get("evaluation", {})
            reasons = "; ".join(eval_data.get("reasons", [])) or "(no reasons)"
            prompt_lines.append(
                textwrap.dedent(
                    f"""
                    Candidate {idx}:
                      Title: {item.get('title') or 'Untitled'}
                      URL: {item.get('link')}
                      Host: {item.get('host') or 'unknown'}
                      Score: {eval_data.get('score', 'N/A')}
                      Reasons: {reasons}
                    """
                ).strip()
            )

        prompt_lines.append(
            "Choose the single best candidate index that meets the criteria and explain briefly."
        )
        prompt = "\n".join(prompt_lines)

        success, output = run_llm(
            prompt=prompt,
            system_prompt=system_prompt,
            llm_executable=llm_executable,
            model=model,
            provider=provider,
            openrouter_key=openrouter_key,
        )

        if not success:
            entry["finalSelection"] = {
                "item": candidates[0],
                "explanation": f"LLM selection failed: {output}",
                "fallback": True,
            }
            candidates[0]["finalChoice"] = True
            candidates[0]["finalChoiceReason"] = entry["finalSelection"]["explanation"]
            continue

        parsed = parse_json_from_response(output)
        if not parsed or "chosen_index" not in parsed:
            entry["finalSelection"] = {
                "item": candidates[0],
                "explanation": "LLM response unreadable; defaulted to top-scoring candidate",
                "fallback": True,
            }
            candidates[0]["finalChoice"] = True
            candidates[0]["finalChoiceReason"] = entry["finalSelection"]["explanation"]
            continue

        chosen_index = parsed.get("chosen_index")
        explanation = parsed.get("explanation", "")
        try:
            chosen_idx = int(chosen_index)
        except (TypeError, ValueError):
            chosen_idx = 1
        if chosen_idx < 1 or chosen_idx > len(candidates):
            chosen_idx = 1

        winner = candidates[chosen_idx - 1]
        winner["finalChoice"] = True
        winner["finalChoiceReason"] = explanation or "Chosen by LLM"
        entry["finalSelection"] = {
            "item": winner,
            "explanation": explanation or "Chosen by LLM",
            "fallback": False,
        }


def extract_visual_terms(
    note_content: str,
    llm_executable: Path = DEFAULT_LLM_EXECUTABLE,
    model: str = DEFAULT_LLM_MODEL,
    system_prompt: str = DEFAULT_TERM_EXTRACTION_PROMPT,
    openrouter_key: Optional[str] = None,
    provider: Optional[str] = DEFAULT_LLM_PROVIDER,
) -> List[Dict[str, Any]]:
    """Use LLM to extract visual-worthy terms from note content."""
    # Truncate very long notes
    max_chars = 8000
    if len(note_content) > max_chars:
        note_content = note_content[:max_chars] + "\n\n[... truncated ...]"

    prompt = f"Analyze this note and extract terms that would benefit from images:\n\n{note_content}"

    success, output = run_llm(
        prompt=prompt,
        system_prompt=system_prompt,
        llm_executable=llm_executable,
        model=model,
        provider=provider,
        openrouter_key=openrouter_key,
    )

    if not success:
        return []

    terms = parse_json_array_from_response(output)
    return terms if terms else []


def generate_config_from_terms(
    terms: List[str],
    llm_executable: Path = DEFAULT_LLM_EXECUTABLE,
    model: str = DEFAULT_LLM_MODEL,
    openrouter_key: Optional[str] = None,
    provider: Optional[str] = DEFAULT_LLM_PROVIDER,
    num_results: int = 5,
) -> List[Dict[str, Any]]:
    """Use LLM to generate full config entries from a list of terms."""
    system_prompt = textwrap.dedent(
        """
        Generate image search config entries for the provided terms.
        For each term, create an entry with:
        - id: slugified term
        - heading: human-readable title
        - description: what kind of image to find
        - query: optimized search query
        - selectionCriteria: what makes a good image
        - requiredTerms: terms that MUST appear (usually the main subject)
        - optionalTerms: bonus terms that improve relevance
        - excludeTerms: terms to avoid (stock photo, clipart, etc.)

        Respond with JSON array of entries.
        """
    ).strip()

    prompt = f"Generate image search configs for these terms:\n{json.dumps(terms)}"

    success, output = run_llm(
        prompt=prompt,
        system_prompt=system_prompt,
        llm_executable=llm_executable,
        model=model,
        provider=provider,
        openrouter_key=openrouter_key,
    )

    if not success:
        # Fallback to simple entries
        from .config import create_entry_from_term
        return [create_entry_from_term(term, num_results=num_results) for term in terms]

    entries = parse_json_array_from_response(output)
    if not entries:
        from .config import create_entry_from_term
        return [create_entry_from_term(term, num_results=num_results) for term in terms]

    # Ensure required fields
    for entry in entries:
        entry.setdefault("numResults", num_results)
        entry.setdefault("selectionCount", 2)
        entry.setdefault("safe", "active")

    return entries
