#!/usr/bin/env python3
"""Score human inter-annotator agreement (IAA) from annotator.html exports.

Ingests `labels.<doc>.<annotator>.json` files (the annotator tool's Export output),
groups them by document, and computes — per doc and overall:

  • Cohen's kappa (pairwise) and Fleiss' kappa (3+ annotators), character-level over the
    canonical type label (PERSON/.../O). Character-level avoids tokenization disputes.
  • Span/entity F1 (pairwise, relaxed overlap + same canonical type) — the de-id view.
  • A disagreement report: spans not all annotators agree on (overlap+type), and any
    span carrying a `QUESTION:` note — the queue for adjudication.
  • A DRAFT adjudicated gold: majority span per overlap-cluster, ties/questions flagged
    `needs_review:true` for a human adjudicator (never auto-finalised).

This is REAL human IAA — the replacement for the LLM-assisted consistency check (R4).
Stdlib only. Usage:
  python3 score_iaa.py --labels-dir labels/ [--out-prefix human-]
"""
import argparse
import glob
import itertools
import json
import os
from collections import defaultdict, Counter

# Standalone (stdlib only): no external package dependency. Outputs land in
# --out-dir (defaults to the labels dir) so the skill runs anywhere.
TYPES = ["PERSON", "LOCATION", "ORG", "PHONE", "EMAIL", "ID", "DATE", "MEDICATION", "AGE", "PROFESSION"]
O = "O"


def char_labels(n, spans):
    """Per-character canonical type over a doc of length n (last-wins on overlap)."""
    lab = [O] * n
    for s in sorted(spans, key=lambda s: s["end"] - s["start"]):  # longer overrides shorter
        for i in range(max(0, s["start"]), min(n, s["end"])):
            lab[i] = s["type"]
    return lab


def cohen_kappa(a, b):
    cats = set(a) | set(b)
    n = len(a)
    if n == 0:
        return None
    po = sum(1 for x, y in zip(a, b) if x == y) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum((ca[c] / n) * (cb[c] / n) for c in cats)
    return 1.0 if pe == 1 else (po - pe) / (1 - pe)


def fleiss_kappa(label_lists):
    """label_lists: list (per annotator) of equal-length per-char label sequences."""
    n_ann = len(label_lists)
    if n_ann < 2:
        return None
    N = len(label_lists[0])
    cats = sorted({l for seq in label_lists for l in seq})
    idx = {c: i for i, c in enumerate(cats)}
    P_i = []
    col = [0] * len(cats)
    for j in range(N):
        counts = [0] * len(cats)
        for seq in label_lists:
            counts[idx[seq[j]]] += 1
        for k in range(len(cats)):
            col[k] += counts[k]
        P_i.append((sum(c * c for c in counts) - n_ann) / (n_ann * (n_ann - 1)) if n_ann > 1 else 1.0)
    Pbar = sum(P_i) / N if N else 0.0
    pj = [c / (N * n_ann) for c in col]
    Pe = sum(p * p for p in pj)
    return 1.0 if Pe == 1 else (Pbar - Pe) / (1 - Pe)


def overlaps(a, b):
    return a["start"] < b["end"] and b["start"] < a["end"]


def span_f1(ref, hyp):
    """relaxed overlap + same canonical type, pairwise."""
    tp = sum(1 for h in hyp if any(overlaps(h, r) and h["type"] == r["type"] for r in ref))
    fp = len(hyp) - tp
    fn = sum(1 for r in ref if not any(overlaps(h, r) and h["type"] == r["type"] for h in hyp))
    p = tp / (tp + fp) if (tp + fp) else 0.0
    r = tp / (tp + fn) if (tp + fn) else 0.0
    return 2 * p * r / (p + r) if (p + r) else 0.0


def cluster_spans(all_spans):
    """Group overlapping spans (across annotators) into clusters for adjudication."""
    items = sorted(all_spans, key=lambda s: (s["start"], s["end"]))
    clusters, cur = [], []
    cur_end = -1
    for s in items:
        if cur and s["start"] < cur_end:
            cur.append(s); cur_end = max(cur_end, s["end"])
        else:
            if cur: clusters.append(cur)
            cur = [s]; cur_end = s["end"]
    if cur: clusters.append(cur)
    return clusters


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--labels-dir", default="labels", help="dir with labels.<doc>.<annotator>.json files")
    ap.add_argument("--out-dir", default=None, help="where to write results (default: --labels-dir)")
    ap.add_argument("--out-prefix", default="human-")
    args = ap.parse_args()
    out_dir = args.out_dir or args.labels_dir
    os.makedirs(out_dir, exist_ok=True)

    files = glob.glob(os.path.join(args.labels_dir, "labels.*.json"))
    if not files:
        print(f"No labels.*.json in {args.labels_dir}"); return
    by_doc = defaultdict(dict)  # doc_id -> annotator -> payload
    for f in files:
        d = json.load(open(f, encoding="utf-8"))
        by_doc[d["doc_id"]][d.get("annotator", os.path.basename(f))] = d

    docs_out, draft_gold, disagreements = {}, [], []
    all_pairwise_k, all_pairwise_f1, all_fleiss = [], [], []

    for doc_id, anns in sorted(by_doc.items()):
        if len(anns) < 2:
            print(f"  ⚠ {doc_id}: only {len(anns)} annotator — skipped (need ≥2)"); continue
        text = next(iter(anns.values())).get("text", "")
        n = len(text)
        names = sorted(anns)
        seqs = {a: char_labels(n, anns[a]["spans"]) for a in names}
        # pairwise Cohen + span-F1
        pk, pf = [], []
        for a, b in itertools.combinations(names, 2):
            k = cohen_kappa(seqs[a], seqs[b])
            f = span_f1(anns[a]["spans"], anns[b]["spans"])
            if k is not None: pk.append(k)
            pf.append(f)
        fk = fleiss_kappa([seqs[a] for a in names]) if len(names) >= 3 else None
        docs_out[doc_id] = {
            "annotators": names,
            "cohen_kappa_pairwise_mean": round(sum(pk) / len(pk), 3) if pk else None,
            "fleiss_kappa": round(fk, 3) if fk is not None else None,
            "span_f1_pairwise_mean": round(sum(pf) / len(pf), 3) if pf else None,
        }
        all_pairwise_k += pk; all_pairwise_f1 += pf
        if fk is not None: all_fleiss.append(fk)

        # disagreement clusters + draft adjudicated gold
        tagged = [dict(s, _by=a) for a in names for s in anns[a]["spans"]]
        for cl in cluster_spans(tagged):
            voters = {s["_by"] for s in cl}
            types = Counter(s["type"] for s in cl)
            top_type, top_n = types.most_common(1)[0]
            unanimous = len(voters) == len(names) and len(types) == 1
            has_q = any(str(s.get("note", "")).strip().upper().startswith("QUESTION") for s in cl)
            start = min(s["start"] for s in cl if s["type"] == top_type)
            end = max(s["end"] for s in cl if s["type"] == top_type)
            entry = {
                "doc_id": doc_id, "start": start, "end": end, "text": text[start:end],
                "type": top_type, "agreement": f"{top_n}/{len(names)}",
                "needs_review": (not unanimous) or has_q,
                "note": "; ".join(s["note"] for s in cl if s.get("note")),
            }
            draft_gold.append(entry)
            if entry["needs_review"]:
                disagreements.append({**entry, "votes": dict(types), "voters": sorted(voters)})

    overall = {
        "n_docs_scored": len(docs_out),
        "cohen_kappa_pairwise_mean": round(sum(all_pairwise_k) / len(all_pairwise_k), 3) if all_pairwise_k else None,
        "fleiss_kappa_mean": round(sum(all_fleiss) / len(all_fleiss), 3) if all_fleiss else None,
        "span_f1_pairwise_mean": round(sum(all_pairwise_f1) / len(all_pairwise_f1), 3) if all_pairwise_f1 else None,
        "n_clusters": len(draft_gold), "n_needs_review": len(disagreements),
    }
    result = {"overall": overall, "per_doc": docs_out}
    json.dump(result, open(os.path.join(out_dir, f"{args.out_prefix}iaa-results.json"), "w"), ensure_ascii=False, indent=2)
    json.dump({"disagreements": disagreements}, open(os.path.join(out_dir, f"{args.out_prefix}iaa-disagreements.json"), "w"), ensure_ascii=False, indent=2)
    json.dump({"draft_gold": draft_gold}, open(os.path.join(out_dir, f"{args.out_prefix}adjudicated-gold-draft.json"), "w"), ensure_ascii=False, indent=2)

    print(f"[iaa] {overall['n_docs_scored']} docs, Cohen κ {overall['cohen_kappa_pairwise_mean']}, "
          f"Fleiss κ {overall['fleiss_kappa_mean']}, span-F1 {overall['span_f1_pairwise_mean']}")
    print(f"[iaa] {overall['n_clusters']} span-clusters, {overall['n_needs_review']} need adjudication "
          f"-> {args.out_prefix}iaa-disagreements.json")
    md = [f"# CONFIDE — Human IAA results ({overall['n_docs_scored']} docs)", "",
          "**Real human inter-annotator agreement** (replaces the LLM-assisted consistency check, R4).",
          f"Annotators labelled blind via `annotator.html`; scored by `score_iaa.py`. Codebook v1.", "",
          f"- **Cohen's κ (pairwise mean): {overall['cohen_kappa_pairwise_mean']}**",
          f"- Fleiss' κ (mean, 3+ annotators): {overall['fleiss_kappa_mean']}",
          f"- Span/entity F1 (pairwise mean, relaxed+type): {overall['span_f1_pairwise_mean']}",
          f"- Span-clusters: {overall['n_clusters']} · needing adjudication: {overall['n_needs_review']}", "",
          "Target κ ≥ 0.80 = a defensible gold standard. Disagreements go to adjudication; the "
          "adjudicated gold is the published label set, and post-adjudication κ is reported too.", "",
          "| doc | annotators | Cohen κ | Fleiss κ | span-F1 |", "|---|---|--:|--:|--:|"]
    for d, v in docs_out.items():
        md.append(f"| {d} | {len(v['annotators'])} | {v['cohen_kappa_pairwise_mean']} | {v['fleiss_kappa']} | {v['span_f1_pairwise_mean']} |")
    open(os.path.join(out_dir, f"{args.out_prefix}IAA-HUMAN-RESULTS.md"), "w").write("\n".join(md) + "\n")
    print(f"[iaa] wrote {args.out_prefix}IAA-HUMAN-RESULTS.md + draft adjudicated gold")


if __name__ == "__main__":
    main()
