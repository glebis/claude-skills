"""Offline stereo mixdown of a timeline's audio (music + every other audio track) for loudness/peak checks.

python3 mixcheck.py WORKDIR [--out mix.wav]        # uses WORKDIR/timeline.json + media.json written by build_reel.py
Forces 48 kHz stereo: mono sources otherwise make ffmpeg negotiate a mono mix and fake +3–6 dB peaks.
Ignores volume keyframes other than static clip volumeDb.
"""
import argparse, json, os, subprocess
ap = argparse.ArgumentParser(); ap.add_argument('work'); ap.add_argument('--out')
a = ap.parse_args(); W = a.work; out = a.out or os.path.join(W, 'mix-preview-audio-only.wav')
tl = json.load(open(os.path.join(W, 'timeline.json'))); cache = json.load(open(os.path.join(W, 'media.json')))
path_of = {v: k.split('|')[0] for k, v in cache.items() if not k.startswith('matte')}
FMT = 'aformat=sample_rates=48000:channel_layouts=stereo'; ins, flt, lab = [], [], []
for t in tl['tracks']:
    if t['type'] != 'audio': continue
    for c in t.get('clips', []):
        src = path_of.get(c['mediaRef'])
        if not src: continue
        i = len(lab); ss = c.get('trimStartFrame', 0) / 30; dur = (c['frames'][1] - c['frames'][0]) / 30
        ins += ['-ss', f'{ss:.3f}', '-t', f'{dur:.3f}', '-i', src]; ms = round(c['frames'][0] / 30 * 1000)
        flt.append(f'[{i}]{FMT},volume={c.get("volumeDb", 0)}dB,adelay={ms}|{ms}[s{i}]'); lab.append(f'[s{i}]')
flt.append(''.join(lab) + f'amix=inputs={len(lab)}:normalize=0:duration=longest,{FMT}[o]')
subprocess.run(['ffmpeg', '-v', 'error', '-y', *ins, '-filter_complex', ';'.join(flt), '-map', '[o]', '-c:a', 'pcm_s24le', out], check=True)
r = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', out, '-af', 'ebur128=peak=sample+true', '-f', 'null', '-'], capture_output=True, text=True).stderr
print(out); print('\n'.join(l.strip() for l in r.splitlines() if l.strip().startswith(('I:', 'Peak:'))))
