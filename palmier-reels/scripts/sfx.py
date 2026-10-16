"""Generate the reel's sound kit with ElevenLabs sound-generation, peak-normalise, and measure onset/peak.

python3 sfx.py spec.json            # writes <workdir>/sfx/*.wav + manifest.json (cached; delete a wav to regenerate it)
Key: SOPS ~/.claude/skills/secrets.enc.yaml (ELEVENLABS_API_KEY), else env ELEVENLABS_API_KEY. Never printed.
Per-scene Foley comes from scene["sfx"]; transition prompts can be overridden in spec["sfx_prompts"].
"""
import json, os, subprocess, sys, urllib.request
import numpy as np

DEFAULTS = {   # name: (prompt, seconds) — names are what build_reel.py places
 'whoosh':     ('fast airy cinematic whoosh, analog tape swish passing close, transition, no music', 0.8),
 'hit-accent': ('deep 808 sub bass drop impact, punchy trailer hit with short warm tail, no melody', 1.3),
 'hit-ink':    ('16mm film splice clunk with a low cinematic thud, dry, vintage', 1.0),
 'card-out':   ('quick paper card sliding away, soft swish', 0.5),
 'riser':      ('short reverse cymbal riser swelling into silence, tense, cinematic', 1.6),
 'opening':    ('old film projector starting up, reel clatter and mechanical shutter clicking', 1.6),
 'end':        ('deep cinematic sub boom with soft tape-stop tail, final hit', 1.2),
}

def key():
    env = dict(os.environ, OPENAI_API_KEY='', SOPS_AGE_KEY_FILE=os.path.expanduser('~/.config/sops/age/keys.txt'))
    k = subprocess.run(['sops', '-d', '--extract', '["ELEVENLABS_API_KEY"]', os.path.expanduser('~/.claude/skills/secrets.enc.yaml')],
                       capture_output=True, text=True, env=env).stdout.strip()
    return k or os.environ.get('ELEVENLABS_API_KEY') or sys.exit('No ElevenLabs key: ask the user via a hidden AppleScript dialog, then store it in SOPS')

def analyse(wav):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', wav, '-f', 'f32le', '-ac', '1', '-ar', '48000', '-'], capture_output=True).stdout
    x = np.frombuffer(raw, np.float32); hop = 480
    rms = np.sqrt(np.convolve(x ** 2, np.ones(hop) / hop, 'same'))[::hop]
    X = np.abs(np.fft.rfft(x)); f = np.fft.rfftfreq(len(x), 1 / 48000)
    return {'onset': round(float(np.argmax(rms > rms.max() * 0.25) * hop / 48000), 3),
            'peak': round(float(rms.argmax() * hop / 48000), 3), 'seconds': round(len(x) / 48000, 3),
            'low_share': round(float(X[f < 120].sum() / X.sum()), 3)}

def main(spec_path):
    spec = json.load(open(spec_path)); base = os.path.dirname(os.path.abspath(spec_path))
    work = os.path.join(base, spec.get('workdir', 'reel-work'), 'sfx'); os.makedirs(os.path.join(work, 'raw'), exist_ok=True)
    want = dict(DEFAULTS); want.update({k: tuple(v) for k, v in spec.get('sfx_prompts', {}).items()})
    for i, sc in enumerate(spec['scenes']):
        if sc.get('sfx'): want[f'scene-{i}'] = (sc['sfx'], sc.get('sfx_seconds', 2.0))
    K = None; man = {}
    for name, (prompt, sec) in want.items():
        raw, wav = os.path.join(work, 'raw', name + '.mp3'), os.path.join(work, name + '.wav')
        if not os.path.exists(wav):
            K = K or key()
            req = urllib.request.Request('https://api.elevenlabs.io/v1/sound-generation', method='POST',
                  data=json.dumps({'text': prompt, 'duration_seconds': sec, 'prompt_influence': 0.55}).encode(),
                  headers={'xi-api-key': K, 'Content-Type': 'application/json'})
            open(raw, 'wb').write(urllib.request.urlopen(req, timeout=180).read())
            mx = float([l for l in subprocess.run(['ffmpeg', '-hide_banner', '-i', raw, '-af', 'volumedetect', '-f', 'null', '-'],
                        capture_output=True, text=True).stderr.splitlines() if 'max_volume' in l][0].split(':')[1].split()[0])
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', raw, '-af', f'volume={-3 - mx}dB', '-ar', '48000', '-ac', '2', wav], check=True)
        man[name] = {'prompt': prompt, **analyse(wav)}
        print(name, man[name], flush=True)
    json.dump(man, open(os.path.join(work, 'manifest.json'), 'w'), ensure_ascii=False, indent=1)

if __name__ == '__main__':
    main(sys.argv[1])
