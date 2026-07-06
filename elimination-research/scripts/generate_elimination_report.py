#!/usr/bin/env python3
"""Generate elimination-research reports from a structured dataset."""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
LIB_DIR = SCRIPT_DIR / "elimination_research_lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from application.report_generator import generate_final_report_artifacts
from domain.scoring_engine import ProductCandidate, score_product_candidates
from infrastructure.google_image_search import (
    resolve_google_image_search_credentials,
    search_candidate_images,
)


def main() -> int:
    args = _parse_args()
    dataset_path = args.dataset.expanduser().resolve()
    output_dir = args.output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    dataset = _load_json(dataset_path)
    dataset = _normalize_dataset(dataset)
    domain_registry = _load_domain_registry(args, dataset)
    max_price = _price_limit(args, dataset)
    price_basis = args.price_limit_basis or dataset.get("constraints", {}).get(
        "price_limit_basis",
        "device_price_eur",
    )
    image_search = _load_or_refresh_image_search(
        args=args,
        dataset=dataset,
        output_path=output_dir / "image_search_results.json",
    )

    candidates = [
        ProductCandidate(
            id=item["id"],
            name=item["name"],
            three_year_cost_eur=item["three_year_cost_eur"],
            metrics=item["metrics"],
        )
        for item in dataset["candidates"]
    ]
    scoring_result = score_product_candidates(candidates)
    evidence_summary = _evidence_summary(dataset, candidates, scoring_result, max_price)
    report_context = _report_context(
        args=args,
        dataset=dataset,
        domain_registry=domain_registry,
        image_search=image_search,
        max_price=max_price,
        price_basis=price_basis,
    )
    artifacts = generate_final_report_artifacts(
        title=args.title or dataset["title"],
        candidates=candidates,
        scoring_result=scoring_result,
        evidence_summary=evidence_summary,
        report_context=report_context,
    )

    paths = {
        "json": output_dir / "final_report.json",
        "markdown": output_dir / "report.md",
        "html": output_dir / "report.html",
        "quick_html": output_dir / "quick_report.html",
        "raw": output_dir / "raw_research_data.json",
    }
    paths["json"].write_text(
        json.dumps(artifacts["payload"], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    paths["markdown"].write_text(artifacts["markdown"], encoding="utf-8")
    paths["html"].write_text(artifacts["html"], encoding="utf-8")
    paths["quick_html"].write_text(artifacts["quick_html"], encoding="utf-8")
    paths["raw"].write_text(
        json.dumps(dataset, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    for path in paths.values():
        print(path)
    return 0


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate quick and full elimination-research reports.",
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        required=True,
        help="Path to a structured elimination-research dataset JSON file.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory for final_report.json, quick_report.html, report.html, report.md.",
    )
    parser.add_argument("--title", default="", help="Override report title.")
    parser.add_argument("--question", default="", help="Override task question.")
    parser.add_argument("--market", default="", help="Override purchase country/market.")
    parser.add_argument("--currency", default="", help="Override currency label.")
    parser.add_argument(
        "--max-price-eur",
        type=float,
        default=None,
        help="Override purchase-price ceiling.",
    )
    parser.add_argument(
        "--price-limit-basis",
        default="",
        help="Field used for price ceiling, usually device_price_eur or three_year_cost_eur.",
    )
    parser.add_argument(
        "--domain-registry",
        type=Path,
        default=None,
        help="Optional domain registry JSON. Falls back to dataset.domain_registry.",
    )
    parser.add_argument(
        "--refresh-images",
        action="store_true",
        help="Call Google Custom Search and refresh image_search_results.json.",
    )
    parser.add_argument(
        "--image-results",
        type=int,
        default=5,
        help="Image results per candidate when --refresh-images is used.",
    )
    parser.add_argument(
        "--observed-at",
        default="",
        help="ISO timestamp for refreshed image searches.",
    )
    return parser.parse_args()


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _normalize_dataset(dataset: dict) -> dict:
    if "title" not in dataset:
        dataset["title"] = "Elimination Research Shortlist"
    dataset.setdefault("source_policy", "")
    dataset.setdefault("sources", [])
    dataset.setdefault("open_caveats", [])
    dataset.setdefault("constraints", {})

    for candidate in dataset.get("candidates", []):
        candidate.setdefault("metrics", {})
        device_price = candidate.get("device_price_eur")
        unit_price = candidate.get("replacement_unit_price_eur")
        quantity = candidate.get("replacement_quantity_3y", 0)
        if candidate.get("replacement_head_eur") is None and unit_price is not None:
            candidate["replacement_head_eur"] = round(float(unit_price) * float(quantity), 2)
        if candidate.get("three_year_cost_eur") is None:
            replacement = candidate.get("replacement_head_eur") or 0
            if device_price is None:
                raise ValueError(
                    f"{candidate.get('id', candidate.get('name'))} needs three_year_cost_eur or device_price_eur",
                )
            candidate["three_year_cost_eur"] = round(float(device_price) + float(replacement), 2)
    return dataset


def _load_domain_registry(args: argparse.Namespace, dataset: dict) -> list[dict]:
    if args.domain_registry:
        payload = _load_json(args.domain_registry.expanduser().resolve())
    else:
        payload = dataset.get("domain_registry", [])
    if isinstance(payload, dict):
        return payload.get("domains", payload.get("registry", []))
    return payload


def _price_limit(args: argparse.Namespace, dataset: dict) -> float | None:
    if args.max_price_eur is not None:
        return args.max_price_eur
    constraints = dataset.get("constraints", {})
    return constraints.get("max_device_price_eur") or constraints.get("max_price_eur")


def _load_or_refresh_image_search(args, dataset: dict, output_path: Path) -> dict:
    if args.refresh_images:
        credentials = resolve_google_image_search_credentials()
        observed_at = args.observed_at or datetime.now(timezone.utc).isoformat()
        results = search_candidate_images(
            candidates=dataset["candidates"],
            credentials=credentials,
            num_results=args.image_results,
            observed_at=observed_at,
        )
        output_path.write_text(
            json.dumps(results, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return results

    if dataset.get("image_search"):
        return dataset["image_search"]
    if output_path.exists():
        return _load_json(output_path)
    return {
        "enabled": False,
        "provider": "google_custom_search",
        "mode": "cache_missing",
        "observed_at": "",
        "search_count": 0,
        "searches": [],
    }


def _evidence_summary(dataset, candidates, scoring_result, max_price):
    candidate_details = dataset.get("candidates", [])
    return {
        "source_count": len(dataset.get("sources", [])),
        "summary": dataset.get("source_policy", ""),
        "tournament": dataset.get("tournament")
        or _tournament_rows(candidates, scoring_result, max_price),
        "caveats": dataset.get("open_caveats", []),
        "sources": [
            _source_row(source, candidate_details)
            for source in dataset.get("sources", [])
        ],
    }


def _report_context(args, dataset, domain_registry, image_search, max_price, price_basis):
    return {
        "question": args.question
        or dataset.get("question")
        or "Which option should be chosen from this shortlist?",
        "scope": dataset.get("source_policy", ""),
        "market": args.market or dataset.get("market", ""),
        "currency": args.currency or dataset.get("currency", "EUR"),
        "created_at": dataset.get("created_at", ""),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "data_sources": dataset.get(
            "data_sources",
            [
                "dataset JSON",
                "domain registry",
                "image_search_results.json",
                "deterministic scoring engine",
            ],
        ),
        "candidate_details": dataset["candidates"],
        "source_details": [
            _source_row(source, dataset["candidates"])
            for source in dataset.get("sources", [])
        ],
        "domain_registry": domain_registry,
        "image_search": image_search,
        "price_limit_eur": max_price,
        "price_limit_basis": price_basis,
        "criteria": dataset.get("criteria", []),
    }


def _candidate_ids_for_source(source_id: str, candidates: list[dict]) -> list[str]:
    return [
        candidate["id"]
        for candidate in candidates
        if source_id in candidate.get("source_refs", [])
    ]


def _source_row(source: dict, candidates: list[dict]) -> dict:
    return {
        "id": source.get("id", source.get("url", "")),
        "title": source.get("title", ""),
        "url": source.get("url", ""),
        "domain": source.get("domain", ""),
        "role": source.get("role", ""),
        "candidate_ids": _candidate_ids_for_source(source.get("id", ""), candidates),
        "metrics": source.get("metrics", {}),
        "notes": source.get("notes", ""),
    }


def _tournament_rows(candidates, scoring_result, max_price: float | None) -> list[dict]:
    names = {candidate.id: candidate.name for candidate in candidates}
    ranked = scoring_result.weighted_ranking
    if max_price is not None:
        costs = {candidate.id: candidate.three_year_cost_eur for candidate in candidates}
        ranked = [row for row in ranked if costs[row.candidate_id] <= max_price] or ranked
    if len(ranked) < 2:
        return []

    rows = []
    for index, row in enumerate(ranked[1:4], start=1):
        winner = ranked[0]
        rows.append(
            {
                "round": f"Comparison {index}",
                "a": names[winner.candidate_id],
                "b": names[row.candidate_id],
                "winner": names[winner.candidate_id],
                "reason": "Higher weighted score under the current criteria and price assumptions.",
            }
        )
    return rows


if __name__ == "__main__":
    raise SystemExit(main())
