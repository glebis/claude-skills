// The sound for v2, all synthesised (no samples, no generated music): a 120 BPM pulse under the cut so the hits land
// where the picture's cuts do (beat 15 f, bar 30 f), and one small sound per interface event, read from AT.
import { Mix } from "raea";
import * as Tone from "raea/tone";
import { AT, BAR, BEAT } from "../components/cut2";

const fr = (f: number) => f / 30;
const Tr = Tone.getTransport();
Tr.bpm.value = 120;
Tr.start(); // time 0 = the first frame
Tone.buses.music.volume.value = -10;
Tone.buses.sfx.volume.value = -12;
const room = new Tone.Reverb({ decay: 2.4, wet: 0.25 }).connect(Tone.buses.sfx);

// pulse: a soft kick on every beat from the app's arrival to the end card, a felt chord on every bar
const kick = new Tone.MembraneSynth({ pitchDecay: 0.03, octaves: 3, envelope: { attack: 0.001, decay: 0.28, sustain: 0, release: 0.1 } }).connect(Tone.buses.music);
kick.volume.value = -20;
const hatF = new Tone.Filter({ type: "highpass", frequency: 7000 }).connect(Tone.buses.music);
const hat = new Tone.NoiseSynth({ noise: { type: "white" }, envelope: { attack: 0.001, decay: 0.03, sustain: 0 } }).connect(hatF);
hat.volume.value = -24;
const pad = new Tone.PolySynth(Tone.FMSynth, { harmonicity: 1.5, modulationIndex: 0.8, envelope: { attack: 0.08, decay: 1.6, sustain: 0.2, release: 1.2 }, modulationEnvelope: { attack: 0.05, decay: 0.6, sustain: 0, release: 0.4 } }).connect(room);
pad.volume.value = -10;
const CHORDS = [["A3", "C#4", "E4"], ["F#3", "A3", "C#4"], ["D3", "F#3", "A3"], ["E3", "G#3", "B3"]];
for (let f = AT.appIn; f < AT.done - BAR; f += BEAT) {
  const onBar = (f - AT.appIn) % BAR === 0;
  const quiet = f >= AT.end; // the end card keeps only the dots' notes
  if (!quiet) Tr.schedule((t) => kick.triggerAttackRelease("A1", 0.2, t, onBar ? 0.9 : 0.45), fr(f));
  if (!quiet) Tr.schedule((t) => hat.triggerAttackRelease(0.03, t, 0.6), fr(f + BEAT / 2));
  if (onBar) {
    const c = CHORDS[Math.floor((f - AT.appIn) / BAR) % CHORDS.length];
    Tr.schedule((t) => pad.triggerAttackRelease(c, 1.6, t, quiet ? 0.35 : 0.5), fr(f));
  }
}

// events
const thud = new Tone.MembraneSynth({ pitchDecay: 0.02, octaves: 1.4, envelope: { attack: 0.004, decay: 0.22, sustain: 0, release: 0.1 } }).connect(Tone.buses.sfx);
thud.volume.value = -12;
const bell = new Tone.PolySynth(Tone.FMSynth, { harmonicity: 2.01, modulationIndex: 1.4, envelope: { attack: 0.004, decay: 1.2, sustain: 0, release: 0.5 }, modulationEnvelope: { attack: 0.002, decay: 0.3, sustain: 0, release: 0.2 } }).connect(room);
bell.volume.value = -12;
const keyF = new Tone.Filter({ type: "highpass", frequency: 2600 }).connect(Tone.buses.sfx);
const key = new Tone.NoiseSynth({ noise: { type: "white" }, envelope: { attack: 0.001, decay: 0.016, sustain: 0 } }).connect(keyF);
key.volume.value = -18;
const wF = new Tone.Filter({ type: "bandpass", frequency: 400, Q: 1.2 }).connect(Tone.buses.sfx);
const wN = new Tone.NoiseSynth({ noise: { type: "pink" }, envelope: { attack: 0.18, decay: 0.3, sustain: 0 } }).connect(wF);
wN.volume.value = -18;
const whoosh = (t: number) => {
  wF.frequency.cancelScheduledValues(t);
  wF.frequency.setValueAtTime(320, t);
  wF.frequency.exponentialRampToValueAtTime(1800, t + 0.2);
  wF.frequency.exponentialRampToValueAtTime(420, t + 0.5);
  wN.triggerAttackRelease(0.5, t, 0.8);
};
const click = (f: number, g = 1) => {
  Tr.schedule((t) => key.triggerAttackRelease(0.02, t, 0.9 * g), fr(f - 1));
  Tr.schedule((t) => key.triggerAttackRelease(0.015, t, 0.4 * g), fr(f + 3));
};
const land = (f: number, g = 1) => Tr.schedule((t) => thud.triggerAttackRelease("A2", 0.3, t, 0.6 * g), fr(f));
const ping = (f: number, n: string, g = 0.7) => Tr.schedule((t) => bell.triggerAttackRelease(n, 1.2, t, g), fr(f));

land(AT.dropA); land(AT.dropB);
ping(AT.tickA, "A5", 0.5); ping(AT.tickB, "C#6", 0.5);
click(AT.run);
[0, 1, 2, 3, 4, 5].forEach((i) => ping(AT.bloom + i * 8, ["E5", "A5", "C#6", "E6", "A5", "C#6"][i], 0.35));
click(AT.clickMark); Tr.schedule(whoosh, fr(AT.clickMark));
ping(AT.takes + 4, "E5", 0.5); ping(AT.takes + 18, "A5", 0.5);
click(AT.key, 1.3); ping(AT.key, "A5", 0.6);
for (let c = 0; c < 18; c++) Tr.schedule((t) => key.triggerAttackRelease(0.015, t, 0.35 + 0.3 * Math.abs(Math.sin(c * 1.7))), fr(AT.type + c * (40 / 18)));
Tr.schedule(whoosh, fr(AT.isoAuto));
land(AT.hit, 0.8); ping(AT.hit, "A4", 0.55); ping(AT.hit, "E5", 0.4);
click(AT.clickClean);
Tr.schedule(whoosh, fr(AT.end - 4));
["A4", "C#5", "E5", "F#5", "A5"].forEach((n, i) => { const at = AT.end + BAR + i * BEAT; land(at, 0.5); ping(at, n, 0.55); });

export function score() {
  return <Mix lufs={-14} ceiling={-1.5} />;
}
