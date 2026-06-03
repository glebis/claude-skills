#!/usr/bin/env python3
"""Trigger eval: assert each skill's description carries the phrasings it must fire on
(a lightweight proxy for skill-tool trigger matching)."""
import os, re, sys
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.join(HERE,"..")
EXPECT={
 "setup":["set up confide","install","configur"],
 "anon":["anonymize","redact","de-identif"],
 "red":["residual","re-identif","risk","red-team"],
 "rehydrate":["rehydrate","restore","unmask","placeholder"],
 "view":["visuali","redact","highlight","diff"],
 "audit":["audit","scan","pii","corpus"],
 "vault":["vault","encrypt","three lock","sops"],
 "annotate":["annotate","label","gold","agreement"],
}
def desc(skill):
    t=open(os.path.join(ROOT,"skills",skill,"SKILL.md"),encoding="utf-8").read().lower()
    m=re.search(r"^---\s*(.*?)\s*---",t,re.DOTALL|re.MULTILINE)
    return m.group(1) if m else t
fails=[]
for s,kws in EXPECT.items():
    d=desc(s)
    for kw in kws:
        if kw not in d: fails.append(f"{s}: description missing trigger '{kw}'")
print(f"[trigger-eval] checked {sum(len(v) for v in EXPECT.values())} trigger phrasings across {len(EXPECT)} skills")
if fails: print("FAIL:"); [print("  -",f) for f in fails]; sys.exit(1)
print("PASS ✓ all skills carry their trigger phrasings"); sys.exit(0)
