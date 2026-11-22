#!/usr/bin/env python3
"""Tempo, beats, downbeats and key of an audio file.

    beats.py AUDIO [--out beats.json]

Downbeats = the beat phase (mod 4) with the strongest onsets — good for pop/jazz in 4/4,
check by ear for anything else. Key = Krumhansl–Schmuckler on a CQT chromagram.
"""
import argparse, json, pathlib, warnings
import numpy as np
warnings.filterwarnings('ignore')
import librosa

MAJ = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
MIN = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
NAMES = ['C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B']


def key_of(y, sr):
    c = librosa.feature.chroma_cqt(y=y, sr=sr).mean(1)
    sc = sorted(((float(np.corrcoef(np.roll(p, k), c)[0, 1]), NAMES[k], m)
                 for p, m in ((MAJ, 'major'), (MIN, 'minor')) for k in range(12)), reverse=True)
    return [{'tonic': t, 'mode': m, 'score': round(s, 2)} for s, t, m in sc[:3]]


def analyse(path):
    y, sr = librosa.load(path, sr=22050)
    tempo, beats = librosa.beat.beat_track(y=y, sr=sr, units='time')
    on = librosa.onset.onset_strength(y=y, sr=sr)
    st = on[librosa.time_to_frames(beats, sr=sr)]
    ph = [float(np.mean(st[k::4])) if len(st[k::4]) else 0 for k in range(4)]
    d0 = int(np.argmax(ph))
    return {'file': str(path), 'duration': round(len(y) / sr, 3), 'tempo': round(float(np.atleast_1d(tempo)[0]), 1),
            'beat_period': round(float(np.median(np.diff(beats))), 4) if len(beats) > 1 else None,
            'beats': [round(float(b), 3) for b in beats], 'downbeats': [round(float(b), 3) for b in beats[d0::4]],
            'key': key_of(y, sr)}


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('audio'); ap.add_argument('--out')
    a = ap.parse_args(); r = analyse(a.audio)
    out = pathlib.Path(a.out) if a.out else pathlib.Path(a.audio).with_suffix('.beats.json')
    out.write_text(json.dumps(r, indent=1))
    k = r['key'][0]
    print(f"{pathlib.Path(a.audio).name}: {r['duration']}s, {r['tempo']} BPM (period {r['beat_period']}s), "
          f"key {k['tonic']} {k['mode']} ({k['score']}), {len(r['beats'])} beats, first downbeat {r['downbeats'][:1]} → {out}")
