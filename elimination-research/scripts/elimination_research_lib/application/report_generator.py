import json
from collections import Counter, defaultdict
from html import escape

from domain.scoring_engine import (
    CONVENIENCE_WEIGHT,
    COST_PENALTY_WEIGHT,
    EFFECTIVENESS_WEIGHT,
    SKIN_SAFETY_WEIGHT,
)


def generate_final_report_artifacts(
    title,
    candidates,
    scoring_result,
    evidence_summary,
    report_context=None,
):
    report_context = report_context or {}
    names_by_id = {candidate.id: candidate.name for candidate in candidates}
    scores_by_id = _scores_by_candidate_id(scoring_result)

    candidate_payload = [
        {
            "candidate_id": candidate.id,
            "candidate_name": candidate.name,
            "three_year_cost_eur": candidate.three_year_cost_eur,
            "metrics": dict(candidate.metrics),
        }
        for candidate in candidates
    ]

    source_data = _source_data(evidence_summary, report_context)
    domain_summary = _domain_summary(source_data, report_context.get("domain_registry", []))
    image_search = report_context.get("image_search") or {
        "enabled": False,
        "provider": "google_custom_search",
        "mode": "not_configured",
        "searches": [],
    }
    image_rows = _image_search_rows(image_search)
    candidate_data = _attach_source_links(
        _attach_image_rows(
            _candidate_data(candidates, report_context, scores_by_id),
            image_rows,
        ),
        source_data,
    )
    budget = _budget_payload(report_context, candidate_data)
    decision_candidate_ids = _decision_candidate_ids(candidate_data, budget)

    def ranking_rows(rows, allowed_candidate_ids=None):
        rendered = []
        for row in rows:
            if allowed_candidate_ids is not None and row.candidate_id not in allowed_candidate_ids:
                continue
            item = {
                "rank": len(rendered) + 1,
                "candidate_id": row.candidate_id,
                "candidate_name": names_by_id[row.candidate_id],
                "score": row.score,
            }
            if hasattr(row, "score_per_eur"):
                item["score_per_eur"] = row.score_per_eur
            rendered.append(item)
        return rendered

    weighted = ranking_rows(scoring_result.weighted_ranking, decision_candidate_ids)
    cost_benefit = ranking_rows(scoring_result.cost_benefit_ranking, decision_candidate_ids)
    if not weighted:
        weighted = ranking_rows(scoring_result.weighted_ranking)
        cost_benefit = ranking_rows(scoring_result.cost_benefit_ranking)
    winner = {
        "candidate_id": weighted[0]["candidate_id"],
        "candidate_name": weighted[0]["candidate_name"],
        "score": weighted[0]["score"],
    }
    sensitivity_rankings = _decision_sensitivity_rankings(
        scoring_result.sensitivity_rankings,
        decision_candidate_ids,
    )
    pareto_frontier = _decision_pareto_frontier(candidates, decision_candidate_ids)

    payload = {
        "title": title,
        "candidate_count": len(candidates),
        "decision_candidate_count": len(weighted),
        "winner": winner,
        "task": _task_payload(title, report_context),
        "budget": budget,
        "criteria": _criteria_payload(report_context),
        "candidates": candidate_payload,
        "candidate_data": candidate_data,
        "rankings": {
            "weighted": weighted,
            "cost_benefit": cost_benefit,
        },
        "all_rankings": {
            "weighted": ranking_rows(scoring_result.weighted_ranking),
            "cost_benefit": ranking_rows(scoring_result.cost_benefit_ranking),
        },
        "pareto_frontier": pareto_frontier,
        "all_pareto_frontier": scoring_result.pareto_frontier,
        "sensitivity_rankings": sensitivity_rankings,
        "all_sensitivity_rankings": scoring_result.sensitivity_rankings,
        "evidence_summary": evidence_summary,
        "source_data": source_data,
        "domain_summary": domain_summary,
        "domain_registry": report_context.get("domain_registry", []),
        "image_search": image_search,
        "image_search_rows": image_rows,
    }

    markdown = _render_markdown(payload)
    html = _render_html(payload)
    quick_html = _render_quick_html(payload)

    return {"payload": payload, "markdown": markdown, "html": html, "quick_html": quick_html}


def _task_payload(title, report_context):
    return {
        "title": title,
        "question": report_context.get(
            "question",
            "Which option should be chosen from this shortlist?",
        ),
        "market": report_context.get("market", ""),
        "currency": report_context.get("currency", "EUR"),
        "created_at": report_context.get("created_at", ""),
        "generated_at": report_context.get("generated_at", ""),
        "data_sources": report_context.get(
            "data_sources",
            ["dataset JSON", "domain_registry.json", "final_report.json"],
        ),
        "scope": report_context.get(
            "scope",
            "Shortlist comparison using observed prices, product specs, and evidence proxies.",
        ),
    }


def _criteria_payload(report_context=None):
    custom_criteria = (report_context or {}).get("criteria") or []
    if custom_criteria:
        return [
            {
                "id": item.get("id", ""),
                "label": item.get("label", item.get("id", "")),
                "coefficient": item.get("coefficient", item.get("weight", "")),
                "unit": item.get("unit", ""),
                "direction": item.get("direction", ""),
                "definition": item.get("definition", ""),
            }
            for item in custom_criteria
        ]
    return [
        {
            "id": "effectiveness",
            "label": "Effectiveness proxy",
            "coefficient": EFFECTIVENESS_WEIGHT,
            "unit": "0-100",
            "direction": "higher is better",
            "definition": "Primary product-performance proxy.",
        },
        {
            "id": "skin_safety",
            "label": "Fit / safety",
            "coefficient": SKIN_SAFETY_WEIGHT,
            "unit": "0-100",
            "direction": "higher is better",
            "definition": "User-fit, safety, comfort, or risk proxy.",
        },
        {
            "id": "convenience",
            "label": "Convenience",
            "coefficient": CONVENIENCE_WEIGHT,
            "unit": "0-100",
            "direction": "higher is better",
            "definition": "Battery, cleaning station, charging, maintenance, and bundle convenience.",
        },
        {
            "id": "three_year_cost_eur",
            "label": "Three-year cost penalty",
            "coefficient": -COST_PENALTY_WEIGHT,
            "unit": "EUR",
            "direction": "lower is better",
            "definition": "Device price plus replaceable-part allowance; subtracts points per EUR.",
        },
    ]


def _scores_by_candidate_id(scoring_result):
    return {
        row.candidate_id: {
            "weighted_score": row.score,
            "score_per_eur": row.score_per_eur,
        }
        for row in scoring_result.weighted_ranking
    }


def _candidate_data(candidates, report_context, scores_by_id):
    raw_by_id = {
        item.get("id"): item
        for item in report_context.get("candidate_details", [])
        if item.get("id")
    }
    price_limit = report_context.get("price_limit_eur")
    price_basis = report_context.get("price_limit_basis", "device_price_eur")
    rows = []
    for candidate in candidates:
        raw = raw_by_id.get(candidate.id, {})
        metrics = dict(candidate.metrics)
        scores = scores_by_id[candidate.id]
        price_value = raw.get(price_basis)
        if price_basis == "three_year_cost_eur":
            price_value = candidate.three_year_cost_eur
        within_price_limit = (
            None
            if price_limit is None or price_value is None
            else price_value <= price_limit
        )
        rows.append(
            {
                "candidate_id": candidate.id,
                "candidate_name": candidate.name,
                "brand": raw.get("brand", ""),
                "type": raw.get("type", ""),
                "device_price_eur": raw.get("device_price_eur"),
                "replacement_head_eur": raw.get("replacement_head_eur"),
                "replacement_unit_price_eur": raw.get("replacement_unit_price_eur"),
                "replacement_quantity_3y": raw.get("replacement_quantity_3y"),
                "replacement_interval_months": raw.get("replacement_interval_months"),
                "replacement_part_name": raw.get("replacement_part_name", "replacement part"),
                "three_year_cost_eur": candidate.three_year_cost_eur,
                "ownership_summary": _ownership_summary(raw, candidate),
                "ownership_note": raw.get("ownership_note", ""),
                "runtime_min": raw.get("runtime_min"),
                "charging_min": raw.get("charging_min"),
                "cleaning_station": raw.get("cleaning_station"),
                "wet_dry": raw.get("wet_dry"),
                "effectiveness": metrics.get("effectiveness"),
                "skin_safety": metrics.get("skin_safety"),
                "convenience": metrics.get("convenience"),
                "weighted_score": scores["weighted_score"],
                "score_per_eur": scores["score_per_eur"],
                "source_refs": raw.get("source_refs", []),
                "price_limit_value_eur": price_value,
                "within_price_limit": within_price_limit,
            }
        )
    return rows


def _budget_payload(report_context, candidate_data):
    max_price = report_context.get("price_limit_eur")
    price_basis = report_context.get("price_limit_basis", "device_price_eur")
    if max_price is None:
        return {
            "enabled": False,
            "max_price_eur": None,
            "basis": price_basis,
            "basis_label": _price_basis_label(price_basis),
            "eligible_candidate_count": len(candidate_data),
            "excluded_candidate_count": 0,
        }
    eligible = [row for row in candidate_data if row.get("within_price_limit") is True]
    excluded = [row for row in candidate_data if row.get("within_price_limit") is False]
    return {
        "enabled": True,
        "max_price_eur": max_price,
        "basis": price_basis,
        "basis_label": _price_basis_label(price_basis),
        "eligible_candidate_count": len(eligible),
        "excluded_candidate_count": len(excluded),
    }


def _price_basis_label(price_basis):
    labels = {
        "device_price_eur": "device price",
        "three_year_cost_eur": "three-year cost",
    }
    return labels.get(price_basis, price_basis.replace("_", " "))


def _decision_candidate_ids(candidate_data, budget):
    if not budget.get("enabled"):
        return None
    return {
        row["candidate_id"]
        for row in candidate_data
        if row.get("within_price_limit") is True
    }


def _decision_sensitivity_rankings(rankings, decision_candidate_ids):
    if decision_candidate_ids is None:
        return rankings
    return {
        profile: [
            candidate_id
            for candidate_id in ordered_ids
            if candidate_id in decision_candidate_ids
        ]
        for profile, ordered_ids in rankings.items()
    }


def _decision_pareto_frontier(candidates, decision_candidate_ids):
    if decision_candidate_ids is None:
        return [candidate.id for candidate in candidates if not _candidate_is_dominated(candidate, candidates)]
    decision_candidates = [
        candidate
        for candidate in candidates
        if candidate.id in decision_candidate_ids
    ]
    return [
        candidate.id
        for candidate in decision_candidates
        if not _candidate_is_dominated(candidate, decision_candidates)
    ]


def _candidate_is_dominated(candidate, candidates):
    return any(
        other.id != candidate.id
        and other.three_year_cost_eur <= candidate.three_year_cost_eur
        and all(other.metrics[name] >= value for name, value in candidate.metrics.items())
        and (
            other.three_year_cost_eur < candidate.three_year_cost_eur
            or any(other.metrics[name] > value for name, value in candidate.metrics.items())
        )
        for other in candidates
    )


def _ownership_summary(raw, candidate):
    parts = []
    if candidate.three_year_cost_eur is not None:
        parts.append(f"3-year cost ~{_format_rounded_currency(candidate.three_year_cost_eur)}")

    part_name = raw.get("replacement_part_name") or "replacement part"
    unit_price = raw.get("replacement_unit_price_eur")
    if unit_price is None:
        unit_price = raw.get("replacement_head_eur")
    interval = _replacement_interval_label(raw.get("replacement_interval_months"))
    if unit_price is not None and interval:
        parts.append(f"{part_name} ~{_format_rounded_currency(unit_price)} {interval}")
    elif unit_price is not None:
        parts.append(f"{part_name} allowance ~{_format_rounded_currency(unit_price)}")

    quantity = raw.get("replacement_quantity_3y")
    if _is_number(quantity):
        replacements = "replacement" if round(quantity) == 1 else "replacements"
        parts.append(f"{_format_number(quantity, 0)} {replacements} in 3 years")

    return "; ".join(parts)


def _replacement_interval_label(interval_months):
    if not _is_number(interval_months):
        return ""
    if interval_months == 12:
        return "every ~12 mo"
    if interval_months % 12 == 0:
        years = int(interval_months / 12)
        suffix = "year" if years == 1 else "years"
        return f"every ~{years} {suffix}"
    return f"every ~{_format_number(interval_months, 0)} mo"


def _source_data(evidence_summary, report_context):
    details_by_url = {
        item.get("url"): item
        for item in report_context.get("source_details", [])
        if item.get("url")
    }
    details_by_title = {
        item.get("title"): item
        for item in report_context.get("source_details", [])
        if item.get("title")
    }
    rows = []
    for source in evidence_summary.get("sources", []):
        detail = details_by_url.get(source.get("url")) or details_by_title.get(source.get("title")) or {}
        candidate_ids = source.get("candidate_ids") or detail.get("candidate_ids") or []
        metrics = source.get("metrics") or detail.get("metrics") or []
        rows.append(
            {
                "id": detail.get("id", ""),
                "title": source.get("title", detail.get("title", "")),
                "url": source.get("url", detail.get("url", "")),
                "domain": source.get("domain", detail.get("domain", "")),
                "role": source.get("role", detail.get("role", "")),
                "candidate_ids": candidate_ids,
                "candidate_count": len(candidate_ids),
                "metrics": metrics,
                "metric_count": len(metrics),
                "notes": detail.get("notes", ""),
            }
        )
    return rows


def _domain_summary(source_data, domain_registry):
    registry_by_domain = {entry.get("domain"): entry for entry in domain_registry}
    counts = Counter(row["domain"] or "unknown" for row in source_data)
    role_counts = defaultdict(set)
    metric_counts = Counter()
    candidate_counts = Counter()
    for row in source_data:
        domain = row["domain"] or "unknown"
        if row.get("role"):
            role_counts[domain].add(row["role"])
        metric_counts[domain] += row.get("metric_count", 0)
        candidate_counts[domain] += row.get("candidate_count", 0)

    rows = []
    for domain, count in sorted(counts.items(), key=lambda item: (-item[1], item[0])):
        registry = registry_by_domain.get(domain, {})
        rows.append(
            {
                "domain": domain,
                "source_count": count,
                "candidate_refs": candidate_counts[domain],
                "metric_refs": metric_counts[domain],
                "roles": sorted(role_counts[domain]),
                "trust_tier": registry.get("trust_tier", "unregistered"),
                "human_status": registry.get("human_status", "unregistered"),
                "api_preferred": registry.get("api_preferred"),
                "source_types": registry.get("source_types", []),
            }
        )
    return rows


def _image_search_rows(image_search):
    rows = []
    for search in image_search.get("searches", []):
        selected = search.get("selected") or {}
        rows.append(
            {
                "candidate_id": search.get("candidate_id", ""),
                "candidate_name": search.get("candidate_name", ""),
                "query": search.get("query", ""),
                "result_count": search.get("result_count", 0),
                "selected_title": selected.get("title", ""),
                "selected_url": selected.get("link", ""),
                "context_url": selected.get("context_link", ""),
                "host": selected.get("host", ""),
                "width": selected.get("width"),
                "height": selected.get("height"),
                "score": selected.get("score"),
            }
        )
    return rows


def _attach_image_rows(candidate_data, image_rows):
    images_by_id = {
        row.get("candidate_id"): row
        for row in image_rows
        if row.get("candidate_id")
    }
    enriched = []
    for row in candidate_data:
        image = images_by_id.get(row["candidate_id"], {})
        item = dict(row)
        item.update(
            {
                "image_url": image.get("selected_url", ""),
                "image_context_url": image.get("context_url", ""),
                "image_host": image.get("host", ""),
                "image_title": image.get("selected_title", ""),
                "image_width": image.get("width"),
                "image_height": image.get("height"),
                "image_score": image.get("score"),
            }
        )
        enriched.append(item)
    return enriched


def _attach_source_links(candidate_data, source_data):
    sources_by_id = {
        row.get("id"): row
        for row in source_data
        if row.get("id")
    }
    enriched = []
    for row in candidate_data:
        item = dict(row)
        item["item_links"] = _candidate_item_links(row.get("source_refs", []), sources_by_id)
        enriched.append(item)
    return enriched


def _candidate_item_links(source_refs, sources_by_id):
    candidates = []
    for source_id in source_refs:
        source = sources_by_id.get(source_id)
        if not source or not source.get("url"):
            continue
        candidates.append(
            {
                "label": _source_link_label(source.get("role", "")),
                "url": source["url"],
                "title": source.get("title", ""),
                "role": source.get("role", ""),
                "priority": _source_link_priority(source.get("role", "")),
            }
        )

    links = []
    seen_urls = set()
    seen_labels = Counter()
    for link in sorted(candidates, key=lambda item: item["priority"]):
        if link["url"] in seen_urls:
            continue
        seen_urls.add(link["url"])
        seen_labels[link["label"]] += 1
        if seen_labels[link["label"]] > 1:
            link = dict(link)
            link["label"] = f"{link['label']} {seen_labels[link['label']]}"
        links.append({key: value for key, value in link.items() if key != "priority"})
        if len(links) == 3:
            break
    return links


def _source_link_label(role):
    labels = {
        "price": "Price",
        "price_specs": "Price",
        "official_specs": "Official",
        "performance_proxy": "Review",
        "replacement_price": "Head price",
        "replacement_interval": "Head interval",
        "replacement_part_reference": "Parts",
    }
    return labels.get(role, "Info")


def _source_link_priority(role):
    priorities = {
        "price": 0,
        "price_specs": 0,
        "official_specs": 1,
        "performance_proxy": 2,
        "replacement_price": 3,
        "replacement_interval": 4,
        "replacement_part_reference": 4,
    }
    return priorities.get(role, 5)


def _render_markdown(payload):
    lines = [
        f"# {payload['title']}",
        f"Question: {payload['task']['question']}",
        f"Market: {payload['task']['market']}",
        f"Currency: {payload['task']['currency']}",
        f"Candidate count: {payload['candidate_count']}",
        _budget_markdown_line(payload),
        f"Winner: {payload['winner']['candidate_name']} ({payload['winner']['candidate_id']})",
        "",
        "## Criteria",
        "| Criterion | Coefficient | Unit | Direction | Definition |",
        "|---|---:|---|---|---|",
    ]
    lines = [line for line in lines if line]

    for criterion in payload["criteria"]:
        lines.append(
            "| {label} | {coefficient:.5f} | {unit} | {direction} | {definition} |".format(
                **criterion
            )
        )

    lines.extend(["", "## Raw numeric shortlist data"])
    lines.extend(_markdown_table(_candidate_numeric_columns(), payload["candidate_data"]))
    lines.append(
        "Product image provenance: "
        f"provider={payload['image_search'].get('provider', 'google_custom_search')}; "
        f"mode={payload['image_search'].get('mode', '')}"
    )
    lines.extend(
        _markdown_table(
            _image_columns(),
            payload["image_search_rows"],
        )
    )

    for ranking_name, rows in payload["rankings"].items():
        lines.extend(["", f"## {ranking_name}"])
        for row in rows:
            lines.append(f"{row['rank']}. {row['candidate_name']} ({row['candidate_id']})")
        lines.extend(
            _markdown_table(
                [
                    ("rank", "Rank"),
                    ("candidate_name", "Candidate"),
                    ("score", "Score"),
                    ("score_per_eur", "Score/EUR"),
                ],
                rows,
            )
        )

    lines.append(f"Pareto frontier: {', '.join(payload['pareto_frontier'])}")

    for profile_name, ordered_ids in payload["sensitivity_rankings"].items():
        lines.append(f"{profile_name}: {', '.join(ordered_ids)}")

    lines.extend(["", "## Evidence sources"])
    lines.append(f"Evidence sources: {payload['evidence_summary']['source_count']}")
    lines.append(payload["evidence_summary"]["summary"])
    lines.extend(
        _markdown_table(
            [
                ("domain", "Domain"),
                ("role", "Role"),
                ("candidate_count", "Candidates"),
                ("metric_count", "Metrics"),
                ("title", "Title"),
            ],
            payload["source_data"],
        )
    )
    for matchup in payload["evidence_summary"].get("tournament", []):
        lines.append(
            f"{matchup['round']}: {matchup['a']} vs {matchup['b']} -> "
            f"{matchup['winner']} ({matchup['reason']})"
        )
    for caveat in payload["evidence_summary"].get("caveats", []):
        lines.append(f"Caveat: {caveat}")
    for source in payload["evidence_summary"]["sources"]:
        lines.append(source["title"])
        lines.append(source["url"])

    return "\n".join(lines)


def _render_html(payload):
    names_by_id = {
        candidate["candidate_id"]: candidate["candidate_name"]
        for candidate in payload["candidates"]
    }
    weighted = payload["rankings"]["weighted"]
    value = payload["rankings"]["cost_benefit"]
    winner = payload["winner"]
    value_winner = value[0]
    source_count = payload["evidence_summary"]["source_count"]
    runtime_values = _numbers(payload["candidate_data"], "runtime_min")
    third_card_value = _format_number(max(runtime_values), 0) if runtime_values else str(payload["candidate_count"])
    third_card_detail = "minutes among shortlisted devices" if runtime_values else "candidates with complete score data"
    budget_note = _budget_html_note(payload)
    decision_pool_note = _decision_pool_note(payload)

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(payload['title'])}</title>
  <link href="https://fonts.googleapis.com/css2?family=EB+Garamond:ital,wght@0,400;0,500;0,600;0,700;1,400;1,500&display=swap" rel="stylesheet">
  <style>{_report_css()}</style>
</head>
<body>
  <main class="page" id="top">
    <header class="report-header">
      <div class="source-tags">{_source_tags(payload)}</div>
      <h1>{escape(payload['title'])}</h1>
      <p class="subtitle">{escape(payload['task']['question'])}</p>
      <p class="meta-line">Market: <span class="mono">{escape(payload['task']['market'])}</span> / currency: <span class="mono">{escape(payload['task']['currency'])}</span>{_budget_meta_fragment(payload)} / generated: <span class="mono">{escape(payload['task'].get('generated_at') or payload['task'].get('created_at') or 'not recorded')}</span></p>
      <p class="view-switch"><a href="quick_report.html">open quick consumer version</a></p>
    </header>

    <section class="status-strip" id="status">
      <div class="status-cell status-green">
        <div class="status-label">Balanced winner</div>
        <div class="status-value">{escape(winner['candidate_name'])}</div>
        <div class="status-note">score <span class="mono">{_format_number(winner['score'])}</span></div>
      </div>
      <div class="status-cell status-amber">
        <div class="status-label">Value winner</div>
        <div class="status-value">{escape(value_winner['candidate_name'])}</div>
        <div class="status-note"><span class="mono">{_format_number(value_winner['score_per_eur'], 3)}</span> score/EUR</div>
      </div>
      <div class="status-cell status-blue">
        <div class="status-label">Decision pool</div>
        <div class="status-value mono">{payload['decision_candidate_count']} / {payload['candidate_count']}</div>
        <div class="status-note">{escape(decision_pool_note)}</div>
      </div>
      <div class="status-cell status-blue">
        <div class="status-label">Evidence base</div>
        <div class="status-value mono">{source_count}</div>
        <div class="status-note">classified sources</div>
      </div>
    </section>

    {_decision_product_strip(payload, winner, value_winner)}

    <div class="toc-layout">
      <section class="overview">
        <p class="lede">This report answers one task: choose the best option from a defined shortlist using transparent, numeric criteria.</p>
        <p>Candidate count: {payload['candidate_count']}. Decision pool: {payload['decision_candidate_count']}. Winner: {escape(winner['candidate_name'])}. Evidence sources: {source_count}. The score combines three 0-100 quality proxies and one EUR cost penalty.</p>
        <p>{budget_note} The balanced winner costs about <span class="mono">{_format_rounded_currency(_candidate_by_id(payload, winner['candidate_id'])['three_year_cost_eur'])}</span> over three years, while the value winner costs about <span class="mono">{_format_rounded_currency(_candidate_by_id(payload, value_winner['candidate_id'])['three_year_cost_eur'])}</span>.</p>
      </section>
      <nav class="toc" id="toc">
        <div class="toc-title">contents</div>
        <a href="#task">Task and criteria</a>
        <a href="#raw-data">Raw shortlist data</a>
        <a href="#balanced">Balanced ranking</a>
        <a href="#value">Value and frontier</a>
        <a href="#sensitivity">Sensitivity and tournament</a>
        <a href="#evidence">Evidence and domains</a>
      </nav>
    </div>

    <div class="summary-row">
      {_summary_card('Weighted score', _format_number(winner['score']), f"{winner['candidate_name']} leads the balanced model", 'primary')}
      {_summary_card('Value score', _format_number(value_winner['score_per_eur'], 3), f"{value_winner['candidate_name']} leads score per EUR", 'secondary')}
      {_summary_card('Data depth', third_card_value, third_card_detail, 'tertiary')}
    </div>

    <div class="ornament">:::</div>
    {_task_section(payload)}
    <div class="ornament">:::</div>
    {_raw_data_section(payload)}
    <div class="ornament">:::</div>
    {_balanced_section(payload)}
    <div class="ornament">:::</div>
    {_value_section(payload, names_by_id)}
    <div class="ornament">:::</div>
    {_sensitivity_section(payload, names_by_id)}
    <div class="ornament">:::</div>
    {_evidence_section(payload)}

    <footer>
      <p>Generated from the structured dataset, domain registry, and deterministic scoring engine. Prices should be refreshed before purchase.</p>
    </footer>

    {_machine_audit(payload)}
  </main>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js"></script>
  <script type="application/json" id="report-data">{_json_for_script(payload)}</script>
  <script>{_report_js(payload)}</script>
</body>
</html>"""


def _render_quick_html(payload):
    weighted = payload["rankings"]["weighted"]
    value = payload["rankings"]["cost_benefit"]
    winner = _candidate_by_id(payload, weighted[0]["candidate_id"])
    value_winner = _candidate_by_id(payload, value[0]["candidate_id"])
    skin_ids = payload.get("sensitivity_rankings", {}).get("skin", [])
    skin_winner = _candidate_by_id(payload, skin_ids[0]) if skin_ids else winner
    ordered_candidates = [
        _candidate_by_id(payload, row["candidate_id"])
        for row in weighted
    ]
    quick_scope = _quick_scope_sentence(payload)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(payload['title'])} - quick version</title>
  <style>{_quick_report_css()}</style>
</head>
<body>
  <main class="quick-page">
    <header class="quick-header">
      <h1>{escape(payload['title'])}</h1>
      <p>{escape(payload['task']['question'])} {escape(quick_scope)} Prices are rounded to the nearest EUR.</p>
      <nav class="quick-links">
        <a href="report.html">full audit report</a>
      </nav>
    </header>

    <section class="quick-decision" aria-label="Recommended choices">
      {_quick_pick_card('Best overall', winner, 'Choose this if shaving quality matters more than lowest price.')}
      {_quick_pick_card('Best value', value_winner, 'Choose this if price matters first.')}
      {_quick_pick_card('Fit pick', skin_winner, 'Choose this if fit, safety, or comfort risk matters most.')}
    </section>

    <section class="quick-shortlist" aria-label="All options">
      <div class="quick-section-heading">
        <div class="quick-heading-title-row">
          <h2>Options</h2>
          <div class="quick-view-toggle" aria-label="Options view">
            <button type="button" class="active" data-view="cards" aria-pressed="true">Cards</button>
            <button type="button" data-view="table" aria-pressed="false">Table</button>
          </div>
        </div>
        <p>{escape(_quick_options_note(payload))}</p>
      </div>
      <div class="quick-grid" data-view-panel="cards">
        {''.join(_quick_option_card(row) for row in ordered_candidates)}
      </div>
      <div class="quick-table-wrap hidden" data-view-panel="table" hidden>
        {_quick_comparison_table(ordered_candidates)}
      </div>
    </section>
  </main>
  <script>{_quick_report_js()}</script>
</body>
</html>"""


def _quick_pick_card(label, row, reason):
    return f"""
      <article class="quick-pick">
        {_quick_image(row)}
        <h2>{escape(row['candidate_name'])}</h2>
        <div class="quick-price">{escape(_quick_display_price(row))}</div>
        <p><strong>{escape(label)}.</strong> {escape(reason)}</p>
        {_quick_specs(row)}
        {_quick_ownership(row)}
        {_quick_links(row)}
        {_quick_details(row)}
      </article>
    """


def _quick_option_card(row):
    return f"""
      <article class="quick-option">
          {_quick_image(row)}
        <div class="quick-option-body">
          <h3>{escape(row['candidate_name'])}</h3>
          <div class="quick-price">{escape(_quick_display_price(row))}</div>
          {_quick_specs(row)}
          {_quick_ownership(row)}
          {_quick_links(row)}
          {_quick_details(row)}
        </div>
      </article>
    """


def _quick_image(row):
    if row.get("image_url"):
        return f"""
        <div class="quick-image">
          <img src="{escape(row['image_url'])}" alt="{escape(row['candidate_name'])}" loading="lazy" referrerpolicy="no-referrer">
        </div>
        """
    return f'<div class="quick-image quick-image-empty">{escape(row["candidate_name"])}</div>'


def _quick_comparison_table(rows):
    table_rows = "".join(
        f"""
        <tr>
          <th>{escape(row['candidate_name'])}</th>
          <td>{escape(_quick_display_price(row))}</td>
          <td>{escape(row.get('ownership_summary', ''))}</td>
          <td>{escape(_short_type(row.get('type')))}</td>
          <td>{escape(_wet_dry_label(row.get('wet_dry')))}</td>
          <td>{escape(_station_label(row.get('cleaning_station')))}</td>
          <td>{escape(_runtime_label(row.get('runtime_min')))}</td>
          <td>{_quick_table_links(row)}</td>
        </tr>
        """
        for row in rows
    )
    return f"""
      <table class="quick-comparison-table">
        <thead>
          <tr>
            <th>Option</th>
            <th>Price</th>
            <th>Ownership</th>
            <th>Type</th>
            <th>Use</th>
            <th>Cleaning</th>
            <th>Battery</th>
            <th>Links</th>
          </tr>
        </thead>
        <tbody>{table_rows}</tbody>
      </table>
    """


def _quick_scope_sentence(payload):
    budget = payload.get("budget", {})
    if not budget.get("enabled"):
        return f"quick consumer view for {payload['task']['market']}."
    return (
        f"quick consumer view for {payload['task']['market']}, filtered to "
        f"{payload['decision_candidate_count']} options with "
        f"{budget.get('basis_label', 'price')} at or below "
        f"{_format_rounded_currency(budget.get('max_price_eur'))}."
    )


def _quick_options_note(payload):
    budget = payload.get("budget", {})
    if not budget.get("enabled"):
        return f"Showing {payload['decision_candidate_count']} options."
    return (
        f"Showing {payload['decision_candidate_count']} of {payload['candidate_count']} options under "
        f"{_format_rounded_currency(budget.get('max_price_eur'))} {budget.get('basis_label', 'price')}."
    )


def _quick_links(row):
    links = _item_link_anchors(row, "quick-link")
    if not links:
        return ""
    return f'<div class="quick-item-links">{links}</div>'


def _quick_ownership(row):
    summary = row.get("ownership_summary")
    if not summary:
        return ""
    return f'<div class="quick-ownership">{escape(summary)}</div>'


def _quick_table_links(row):
    links = _item_link_anchors(row, "quick-table-link")
    if not links:
        return ""
    return f'<div class="quick-table-links">{links}</div>'


def _item_link_anchors(row, class_name):
    anchors = []
    for link in row.get("item_links", [])[:3]:
        url = link.get("url")
        if not url:
            continue
        label = link.get("label") or "Info"
        title = link.get("title") or label
        anchors.append(
            f'<a class="{escape(class_name)}" href="{escape(url, quote=True)}" '
            f'target="_blank" rel="noreferrer" title="{escape(title, quote=True)}">'
            f'{escape(label)}</a>'
        )
    return "".join(anchors)


def _quick_specs(row):
    specs = [
        _short_type(row.get("type")),
        _wet_dry_label(row.get("wet_dry")),
        _station_label(row.get("cleaning_station")),
        _runtime_label(row.get("runtime_min")),
    ]
    specs = [spec for spec in specs if spec]
    return f'<div class="quick-specs">{"".join(f"<span>{escape(spec)}</span>" for spec in specs)}</div>'


def _quick_details(row):
    details = [
        ("device price", _format_rounded_currency(row.get("device_price_eur")) if row.get("device_price_eur") is not None else ""),
        ("three-year cost", _format_rounded_currency(row.get("three_year_cost_eur")) if row.get("three_year_cost_eur") is not None else ""),
        ("replacement allowance", _format_rounded_currency(row.get("replacement_head_eur")) if row.get("replacement_head_eur") is not None else ""),
        ("part unit price", _format_rounded_currency(row.get("replacement_unit_price_eur")) if row.get("replacement_unit_price_eur") is not None else ""),
        ("part interval", _replacement_interval_label(row.get("replacement_interval_months"))),
        ("parts in 3 years", _format_cell(row.get("replacement_quantity_3y"), "replacement_quantity_3y")),
        ("balanced score", _format_cell(row.get("weighted_score"), "weighted_score")),
        ("score per EUR", _format_cell(row.get("score_per_eur"), "score_per_eur")),
        ("effectiveness", _format_cell(row.get("effectiveness"), "effectiveness")),
        ("fit / safety", _format_cell(row.get("skin_safety"), "skin_safety")),
        ("convenience", _format_cell(row.get("convenience"), "convenience")),
        ("ownership note", row.get("ownership_note", "")),
    ]
    rows = "".join(
        f"<tr><th>{escape(label)}</th><td>{escape(value)}</td></tr>"
        for label, value in details
        if value
    )
    return f"""
      <details class="quick-details">
        <summary>numbers and evidence</summary>
        <table>{rows}</table>
      </details>
    """


def _quick_display_price(row):
    if row.get("device_price_eur") is not None:
        return _format_rounded_currency(row.get("device_price_eur"))
    return _format_rounded_currency(row.get("three_year_cost_eur"))


def _short_type(value):
    return str(value).strip().lower() if value else ""


def _wet_dry_label(value):
    if value is True:
        return "wet/dry"
    if value is False:
        return "dry only"
    return ""


def _station_label(value):
    if value is True:
        return "cleaning station"
    if value is False:
        return "no station"
    return ""


def _runtime_label(value):
    if _is_number(value):
        return f"{_format_number(value, 0)} min runtime"
    return ""


def _quick_report_css():
    return """
    :root {
      --ink: #171717;
      --muted: #666;
      --line: #ddd;
      --bg: #f7f5ef;
      --card: oklch(99% 0.006 95);
      --image: oklch(99.4% 0.004 95);
      --on-accent: oklch(99% 0.006 145);
      --accent: #2a7a5a;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      line-height: 1.45;
    }
    .quick-page {
      max-width: 1120px;
      margin: 0 auto;
      padding: 28px 18px 56px;
    }
    .quick-header {
      margin-bottom: 22px;
    }
    h1 {
      font-size: clamp(30px, 5vw, 54px);
      letter-spacing: 0;
      line-height: 1;
      margin: 8px 0;
    }
    h2, h3 {
      letter-spacing: 0;
      line-height: 1.15;
      margin: 0;
    }
    .quick-header p {
      color: var(--muted);
      font-size: 18px;
      margin: 0 0 12px;
      max-width: 680px;
    }
    .quick-links a,
    .quick-details summary {
      align-items: center;
      color: var(--accent);
      cursor: pointer;
      display: inline-flex;
      font-weight: 700;
      min-height: 44px;
      text-decoration: underline;
      text-underline-offset: 3px;
    }
    .quick-decision {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 14px;
      margin: 20px 0 30px;
    }
    .quick-pick,
    .quick-option {
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 8px;
    }
    .quick-pick {
      padding: 14px;
    }
    .quick-pick h2 {
      font-size: clamp(20px, 2.1vw, 28px);
      margin-top: 12px;
      overflow-wrap: anywhere;
    }
    .quick-pick p {
      color: var(--muted);
      margin: 10px 0;
    }
    .quick-pick p strong {
      color: var(--ink);
      font-weight: 800;
    }
    .quick-price {
      font-size: 21px;
      font-weight: 800;
      margin-top: 6px;
    }
    .quick-image {
      align-items: center;
      aspect-ratio: 4 / 3;
      background: var(--image);
      display: flex;
      justify-content: center;
      overflow: hidden;
      width: 100%;
    }
    .quick-pick .quick-image {
      aspect-ratio: 16 / 10;
      max-height: 280px;
    }
    .quick-image img {
      display: block;
      height: 100%;
      object-fit: contain;
      width: 100%;
    }
    .quick-image-empty {
      color: var(--muted);
      padding: 16px;
      text-align: center;
    }
    .quick-section-heading {
      align-items: stretch;
      display: flex;
      flex-direction: column;
      gap: 14px;
      margin-bottom: 14px;
    }
    .quick-heading-title-row {
      align-items: center;
      display: flex;
      gap: 12px;
      justify-content: space-between;
    }
    .quick-section-heading p {
      color: var(--muted);
      font-size: 14px;
      margin: 0;
    }
    .quick-shortlist h2 {
      font-size: 26px;
      margin: 0;
    }
    .quick-view-toggle {
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 999px;
      display: inline-flex;
      padding: 3px;
    }
    .quick-view-toggle button {
      background: transparent;
      border: 0;
      border-radius: 999px;
      color: var(--muted);
      cursor: pointer;
      font: inherit;
      font-size: 14px;
      font-weight: 700;
      min-height: 44px;
      padding: 7px 13px;
    }
    .quick-view-toggle button.active {
      background: var(--accent);
      color: var(--on-accent);
    }
    .quick-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
    }
    .quick-option {
      display: grid;
      grid-template-columns: 180px 1fr;
      gap: 14px;
      padding: 12px;
    }
    .quick-option h3 {
      font-size: 21px;
      overflow-wrap: anywhere;
    }
    .quick-table-wrap {
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 8px;
      overflow-x: auto;
    }
    [data-view-panel].hidden,
    [data-view-panel][hidden] {
      display: none;
    }
    .quick-comparison-table {
      border-collapse: collapse;
      min-width: 1040px;
      width: 100%;
    }
    .quick-comparison-table th,
    .quick-comparison-table td {
      border-bottom: 1px solid var(--line);
      padding: 12px 14px;
      text-align: left;
      vertical-align: top;
    }
    .quick-comparison-table thead th {
      color: var(--muted);
      font-size: 14px;
      font-weight: 700;
    }
    .quick-comparison-table tbody th {
      font-size: 16px;
      width: 30%;
    }
    .quick-specs {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin: 12px 0;
    }
    .quick-specs span {
      background: #f1f1f1;
      border-radius: 999px;
      color: #333;
      font-size: 13px;
      padding: 5px 9px;
    }
    .quick-ownership {
      background: #f7faf8;
      border: 1px solid #d7e4dc;
      border-radius: 6px;
      color: #315946;
      font-size: 13px;
      font-weight: 650;
      line-height: 1.35;
      margin: 10px 0;
      padding: 8px 10px;
    }
    .quick-item-links,
    .quick-table-links {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin: 10px 0;
    }
    .quick-link,
    .quick-table-link {
      border: 1px solid #cfd8d3;
      border-radius: 999px;
      color: var(--accent);
      align-items: center;
      display: inline-flex;
      font-size: 13px;
      font-weight: 750;
      line-height: 1;
      min-height: 44px;
      padding: 7px 9px;
      text-decoration: none;
      white-space: nowrap;
    }
    .quick-link:hover,
    .quick-table-link:hover {
      border-color: var(--accent);
      text-decoration: underline;
      text-underline-offset: 3px;
    }
    .quick-table-links {
      margin: 0;
    }
    .quick-details {
      margin-top: 8px;
    }
    .quick-details table {
      border-collapse: collapse;
      font-size: 14px;
      margin-top: 8px;
      width: 100%;
    }
    .quick-details th,
    .quick-details td {
      border-top: 1px solid var(--line);
      padding: 6px 0;
      text-align: left;
      vertical-align: top;
    }
    .quick-details th {
      color: var(--muted);
      font-weight: 600;
      width: 45%;
    }
    @media (max-width: 860px) {
      .quick-decision,
      .quick-grid {
        grid-template-columns: 1fr;
      }
      .quick-option {
        grid-template-columns: 130px 1fr;
      }
    }
    @media (max-width: 560px) {
      .quick-heading-title-row {
        align-items: flex-start;
        flex-direction: column;
      }
      .quick-option {
        grid-template-columns: 1fr;
      }
    }
    """


def _quick_report_js():
    return """
    document.querySelectorAll('[data-view]').forEach((button) => {
      button.addEventListener('click', () => {
        const view = button.dataset.view;
        document.querySelectorAll('[data-view]').forEach((item) => {
          item.classList.toggle('active', item.dataset.view === view);
          item.setAttribute('aria-pressed', item.dataset.view === view ? 'true' : 'false');
        });
        document.querySelectorAll('[data-view-panel]').forEach((panel) => {
          const shouldHide = panel.dataset.viewPanel !== view;
          panel.classList.toggle('hidden', shouldHide);
          panel.hidden = shouldHide;
        });
      });
    });
    """


def _decision_product_strip(payload, winner, value_winner):
    skin_ids = payload.get("sensitivity_rankings", {}).get("skin", [])
    featured = [
        ("Balanced pick", winner["candidate_id"], "weighted_score", "score"),
        ("Value pick", value_winner["candidate_id"], "score_per_eur", "score/EUR"),
    ]
    if skin_ids:
        featured.append(("Skin pick", skin_ids[0], "skin_safety", "skin"))

    seen = set()
    cards = []
    for label, candidate_id, metric_key, metric_label in featured:
        if candidate_id in seen:
            continue
        seen.add(candidate_id)
        cards.append(
            _product_spotlight_card(
                _candidate_by_id(payload, candidate_id),
                label,
                metric_key,
                metric_label,
            )
        )

    return f"""
    <div class="product-showcase">
      {''.join(cards)}
    </div>
    """


def _product_spotlight_card(row, label, metric_key, metric_label):
    metric_value = _format_cell(row.get(metric_key), metric_key)
    cost = _format_rounded_currency(row["three_year_cost_eur"])
    return f"""
      <figure class="product-spotlight">
        {_product_image_frame(row)}
        <figcaption>
          <strong>{escape(label)}: {escape(row['candidate_name'])}</strong>
          <span class="mono">{escape(metric_label)} {escape(metric_value)} / {escape(cost)}</span>
          {_product_link_row(row)}
        </figcaption>
      </figure>
    """


def _product_image_frame(row):
    if row.get("image_url"):
        return f"""
        <div class="product-image-frame">
          <img src="{escape(row['image_url'])}" alt="{escape(row['candidate_name'])}" loading="lazy" referrerpolicy="no-referrer">
        </div>
        """
    return f"""
        <div class="product-image-frame product-image-placeholder">
          <span>{escape(row['candidate_name'])}</span>
        </div>
    """


def _task_section(payload):
    return f"""
    <section id="task">
      <h2>task and criteria <a href="#toc" class="back-to-top" title="Back to contents">+</a></h2>
      <p class="state-line">The model uses <strong>4</strong> coefficients: three quality proxies and one EUR cost penalty.</p>
      <div class="aside-container">
        <div>
          <div class="table-wrapper">
            {_html_table(_criteria_columns(), payload['criteria'])}
          </div>
          <div class="caption">Score formula: effectiveness*0.44880 + fit/safety*0.23600 + convenience*0.35680 - three-year cost EUR*0.00584.</div>
        </div>
        <aside class="aside">
          <div class="aside-title">method</div>
          <p><strong>Task:</strong> rank the researched shortlist, not discover every possible option.</p>
          <p><strong>Criteria:</strong> all quality inputs use a 0-100 proxy scale, while price enters as a direct EUR penalty.</p>
          <p><strong>Limit:</strong> the coefficients are deterministic default coefficients, not lab-calibrated consumer research weights.</p>
        </aside>
      </div>
    </section>
    """


def _raw_data_section(payload):
    top_quality = ", ".join(
        row["candidate_name"]
        for row in sorted(payload["candidate_data"], key=lambda item: item["weighted_score"], reverse=True)[:3]
    )
    cheapest = min(payload["candidate_data"], key=lambda item: item["three_year_cost_eur"])
    runtime_values = _numbers(payload["candidate_data"], "runtime_min")
    budget = payload.get("budget", {})
    budget_shape = ""
    if budget.get("enabled"):
        excluded_names = ", ".join(
            row["candidate_name"]
            for row in payload["candidate_data"]
            if row.get("within_price_limit") is False
        )
        budget_shape = (
            f"<p><strong>Budget:</strong> decision tables use {payload['decision_candidate_count']} candidates under "
            f"{escape(_format_rounded_currency(budget.get('max_price_eur')))} {escape(budget.get('basis_label', 'price'))}; "
            f"excluded from the decision: {escape(excluded_names)}.</p>"
        )
    runtime_sentence = (
        f"{sum(1 for row in payload['candidate_data'] if row.get('runtime_min') == max(runtime_values))} devices list {_format_number(max(runtime_values), 0)} min runtime."
        if runtime_values
        else "Runtime was not included in the minimal test dataset."
    )
    return f"""
    <section id="raw-data">
      <h2>raw shortlist data <a href="#toc" class="back-to-top" title="Back to contents">+</a></h2>
      <p class="state-line">All <strong>{payload['candidate_count']}</strong> candidates expose price, runtime, charging, and three 0-100 proxy metrics; <strong>{payload['decision_candidate_count']}</strong> are used for the decision ranking.</p>
      <div class="aside-container">
        <div class="consumer-image-grid">
          {_candidate_gallery_cards(payload['candidate_data'])}
        </div>
        <aside class="aside">
          <div class="aside-title">shape</div>
          <p><strong>Top cluster:</strong> {escape(top_quality)} lead the balanced score table.</p>
          <p><strong>Cost floor:</strong> {escape(cheapest['candidate_name'])} has the lowest three-year cost at about {escape(_format_rounded_currency(cheapest['three_year_cost_eur']))}.</p>
          <p><strong>Runtime:</strong> {escape(runtime_sentence)}</p>
          {budget_shape}
        </aside>
      </div>
      <div class="aside-container">
        <div class="chart-container reveal">
          <canvas id="metricChart" height="310"></canvas>
          <div class="caption">Effectiveness, fit/safety, and convenience are the three default quality proxies used in the balanced score.</div>
        </div>
        <aside class="aside">
          <div class="aside-title">metric view</div>
          <p><strong>Visual first:</strong> the shortlist is presented as products before the score chart because this is a consumer decision report.</p>
          <p><strong>Audit path:</strong> image provenance stays in the JSON payload instead of the consumer-facing product cards.</p>
          <p><strong>Model:</strong> the chart below still shows the three quality proxies before weighting.</p>
        </aside>
      </div>
      <div class="aside-container">
        <div class="table-wrapper">
          {_html_table(_candidate_numeric_columns(), payload['candidate_data'])}
        </div>
        <aside class="aside">
          <div class="aside-title">numeric audit</div>
          <p><strong>Price:</strong> device price, replaceable-part allowance, and three-year cost are all visible in EUR.</p>
          <p><strong>Battery:</strong> runtime and charging minutes are visible so convenience can be checked independently.</p>
          <p><strong>Proxies:</strong> effectiveness, fit/safety, and convenience are visible before any weighted score is applied.</p>
        </aside>
      </div>
    </section>
    """


def _balanced_section(payload):
    weighted = payload["rankings"]["weighted"]
    leader_gap = weighted[0]["score"] - weighted[1]["score"] if len(weighted) > 1 else 0
    cutoff_gap = weighted[-2]["score"] - weighted[-1]["score"] if len(weighted) > 1 else 0
    scope_phrase = " in the budget-filtered decision pool" if payload.get("budget", {}).get("enabled") else ""
    return f"""
    <section id="balanced">
      <h2>balanced ranking <a href="#toc" class="back-to-top" title="Back to contents">+</a></h2>
      <p class="state-line">{escape(weighted[0]['candidate_name'])} wins{scope_phrase} by <strong>{_format_number(leader_gap)}</strong> points over rank 2.</p>
      {_rank_image_row(payload, weighted[:3], 'balanced top three', 'score', 'score')}
      <div class="aside-container">
        <div class="chart-container reveal">
          <canvas id="weightedChart" height="300"></canvas>
          <div class="caption">Weighted score after the EUR cost penalty; higher is better.</div>
        </div>
        <aside class="aside">
          <div class="aside-title">decision</div>
          <p><strong>Winner:</strong> {escape(weighted[0]['candidate_name'])} reaches {_format_number(weighted[0]['score'])} points in the full formula.</p>
          <p><strong>Runner-up:</strong> {escape(weighted[1]['candidate_name']) if len(weighted) > 1 else 'No runner-up'} scores {_format_number(weighted[1]['score']) if len(weighted) > 1 else '0.00'}.</p>
          <p><strong>Cutoff:</strong> the last adjacent gap is {_format_number(cutoff_gap)} points.</p>
        </aside>
      </div>
      <div class="aside-container">
        <div class="table-wrapper">
          {_html_table(_ranking_columns(include_value=True), payload['rankings']['weighted'])}
        </div>
        <aside class="aside">
          <div class="aside-title">rank table</div>
          <p><strong>Score:</strong> balanced score is the primary decision score when budget is not fixed.</p>
          <p><strong>Score/EUR:</strong> shown in the same table so premium wins are not mistaken for value wins.</p>
          <p><strong>Traceability:</strong> candidate IDs remain in the JSON payload while the visible report uses product names.</p>
        </aside>
      </div>
    </section>
    """


def _value_section(payload, names_by_id):
    frontier_names = _names_for_ids(payload["pareto_frontier"], names_by_id)
    value_rows = payload["rankings"]["cost_benefit"]
    value_winner = value_rows[0]
    decision_rows = _decision_rows(payload)
    highest_cost = max(decision_rows, key=lambda item: item["three_year_cost_eur"])
    cheapest = min(decision_rows, key=lambda item: item["three_year_cost_eur"])
    return f"""
    <section id="value">
      <h2>value and frontier <a href="#toc" class="back-to-top" title="Back to contents">+</a></h2>
      <p class="state-line">{escape(value_winner['candidate_name'])} leads value at <strong>{_format_number(value_winner['score_per_eur'], 3)}</strong> score/EUR.</p>
      {_rank_image_row(payload, value_rows[:3], 'value top three', 'score_per_eur', 'score/EUR')}
      <div class="aside-container">
        <div class="chart-container reveal">
          <canvas id="valueChart" height="300"></canvas>
          <div class="caption">Score per EUR reverses the premium ranking; higher is better.</div>
        </div>
        <aside class="aside">
          <div class="aside-title">budget view</div>
          <p><strong>Value winner:</strong> {escape(value_winner['candidate_name'])} costs about {_format_rounded_currency(_candidate_by_id(payload, value_winner['candidate_id'])['three_year_cost_eur'])} over three years.</p>
          <p><strong>Price floor:</strong> {escape(cheapest['candidate_name'])} is the cheapest observed candidate at about {_format_rounded_currency(cheapest['three_year_cost_eur'])}.</p>
          <p><strong>Price ceiling:</strong> {escape(highest_cost['candidate_name'])} is the highest observed candidate at about {_format_rounded_currency(highest_cost['three_year_cost_eur'])}.</p>
        </aside>
      </div>
      <div class="aside-container">
        <div class="table-wrapper">
          {_html_table(_ranking_columns(include_value=True), payload['rankings']['cost_benefit'])}
        </div>
        <aside class="aside">
          <div class="aside-title">pareto check</div>
          <p><strong>Frontier:</strong> {escape(frontier_names)}.</p>
          <p><strong>Interpretation:</strong> no listed candidate is strictly dominated on all quality metrics and three-year cost.</p>
          <p><strong>Decision rule:</strong> use value ranking first only if price ceiling matters more than shaving quality.</p>
        </aside>
      </div>
    </section>
    """


def _sensitivity_section(payload, names_by_id):
    sensitivity_rows = [
        {
            "profile": profile,
            "rank_1": names_by_id.get(ids[0], ids[0]),
            "rank_2": names_by_id.get(ids[1], ids[1]) if len(ids) > 1 else "",
            "rank_3": names_by_id.get(ids[2], ids[2]) if len(ids) > 2 else "",
            "full_order": _names_for_ids(ids, names_by_id),
        }
        for profile, ids in payload["sensitivity_rankings"].items()
    ]
    tournament_rows = payload["evidence_summary"].get("tournament", [])
    balanced_pick = names_by_id.get(payload["sensitivity_rankings"].get("balanced", [""])[0], "")
    value_pick = names_by_id.get(payload["sensitivity_rankings"].get("value", [""])[0], "")
    skin_pick = names_by_id.get(payload["sensitivity_rankings"].get("skin", [""])[0], "")
    sensitivity_scope = (
        f"Across the {payload['decision_candidate_count']} decision candidates, balanced picks {balanced_pick}, "
        f"value picks {value_pick}, and fit picks {skin_pick}."
    )
    return f"""
    <section id="sensitivity">
      <h2>sensitivity and tournament <a href="#toc" class="back-to-top" title="Back to contents">+</a></h2>
      <p class="state-line">{escape(sensitivity_scope)}</p>
      <div class="aside-container">
        <div class="table-wrapper">
          {_html_table(_sensitivity_columns(), sensitivity_rows)}
        </div>
        <aside class="aside">
          <div class="aside-title">sensitivity</div>
          <p><strong>Balanced:</strong> uses the full score formula and selects {escape(balanced_pick)}.</p>
          <p><strong>Value:</strong> ranks score per EUR and selects {escape(value_pick)}.</p>
          <p><strong>Fit:</strong> sorts by the fit/safety proxy and selects {escape(skin_pick)}.</p>
        </aside>
      </div>
      <div class="aside-container">
        <div class="table-wrapper">
          {_html_table(_tournament_columns(), tournament_rows)}
        </div>
        <aside class="aside">
          <div class="aside-title">tournament</div>
          <p><strong>Comparisons:</strong> the top balanced decision candidates are compared head-to-head.</p>
          <p><strong>Final:</strong> the listed winner follows the same budget-filtered ranking used above.</p>
          <p><strong>Guardrail:</strong> tournament language is explanatory; the numeric ranking remains the source of truth.</p>
        </aside>
      </div>
    </section>
    """


def _candidate_gallery_cards(rows):
    ordered = sorted(rows, key=lambda item: item["weighted_score"], reverse=True)
    return "".join(_candidate_gallery_card(row) for row in ordered)


def _candidate_gallery_card(row):
    return f"""
      <figure class="candidate-product-card">
        {_product_image_frame(row)}
        <figcaption>
          <strong>{escape(row['candidate_name'])}</strong>
          <span class="mono">score {_format_cell(row.get('weighted_score'), 'weighted_score')} / {_format_rounded_currency(row['three_year_cost_eur'])}</span>
          {_product_link_row(row)}
        </figcaption>
      </figure>
    """


def _rank_image_row(payload, ranking_rows, label, metric_key, metric_label):
    cards = []
    for row in ranking_rows:
        candidate = dict(_candidate_by_id(payload, row["candidate_id"]))
        candidate[metric_key] = row.get(metric_key, candidate.get(metric_key))
        cards.append(_rank_image_card(candidate, row["rank"], metric_key, metric_label))
    return f"""
      <div class="rank-image-row" aria-label="{escape(label)}">
        {''.join(cards)}
      </div>
    """


def _rank_image_card(row, rank, metric_key, metric_label):
    return f"""
      <figure class="rank-image-card">
        {_product_image_frame(row)}
        <figcaption>
          <strong>{rank}. {escape(row['candidate_name'])}</strong>
          <span class="mono">{escape(metric_label)} {_format_cell(row.get(metric_key), metric_key)}</span>
          {_product_link_row(row)}
        </figcaption>
      </figure>
    """


def _product_link_row(row):
    links = _item_link_anchors(row, "product-link")
    if not links:
        return ""
    return f'<span class="product-link-row">{links}</span>'


def _evidence_section(payload):
    return f"""
    <section id="evidence">
      <h2>evidence and domains <a href="#toc" class="back-to-top" title="Back to contents">+</a></h2>
      <p class="state-line">The source set contains <strong>{payload['evidence_summary']['source_count']}</strong> sources across <strong>{len(payload['domain_summary'])}</strong> registered or observed domains.</p>
      <div class="aside-container">
        <div class="table-wrapper">
          {_html_table(_domain_columns(), payload['domain_summary'])}
        </div>
        <aside class="aside">
          <div class="aside-title">domain policy</div>
          <p><strong>Registry:</strong> domains are classified by role, trust tier, human status, and API preference.</p>
          <p><strong>Separation:</strong> price, official specifications, expert reviews, forums, and aggregators should keep distinct source roles.</p>
          <p><strong>Review flag:</strong> domains marked needs_review should be treated as supporting evidence, not final purchase authority.</p>
        </aside>
      </div>
      <div class="aside-container">
        <div class="table-wrapper">
          {_html_table(_source_columns(), payload['source_data'])}
        </div>
        <aside class="aside">
          <div class="aside-title">source audit</div>
          <p><strong>Candidate refs:</strong> each source row shows how many candidates it supports.</p>
          <p><strong>Metric refs:</strong> each source row shows how many metric names it contributes.</p>
          <p><strong>Caveat:</strong> source notes are preserved in the raw JSON and summarized here by domain and role.</p>
        </aside>
      </div>
      <div class="flyout">
        <div class="flyout-title">open caveats</div>
        <ul>{''.join(f"<li>{escape(caveat)}</li>" for caveat in payload['evidence_summary'].get('caveats', []))}</ul>
      </div>
    </section>
    """


def _candidate_numeric_columns():
    return [
        ("candidate_name", "Candidate"),
        ("device_price_eur", "Device EUR"),
        ("replacement_head_eur", "Replacement EUR"),
        ("replacement_unit_price_eur", "Part unit EUR"),
        ("replacement_interval_months", "Part interval mo"),
        ("replacement_quantity_3y", "Parts in 3y"),
        ("three_year_cost_eur", "3-year EUR"),
        ("within_price_limit", "Under limit"),
        ("runtime_min", "Runtime min"),
        ("charging_min", "Charge min"),
        ("effectiveness", "Effect."),
        ("skin_safety", "Skin"),
        ("convenience", "Conven."),
        ("weighted_score", "Score"),
        ("score_per_eur", "Score/EUR"),
    ]


def _criteria_columns():
    return [
        ("label", "Criterion"),
        ("coefficient", "Coefficient"),
        ("unit", "Unit"),
        ("direction", "Direction"),
        ("definition", "Definition"),
    ]


def _ranking_columns(include_value=False):
    columns = [
        ("rank", "Rank"),
        ("candidate_name", "Candidate"),
        ("score", "Score"),
    ]
    if include_value:
        columns.append(("score_per_eur", "Score/EUR"))
    return columns


def _sensitivity_columns():
    return [
        ("profile", "Profile"),
        ("rank_1", "Rank 1"),
        ("rank_2", "Rank 2"),
        ("rank_3", "Rank 3"),
        ("full_order", "Full order"),
    ]


def _tournament_columns():
    return [
        ("round", "Round"),
        ("a", "A"),
        ("b", "B"),
        ("winner", "Winner"),
        ("reason", "Reason"),
    ]


def _domain_columns():
    return [
        ("domain", "Domain"),
        ("source_count", "Sources"),
        ("candidate_refs", "Candidate refs"),
        ("metric_refs", "Metric refs"),
        ("roles", "Roles"),
        ("trust_tier", "Trust tier"),
        ("human_status", "Human status"),
        ("api_preferred", "API"),
    ]


def _source_columns():
    return [
        ("domain", "Domain"),
        ("role", "Role"),
        ("candidate_count", "Candidates"),
        ("metric_count", "Metrics"),
        ("title", "Source"),
        ("metrics", "Metric names"),
    ]


def _image_columns():
    return [
        ("candidate_name", "Candidate"),
        ("result_count", "Results"),
        ("host", "Host"),
        ("width", "Width"),
        ("height", "Height"),
        ("score", "Score"),
        ("selected_title", "Selected title"),
        ("selected_url", "Image URL"),
    ]


def _html_table(columns, rows):
    header = "".join(f"<th>{escape(label)}</th>" for _, label in columns)
    body = "".join(_html_table_row(columns, row) for row in rows)
    return f"<table><thead><tr>{header}</tr></thead><tbody>{body}</tbody></table>"


def _html_table_row(columns, row):
    cells = []
    for key, _ in columns:
        value = row.get(key, "")
        class_name = "num" if _is_number(value) else ""
        cells.append(f'<td class="{class_name}">{escape(_format_cell(value, key))}</td>')
    return f"<tr>{''.join(cells)}</tr>"


def _markdown_table(columns, rows):
    lines = []
    lines.append("| " + " | ".join(label for _, label in columns) + " |")
    lines.append("| " + " | ".join("---" for _ in columns) + " |")
    for row in rows:
        lines.append("| " + " | ".join(_format_cell(row.get(key, ""), key) for key, _ in columns) + " |")
    return lines


def _format_cell(value, key):
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    if isinstance(value, bool):
        return "yes" if value else "no"
    if value is None:
        return ""
    if _is_number(value):
        places = 3 if key == "score_per_eur" else 2
        if key in {
            "runtime_min",
            "charging_min",
            "candidate_count",
            "metric_count",
            "source_count",
            "candidate_refs",
            "metric_refs",
            "rank",
            "result_count",
            "width",
            "height",
            "image_width",
            "image_height",
            "image_score",
            "replacement_interval_months",
            "replacement_quantity_3y",
        }:
            places = 0
        if key == "coefficient":
            places = 5
        return _format_number(value, places)
    return str(value)


def _budget_markdown_line(payload):
    budget = payload.get("budget", {})
    if not budget.get("enabled"):
        return ""
    return (
        "Budget: max "
        f"{_format_rounded_currency(budget.get('max_price_eur'))} "
        f"{budget.get('basis_label', 'price')}; "
        f"decision candidates: {budget.get('eligible_candidate_count', 0)} of {payload['candidate_count']}"
    )


def _budget_html_note(payload):
    budget = payload.get("budget", {})
    if not budget.get("enabled"):
        return "The report separates balanced score from value score because no fixed budget was supplied."
    return (
        "The decision ranking is filtered to candidates with "
        f"{escape(budget.get('basis_label', 'price'))} at or below "
        f"<span class=\"mono\">{escape(_format_rounded_currency(budget.get('max_price_eur')))}</span>; "
        "over-budget rows stay in the raw data for audit."
    )


def _budget_meta_fragment(payload):
    budget = payload.get("budget", {})
    if not budget.get("enabled"):
        return ""
    return (
        " / budget: "
        f"<span class=\"mono\">max {escape(_format_rounded_currency(budget.get('max_price_eur')))} "
        f"{escape(budget.get('basis_label', 'price'))}</span>"
    )


def _decision_pool_note(payload):
    budget = payload.get("budget", {})
    if not budget.get("enabled"):
        return "candidate options"
    return (
        "under max "
        f"{_format_rounded_currency(budget.get('max_price_eur'))} "
        f"{budget.get('basis_label', 'price')}"
    )


def _source_tags(payload):
    tags = [
        payload["task"]["market"],
        payload["task"]["currency"],
        f"{payload['decision_candidate_count']} decision candidates",
        f"{payload['evidence_summary']['source_count']} sources",
    ]
    if payload.get("budget", {}).get("enabled"):
        tags.insert(
            2,
            f"max {_format_rounded_currency(payload['budget'].get('max_price_eur'))}",
        )
    return " ".join(f"<span>{escape(tag)}</span>" for tag in tags)


def _summary_card(label, value, detail, color):
    return f"""
      <div class="summary-card" style="--card-color: var(--spark-{escape(color)})">
        <div class="label">{escape(label)}</div>
        <div class="big-number-row"><div class="big-number">{escape(value)}</div></div>
        <div class="detail">{escape(detail)}</div>
      </div>
    """


def _candidate_by_id(payload, candidate_id):
    for row in payload["candidate_data"]:
        if row["candidate_id"] == candidate_id:
            return row
    raise KeyError(candidate_id)


def _decision_rows(payload):
    decision_ids = {
        row["candidate_id"]
        for row in payload["rankings"]["weighted"]
    }
    return [
        row
        for row in payload["candidate_data"]
        if row["candidate_id"] in decision_ids
    ]


def _numbers(rows, key):
    return [row[key] for row in rows if _is_number(row.get(key))]


def _names_for_ids(candidate_ids, names_by_id):
    return ", ".join(names_by_id.get(candidate_id, candidate_id) for candidate_id in candidate_ids)


def _format_number(value, places=2):
    if value is None or value == "":
        return ""
    return f"{value:.{places}f}"


def _format_currency(value):
    return f"{_format_number(value, 2)} EUR"


def _format_rounded_currency(value):
    if value is None or value == "":
        return ""
    return f"{round(value):.0f} EUR"


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _json_for_script(payload):
    return (
        json.dumps(payload, ensure_ascii=False)
        .replace("&", "\\u0026")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
    )


def _machine_audit(payload):
    names_by_id = {
        candidate["candidate_id"]: candidate["candidate_name"]
        for candidate in payload["candidates"]
    }
    lines = [
        f"<p>Candidate count: {payload['candidate_count']}</p>",
        f"<p>Winner: {escape(payload['winner']['candidate_name'])} ({escape(payload['winner']['candidate_id'])})</p>",
    ]
    for ranking_name, rows in payload["rankings"].items():
        lines.append(f"<p>{escape(ranking_name)}</p>")
        for row in rows:
            lines.append(
                f"<p>{row['rank']}. {escape(row['candidate_name'])} ({escape(row['candidate_id'])})</p>"
            )
    lines.append(f"<p>Pareto frontier: {escape(', '.join(payload['pareto_frontier']))}</p>")
    lines.append(f"<p>Pareto frontier names: {escape(_names_for_ids(payload['pareto_frontier'], names_by_id))}</p>")
    for profile, ordered_ids in payload["sensitivity_rankings"].items():
        lines.append(f"<p>{escape(profile)}: {escape(', '.join(ordered_ids))}</p>")
    lines.append(f"<p>Evidence sources: {payload['evidence_summary']['source_count']}</p>")
    return f"<div hidden>{''.join(lines)}</div>"


def _report_css():
    return """
    @font-face {
      font-family: 'Monaspace Argon';
      src: url('https://cdn.jsdelivr.net/gh/githubnext/monaspace@v1.101/fonts/webfonts/MonaspaceArgon-Regular.woff2') format('woff2');
      font-weight: 400;
      font-display: swap;
    }
    @font-face {
      font-family: 'Monaspace Argon';
      src: url('https://cdn.jsdelivr.net/gh/githubnext/monaspace@v1.101/fonts/webfonts/MonaspaceArgon-Bold.woff2') format('woff2');
      font-weight: 700;
      font-display: swap;
    }
    :root {
      --ink: #1a1a1a;
      --ink-light: #555;
      --ink-muted: #888;
      --bg: oklch(99% 0.008 98);
      --bg-aside: oklch(97% 0.012 95);
      --image-bg: oklch(99.4% 0.004 95);
      --accent: #a00;
      --rule: #ccc;
      --spark-primary: #c45a28;
      --spark-secondary: #2a7a5a;
      --spark-tertiary: #5a5aaa;
      --status-red: #a02a2a;
      --status-amber: #c89000;
      --status-green: #2a7a3a;
      --status-blue: rgba(42,80,140,0.7);
    }
    * { box-sizing: border-box; }
    html { scroll-behavior: smooth; }
    body {
      margin: 0;
      color: var(--ink);
      background: var(--bg);
      font-family: 'EB Garamond', Georgia, serif;
      font-size: 18px;
      line-height: 1.6;
    }
    .page {
      max-width: 1200px;
      margin: 0 auto;
      padding: 2rem 1.5rem 4rem;
    }
    h1, h2, h3 {
      font-weight: 400;
      font-variant: small-caps;
      letter-spacing: 0;
      line-height: 1.1;
    }
    h1 { font-size: 2.2rem; margin: 0.75rem 0 0.5rem; }
    h2 { font-size: 1.5rem; margin: 0 0 1rem; }
    h3 { color: var(--ink-light); font-size: 1.15rem; }
    section { margin: 0; }
    footer {
      border-top: 1px solid var(--rule);
      color: var(--ink-light);
      font-style: italic;
      margin-top: 2rem;
      padding-top: 1.5rem;
    }
    .subtitle {
      color: var(--ink-light);
      font-size: 1.35rem;
      font-style: italic;
      max-width: 760px;
      margin: 0;
    }
    .meta-line { color: var(--ink-muted); margin-top: 0.75rem; }
    .view-switch {
      margin: 0.75rem 0 0;
    }
    .view-switch a {
      color: var(--accent);
      font-size: 0.92rem;
      font-variant: small-caps;
      text-decoration: underline;
      text-underline-offset: 3px;
    }
    .mono, .num, .source-tags span, .big-number, .status-value {
      font-family: 'Monaspace Argon', ui-monospace, monospace;
      font-variant-numeric: tabular-nums;
    }
    .source-tags {
      display: flex;
      flex-wrap: wrap;
      gap: 0.45rem;
      color: var(--rule);
      font-size: 0.65rem;
    }
    .source-tags span {
      border: 1px solid var(--rule);
      padding: 0.15rem 0.35rem;
    }
    .status-strip {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      border-top: 1px solid var(--rule);
      border-bottom: 1px solid var(--rule);
      margin: 2rem 0;
    }
    .status-cell {
      min-width: 0;
      padding: 1rem;
      border-top: 3px solid var(--status-blue);
    }
    .status-cell + .status-cell { border-left: 1px solid var(--rule); }
    .status-green { border-top-color: var(--status-green); }
    .status-amber { border-top-color: var(--status-amber); }
    .status-blue { border-top-color: var(--status-blue); }
    .status-label {
      color: var(--ink-muted);
      font-size: 0.78rem;
      font-variant: small-caps;
    }
    .status-value {
      font-size: 1.1rem;
      line-height: 1.25;
      margin: 0.25rem 0;
      overflow-wrap: anywhere;
    }
    .status-note {
      color: var(--ink-light);
      font-size: 0.85rem;
    }
    .toc-layout {
      display: grid;
      grid-template-columns: 1fr 180px;
      gap: 2rem;
      align-items: start;
    }
    .lede {
      font-size: 1.25rem;
      line-height: 1.6;
      max-width: 780px;
    }
    .lede::first-letter {
      float: left;
      font-size: 3.4rem;
      line-height: 0.85;
      padding-right: 0.2rem;
    }
    .toc {
      position: sticky;
      top: 2rem;
      border-left: 1px solid var(--rule);
      padding-left: 1rem;
    }
    .toc-title {
      color: var(--ink-muted);
      font-size: 0.8rem;
      font-variant: small-caps;
      margin-bottom: 0.45rem;
    }
    .toc a {
      display: block;
      color: var(--ink-light);
      text-decoration: none;
      margin: 0.3rem 0;
      font-size: 0.92rem;
    }
    .toc a::before {
      content: "$ ";
      color: var(--rule);
      font-family: 'Monaspace Argon', monospace;
    }
    .summary-row {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 1.5rem;
      margin: 2rem 0;
    }
    .summary-card {
      border: 1px solid var(--rule);
      border-top: 3px solid var(--card-color);
      padding: 1rem 1rem 1.1rem;
    }
    .summary-card .label {
      color: var(--ink-muted);
      font-size: 0.78rem;
      font-variant: small-caps;
    }
    .big-number {
      font-size: 2.2rem;
      line-height: 1.2;
      margin: 0.35rem 0;
    }
    .detail { color: var(--ink-light); font-size: 0.95rem; }
    .ornament {
      color: var(--rule);
      font-family: 'Monaspace Argon', monospace;
      font-size: 0.9rem;
      font-variant-ligatures: discretionary-ligatures;
      margin: 2rem 0;
      text-align: center;
    }
    .state-line {
      color: var(--ink-light);
      font-size: 1.5rem;
      font-style: italic;
      line-height: 1.45;
      max-width: 750px;
      margin: 1.5rem 0 2rem;
    }
    .state-line strong { color: var(--ink); font-weight: 400; }
    .aside-container {
      display: grid;
      grid-template-columns: 1fr 280px;
      gap: 2rem;
      align-items: start;
      margin: 1.5rem 0 2rem;
    }
    .aside {
      color: var(--ink-light);
      font-size: 0.85rem;
      font-style: italic;
      line-height: 1.5;
      padding-top: 0;
    }
    .aside-title {
      color: var(--ink-light);
      font-size: 0.82rem;
      font-style: normal;
      font-variant: small-caps;
      letter-spacing: 0.08em;
      margin-bottom: 0.5rem;
      text-transform: lowercase;
    }
    .chart-container {
      margin: 0;
      padding: 0 5%;
      height: 360px;
      min-height: 360px;
      position: relative;
    }
    .chart-container canvas {
      display: block;
      width: 100% !important;
      height: 300px !important;
    }
    .caption {
      color: var(--ink-muted);
      font-size: 0.82rem;
      font-style: italic;
      margin-top: 0.75rem;
      text-align: center;
    }
    .table-wrapper {
      max-width: 100%;
      overflow-x: auto;
    }
    table {
      border-collapse: collapse;
      width: 100%;
      font-size: 0.92rem;
    }
    th {
      color: var(--ink-muted);
      font-size: 0.82rem;
      font-variant: small-caps;
      font-weight: 400;
      text-align: left;
    }
    th, td {
      border-bottom: 1px solid rgba(204,204,204,0.75);
      padding: 0.45rem 0.5rem;
      vertical-align: top;
    }
    tbody tr:hover { background: rgba(249,246,238,0.75); }
    td { overflow-wrap: anywhere; }
    td.num {
      font-family: 'Monaspace Argon', ui-monospace, monospace;
      font-variant-numeric: tabular-nums;
      text-align: right;
      white-space: nowrap;
    }
    .product-showcase {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 1.25rem;
      margin: -0.5rem 0 2rem;
      padding-bottom: 1.5rem;
      border-bottom: 1px solid var(--rule);
    }
    .consumer-image-grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 1rem;
    }
    .rank-image-row {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 1rem;
      margin: 0 0 2rem;
    }
    .product-spotlight,
    .candidate-product-card,
    .rank-image-card {
      border-top: 1px solid var(--rule);
      margin: 0;
      min-width: 0;
      padding-top: 0.75rem;
    }
    .product-image-frame {
      align-items: center;
      aspect-ratio: 4 / 3;
      background: var(--image-bg);
      display: flex;
      justify-content: center;
      overflow: hidden;
      width: 100%;
    }
    .product-spotlight .product-image-frame {
      aspect-ratio: 5 / 4;
    }
    .product-image-frame img {
      display: block;
      height: 100%;
      object-fit: contain;
      width: 100%;
    }
    .product-image-placeholder {
      color: var(--ink-muted);
      font-size: 0.9rem;
      font-style: italic;
      padding: 1rem;
      text-align: center;
    }
    .product-spotlight figcaption,
    .candidate-product-card figcaption,
    .rank-image-card figcaption {
      color: var(--ink-light);
      font-size: 0.84rem;
      line-height: 1.35;
      margin-top: 0.55rem;
    }
    .product-spotlight figcaption strong,
    .candidate-product-card figcaption strong,
    .rank-image-card figcaption strong,
    .product-spotlight figcaption span,
    .candidate-product-card figcaption span,
    .rank-image-card figcaption span {
      display: block;
      overflow-wrap: anywhere;
    }
    .product-link-row {
      display: flex !important;
      flex-wrap: wrap;
      gap: 0.35rem;
      margin-top: 0.45rem;
    }
    .product-link {
      border: 1px solid rgba(204,204,204,0.95);
      color: var(--accent);
      font-family: 'Monaspace Argon', ui-monospace, monospace;
      font-size: 0.68rem;
      font-style: normal;
      line-height: 1;
      padding: 0.25rem 0.35rem;
      text-decoration: none;
      white-space: nowrap;
    }
    .product-link:hover {
      border-color: var(--accent);
      text-decoration: underline;
      text-underline-offset: 3px;
    }
    .flyout {
      background: var(--bg-aside);
      border: 1px solid rgba(204,204,204,0.9);
      margin: 1.5rem 0;
      padding: 1rem 1.25rem;
      position: relative;
    }
    .flyout::before {
      content: "";
      width: 0.45rem;
      height: 0.45rem;
      background: var(--accent);
      position: absolute;
      left: 1rem;
      top: -0.25rem;
      transform: rotate(45deg);
    }
    .flyout-title {
      color: var(--ink-light);
      font-size: 0.82rem;
      font-variant: small-caps;
      margin-bottom: 0.5rem;
    }
    .empty-note {
      color: var(--ink-light);
      font-style: italic;
    }
    .back-to-top {
      color: var(--rule);
      font-family: 'Monaspace Argon', monospace;
      text-decoration: none;
      transition: color 0.3s ease, transform 0.3s ease;
    }
    .back-to-top:hover {
      color: var(--ink);
      display: inline-block;
      transform: translateY(-2px);
    }
    .reveal {
      opacity: 0;
      transform: translateY(16px);
      transition: opacity 0.6s cubic-bezier(0.25,0.1,0.25,1), transform 0.6s;
    }
    .reveal.visible {
      opacity: 1;
      transform: translateY(0);
    }
    @media (max-width: 800px) {
      body { font-size: 17px; }
      .page { padding: 1.25rem 1rem 3rem; }
      .status-strip { grid-template-columns: repeat(2, 1fr); }
      .toc-layout, .aside-container, .summary-row, .product-showcase, .consumer-image-grid, .rank-image-row { grid-template-columns: 1fr; }
      .toc { position: static; border-left: none; padding-left: 0; }
      .chart-container { padding: 0; }
      .status-value { font-size: 0.98rem; }
    }
    @media (prefers-reduced-motion: reduce) {
      * { scroll-behavior: auto !important; transition: none !important; animation: none !important; }
      .reveal { opacity: 1; transform: none; }
    }
    """


def _report_js(payload):
    chart_payload = {
        "weighted": payload["rankings"]["weighted"],
        "value": payload["rankings"]["cost_benefit"],
        "candidates": payload["candidate_data"],
    }
    return f"""
    const report = {json.dumps(chart_payload, ensure_ascii=False)};

    Chart.defaults.font.family = "'EB Garamond', Georgia, serif";
    Chart.defaults.font.size = 13;
    Chart.defaults.color = '#555';
    Chart.defaults.plugins.legend.labels.usePointStyle = false;
    Chart.defaults.plugins.legend.labels.boxWidth = 8;
    Chart.defaults.plugins.legend.labels.boxHeight = 8;
    Chart.defaults.plugins.legend.labels.borderRadius = 4;
    Chart.defaults.plugins.legend.labels.font = {{ family: "'EB Garamond', serif", size: 11 }};
    Chart.defaults.plugins.legend.labels.padding = 14;
    Chart.defaults.plugins.tooltip.backgroundColor = '#1a1a1a';
    Chart.defaults.plugins.tooltip.cornerRadius = 2;
    Chart.defaults.plugins.tooltip.padding = 10;
    Chart.defaults.scale.grid.color = '#eee';
    Chart.defaults.animation = {{
      duration: 800,
      easing: 'easeOutQuart',
      delay: (ctx) => ctx.type === 'data' ? ctx.dataIndex * 8 : 0
    }};

    const defaultGen = Chart.defaults.plugins.legend.labels.generateLabels;
    Chart.defaults.plugins.legend.labels.generateLabels = function(chart) {{
      const items = defaultGen.call(this, chart);
      items.forEach(item => {{
        const ds = chart.data.datasets[item.datasetIndex];
        const color = ds.borderColor || ds.backgroundColor;
        item.fillStyle = Array.isArray(color) ? color[0] : color;
        item.strokeStyle = 'transparent';
        item.lineWidth = 0;
        item.borderRadius = 4;
      }});
      return items;
    }};

    function shortName(name) {{
      return name;
    }}

    function barChart(id, rows, valueKey, label, color) {{
      new Chart(document.getElementById(id), {{
        type: 'bar',
        data: {{
          labels: rows.map(row => shortName(row.candidate_name)),
          datasets: [{{
            label,
            data: rows.map(row => row[valueKey]),
            backgroundColor: color,
            borderWidth: 0,
            borderRadius: 2
          }}]
        }},
        options: {{
          indexAxis: 'y',
          responsive: true,
          maintainAspectRatio: false,
          scales: {{
            x: {{ grid: {{ color: '#eee' }} }},
            y: {{ grid: {{ display: false }}, ticks: {{ font: {{ size: 11 }} }} }}
          }},
          plugins: {{ legend: {{ display: false }} }}
        }}
      }});
    }}

    barChart('weightedChart', report.weighted, 'score', 'Weighted score', 'rgba(196,90,40,0.55)');
    barChart('valueChart', report.value, 'score_per_eur', 'Score per EUR', 'rgba(42,122,90,0.55)');

    new Chart(document.getElementById('metricChart'), {{
      type: 'bar',
      data: {{
        labels: report.candidates.map(row => shortName(row.candidate_name)),
        datasets: [
          {{
            label: 'Effectiveness',
            data: report.candidates.map(row => row.effectiveness),
            backgroundColor: 'rgba(196,90,40,0.50)',
            borderWidth: 0,
            borderRadius: 1
          }},
          {{
            label: 'Fit / safety',
            data: report.candidates.map(row => row.skin_safety),
            backgroundColor: 'rgba(42,122,90,0.50)',
            borderWidth: 0,
            borderRadius: 1
          }},
          {{
            label: 'Convenience',
            data: report.candidates.map(row => row.convenience),
            backgroundColor: 'rgba(90,90,170,0.45)',
            borderWidth: 0,
            borderRadius: 1
          }}
        ]
      }},
      options: {{
        responsive: true,
        maintainAspectRatio: false,
        scales: {{
          x: {{ grid: {{ display: false }}, ticks: {{ maxRotation: 35, minRotation: 0, font: {{ size: 10 }} }} }},
          y: {{ title: {{ display: true, text: '0-100 proxy score' }}, suggestedMin: 50, suggestedMax: 100 }}
        }},
        plugins: {{ legend: {{ position: 'top', align: 'end' }} }}
      }}
    }});

    document.querySelectorAll('.chart-container, .flyout, .aside-container').forEach(el => el.classList.add('reveal'));
    const observer = new IntersectionObserver((entries) => {{
      entries.forEach(entry => {{
        if (entry.isIntersecting) {{
          entry.target.classList.add('visible');
          observer.unobserve(entry.target);
        }}
      }});
    }}, {{ threshold: 0.15 }});
    document.querySelectorAll('.reveal').forEach(el => observer.observe(el));
    """
