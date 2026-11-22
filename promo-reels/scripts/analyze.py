#!/usr/bin/env python3
"""Look at the footage before cutting it.

    analyze.py scan VIDEO... --out WORK     probe + motion timeline + contact sheets
    analyze.py grab WORK TAG@SEC...         gridded frames to read crop centres (10% grid)

scan writes WORK/sources.json (tag → path, size, fps, VFR flag, duration, loudness),
WORK/motion.json (mean frame difference per 0.25 s, from real timestamps — phone
footage is often VFR) and WORK/sheet_<TAG>.jpg (a frame every 0.5 s with time and
motion burned in). Tags are A, B, C… in argument order.
Open and look at the sheet images: they are how you see the material.
"""
import argparse, json, pathlib, subprocess, string, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent)); import runlog  # noqa: E402
import cv2, numpy as np

WIN = 0.25


def probe(path):
    j = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', path],
                                  capture_output=True, text=True).stdout)
    v = next(s for s in j['streams'] if s['codec_type'] == 'video')
    rot = 0
    for sd in v.get('side_data_list', []):
        rot = int(sd.get('rotation', 0) or 0)
    w, h = int(v['width']), int(v['height'])
    if abs(rot) in (90, 270):
        w, h = h, w
    dur = float(j['format']['duration'])
    nb = int(v.get('nb_frames') or 0)
    num, den = map(int, v['r_frame_rate'].split('/'))
    rfps = num / den if den else 0
    real = nb / dur if nb else rfps
    has_audio = any(s['codec_type'] == 'audio' for s in j['streams'])
    loud = None
    if has_audio:
        r = subprocess.run(['ffmpeg', '-i', path, '-af', 'volumedetect', '-f', 'null', '-'], capture_output=True, text=True).stderr
        loud = {k: float(r.split(f'{k}: ')[1].split(' dB')[0]) for k in ('mean_volume', 'max_volume') if f'{k}: ' in r}
    return {'path': str(path), 'w': w, 'h': h, 'dur': round(dur, 3), 'fps_nominal': round(rfps, 2),
            'fps_real': round(real, 2), 'vfr': abs(real - rfps) > 1, 'vertical': h > w, 'audio': loud}


def motion(path):
    cap = cv2.VideoCapture(path); prev = None; pts = []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        t = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000
        g = cv2.cvtColor(cv2.resize(f, (90, 160)), cv2.COLOR_BGR2GRAY).astype(np.float32)
        if prev is not None:
            pts.append((t, float(np.mean(np.abs(g - prev)))))
        prev = g
    end = pts[-1][0] if pts else 0
    return [round(float(np.mean([v for t, v in pts if i * WIN <= t < (i + 1) * WIN] or [0])), 1) for i in range(int(end / WIN) + 1)]


def sheet(path, tag, bins, out, step=0.5, cols=9):
    cap = cv2.VideoCapture(path); tiles = []; nxt = 0.0
    while True:
        ok, f = cap.read()
        if not ok:
            break
        t = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000
        if t + 1e-3 >= nxt:
            h, w = f.shape[:2]; tw = 180; th = int(tw * h / w)
            im = cv2.resize(f, (tw, th)); b = bins[min(int(t / WIN), len(bins) - 1)] if bins else 0
            cv2.rectangle(im, (0, 0), (tw, 24), (0, 0, 0), -1)
            cv2.putText(im, f'{tag} {t:4.1f}s m{b}', (4, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
            tiles.append(im); nxt += step
    rows = -(-len(tiles) // cols)
    tiles += [np.zeros_like(tiles[0])] * (rows * cols - len(tiles))
    cv2.imwrite(str(out), np.vstack([np.hstack(tiles[r * cols:(r + 1) * cols]) for r in range(rows)]), [cv2.IMWRITE_JPEG_QUALITY, 80])


def scan(a):
    work = pathlib.Path(a.out); work.mkdir(parents=True, exist_ok=True)
    tags = list(string.ascii_uppercase)
    sources, mot = {}, {}
    for tag, v in zip(tags, a.videos):
        p = probe(v); sources[tag] = p
        mot[tag] = {'win': WIN, 'bins': motion(v)}
        sheet(v, tag, mot[tag]['bins'], work / f'sheet_{tag}.jpg')
        if p['vfr']:
            runlog.signal('scenario', 'video', 'variable frame rate source', file=pathlib.Path(v).name, fps_real=p['fps_real'])
        if p['h'] < p['w']:
            runlog.signal('scenario', 'video', 'landscape source in a vertical reel', file=pathlib.Path(v).name, size=f"{p['w']}x{p['h']}")
        top = sorted(range(len(mot[tag]['bins'])), key=lambda i: -mot[tag]['bins'][i])[:6]
        print(f"{tag} {pathlib.Path(v).name}: {p['w']}x{p['h']} {p['dur']}s fps {p['fps_real']}{' VFR' if p['vfr'] else ''}"
              f" audio {p['audio']}  | busiest at " + ', '.join(f'{i * WIN:.2f}s' for i in sorted(top)))
    (work / 'sources.json').write_text(json.dumps(sources, indent=1, ensure_ascii=False))
    (work / 'motion.json').write_text(json.dumps(mot))
    print(f'→ {work}/sheet_*.jpg  (read them)')


def grab(a):
    work = pathlib.Path(a.work); src = json.loads((work / 'sources.json').read_text()); tiles = []
    for spec in a.specs:
        tag, t = spec.split('@'); cap = cv2.VideoCapture(src[tag]['path']); cap.set(cv2.CAP_PROP_POS_MSEC, float(t) * 1000)
        ok, f = cap.read()
        if not ok:
            print('cannot read', spec); continue
        im = cv2.resize(f, (270, 480))
        for i in range(1, 10):
            cv2.line(im, (27 * i, 0), (27 * i, 480), (0, 255, 255), 1); cv2.line(im, (0, 48 * i), (270, 48 * i), (0, 255, 255), 1)
        cv2.putText(im, spec, (4, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 255), 2); tiles.append(im)
    out = work / f"grab_{'_'.join(s.replace('@', '') for s in a.specs)[:60]}.jpg"
    cv2.imwrite(str(out), np.hstack(tiles), [cv2.IMWRITE_JPEG_QUALITY, 85]); print('→', out)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); sp = ap.add_subparsers(dest='cmd', required=True)
    s = sp.add_parser('scan'); s.add_argument('videos', nargs='+'); s.add_argument('--out', required=True); s.set_defaults(fn=scan)
    g = sp.add_parser('grab'); g.add_argument('work'); g.add_argument('specs', nargs='+'); g.set_defaults(fn=grab)
    a = ap.parse_args(); runlog.init(); a.fn(a)
