"""Prepare art for Palmier: knock a white/paper background out to real alpha (un-multiply), optionally cut a sheet.

python3 art.py knockout in.png [more.png ...] --out DIR     # -> DIR/<name>-a.png
python3 art.py sheet sheet.png --grid 4x2 --out DIR         # -> DIR/tile-RC.png, then knockout them
Why: Palmier's blend modes preview but do not render in export; alpha is the only reliable way to drop paper boxes.
"""
import argparse, os
import numpy as np
from PIL import Image

def knockout(src, dst, pct=75, floor=0.05):
    c = np.asarray(Image.open(src).convert('RGB')).astype(float)
    ref = np.percentile(c.reshape(-1, 3), pct, axis=0); c = np.clip(c / ref * 255, 0, 255)   # paper -> pure white
    a = np.clip((255 - c).max(2) / 255, 0, 1); a = np.where(a < floor, 0, a)
    rgb = np.where(a[..., None] > 0, (c - 255 * (1 - a[..., None])) / np.maximum(a[..., None], 1e-3), 0)
    Image.fromarray(np.dstack([np.clip(rgb, 0, 255), a * 255]).astype(np.uint8)).save(dst)

ap = argparse.ArgumentParser(); ap.add_argument('mode', choices=['knockout', 'sheet']); ap.add_argument('files', nargs='+')
ap.add_argument('--out', required=True); ap.add_argument('--grid', default='4x2'); ap.add_argument('--size', type=int, default=1100)
a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
if a.mode == 'knockout':
    for f in a.files:
        d = os.path.join(a.out, os.path.splitext(os.path.basename(f))[0] + '-a.png'); knockout(f, d); print(d)
else:
    cols, rows = map(int, a.grid.split('x')); im = Image.open(a.files[0]).convert('RGB'); W, H = im.size
    for r in range(rows):
        for c in range(cols):
            t = im.crop((round(c * W / cols) + 6, round(r * H / rows) + 6, round((c + 1) * W / cols) - 6, round((r + 1) * H / rows) - 6)).resize((a.size, a.size), Image.LANCZOS)
            raw = os.path.join(a.out, f'tile-{r}{c}.png'); t.save(raw); knockout(raw, raw.replace('.png', '-a.png')); print(raw.replace('.png', '-a.png'))
