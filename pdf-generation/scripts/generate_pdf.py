#!/usr/bin/env python3
"""
Professional PDF generation script using Pandoc with Eisvogel template.
Supports both English and Russian documents with proper typography.
Includes mobile-friendly layout option for phone/tablet reading.
"""

import argparse
import subprocess
import sys
from pathlib import Path

# Color themes for different document types
THEMES = {
    'white-paper': '1e3a8a',     # Blue
    'marketing': '059669',        # Green
    'research': '7c3aed',         # Purple
    'technical': '374151',        # Gray
}

def generate_pdf(
    input_file: str,
    output_file: str = None,
    theme: str = 'white-paper',
    russian: bool = False,
    toc: bool = True,
    toc_depth: int = 2,
    margin: str = '2.5cm',
    fontsize: str = '11pt',
    mobile: bool = False
):
    """
    Generate PDF from markdown using Pandoc.

    Args:
        input_file: Path to input markdown file
        output_file: Path to output PDF file (auto-generated if not provided)
        theme: Document theme (white-paper, marketing, research, technical)
        russian: Use EB Garamond font for Russian text
        toc: Include table of contents
        toc_depth: Depth of table of contents
        margin: Page margin size
        fontsize: Base font size
        mobile: Generate mobile-optimized PDF (6x9in, smaller margins, 10pt font)
    """
    input_path = Path(input_file)

    if not input_path.exists():
        print(f"Error: Input file '{input_file}' not found", file=sys.stderr)
        sys.exit(1)

    # Auto-generate output filename if not provided
    if output_file is None:
        if mobile:
            output_file = input_path.stem + '-mobile.pdf'
        else:
            output_file = str(input_path.with_suffix('.pdf'))

    # Override settings for mobile layout
    if mobile:
        margin = '0.5in'
        fontsize = '10pt'

    # Build pandoc command
    cmd = [
        'pandoc',
        str(input_file),
        '-o', str(output_file),
        '--pdf-engine=xelatex',
        '-V', f'geometry:margin={margin}',
        '-V', f'fontsize={fontsize}',
        '-V', 'documentclass=article',
        '-V', 'colorlinks=true',
        '-V', 'linkcolor=blue',
        '-V', 'urlcolor=blue',
    ]

    # Add mobile-specific geometry
    if mobile:
        cmd.extend([
            '-V', 'geometry:paperwidth=6in',
            '-V', 'geometry:paperheight=9in',
            '-V', 'linestretch=1.2'
        ])

    # Add table of contents
    if toc:
        cmd.extend(['--toc', f'--toc-depth={toc_depth}'])

    # Add Russian font support
    if russian:
        cmd.extend(['-V', 'mainfont=EB Garamond'])

    # Execute pandoc
    try:
        layout_type = "Mobile (6x9in)" if mobile else "Desktop (Letter)"
        print(f"Generating PDF: {output_file}")
        print(f"Layout: {layout_type}")
        print(f"Theme: {theme} ({THEMES.get(theme, 'custom')})")
        print(f"Russian font: {'Yes (EB Garamond)' if russian else 'No'}")

        result = subprocess.run(cmd, check=True, capture_output=True, text=True)

        print(f"✅ Success: PDF generated at {output_file}")
        return 0

    except subprocess.CalledProcessError as e:
        print(f"❌ Error generating PDF:", file=sys.stderr)
        print(e.stderr, file=sys.stderr)
        return 1
    except FileNotFoundError:
        print("Error: pandoc not found. Install with: brew install pandoc", file=sys.stderr)
        return 1

def main():
    parser = argparse.ArgumentParser(
        description='Generate professional PDFs from markdown'
    )
    parser.add_argument('input', help='Input markdown file')
    parser.add_argument('-o', '--output', help='Output PDF file')
    parser.add_argument(
        '-t', '--theme',
        choices=list(THEMES.keys()),
        default='white-paper',
        help='Document theme'
    )
    parser.add_argument('-r', '--russian', action='store_true', help='Use EB Garamond for Russian')
    parser.add_argument('-m', '--mobile', action='store_true', help='Generate mobile-friendly layout (6x9in, 10pt)')
    parser.add_argument('--no-toc', action='store_true', help='Disable table of contents')
    parser.add_argument('--toc-depth', type=int, default=2, help='TOC depth (default: 2)')
    parser.add_argument('--margin', default='2.5cm', help='Page margin (overridden by --mobile)')
    parser.add_argument('--fontsize', default='11pt', help='Font size (overridden by --mobile)')

    args = parser.parse_args()

    return generate_pdf(
        input_file=args.input,
        output_file=args.output,
        theme=args.theme,
        russian=args.russian,
        toc=not args.no_toc,
        toc_depth=args.toc_depth,
        margin=args.margin,
        fontsize=args.fontsize,
        mobile=args.mobile
    )

if __name__ == '__main__':
    sys.exit(main())
