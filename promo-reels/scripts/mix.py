#!/usr/bin/env python3
"""Put music under a cut.

    mix.py VIDEO.mp4 MUSIC... [--offset 0] [--lufs -14] [--out DIR] [--click BPM]

One output per track: DIR/<video>__<music>.mp4, music from --offset, trimmed to the video,
normalised to --lufs (Instagram ≈ -14) with a measured correction pass, 0.4 s fade-out,
video stream copied. --click BPM adds a metronome preview (downbeat accented) instead of
music — for checking a grid when the real track is licensed and can't be embedded.
"""
import argparse, pathlib, subprocess, sys
import numpy as np
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent)); import runlog  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument('video'); ap.add_argument('music', nargs='*')
ap.add_argument('--offset', type=float, default=0.0); ap.add_argument('--lufs', type=float, default=-14.0)
ap.add_argument('--out'); ap.add_argument('--click', type=float)
a = ap.parse_args()
runlog.init()
video = pathlib.Path(a.video); out = pathlib.Path(a.out) if a.out else video.parent / 'final'
out.mkdir(parents=True, exist_ok=True)
FADE = 0.4


def dur(p):
    return float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(p)],
                                capture_output=True, text=True).stdout)


def lufs(p):
    r = subprocess.run(['ffmpeg', '-i', str(p), '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
    I = [l.split()[1] for l in r.splitlines() if l.strip().startswith('I:')]
    pk = [l.split()[1] for l in r.splitlines() if l.strip().startswith('Peak:')]
    return float(I[-1]), float(pk[-1]) if pk else None


def mux(music, dst, gain=0.0):
    D = dur(video)
    af = (f"atrim=start={a.offset}:end={a.offset + D},asetpts=PTS-STARTPTS,loudnorm=I={a.lufs}:TP=-1.5:LRA=11,"
          f"volume={gain}dB,afade=t=out:st={D - FADE:.3f}:d={FADE},apad")
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(video), '-i', str(music), '-map', '0:v', '-map', '1:a', '-c:v', 'copy',
                    '-af', af, '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-t', f'{D}', '-movflags', '+faststart', str(dst)], check=True)


if a.click:
    import soundfile as sf
    sr, beat, D = 48000, 60 / a.click, dur(video)
    y = np.zeros(int(D * sr) + sr)
    for k in range(int(D / beat) + 1):
        f, amp = (1760, 0.6) if k % 4 == 0 else (1175, 0.35)
        n = np.arange(int(0.04 * sr)); i = int(round(k * beat * sr))
        y[i:i + len(n)] += amp * np.sin(2 * np.pi * f * n / sr) * np.exp(-n / (0.008 * sr))
    wav = out / f'click_{a.click:g}.wav'; sf.write(wav, np.stack([y, y], 1), sr)
    dst = out / f'{video.stem}__click_guide.mp4'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(video), '-i', str(wav), '-map', '0:v', '-map', '1:a', '-c:v', 'copy',
                    '-c:a', 'aac', '-b:a', '160k', '-shortest', '-movflags', '+faststart', str(dst)], check=True)
    print(f'{dst}  (preview only, not for publishing)')

for m in a.music:
    m = pathlib.Path(m); dst = out / f'{video.stem}__{m.stem}.mp4'
    mux(m, dst)
    I, pk = lufs(dst)
    if abs(I - a.lufs) > 0.5:          # single-pass loudnorm can miss on dense cues: correct once
        runlog.signal('fix', 'music', 'loudnorm missed the target; corrected with a second pass', track=m.name, measured=I, target=a.lufs)
        mux(m, dst, gain=round(a.lufs - I, 2)); I, pk = lufs(dst)
    print(f'{dst.name:44} {dur(dst):6.2f}s  {I:6.1f} LUFS  peak {pk} dBFS')
    runlog._write('mix', video=video.name, track=m.name, lufs=I, peak=pk)
runlog.remind()
