#!/usr/bin/env python3
"""
Fix common markdown formatting issues for better PDF rendering.
Ensures proper spacing before lists and handles nested lists correctly.
"""

import re
import sys
from pathlib import Path

def fix_markdown_lists(content):
    """Add blank lines before lists that don't have them."""
    lines = content.split('\n')
    fixed_lines = []
    
    for i, line in enumerate(lines):
        # Check if this is a list item (numbered or bullet)
        is_list = re.match(r'^(\s*)([-*+]|\d+\.)\s', line)
        
        if is_list:
            indent = len(is_list.group(1))
            prev_line = lines[i-1] if i > 0 else ''
            
            # Check if previous line is not blank and not a list item
            prev_is_list = re.match(r'^(\s*)([-*+]|\d+\.)\s', prev_line)
            
            # Add blank line if needed (not indented nested list)
            if prev_line.strip() and not prev_is_list and indent == 0:
                if not (i > 0 and not lines[i-1].strip()):
                    fixed_lines.append('')
        
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)

def main():
    if len(sys.argv) < 2:
        print("Usage: fix_markdown.py <input.md> [output.md]", file=sys.stderr)
        sys.exit(1)
    
    input_file = Path(sys.argv[1])
    output_file = Path(sys.argv[2]) if len(sys.argv) > 2 else input_file
    
    if not input_file.exists():
        print(f"Error: {input_file} not found", file=sys.stderr)
        sys.exit(1)
    
    content = input_file.read_text()
    fixed_content = fix_markdown_lists(content)
    output_file.write_text(fixed_content)
    
    print(f"Fixed markdown formatting: {output_file}")

if __name__ == '__main__':
    main()
