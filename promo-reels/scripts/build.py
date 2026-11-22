#!/usr/bin/env python3
"""Render a 1080x1920 Reel from an EDL.

    build.py EDL.json [--out DIR] [--name NAME]

Paths in the EDL are relative to the EDL file. Output: DIR/NAME.mp4 (video + silent
stereo track; music is added by mix.py) and DIR/NAME/shots/NN.mp4 (one file per shot,
for hand-finishing in Edits/CapCut).

EDL:
{ "sources": {"A": "clip.mov", ...}, "fps": 30,
  "xfade": 0,            # dissolve length in s (0 = hard cuts)
  "move_amount": 0.06,   # push-in/out per shot
  "style": "style.json", # optional: preset name or style file → motion.footage_move, motion.slide_move
                         # (0 = static slides) and grade.contrast/saturation; explicit EDL keys win
  "shots": [
    {"slide": "slides/hook.png", "dur": 1.8},
    {"src": "A", "in": 7.2, "dur": 1.0, "zoom": 1.4, "c": [0.42, 0.36], "move": "in|out|none",
     "caption": "slides/cap_what.png", "note": "..."},
    ...]}
zoom 1.0 = full frame; c = crop centre as fractions of the source frame. Durations
come from you (free pacing) or from grid.py (music grid).
"""
import argparse, json, pathlib, subprocess, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent)); import runlog, tokens  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument('edl'); ap.add_argument('--out'); ap.add_argument('--name')
a = ap.parse_args()
edl_path = pathlib.Path(a.edl).resolve(); base = edl_path.parent
edl = json.loads(edl_path.read_text())
runlog.init(base)
name = a.name or edl_path.stem
out_root = pathlib.Path(a.out).resolve() if a.out else base / 'out'
FPS, W, H = edl.get('fps', 30), 1080, 1920
STYLE = {}
if edl.get('style'):
    sp = base / edl['style']
    STYLE = tokens.load(str(sp) if sp.is_file() else edl['style'])
MOVE = edl.get('move_amount', STYLE.get('motion', {}).get('footage_move', 0.06))
SLIDE_MOVE = edl.get('slide_move', STYLE.get('motion', {}).get('slide_move', 0.03))
GRADE = {'contrast': 1.06, 'saturation': 0.92, **STYLE.get('grade', {}), **edl.get('grade', {})}
X = edl.get('xfade', 0.0)
shot_dir = out_root / name / 'shots'; shot_dir.mkdir(parents=True, exist_ok=True)
ENC = ['-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', '-r', str(FPS)]


def P(rel):
    p = pathlib.Path(rel)
    return str(p if p.is_absolute() else base / p)


def run(args):
    r = subprocess.run(['ffmpeg', '-v', 'error', '-y', *args], capture_output=True, text=True)
    if r.returncode:
        runlog.signal('error', 'video', 'ffmpeg failed', stderr=r.stderr[-400:])
        sys.exit(f'ffmpeg failed: {r.stderr[-800:]}')


def footage(s, path, dur):
    n = round(dur * FPS)
    z0 = s.get('zoom', 1.0); mv = s.get('move', 'in')
    z1 = z0 * (1 + MOVE) if mv == 'in' else z0 / (1 + MOVE) if mv == 'out' else z0
    z1 = max(1.0, z1); cx, cy = s.get('c', [0.5, 0.5])
    # Fill 9:16 first (centre-crop non-vertical sources), then zoompan on a 2x canvas:
    # integer crop offsets jitter less at higher resolution.
    z = f"{z0}+({z1}-{z0})*on/{max(n - 1, 1)}"
    x = f"max(0,min(iw-iw/zoom,{cx}*iw-iw/zoom/2))"
    y = f"max(0,min(ih-ih/zoom,{cy}*ih-ih/zoom/2))"
    vf = (f"fps={FPS},scale=2160:3840:force_original_aspect_ratio=increase:flags=lanczos,crop=2160:3840,"
          f"zoompan=z='{z}':x='{x}':y='{y}':d=1:s={W}x{H}:fps={FPS},"
          f"eq=contrast={GRADE['contrast']}:saturation={GRADE['saturation']},unsharp=5:5:0.6,setsar=1")
    args = ['-ss', str(s['in']), '-t', f"{dur + 0.2}", '-i', P(edl['sources'][s['src']])]
    if s.get('caption'):
        args += ['-i', P(s['caption'])]
        args += ['-filter_complex', f"[0:v]{vf}[v];[1:v]format=rgba[c];[v][c]overlay=0:0:format=auto[o]", '-map', '[o]']
    else:
        args += ['-map', '0:v', '-vf', vf]
    run([*args, '-frames:v', str(n), '-an', *ENC, str(path)])


def slide(s, path, dur):
    n = round(dur * FPS)
    vf = (f"scale=2160:3840,zoompan=z='1+{SLIDE_MOVE}*on/{n}':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d={n}:s={W}x{H}:fps={FPS},setsar=1")
    run(['-loop', '1', '-i', P(s['slide']), '-vf', vf, '-frames:v', str(n), '-an', *ENC, str(path)])


shots = edl['shots']
missing = [i for i, s in enumerate(shots, 1) if 'dur' not in s]
if missing:
    sys.exit(f'shots {missing} have no "dur" — set it, or run grid.py for a music grid')
paths, t0 = [], 0.0
for i, s in enumerate(shots, 1):
    # Snap the cumulative timeline to frames, not each shot: a beat (e.g. 0.594 s) is not a
    # whole number of frames and per-shot rounding drifts off the grid.
    t1 = t0 + s['dur']; on_screen = (round(t1 * FPS) - round(t0 * FPS)) / FPS; t0 = t1
    dur = on_screen + (X if X and i < len(shots) else 0)   # dissolves keep cut points: total = sum(dur)
    p = shot_dir / f"{i:02d}.mp4"
    (slide if 'slide' in s else footage)(s, p, dur)
    paths.append(p); print(f"{i:02d} {s['dur']:5.2f}s {s.get('note', '')}", flush=True)

total = sum(s['dur'] for s in shots)
video = out_root / name / 'video.mp4'
if X:
    inputs = sum((['-i', str(p)] for p in paths), [])
    chain, prev, t = [], '[0:v]', 0.0
    for k in range(1, len(paths)):
        t += shots[k - 1]['dur']
        chain.append(f"{prev}[{k}:v]xfade=transition=fade:duration={X}:offset={t:.3f}[v{k}]"); prev = f'[v{k}]'
    run([*inputs, '-filter_complex', ';'.join(chain), '-map', prev, *ENC, str(video)])
else:
    lst = out_root / name / 'concat.txt'
    lst.write_text(''.join(f"file '{p}'\n" for p in paths))
    run(['-f', 'concat', '-safe', '0', '-i', str(lst), '-c', 'copy', str(video)])

final = out_root / f'{name}.mp4'
run(['-i', str(video), '-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=stereo', '-map', '0:v', '-map', '1:a',
     '-c:v', 'copy', '-c:a', 'aac', '-ar', '48000', '-ac', '2', '-shortest', '-movflags', '+faststart', str(final)])
cuts = len(shots) - 1
print(f"→ {final}  {total:.2f}s, {cuts} cuts ({cuts / total * 60:.0f}/min), xfade {X}s")
# snapshot of the shot list: reflect.py diffs consecutive builds to find hand fixes (moved in-points, reframes)
runlog._write('build', edl=edl_path.name, name=name, total=round(total, 3), cuts=cuts, xfade=X,
              shots=[{k: s.get(k) for k in ('slide', 'src', 'in', 'dur', 'beats', 'zoom', 'c', 'move', 'caption', 'note') if k in s} for s in shots])
print('next: verify.py ' + edl_path.name + f' out/{name}.mp4')
