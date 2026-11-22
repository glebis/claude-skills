#!/usr/bin/env python3
"""Check a rendered reel against its EDL.

    verify.py EDL.json REEL.mp4 [--sheet out.jpg]

- contact sheet: the middle frame of every shot, numbered → read it (framing, subject in frame)
- blur: variance of Laplacian per shot middle frame; low = motion smear or soft crop
- cuts: detected hard cuts vs the EDL's cut points (skip with dissolves)
- format: size, fps, duration, audio
Exit 1 if a cut is off by more than one frame or the duration is wrong.
"""
import argparse, json, pathlib, subprocess, sys
import cv2, numpy as np
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent)); import runlog  # noqa: E402

ap = argparse.ArgumentParser(); ap.add_argument('edl'); ap.add_argument('reel'); ap.add_argument('--sheet')
a = ap.parse_args()
edl = json.loads(pathlib.Path(a.edl).read_text()); shots = edl['shots']; fps = edl.get('fps', 30)
runlog.init(pathlib.Path(a.edl).resolve().parent)
blurred = []
cap = cv2.VideoCapture(a.reel)
W, H = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
frames = []; prev = None; diffs = []
while True:
    ok, f = cap.read()
    if not ok:
        break
    frames.append(cv2.resize(f, (180, 320)))
    g = cv2.cvtColor(cv2.resize(f, (54, 96)), cv2.COLOR_BGR2GRAY).astype(np.float32)
    diffs.append(0 if prev is None else float(np.mean(np.abs(g - prev)))); prev = g
n = len(frames); D = n / fps; expect = sum(s['dur'] for s in shots)
bad = 0
print(f'{W}x{H}, {n} frames = {D:.3f}s (EDL {expect:.3f}s)')
if W != 1080 or H != 1920 or abs(D - expect) > 1.5 / fps:
    print('✗ size or duration mismatch'); bad += 1
    runlog.signal('error', 'video', 'size or duration mismatch', size=f'{W}x{H}', dur=round(D, 3), expected=round(expect, 3))

tiles, t = [], 0.0
for i, s in enumerate(shots, 1):
    mid = min(n - 1, int((t + s['dur'] / 2) * fps)); im = frames[mid].copy()
    sharp = cv2.Laplacian(cv2.cvtColor(im, cv2.COLOR_BGR2GRAY), cv2.CV_64F).var()
    flag = 'slide' if 'slide' in s else ('BLUR?' if sharp < 60 else '')
    cv2.rectangle(im, (0, 0), (180, 22), (0, 0, 0), -1)
    cv2.putText(im, f"{i:02d} {s['dur']:.2f}s {flag}", (4, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1)
    tiles.append(im)
    if flag == 'BLUR?':
        print(f"  shot {i:02d} ({s.get('note', '')}): low sharpness {sharp:.0f} — check for smear, consider another moment")
        blurred.append({'shot': i, 'src': s.get('src'), 'in': s.get('in'), 'zoom': s.get('zoom'), 'sharp': round(sharp), 'note': s.get('note', '')})
    t += s['dur']
cols = min(11, len(tiles)); tiles += [np.zeros_like(tiles[0])] * (-len(tiles) % cols)
sheet = a.sheet or str(pathlib.Path(a.reel).with_suffix('.check.jpg'))
cv2.imwrite(sheet, np.vstack([np.hstack(tiles[r * cols:(r + 1) * cols]) for r in range(len(tiles) // cols)]), [cv2.IMWRITE_JPEG_QUALITY, 85])
print('sheet →', sheet)

if not edl.get('xfade'):
    thr = max(15, np.percentile(diffs, 95))
    cuts = [i / fps for i, v in enumerate(diffs) if v > thr]
    expected = np.cumsum([s['dur'] for s in shots])[:-1]
    worst = 0
    for x in expected:
        near = min(cuts, key=lambda c: abs(c - x)) if cuts else None
        err = abs(near - x) if near is not None else 9
        worst = max(worst, err)
        if err > 1.01 / fps:
            print(f'✗ cut at {x:.3f}s found at {near}'); bad += 1
            runlog.signal('error', 'video', 'cut off the EDL', at=round(float(x), 3), found=near)
    print(f'cuts: {len(expected)} expected, worst error {worst * 1000:.0f} ms')
a_ok = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'a', '-show_entries', 'stream=codec_name', '-of', 'csv=p=0', a.reel],
                      capture_output=True, text=True).stdout.strip()
print('audio:', a_ok or 'none')
if blurred:
    runlog.signal('warning', 'video', 'low-sharpness shots', shots=blurred)
runlog._write('verify', edl=pathlib.Path(a.edl).name, sheet=sheet, frames=n, bad=bad, blur_flags=len(blurred), audio=a_ok or None)
print('LOOK at the sheet now: subjects leaving frame, empty frames and smear the numbers miss are hand fixes — '
      'and every hand fix is a lesson for reflect.py.')
runlog.remind()
sys.exit(1 if bad else 0)
