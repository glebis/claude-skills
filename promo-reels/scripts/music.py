#!/usr/bin/env python3
"""Generate an instrumental cue with ElevenLabs Music, check its key, optionally transpose.

    music.py "PROMPT" --seconds 23 --out music_x.mp3 [--key "D minor"] [--takes 2]

Needs ELEVENLABS_API_KEY in the environment. The model does NOT reliably follow a
requested key (3 of 3 takes missed in testing), so with --key each take is analysed and,
if its mode matches, pitch-shifted (tempo kept) to the requested tonic → *_<Key>.wav.
Takes in the wrong mode are reported, not "fixed".
"""
import argparse, json, os, pathlib, sys, urllib.request, urllib.error, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, str(pathlib.Path(__file__).parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent)); import runlog  # noqa: E402
from beats import analyse, NAMES

ap = argparse.ArgumentParser()
ap.add_argument('prompt'); ap.add_argument('--seconds', type=float, required=True)
ap.add_argument('--out', required=True); ap.add_argument('--key'); ap.add_argument('--takes', type=int, default=1)
a = ap.parse_args()
runlog.init()
key = os.environ.get('ELEVENLABS_API_KEY') or sys.exit('ELEVENLABS_API_KEY not set')
out = pathlib.Path(a.out)

for n in range(1, a.takes + 1):
    dst = out if a.takes == 1 else out.with_name(f'{out.stem}_{n}{out.suffix}')
    body = {'prompt': a.prompt, 'music_length_ms': int(a.seconds * 1000), 'model_id': 'music_v1', 'force_instrumental': True}
    req = urllib.request.Request('https://api.elevenlabs.io/v1/music?output_format=mp3_44100_192', data=json.dumps(body).encode(),
                                 headers={'xi-api-key': key, 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            dst.write_bytes(r.read())
    except urllib.error.HTTPError as e:
        body_ = e.read()[:300]; print(f'take {n}: HTTP {e.code} {body_}')
        runlog.signal('error', 'music', f'music API HTTP {e.code}', body=str(body_)); continue
    r = analyse(dst); k = r['key'][0]
    print(f"{dst.name}: {r['duration']}s, {r['tempo']} BPM, key {k['tonic']} {k['mode']} ({k['score']})")
    if not a.key:
        continue
    want_t, want_m = a.key.split()[0], a.key.split()[1].lower()
    if k['mode'] != want_m:
        print(f'  ✗ mode is {k["mode"]}, wanted {want_m}: not transposing — regenerate or pick another take')
        runlog.signal('warning', 'music', 'generated take in the wrong mode', got=f"{k['tonic']} {k['mode']}", wanted=a.key, prompt=a.prompt[:200]); continue
    shift = (NAMES.index(want_t) - NAMES.index(k['tonic'])) % 12
    shift = shift - 12 if shift > 6 else shift
    if shift:
        runlog.signal('fix', 'music', 'generated take in the wrong key; transposed', got=f"{k['tonic']} {k['mode']}", wanted=a.key, semitones=shift)
    if shift == 0:
        print('  ✓ already in key'); continue
    import librosa, numpy as np, soundfile as sf
    y, sr = librosa.load(dst, sr=44100, mono=False)
    y2 = np.vstack([librosa.effects.pitch_shift(ch, sr=sr, n_steps=shift) for ch in np.atleast_2d(y)])
    t = dst.with_name(f"{dst.stem}_{want_t}{'m' if want_m == 'minor' else ''}.wav")
    sf.write(t, y2.T, sr)
    k2 = analyse(t)['key'][0]
    print(f"  → shifted {shift:+d} st → {t.name}: now {k2['tonic']} {k2['mode']} ({k2['score']}); phase-vocoder may smear attacks, listen")
