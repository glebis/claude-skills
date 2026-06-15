#!/usr/bin/env python3
"""Write a filled LICENSE file for a given SPDX id.

Prefers a bundled template in ../assets/licenses/<id>.txt (offline, with
{{year}}/{{author}} placeholders); otherwise fetches the canonical text from the
SPDX license-list-data repo and fills the common copyright placeholders.

Usage:
    fetch_license.py <SPDX-ID> --author "Name" [--year 2026] [--out LICENSE]

Examples:
    fetch_license.py MIT --author "Gleb Kalinin"
    fetch_license.py Apache-2.0 --author "Gleb Kalinin" --out LICENSE
"""
import argparse
import sys
import urllib.request
from datetime import date
from pathlib import Path

SPDX_URL = "https://raw.githubusercontent.com/spdx/license-list-data/main/text/{id}.txt"
ASSETS = Path(__file__).resolve().parent.parent / "assets" / "licenses"


def fill(text: str, author: str, year: str) -> str:
    # Bundled templates use {{...}}; SPDX texts use <...> / [...] placeholders.
    repl = {
        "{{year}}": year,
        "{{author}}": author,
        "<year>": year,
        "<copyright holders>": author,
        "<name of author>": author,
        "<owner>": author,
        "[yyyy]": year,
        "[year]": year,
        "[name of copyright owner]": author,
        "[fullname]": author,
    }
    for k, v in repl.items():
        text = text.replace(k, v)
    return text


def load(spdx_id: str) -> str:
    local = ASSETS / f"{spdx_id}.txt"
    if local.exists():
        return local.read_text(encoding="utf-8")
    url = SPDX_URL.format(id=spdx_id)
    try:
        with urllib.request.urlopen(url, timeout=20) as r:
            return r.read().decode("utf-8")
    except Exception as e:  # noqa: BLE001
        sys.exit(
            f"error: no bundled template for '{spdx_id}' and fetch failed: {e}\n"
            f"  tried: {url}\n"
            f"  bundled ids: {', '.join(sorted(p.stem for p in ASSETS.glob('*.txt'))) or '(none)'}"
        )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("spdx_id", help="SPDX license id, e.g. MIT, Apache-2.0, GPL-3.0-or-later")
    ap.add_argument("--author", required=True, help="copyright holder")
    ap.add_argument("--year", default=str(date.today().year))
    ap.add_argument("--out", default="LICENSE")
    args = ap.parse_args()

    text = fill(load(args.spdx_id), args.author, args.year)
    Path(args.out).write_text(text, encoding="utf-8")
    print(f"wrote {args.out} ({args.spdx_id}, (c) {args.year} {args.author})")


if __name__ == "__main__":
    main()
