#!/usr/bin/env python3
"""Google Image Search skill - main orchestration script.

Modes:
    1. Simple query: --query "search term"
    2. Batch from JSON: --config queries.json
    3. Generate config: --generate-config --terms "term1" "term2"
    4. Note enrichment: --enrich-note note.md
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

# Add scripts directory to path for relative imports
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

from api import fetch_images_for_entry
from config import (
    create_simple_entry,
    get_openrouter_key,
    load_queries,
    resolve_credentials,
    save_config,
)
from download import download_all_images, download_best_images
from evaluate import evaluate_results
from llm_select import (
    extract_visual_terms,
    generate_config_from_terms,
    run_llm_selection,
)
from obsidian import (
    detect_obsidian_vault,
    enrich_note_with_images,
    extract_headings,
    get_attachments_folder,
    map_terms_to_headings,
)
from output import (
    emit_final_selection_markdown,
    emit_preview_markdown,
    emit_selection_markdown,
    emit_summary_markdown,
    emit_urls_only,
)


def run_simple_query(
    query: str,
    api_key: str,
    cx: str,
    num_results: int,
    output_dir: Optional[Path],
    llm_select: bool,
    llm_executable: Path,
    llm_model: str,
    openrouter_key: Optional[str],
    urls_only: bool,
) -> None:
    """Run a simple single-query search."""
    entry = create_simple_entry(query, num_results=num_results)
    bundle = fetch_images_for_entry(entry=entry, api_key=api_key, cx=cx)
    results = [bundle]

    evaluate_results(results)

    if llm_select:
        run_llm_selection(
            results=results,
            llm_executable=llm_executable,
            model=llm_model,
            openrouter_key=openrouter_key,
        )

    if urls_only:
        print(emit_urls_only(results, best_only=True))
        return

    if output_dir:
        downloaded = download_best_images(results, output_dir)
        print(f"Downloaded {downloaded} image(s) to {output_dir}")

    print(emit_final_selection_markdown(results) if llm_select else emit_selection_markdown(results))


def run_batch(
    config_path: Path,
    api_key: str,
    cx: str,
    output_dir: Optional[Path],
    llm_select: bool,
    llm_executable: Path,
    llm_model: str,
    openrouter_key: Optional[str],
    urls_only: bool,
    output_files: dict,
    download_all: bool,
    limit: Optional[int],
) -> None:
    """Run batch search from JSON config."""
    entries = load_queries(config_path)
    if limit:
        entries = entries[:limit]

    results = []
    for entry in entries:
        bundle = fetch_images_for_entry(entry=entry, api_key=api_key, cx=cx)
        results.append(bundle)

    evaluate_results(results)

    if llm_select:
        run_llm_selection(
            results=results,
            llm_executable=llm_executable,
            model=llm_model,
            openrouter_key=openrouter_key,
        )

    if urls_only:
        print(emit_urls_only(results, best_only=True))
        return

    if output_dir:
        if download_all:
            downloaded = download_all_images(results, output_dir)
        else:
            downloaded = download_best_images(results, output_dir)
        print(f"Downloaded {downloaded} image(s) to {output_dir}")

    # Write output files
    if output_files.get("summary"):
        Path(output_files["summary"]).write_text(emit_summary_markdown(results), encoding="utf-8")
    if output_files.get("preview"):
        Path(output_files["preview"]).write_text(emit_preview_markdown(results, prefer_local=bool(output_dir)), encoding="utf-8")
    if output_files.get("selection"):
        Path(output_files["selection"]).write_text(emit_selection_markdown(results), encoding="utf-8")
    if output_files.get("final") and llm_select:
        Path(output_files["final"]).write_text(emit_final_selection_markdown(results), encoding="utf-8")

    written = [f for f in output_files.values() if f]
    if written:
        print(f"Wrote: {', '.join(written)}")


def run_generate_config(
    terms: List[str],
    output_path: Path,
    llm_executable: Path,
    llm_model: str,
    openrouter_key: Optional[str],
    num_results: int,
) -> None:
    """Generate JSON config from list of terms using LLM."""
    print(f"Generating config for {len(terms)} terms...")

    entries = generate_config_from_terms(
        terms=terms,
        llm_executable=llm_executable,
        model=llm_model,
        openrouter_key=openrouter_key,
        num_results=num_results,
    )

    save_config(entries, output_path)
    print(f"Wrote config with {len(entries)} entries to {output_path}")


def run_enrich_note(
    note_path: Path,
    api_key: str,
    cx: str,
    llm_executable: Path,
    llm_model: str,
    openrouter_key: Optional[str],
    num_results: int,
    attachments_folder: Optional[Path],
    dry_run: bool,
) -> None:
    """Enrich Obsidian note with images."""
    if not note_path.exists():
        print(f"Error: Note not found: {note_path}", file=sys.stderr)
        sys.exit(1)

    note_content = note_path.read_text(encoding="utf-8")

    # Detect Obsidian vault
    vault_root = detect_obsidian_vault(note_path)
    if vault_root:
        print(f"Detected Obsidian vault: {vault_root}")
        if not attachments_folder:
            attachments_folder = get_attachments_folder(vault_root)
    else:
        if not attachments_folder:
            attachments_folder = note_path.parent / "images"

    print(f"Attachments folder: {attachments_folder}")

    # Extract headings
    headings = extract_headings(note_content)
    print(f"Found {len(headings)} headings")

    # Extract visual terms using LLM
    print("Extracting visual terms...")
    terms = extract_visual_terms(
        note_content=note_content,
        llm_executable=llm_executable,
        model=llm_model,
        openrouter_key=openrouter_key,
    )

    if not terms:
        print("No visual terms extracted. Note may be too short or abstract.")
        return

    print(f"Extracted {len(terms)} terms: {[t.get('term') for t in terms]}")

    if dry_run:
        print("\n[DRY RUN] Would search for:")
        for term in terms:
            print(f"  - {term.get('term')} (heading: {term.get('heading', 'general')})")
        return

    # Map terms to headings
    terms_by_heading = map_terms_to_headings(terms, headings)

    # Create config entries and fetch images
    # Use term as ID for unique filenames, track target heading separately
    results = []
    term_to_heading = {}  # Maps entry ID to target heading

    for heading, heading_terms in terms_by_heading.items():
        for term_info in heading_terms:
            term_id = term_info.get("term", "image").lower().replace(" ", "-")[:40]
            entry = {
                "id": term_id,
                "heading": term_id,  # Use term for filename slug
                "description": term_info.get("description", ""),
                "query": term_info.get("term", ""),
                "selectionCriteria": term_info.get("criteria", ""),
                "numResults": num_results,
                "selectionCount": 2,
                "safe": "active",
            }
            term_to_heading[term_id] = heading  # Track target heading for insertion

            bundle = fetch_images_for_entry(entry=entry, api_key=api_key, cx=cx)
            results.append(bundle)

    # Evaluate and select
    evaluate_results(results)
    run_llm_selection(
        results=results,
        llm_executable=llm_executable,
        model=llm_model,
        openrouter_key=openrouter_key,
    )

    # Download best images
    attachments_folder.mkdir(parents=True, exist_ok=True)
    downloaded = download_best_images(results, attachments_folder)
    print(f"Downloaded {downloaded} images")

    # Build images_by_heading for note enrichment
    # Use list of tuples to handle multiple images per heading
    images_by_heading = {}
    for bundle in results:
        entry = bundle["entry"]
        term_id = entry.get("id", "")
        target_heading = term_to_heading.get(term_id, "")
        final_selection = entry.get("finalSelection")
        if final_selection and target_heading:
            # Only keep first image per heading to avoid clutter
            if target_heading not in images_by_heading:
                images_by_heading[target_heading] = final_selection["item"]

    # Enrich note
    enriched_content = enrich_note_with_images(
        note_path=note_path,
        images_by_heading=images_by_heading,
        attachments_folder=attachments_folder,
        use_obsidian_embeds=bool(vault_root),
        create_backup_file=True,
    )

    note_path.write_text(enriched_content, encoding="utf-8")
    print(f"Enriched note: {note_path}")
    print(f"Backup created: {note_path}.bak")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Google Image Search skill - search, download, and integrate images"
    )

    # Mode selection
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument("--query", help="Simple query mode: search for single term")
    mode_group.add_argument("--config", type=Path, help="Batch mode: JSON config file")
    mode_group.add_argument("--generate-config", action="store_true", help="Generate config from terms")
    mode_group.add_argument("--enrich-note", type=Path, help="Enrich Obsidian note with images")

    # Terms for config generation
    parser.add_argument("--terms", nargs="+", help="Terms for config generation")

    # Output options
    parser.add_argument("--output-dir", type=Path, help="Directory to save images")
    parser.add_argument("--output", type=Path, help="Output file for generated config or markdown")
    parser.add_argument("--urls-only", action="store_true", help="Output URLs only, no download")
    parser.add_argument("--download-all", action="store_true", help="Download all images, not just best")

    # Output files for batch mode
    parser.add_argument("--summary-output", default="image_suggestions.md")
    parser.add_argument("--preview-output", default="image_preview.md")
    parser.add_argument("--selection-output", default="image_selection.md")
    parser.add_argument("--final-output", default="image_final_selection.md")

    # API options
    parser.add_argument("--env-file", type=Path, default=Path(".env"))
    parser.add_argument("--api-key", help="Google Custom Search API key")
    parser.add_argument("--cx", help="Google Custom Search Engine ID")
    parser.add_argument("--num-results", type=int, default=5, help="Results per query")

    # LLM options
    parser.add_argument("--llm-select", action="store_true", default=True, help="Use LLM for selection (default)")
    parser.add_argument("--no-llm-select", action="store_true", help="Disable LLM selection")
    parser.add_argument("--llm-executable", type=Path, default=Path("/opt/homebrew/bin/llm"))
    parser.add_argument("--llm-model", default="openrouter/openai/gpt-4o-mini")

    # Obsidian options
    parser.add_argument("--attachments-folder", type=Path, help="Override attachments folder")

    # Other options
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done")
    parser.add_argument("--limit", type=int, help="Limit number of queries (batch mode)")

    args = parser.parse_args()

    # Resolve credentials
    credentials = resolve_credentials(
        api_key=args.api_key,
        cx=args.cx,
        env_file=args.env_file,
    )
    api_key = credentials["api_key"]
    cx = credentials["cx"]

    if not api_key and not args.generate_config:
        print("Error: Missing API key", file=sys.stderr)
        sys.exit(1)
    if not cx and not args.generate_config:
        print("Error: Missing Search Engine ID (cx)", file=sys.stderr)
        sys.exit(1)

    openrouter_key = get_openrouter_key(args.env_file)
    llm_select = args.llm_select and not args.no_llm_select

    # Route to appropriate mode
    if args.query:
        run_simple_query(
            query=args.query,
            api_key=api_key,
            cx=cx,
            num_results=args.num_results,
            output_dir=args.output_dir,
            llm_select=llm_select,
            llm_executable=args.llm_executable,
            llm_model=args.llm_model,
            openrouter_key=openrouter_key,
            urls_only=args.urls_only,
        )

    elif args.config:
        run_batch(
            config_path=args.config,
            api_key=api_key,
            cx=cx,
            output_dir=args.output_dir,
            llm_select=llm_select,
            llm_executable=args.llm_executable,
            llm_model=args.llm_model,
            openrouter_key=openrouter_key,
            urls_only=args.urls_only,
            output_files={
                "summary": args.summary_output,
                "preview": args.preview_output,
                "selection": args.selection_output,
                "final": args.final_output,
            },
            download_all=args.download_all,
            limit=args.limit,
        )

    elif args.generate_config:
        if not args.terms:
            print("Error: --terms required with --generate-config", file=sys.stderr)
            sys.exit(1)
        output_path = args.output or Path("generated_queries.json")
        run_generate_config(
            terms=args.terms,
            output_path=output_path,
            llm_executable=args.llm_executable,
            llm_model=args.llm_model,
            openrouter_key=openrouter_key,
            num_results=args.num_results,
        )

    elif args.enrich_note:
        run_enrich_note(
            note_path=args.enrich_note,
            api_key=api_key,
            cx=cx,
            llm_executable=args.llm_executable,
            llm_model=args.llm_model,
            openrouter_key=openrouter_key,
            num_results=args.num_results,
            attachments_folder=args.attachments_folder,
            dry_run=args.dry_run,
        )


if __name__ == "__main__":
    main()
