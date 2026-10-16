# Sound design

`scripts/sfx.py spec.json` generates (ElevenLabs sound-generation) and measures the kit; `build_reel.py` places it.

| sound | placement | level |
|---|---|---|
| hit-accent (808 drop) | on accent-card cuts, onset on the downbeat | −9 dB |
| hit-ink (film splice) | on ink-card cuts | −10 dB |
| whoosh | peak as the card sweeps in (cut − 6 f − peak) | −13 dB |
| card-out | when the card leaves (cut + hold) | −17 dB |
| scene-K Foley (scene `sfx` prompt, matched to its image) | onset ~4 f after the card clears | −16 dB |
| riser | peak lands on the final scene's cut | −13 dB |
| opening / end | frame 0 / end card | −14 / −8 dB |

- Music −3 dB. Target mix ≈ −16…−18 LUFS integrated, sample peak ≤ −1 dBFS. Check with `scripts/mixcheck.py` (stereo-forced; mono negotiation fakes overs).
- Generated SFX can miss the prompt — the user must listen (`<workdir>/mix-preview-audio-only.wav`) before export.
- Key from SOPS (`ELEVENLABS_API_KEY`); if absent ask via hidden AppleScript dialog and store in SOPS. Never print it.
- Optional VO: ElevenLabs `/v1/text-to-speech/{voice}/with-timestamps` gives character times to sync word reveals; Russian narrator used before: VASKO (shared library, Vl27Cllkuw8BhyPqus2n). Say "эй-ай" for AI. Prefer editorial-only VO (see perception.md).
