"""Nest a finished reel timeline into a master with film gate weave (optional projector flicker).

python3 jitter.py CHILD_TIMELINE_ID [--name "… — master"] [--flicker] [--amount 1.0]
Edits to the child flow through to the master (live nested clip). Flicker animates opacity of everything;
skip it when the style/brand forbids animating artwork opacity.
"""
import argparse, json, math, os, random, sys
sys.path.insert(0, os.path.dirname(__file__))
from palmier import Palmier
ap = argparse.ArgumentParser(); ap.add_argument('child'); ap.add_argument('--name'); ap.add_argument('--flicker', action='store_true')
ap.add_argument('--amount', type=float, default=1.0); ap.add_argument('--seed', type=int, default=1963)
a = ap.parse_args(); P = Palmier()
P.call('set_active_timeline', {'timelineId': a.child}); child = P.timeline(); N = child['totalFrames']
P.call('create_timeline', {'name': a.name or f"{child['name']} — master (film)"})
P.call('add_clips', {'entries': [{'mediaRef': a.child, 'startFrame': 0}]})
tl = P.timeline(); cid = [c for t in tl['tracks'] if t['type'] == 'video' for c in t['clips']][0]['id']
rnd = random.Random(a.seed); m = a.amount; S = 1 + 0.016 * m; base = -(S - 1) / 2
pos, op = [], []
for f in range(0, N, 2):
    t = f / 30
    wx = m * (0.0011 * math.sin(t * 1.7) + 0.0006 * math.sin(t * 4.3 + 1)) + rnd.uniform(-0.0007, 0.0007) * m
    wy = m * (0.0016 * math.sin(t * 1.3 + 2) + 0.0007 * math.sin(t * 5.1)) + rnd.uniform(-0.0009, 0.0009) * m
    pos.append([f, round(base + wx, 5), round(base + wy, 5), 'hold'])
    o = rnd.uniform(0.965, 1.0) if rnd.random() > 0.04 else rnd.uniform(0.92, 0.95); op.append([f, round(o, 3), 'hold'])
P.call('set_keyframes', {'clipId': cid, 'property': 'scale', 'keyframes': [[0, S, S, 'linear']]})
P.call('set_keyframes', {'clipId': cid, 'property': 'position', 'keyframes': pos})
P.call('set_keyframes', {'clipId': cid, 'property': 'rotation', 'keyframes': [[f, round(0.12 * m * math.sin(f / 30 * 0.9) + rnd.uniform(-0.03, 0.03) * m, 3), 'smooth'] for f in range(0, N, 15)]})
if a.flicker: P.call('set_keyframes', {'clipId': cid, 'property': 'opacity', 'keyframes': op})
print(json.dumps({'master_timeline_id': P.timeline()['id'], 'child': a.child}))
