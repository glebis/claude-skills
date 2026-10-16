"""Export a timeline from Palmier (MP4 + self-contained .palmier), verify it, optionally make a Telegram copy.

python3 export.py TIMELINE_ID OUT_BASENAME [--telegram-mb 15] [--no-package]
Only run after the user has approved the edit in Palmier. Verifies: probe, full decode, loudness.
Telegram: send with video attributes (w/h/duration) or it shows square; the telegram skill now does this.
"""
import argparse, json, os, subprocess, sys, time
sys.path.insert(0, os.path.dirname(__file__))
from palmier import Palmier
ap = argparse.ArgumentParser(); ap.add_argument('timeline'); ap.add_argument('out'); ap.add_argument('--telegram-mb', type=float)
ap.add_argument('--no-package', action='store_true')
a = ap.parse_args(); P = Palmier(); out = os.path.abspath(a.out)
jobs = [P.call('export_project', {'mode': 'video', 'timelineId': a.timeline, 'outputPath': out + '.mp4', 'overwrite': False})['jobId']]
if not a.no_package: jobs.append(P.call('export_project', {'mode': 'palmier', 'outputPath': out + '.palmier', 'overwrite': False})['jobId'])
while True:
    lst = P.call('manage_exports', {'action': 'list'}); st = {j['jobId']: j for j in lst.get('exports', lst.get('jobs', []))}
    s = [st[j]['status'] for j in jobs if j in st]
    if s and all(x in ('completed', 'failed', 'cancelled') for x in s): break
    time.sleep(5)
if any(st[j]['status'] != 'completed' for j in jobs): sys.exit(f'export failed: {[st[j] for j in jobs]}')
mp4 = out + '.mp4'
print(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'stream=codec_name,width,height,nb_frames:format=duration,size', '-of', 'compact', mp4], capture_output=True, text=True).stdout)
subprocess.run(['ffmpeg', '-v', 'error', '-i', mp4, '-f', 'null', '-'], check=True); print('decode ok')
r = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', mp4, '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
print('\n'.join(l.strip() for l in r.splitlines() if l.strip().startswith(('I:', 'Peak:'))))
if a.telegram_mb:
    dur = float(json.loads(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'json', mp4], capture_output=True, text=True).stdout)['format']['duration'])
    vk = int(a.telegram_mb * 8 * 1024 * 0.95 / dur - 128); tg = out + '-tg.mp4'; log = out + '-x264'
    common = ['-c:v', 'libx264', '-preset', 'slow', '-b:v', f'{vk}k', '-maxrate', f'{int(vk * 1.35)}k', '-bufsize', f'{vk * 3}k', '-passlogfile', log]
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', mp4, *common, '-pass', '1', '-an', '-f', 'mp4', os.devnull], check=True)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', mp4, *common, '-pass', '2', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart', tg], check=True)
    print(tg, round(os.path.getsize(tg) / 1e6, 1), 'MB')
