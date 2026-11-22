#!/usr/bin/env python3
"""Fill shot durations from a music grid, so every cut lands on a beat.

    grid.py EDL.json --bpm 101 [--out EDL_grid.json]
    grid.py EDL.json --beats track.beats.json [--offset 12.4] [--out ...]

Each shot needs "beats": N (whole beats it lasts). With --bpm the grid is fixed
(use for licensed tracks you can't embed: the user adds them in Instagram).
With --beats the cuts snap to the detected beats of a real file starting at --offset
(the music time where the reel starts; it should be a downbeat), which follows tempo
drift in live recordings. Writes "dur" per shot plus "music" info.
"""
import argparse, json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent)); import runlog  # noqa: E402
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument('edl'); ap.add_argument('--bpm', type=float); ap.add_argument('--beats')
ap.add_argument('--offset', type=float, default=0.0); ap.add_argument('--out')
a = ap.parse_args()
runlog.init(pathlib.Path(a.edl).resolve().parent)
edl = json.loads(pathlib.Path(a.edl).read_text())
need = sum(s.get('beats', 0) for s in edl['shots'])
if any('beats' not in s for s in edl['shots']):
    sys.exit('every shot needs "beats"')

if a.bpm:
    period = 60 / a.bpm
    times = [k * period for k in range(need + 1)]
    edl['music'] = {**edl.get('music', {}), 'bpm': a.bpm, 'grid': 'fixed'}
elif a.beats:
    b = json.loads(pathlib.Path(a.beats).read_text())
    bt = np.array(b['beats']); bt = bt[bt >= a.offset - 0.05]
    if not len(bt):
        sys.exit('no beats after offset')
    period = float(np.median(np.diff(bt))) if len(bt) > 1 else b['beat_period']
    if len(bt) < need + 1:
        runlog.signal('warning', 'pacing', 'beat grid extrapolated past the detected beats', detected=len(bt), needed=need + 1)
    while len(bt) < need + 1:                       # extrapolate past the end of the detection
        bt = np.append(bt, bt[-1] + period)
    times = list(bt[:need + 1] - bt[0])
    edl['music'] = {**edl.get('music', {}), 'beats_file': a.beats, 'offset': round(float(bt[0]), 3),
                    'bpm': b['tempo'], 'grid': 'detected'}
else:
    sys.exit('give --bpm or --beats')

k = 0
for s in edl['shots']:
    s['dur'] = round(times[k + s['beats']] - times[k], 4); k += s['beats']
out = pathlib.Path(a.out) if a.out else pathlib.Path(a.edl)
out.write_text(json.dumps(edl, indent=1, ensure_ascii=False))
t = 0
for s in edl['shots']:
    print(f"{t:7.3f}s +{s['beats']}b {s['dur']:6.3f}s  {s.get('note', '')}"); t += s['dur']
print(f'total {t:.3f}s, {need} beats → {out}')
