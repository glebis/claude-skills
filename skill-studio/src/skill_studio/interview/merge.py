from __future__ import annotations
from skill_studio.schema import DesignJSON


def deep_merge(design: DesignJSON, patch: dict) -> None:
    """Merge a partial JSON patch into a DesignJSON model in-place.

    Shared by extractor.py and updater.py — single source of truth.
    """
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
            # LLM returned a string for a submodel field (common for Trigger).
            # Map to the conventional text field if present, otherwise skip.
            for candidate in ("detail", "what_hurts", "situation", "motivation"):
                if hasattr(current, candidate):
                    setattr(current, candidate, v)
                    break
        elif isinstance(v, list):
            # If the field is typed `list[Submodel]`, coerce dicts into submodels
            # so pydantic doesn't warn on serialization later.
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
            # Non-dict, non-string for a submodel — skip rather than corrupt
            continue
        else:
            setattr(design, k, v)
