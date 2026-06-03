#!/usr/bin/env python3
"""Round-trip eval: anon (reversible) → simulate a cloud analysis on the GREEN that
references the ACTUAL placeholders (+ mangling) → rehydrate. Offline, synthetic."""
import os, sys, re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "shared"))
import confide_core as C

CFG = dict(C.DEFAULTS); CFG["layers"] = ["regex"]
ORIG = "Клиент a.k@example.ru звонил +7-916-555-21-43; виделись last Tuesday."

def mangle(ph):  # [CONFIDE_X_0001] -> a plausible LLM mangling variant
    return ph.replace("[", "").replace("]", "").replace("_", " ", 1)  # "CONFIDE EMAIL_0001"

def run():
    fails = []
    green, mp = C.redact_reversible(ORIG, C.detect_regex(ORIG))
    entries = C.map_lookup(mp)                       # {placeholder: original}
    if not entries: fails.append("no placeholders produced")
    if any(orig in green for orig in entries.values()): fails.append("green leaks an original")
    # cloud-analysis sim: reference every placeholder (mangle the first), + ordinary prose
    refs = []
    for i, ph in enumerate(entries):
        refs.append(mangle(ph) if i == 0 else ph)
    analysis = "Analysis referencing " + ", ".join(refs) + ". Also 'person 1' is plain prose."
    restored, stats = C.rehydrate(analysis, mp)
    for orig in entries.values():
        if orig not in restored: fails.append(f"not restored: {orig[:6]}…")
    if "person 1" not in restored: fails.append("corrupted ordinary prose 'person 1'")
    if "CONFIDE_" in restored.replace("person", ""): fails.append("sentinel left unrestored")
    again, _ = C.rehydrate(restored, mp)
    if again != restored: fails.append("not idempotent")
    print(f"[eval] {len(entries)} placeholders; restored={stats['restored']} unmatched={stats['unmatched']}; prose preserved; idempotent")
    if fails: print("FAIL:"); [print("  -", f) for f in fails]; return 1
    print("PASS ✓ anon→(cloud sim)→rehydrate restores all originals, ignores prose, idempotent")
    return 0

if __name__ == "__main__": sys.exit(run())
