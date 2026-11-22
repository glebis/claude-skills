#!/usr/bin/env python3
"""Check what this machine/container can do before starting a promo-reels run.

    doctor.py [--install]

Prints one line per dependency and, at the end, which workflow modes are available:
core (analyze/slides/build/verify/mix), beat grid, generated music, voice/captions,
learning loop (can the skill folder be written?).
--install tries `pip install` for missing Python packages (works where pip has a mirror/proxy,
e.g. ChatGPT containers; Codex needs network enabled).
Exit 1 when the core pipeline cannot run.
"""
import argparse, importlib, os, pathlib, shutil, subprocess, sys, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
import runlog  # noqa: E402
OK, NO, WARN = '✓', '✗', '!'
PIP = {'cv2': 'opencv-python-headless', 'numpy': 'numpy', 'librosa': 'librosa', 'soundfile': 'soundfile'}


def line(mark, name, note=''):
    print(f'{mark} {name:22} {note}')


def has_module(mod, install):
    try:
        importlib.import_module(mod); return True
    except Exception:
        if install:
            subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', PIP[mod]])
            try:
                importlib.invalidate_caches(); importlib.import_module(mod); return True
            except Exception:
                pass
        return False


def ffmpeg_filters():
    if not shutil.which('ffmpeg'):
        return None
    out = subprocess.run(['ffmpeg', '-hide_banner', '-filters'], capture_output=True, text=True).stdout
    enc = subprocess.run(['ffmpeg', '-hide_banner', '-encoders'], capture_output=True, text=True).stdout
    need = ['zoompan', 'xfade', 'overlay', 'loudnorm', 'scale', 'crop', 'eq', 'unsharp']
    missing = [f for f in need if f' {f} ' not in out]
    missing += [e for e in ('libx264', 'aac') if f' {e} ' not in enc]
    return missing


def online(url='https://api.elevenlabs.io', timeout=4):
    try:
        urllib.request.urlopen(urllib.request.Request(url, method='HEAD'), timeout=timeout); return True
    except urllib.error.HTTPError:
        return True  # reachable, just not a 200
    except Exception:
        return False


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--install', action='store_true'); a = ap.parse_args()
    core = True
    line(OK if sys.version_info >= (3, 9) else NO, 'python', sys.version.split()[0] + ' (need ≥ 3.9)')
    core &= sys.version_info >= (3, 9)

    for mod in ('numpy', 'cv2'):
        ok = has_module(mod, a.install); core &= ok
        line(OK if ok else NO, mod, '' if ok else f'pip install {PIP[mod]}')
    audio = all(has_module(m, a.install) for m in ('librosa', 'soundfile'))
    line(OK if audio else WARN, 'librosa + soundfile', '' if audio else 'needed for beat grid / music key: pip install librosa soundfile')

    miss = ffmpeg_filters()
    if miss is None:
        core = False; line(NO, 'ffmpeg', 'not on PATH (apt-get install ffmpeg / brew install ffmpeg / static build)')
    else:
        core &= not miss
        line(OK if not miss else NO, 'ffmpeg', 'all filters/encoders present' if not miss else 'missing: ' + ', '.join(miss))
    line(OK if shutil.which('ffprobe') else NO, 'ffprobe'); core &= bool(shutil.which('ffprobe'))

    import slides  # reuse its Chrome search
    exe = next((c for c in slides.chrome_candidates() if c and pathlib.Path(c).exists()), None)
    core &= bool(exe)
    line(OK if exe else NO, 'chrome (headless)', exe or 'none: pip install playwright && playwright install chromium, or set CHROME=')

    fonts = sorted(p.name for p in (ROOT / 'assets' / 'fonts').glob('*.ttf'))
    line(OK if fonts else NO, 'bundled fonts', ', '.join(fonts)); core &= bool(fonts)
    import tokens
    broken = {n: tokens.check(tokens.load(n)) for n in tokens.presets()}
    broken = {n: i for n, i in broken.items() if i}
    line(OK if not broken else WARN, 'style presets', f"{len(tokens.presets())} ok" if not broken
         else '; '.join(f"{n}: {i[0]}" for n, i in broken.items()))

    net = online()
    line(OK if net else WARN, 'network → ElevenLabs', 'reachable' if net else 'blocked (sandbox): music/voice unavailable')
    key = bool(os.environ.get('ELEVENLABS_API_KEY'))
    line(OK if key else WARN, 'ELEVENLABS_API_KEY', 'set' if key else 'not set: ask the user for it (never print it)')
    dfn = bool(shutil.which('deepFilter'))
    line(OK if dfn else WARN, 'deepFilter', 'present' if dfn else 'optional local denoiser (pip install deepfilternet)')

    writable = os.access(ROOT / 'references', os.W_OK)
    line(OK if writable else WARN, 'skill folder writable', 'learn.py can save lessons' if writable
         else 'read-only: output lessons as text/patch for the user')

    runlog.init()
    runlog._write('doctor', core=core, audio=audio, ffmpeg_missing=miss, chrome=exe, network=net, key=key, deepfilter=dfn, writable=writable)
    print('\nmodes:')
    print(f'  core pipeline          {"yes" if core else "NO — fix ✗ lines first"}')
    print(f'  beat grid (file/bpm)   {"yes" if audio else "--bpm only (no librosa)"}')
    print(f'  generated music        {"yes" if (net and key and audio) else "no → music mode none / file / licensed"}')
    print(f'  voice + captions       {"yes" if (net and key) else ("denoise only" if dfn else "no → captions from user-supplied text only")}')
    print(f'  learning loop          {"write references" if writable else "propose as text"}')
    sys.exit(0 if core else 1)


if __name__ == '__main__':
    main()
