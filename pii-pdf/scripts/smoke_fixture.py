#!/usr/bin/env python3
"""Build and check the synthetic doctor fixture. Runs inside the pii-pdf venv (needs PyMuPDF).

  smoke_fixture.py build DIR      -> DIR/fixture.pdf (page 1 native text, page 2 image-only scan)
  smoke_fixture.py verify PDF     -> JSON verdict per page (labels only, never values)

All values are invented. Only labels leave this script, so the doctor output stays clean.
"""
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import fitz  # PyMuPDF

LINES = [
    'Invoice 2026-118',
    'Customer: Margaret Holloway',
    'Email: margaret.holloway@fixture-mail.org',
    'Phone: +49 30 1234 5678',
    'IBAN: DE89 3704 0044 0532 0130 00',
    'Total amount due: 412.50 EUR',
]

# Probes are compared after norm(): lowercase, alphanumerics only. Short, distinctive
# fragments catch partial leaks (e.g. surname survives, first name replaced) and are
# robust to OCR spacing noise.
SECRETS = {
    'PERSON': ['holloway', 'margaret'],
    'EMAIL': ['fixturemail', 'margaretholloway'],
    'PHONE': ['4930', '12345678'],
    'IBAN': ['de89', '370400440532013000'],
}
# Non-PII that must survive: proves redaction did not wipe the page.
CONTROLS = {'heading': 'invoice', 'total': 'totalamountdue'}


def norm(text):
    return re.sub(r'[^a-z0-9]', '', text.lower())


def write_lines(page):
    y = 90
    for line in LINES:
        page.insert_text((72, y), line, fontsize=13, fontname='helv')
        y += 28


def build(directory):
    directory.mkdir(parents=True, exist_ok=True)
    doc = fitz.open()
    write_lines(doc.new_page(width=595, height=842))
    # Page 2: same content rasterised, so it has no text layer and must go through OCR.
    scratch = fitz.open()
    sp = scratch.new_page(width=595, height=842)
    write_lines(sp)
    pix = sp.get_pixmap(dpi=200)
    scan = doc.new_page(width=595, height=842)
    scan.insert_image(scan.rect, stream=pix.tobytes('png'))
    target = directory / 'fixture.pdf'
    doc.save(target)
    print(json.dumps({'fixture': str(target), 'pages': 2}))


def ocr(page, workdir):
    tesseract = shutil.which('tesseract')
    if not tesseract:
        return None
    png = workdir / f'p{page.number}.png'
    page.get_pixmap(dpi=300).save(png)
    result = subprocess.run([tesseract, str(png), 'stdout', '-l', 'eng'], capture_output=True, text=True, timeout=120)
    return result.stdout if result.returncode == 0 else None


def judge(text):
    """Return (leaked_labels, missing_controls) for one page's text."""
    flat = norm(text)
    leaked = sorted(label for label, probes in SECRETS.items() if any(p in flat for p in probes))
    missing = sorted(name for name, probe in CONTROLS.items() if probe not in flat)
    return leaked, missing


def verify(pdf):
    doc = fitz.open(pdf)
    pages = []
    with tempfile.TemporaryDirectory(prefix='pii-pdf-doctor-ocr-') as tmp:
        for page in doc:
            native = page.get_text()
            seen = ocr(page, Path(tmp))
            leaked, missing = judge(native + '\n' + (seen or ''))
            pages.append({
                'page': page.number + 1,
                'kind': 'native-text' if page.number == 0 else 'image-scan',
                'ocr_checked': seen is not None,
                'leaked': leaked,
                'missing_controls': missing,
                'ok': not leaked and not missing and seen is not None,
            })
    print(json.dumps({'pages': pages, 'ok': len(pages) == 2 and all(p['ok'] for p in pages)}))


if __name__ == '__main__':
    if len(sys.argv) != 3 or sys.argv[1] not in {'build', 'verify'}:
        sys.exit('usage: smoke_fixture.py build DIR | verify PDF')
    (build if sys.argv[1] == 'build' else verify)(Path(sys.argv[2]))
