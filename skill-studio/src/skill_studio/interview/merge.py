from __future__ import annotations
from skill_studio.schema import DesignJSON


def deep_merge(design: DesignJSON, patch: dict) -> None:
    """Merge a partial JSON patch into a DesignJSON model in-place.

    Supports both nested dicts and dot-notation keys (e.g. "problem.what_hurts").
    """
    expanded = _expand_dot_keys(patch)
    _apply(design, expanded)


def _expand_dot_keys(patch: dict) -> dict:
    """Expand dot-notation keys into nested dicts."""
    result: dict = {}
    for k, v in patch.items():
        if "." in k:
            parts = k.split(".")
            target = result
            for part in parts[:-1]:
                target = target.setdefault(part, {})
            existing = target.get(parts[-1])
            if isinstance(existing, dict) and isinstance(v, dict):
                existing.update(v)
            else:
                target[parts[-1]] = v
        else:
            if k in result and isinstance(result[k], dict) and isinstance(v, dict):
                result[k].update(v)
            else:
                result[k] = v
    return result


def _apply(design: DesignJSON, patch: dict) -> None:
    """Apply an expanded (no dot-keys) patch to a DesignJSON model."""
    for k, v in patch.items():
        if not hasattr(design, k):
            continue
        current = getattr(design, k)
        is_submodel = hasattr(current, "model_copy")
        if isinstance(v, dict) and is_submodel:
            for sub_k, sub_v in v.items():
                if hasattr(current, sub_k):
                    setattr(current, sub_k, sub_v)
        elif is_submodel and isinstance(v, str):
            for candidate in ("detail", "what_hurts", "situation", "motivation"):
                if hasattr(current, candidate):
                    setattr(current, candidate, v)
                    break
        elif isinstance(v, list):
            field = type(design).model_fields.get(k)
            item_type = None
            if field is not None:
                ann = field.annotation
                args = getattr(ann, "__args__", None)
                if args and hasattr(args[0], "model_validate"):
                    item_type = args[0]
            if item_type is not None:
                coerced = []
                for item in v:
                    if isinstance(item, dict):
                        try:
                            coerced.append(item_type.model_validate(item))
                        except Exception:
                            continue
                    else:
                        coerced.append(item)
                setattr(design, k, coerced)
            else:
                setattr(design, k, v)
        elif is_submodel:
            continue
        else:
            setattr(design, k, v)
