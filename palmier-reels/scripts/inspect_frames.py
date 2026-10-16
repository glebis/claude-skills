"""Render composited frames from the active (or given) timeline into one strip for review.

python3 inspect_frames.py FRAME [FRAME ...] [--timeline ID] [--out strip.png]
Frames are 288x512 with a coordinate grid; frames past the end render black (white text tests need that).
"""
import argparse, os, subprocess, sys, tempfile
sys.path.insert(0, os.path.dirname(__file__))
from palmier import Palmier
ap = argparse.ArgumentParser(); ap.add_argument('frames', nargs='+', type=int); ap.add_argument('--timeline'); ap.add_argument('--out', default='strip.png')
a = ap.parse_args(); P = Palmier()
if a.timeline: P.call('set_active_timeline', {'timelineId': a.timeline})
d = tempfile.mkdtemp(); files = []
for f in a.frames: files += P.images('inspect_timeline', {'startFrame': f}, os.path.join(d, f'f{f:05d}'))
subprocess.run(['magick', *files, '+append', a.out], check=True); print(a.out)
