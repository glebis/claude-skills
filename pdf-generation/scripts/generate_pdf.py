#!/usr/bin/env python3
"""
Professional PDF generation script using Pandoc with Eisvogel template.
Supports both English and Russian documents with proper typography.
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
    fontsize: str = '11pt'
):
    """
    Generate PDF from markdown using Pandoc with Eisvogel template.
    
    Args:
        input_file: Path to input markdown file
        output_file: Path to output PDF file (auto-generated if not provided)
        theme: Document theme (white-paper, marketing, research, technical)
        russian: Use EB Garamond font for Russian text
        toc: Include table of contents
        toc_depth: Depth of table of contents
        margin: Page margin size
        fontsize: Base font size
    """
    input_path = Path(input_file)
    
    if not input_path.exists():
        print(f"Error: Input file '{input_file}' not found", file=sys.stderr)
        sys.exit(1)
    
    # Auto-generate output filename if not provided
    if output_file is None:
        output_file = input_path.with_suffix('.pdf')
    
    # Build pandoc command
    cmd = [
        'pandoc',
        str(input_file),
        '-o', str(output_file),
        '--pdf-engine=xelatex',
        '-V', f'geometry:margin={margin}',
        '-V', f'fontsize={fontsize}',
        '-V', 'documentclass=article',
    ]
    
    # Add table of contents
    if toc:
        cmd.extend(['--toc', f'--toc-depth={toc_depth}'])
    
    # Add Russian font support
    if russian:
        cmd.extend(['-V', 'mainfont=EB Garamond'])
    
    # Execute pandoc
    try:
        print(f"Generating PDF: {output_file}")
        print(f"Theme: {theme} ({THEMES.get(theme, 'custom')})")
        print(f"Russian font: {'Yes (EB Garamond)' if russian else 'No'}")
        
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        print(f"Success: PDF generated at {output_file}")
        return 0
        
    except subprocess.CalledProcessError as e:
        print(f"Error generating PDF:", file=sys.stderr)
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
    parser.add_argument('-r', '--russian', action='store_true', help='Use EB Garamond')
    parser.add_argument('--no-toc', action='store_true', help='Disable TOC')
    parser.add_argument('--toc-depth', type=int, default=2, help='TOC depth')
    parser.add_argument('--margin', default='2.5cm', help='Page margin')
    parser.add_argument('--fontsize', default='11pt', help='Font size')
    
    args = parser.parse_args()
    
    return generate_pdf(
        input_file=args.input,
        output_file=args.output,
        theme=args.theme,
        russian=args.russian,
        toc=not args.no_toc,
        toc_depth=args.toc_depth,
        margin=args.margin,
        fontsize=args.fontsize
    )

if __name__ == '__main__':
    sys.exit(main())
