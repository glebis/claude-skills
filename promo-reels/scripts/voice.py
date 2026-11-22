#!/usr/bin/env python3
"""Denoise the footage audio and transcribe it with word timestamps.

    voice.py WORK [--denoise deepfilter|elevenlabs|both] [--lang rus]

Uses WORK/sources.json from analyze.py. Per source:
  WORK/audio/<TAG>_raw.wav, <TAG>_dfn.wav (DeepFilterNet), <TAG>_11l.mp3 (ElevenLabs isolator)
  WORK/audio/<TAG>_stt.json (ElevenLabs Scribe, words + times, audio events)
Prints each source's lines with times and a verdict. DeepFilterNet is a speech model:
it erases singing — use the ElevenLabs isolator for singing or music.
Captions may only quote what the transcript and a second listen agree on.
"""
import argparse, json, os, pathlib, shutil, subprocess, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent)); import runlog  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument('work'); ap.add_argument('--denoise', default='both', choices=['deepfilter', 'elevenlabs', 'both'])
ap.add_argument('--lang', default='rus')
a = ap.parse_args()
runlog.init()
work = pathlib.Path(a.work); aud = work / 'audio'; aud.mkdir(exist_ok=True)
src = json.loads((work / 'sources.json').read_text())
key = os.environ.get('ELEVENLABS_API_KEY')


def curl(url, out, fields):
    args = ['curl', '-s', '-w', '%{http_code}', '-o', str(out), '-X', 'POST', url, '-H', f'xi-api-key: {key}']
    for k, v in fields:
        args += ['-F', f'{k}={v}']
    code = subprocess.run(args, capture_output=True, text=True).stdout
    return code == '200'


for tag, s in src.items():
    if not s.get('audio'):
        print(f'{tag}: no audio'); continue
    raw = aud / f'{tag}_raw.wav'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', s['path'], '-vn', '-ac', '1', '-ar', '48000', str(raw)], check=True)
    cands = []
    if a.denoise in ('deepfilter', 'both'):
        if shutil.which('deepFilter'):
            r = subprocess.run(['deepFilter', '--pf', '-o', str(aud / 'dfn'), str(raw)], capture_output=True, text=True)
            got = list((aud / 'dfn').glob(f'{tag}_raw*.wav'))
            if got:
                dst = aud / f'{tag}_dfn.wav'; got[0].replace(dst); cands.append(dst)
            else:
                print(f'{tag}: deepFilter failed: {r.stderr[-300:]}')
                runlog.signal('error', 'tooling', 'deepFilter failed', stderr=r.stderr[-300:])
        else:
            print('deepFilter not installed: pipx install --python python3.11 deepfilternet && '
                  'pipx inject deepfilternet "torch==2.0.1" "torchaudio==2.0.2" "numpy<2"')
    if a.denoise in ('elevenlabs', 'both') and key:
        dst = aud / f'{tag}_11l.mp3'
        if curl('https://api.elevenlabs.io/v1/audio-isolation', dst, [('audio', f'@{raw}')]):
            cands.append(dst)
    if not key:
        print('ELEVENLABS_API_KEY not set: skipping isolation and transcription'); continue
    for c in cands or [raw]:
        stt = aud / f'{c.stem}_stt.json'
        if not curl('https://api.elevenlabs.io/v1/speech-to-text', stt,
                    [('model_id', 'scribe_v1'), ('language_code', a.lang), ('timestamps_granularity', 'word'),
                     ('diarize', 'true'), ('tag_audio_events', 'true'), ('file', f'@{c}')]):
            print(f'{c.name}: STT failed'); runlog.signal('error', 'audio', 'speech-to-text request failed', file=c.name); continue
        d = json.loads(stt.read_text())
        words = [w for w in d.get('words', []) if w['type'] != 'spacing']
        spoken = [w for w in words if w['type'] == 'word']
        lang = d.get('language_code')
        print(f"== {c.name}: lang {lang} ({d.get('language_probability', 0):.2f}), {len(spoken)} words")
        print('   ' + ' '.join(f"{w['text']}@{w['start']:.1f}" if w['type'] == 'word' else w['text'] for w in words)[:1500])
        if not spoken:
            print('   → no words (only audio events): caption as a stage direction, never invent lines')
            runlog.signal('scenario', 'audio', 'no words, only audio events', file=c.name, events=[w['text'] for w in words][:10])
        elif lang and not lang.startswith(a.lang[:2]):
            print(f'   → language {lang} ≠ requested {a.lang}: Scribe hears another language — check by ear')
            runlog.signal('warning', 'audio', 'transcript language differs from requested', file=c.name, got=lang, wanted=a.lang)
