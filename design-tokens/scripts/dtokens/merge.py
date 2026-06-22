"""Layer a project-override tree on top of a global-base tree.

This layering is a *skill convention*, not DTCG ``$extends`` group inheritance.
Rule: a leaf token in the override replaces the whole base token at that path;
groups merge recursively.
"""

import copy


def _is_token(node):
    return isinstance(node, dict) and "$value" in node


def merge(base, override):
    """Return a new tree = base with override layered on top. Pure function."""
    result = copy.deepcopy(base)

    def recurse(dst, src):
        for key, src_val in src.items():
            if key in dst and isinstance(dst[key], dict) and isinstance(src_val, dict):
                if _is_token(src_val) or _is_token(dst[key]):
                    dst[key] = copy.deepcopy(src_val)  # token override replaces wholesale
                else:
                    recurse(dst[key], src_val)
            else:
                dst[key] = copy.deepcopy(src_val)

    recurse(result, override)
    return result
