#!/usr/bin/env python3
"""
Academic Document Converter
Converts markdown to PDF/DOCX using Pandoc or MyST
"""

import os
import sys
import subprocess
from pathlib import Path

SKILL_DIR = Path(__file__).parent.parent


def check_pandoc():
    """Check if Pandoc is installed"""
    try:
        subprocess.run(['pandoc', '--version'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def check_myst():
    """Check if MyST CLI is installed"""
    try:
        subprocess.run(['myst', '--version'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def convert_pandoc(input_file, output_format='pdf', output_file=None):
    """Convert using Pandoc"""
    if not check_pandoc():
        print("ERROR: Pandoc not installed")
        print("Install: https://pandoc.org/installing.html")
        return False

    input_path = Path(input_file)
    if not input_path.exists():
        print(f"ERROR: File not found: {input_file}")
        return False

    # Determine output file
    if output_file is None:
        output_file = input_path.with_suffix(f'.{output_format}')

    # Build Pandoc command
    cmd = [
        'pandoc',
        str(input_path),
        '-o', str(output_file),
        '--number-sections',
        '--citeproc'
    ]

    # Format-specific options
    if output_format == 'pdf':
        cmd.extend([
            '--pdf-engine=xelatex',
            '-V', 'geometry:margin=1in'
        ])
    elif output_format == 'docx':
        cmd.append('--reference-doc=reference.docx') if Path('reference.docx').exists() else None

    print(f"Converting {input_file} to {output_format.upper()}...")
    print(f"Command: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ Created: {output_file}")
            return True
        else:
            print(f"ERROR: {result.stderr}")
            return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False


def convert_myst(input_file, output_format='pdf', output_file=None):
    """Convert using MyST"""
    if not check_myst():
        print("ERROR: MyST CLI not installed")
        print("Install: npm install -g myst-cli")
        return False

    input_path = Path(input_file)
    if not input_path.exists():
        print(f"ERROR: File not found: {input_file}")
        return False

    # MyST uses build command
    cmd = ['myst', 'build', str(input_path)]

    if output_format:
        cmd.extend(['--' + output_format])

    print(f"Converting {input_file} using MyST...")
    print(f"Command: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=input_path.parent)
        if result.returncode == 0:
            print(f"✓ Output in _build/exports/")
            return True
        else:
            print(f"ERROR: {result.stderr}")
            return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False


def main():
    """Main conversion workflow"""
    if len(sys.argv) < 2:
        print("Usage: python convert_academic.py <file.md> [format] [--myst]")
        print("  file.md : Input markdown file")
        print("  format  : Output format (pdf, docx, html) [default: pdf]")
        print("  --myst  : Use MyST instead of Pandoc")
        print("\nExamples:")
        print("  python convert_academic.py paper.md")
        print("  python convert_academic.py paper.md docx")
        print("  python convert_academic.py paper.md pdf --myst")
        sys.exit(1)

    input_file = sys.argv[1]
    output_format = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith('--') else 'pdf'
    use_myst = '--myst' in sys.argv

    if use_myst:
        success = convert_myst(input_file, output_format)
    else:
        success = convert_pandoc(input_file, output_format)

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
