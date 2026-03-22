#!/usr/bin/env python3
"""
Vault Scanner for Temple Generator.

Scans an Obsidian vault, extracts files/links/tags, builds a link graph,
computes degree centrality, detects clusters, and outputs vault-scan.json.

Usage: python3 extract_entities.py <vault_path> [--output vault-scan.json]
"""

import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path


SKIP_DIRS = {
    '.obsidian', '.git', '.claude', '.trash', 'node_modules',
    '.DS_Store', 'Templates', 'Attachments', 'assets'
}

SKIP_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.svg', '.pdf', '.mp3',
                   '.mp4', '.wav', '.ogg', '.zip', '.html', '.css', '.js',
                   '.json', '.py', '.pkl', '.lock'}


def parse_frontmatter(lines):
    """Extract YAML frontmatter as a dict of strings."""
    fm = {}
    if not lines or lines[0].strip() != '---':
        return fm
    for line in lines[1:]:
        if line.strip() == '---':
            break
        if ':' in line:
            key, _, val = line.partition(':')
            fm[key.strip()] = val.strip().strip("'\"")
    return fm


def extract_wikilinks(text):
    """Extract [[wikilink]] targets, ignoring display text after |."""
    return [m.split('|')[0].strip() for m in re.findall(r'\[\[([^\]]+)\]\]', text)]


def extract_tags(text):
    """Extract #tags from text (not inside code blocks)."""
    return re.findall(r'(?<!\S)#([a-zA-Z][\w/-]*)', text)


def scan_vault(vault_path):
    """Walk the vault and collect file metadata."""
    vault = Path(vault_path).resolve()
    files = {}
    all_links = defaultdict(list)  # source -> [targets]

    for root, dirs, filenames in os.walk(vault):
        # Skip hidden/system dirs
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith('.')]

        rel_root = Path(root).relative_to(vault)

        for fname in filenames:
            fpath = Path(root) / fname
            if fpath.suffix.lower() in SKIP_EXTENSIONS:
                continue
            if fpath.suffix.lower() != '.md':
                continue

            rel_path = str(rel_root / fname)
            try:
                text = fpath.read_text(encoding='utf-8', errors='replace')
            except Exception:
                continue

            lines = text.split('\n')
            fm = parse_frontmatter(lines)
            links = extract_wikilinks(text)
            tags = extract_tags(text)
            word_count = len(text.split())

            # Title: frontmatter title > first H1 > filename
            title = fm.get('title', '')
            if not title:
                for line in lines:
                    if line.startswith('# ') and not line.startswith('## '):
                        title = line[2:].strip()
                        break
            if not title:
                title = fpath.stem

            # Clean title of quotes
            title = title.strip('"\'')

            folder = str(rel_root) if str(rel_root) != '.' else ''
            stem = fpath.stem

            files[stem] = {
                'path': rel_path,
                'title': title,
                'stem': stem,
                'folder': folder,
                'tags': tags[:20],  # cap tags
                'links': links[:50],  # cap links
                'wordCount': word_count,
                'frontmatter': {k: v for k, v in list(fm.items())[:10]},
            }
            all_links[stem] = links

    return files, all_links


def build_graph(files, all_links):
    """Build adjacency list and compute backlinks."""
    # Normalize link targets to stems
    stem_set = set(files.keys())
    # Also build a lowercase lookup for fuzzy matching
    lower_to_stem = {}
    for s in stem_set:
        lower_to_stem[s.lower()] = s

    edges = []
    backlinks = defaultdict(int)

    for source, targets in all_links.items():
        seen = set()
        for t in targets:
            # Resolve target to a known stem
            t_clean = t.split('#')[0].split('|')[0].strip()
            resolved = None
            if t_clean in stem_set:
                resolved = t_clean
            elif t_clean.lower() in lower_to_stem:
                resolved = lower_to_stem[t_clean.lower()]

            if resolved and resolved != source and resolved not in seen:
                edges.append([source, resolved])
                backlinks[resolved] += 1
                seen.add(resolved)

    # Add backlink counts to files
    for stem, count in backlinks.items():
        if stem in files:
            files[stem]['backlinks'] = count

    # Ensure all files have backlinks field
    for stem in files:
        if 'backlinks' not in files[stem]:
            files[stem]['backlinks'] = 0

    return edges


def compute_centrality(files, edges):
    """Compute degree centrality (in + out links)."""
    degree = defaultdict(int)
    for a, b in edges:
        degree[a] += 1
        degree[b] += 1

    max_degree = max(degree.values()) if degree else 1
    centrality = {}
    for stem in files:
        d = degree.get(stem, 0)
        centrality[stem] = round(d / max_degree, 4)
        files[stem]['centrality'] = centrality[stem]
        files[stem]['degree'] = d

    return centrality


def detect_clusters(files, edges, min_cluster_size=3):
    """Simple connected-component clustering with folder hints."""
    # Build adjacency for connected components
    adj = defaultdict(set)
    for a, b in edges:
        adj[a].add(b)
        adj[b].add(a)

    visited = set()
    clusters = []

    def bfs(start):
        queue = [start]
        component = set()
        while queue:
            node = queue.pop(0)
            if node in visited:
                continue
            visited.add(node)
            component.add(node)
            for neighbor in adj[node]:
                if neighbor not in visited:
                    queue.append(neighbor)
        return component

    for stem in files:
        if stem not in visited:
            component = bfs(stem)
            if len(component) >= min_cluster_size:
                clusters.append(sorted(component))

    # Sort clusters by size (largest first)
    clusters.sort(key=len, reverse=True)

    # Also add folder-based clusters
    folder_clusters = defaultdict(list)
    for stem, info in files.items():
        if info['folder']:
            folder_clusters[info['folder']].append(stem)

    folder_groups = []
    for folder, members in folder_clusters.items():
        if len(members) >= min_cluster_size:
            folder_groups.append({
                'type': 'folder',
                'name': folder,
                'members': sorted(members)
            })

    return {
        'connected': [{'type': 'connected', 'members': c} for c in clusters[:20]],
        'folders': folder_groups[:15]
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 extract_entities.py <vault_path> [--output file.json]")
        sys.exit(1)

    vault_path = sys.argv[1]
    output_path = 'vault-scan.json'

    if '--output' in sys.argv:
        idx = sys.argv.index('--output')
        if idx + 1 < len(sys.argv):
            output_path = sys.argv[idx + 1]

    if not os.path.isdir(vault_path):
        print(f"Error: {vault_path} is not a directory")
        sys.exit(1)

    print(f"Scanning vault: {vault_path}")
    files, all_links = scan_vault(vault_path)
    print(f"  Found {len(files)} markdown files")

    edges = build_graph(files, all_links)
    print(f"  Found {len(edges)} link edges")

    centrality = compute_centrality(files, edges)

    # Top nodes by centrality
    top_nodes = sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:30]
    print(f"  Top 10 by centrality:")
    for stem, c in top_nodes[:10]:
        title = files[stem]['title']
        degree = files[stem]['degree']
        print(f"    {c:.3f}  ({degree:3d} links)  {title}")

    clusters = detect_clusters(files, edges)
    print(f"  Found {len(clusters['connected'])} connected clusters, {len(clusters['folders'])} folder clusters")

    # Build output
    # Sort files by centrality for the output
    sorted_files = sorted(files.values(), key=lambda f: f.get('centrality', 0), reverse=True)

    result = {
        'vaultPath': str(Path(vault_path).resolve()),
        'totalFiles': len(files),
        'totalEdges': len(edges),
        'files': sorted_files[:200],  # cap at 200 most central
        'edges': edges[:500],  # cap edges
        'clusters': clusters,
        'topNodes': [{'stem': s, 'centrality': c, 'title': files[s]['title']} for s, c in top_nodes],
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\nOutput written to: {output_path}")
    print(f"  {len(sorted_files[:200])} files, {len(edges[:500])} edges")


if __name__ == '__main__':
    main()
