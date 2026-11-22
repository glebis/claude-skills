#!/usr/bin/env python3
"""Regression evals for agency-docs-updater scripts.

Deterministic: every fixture (video, VTT, MDX) is synthesised or checked in
under evals/fixtures, so results don't depend on any real recording.

  python3 evals/run_evals.py            # all
  python3 evals/run_evals.py --only edit,merge
  python3 evals/run_evals.py --fast     # skip Chrome renders + long encodes

Groups: edit (pause/silence editing, A/V sync), merge (existing MDX pages),
cover (brand covers, transforms), layout (labs.json registry),
upload (YouTube verify + trash gate).
Add a case: write a function `def case_<group>_<name>(t):` that raises
AssertionError on failure. `t` is a per-run temp dir.
"""
import json
import re
import subprocess
import sys
import tempfile
import traceback
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
S = SKILL / "scripts"
FIX = Path(__file__).parent / "fixtures"
sys.path.insert(0, str(S))
PY = sys.executable


def sh(*cmd, ok=True):
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True)
    if ok and r.returncode:
        raise AssertionError(f"{cmd[0]} {cmd[1] if len(cmd) > 1 else ''} failed:\n{r.stderr[-800:]}")
    return r


def durations(path):
    out = sh("ffprobe", "-v", "error", "-show_entries", "stream=codec_type,duration", "-of", "csv=p=0", path).stdout
    return {k: float(v) for k, v in (l.split(",") for l in out.split())}


def silences(path, d=0.3):
    log = sh("ffmpeg", "-hide_banner", "-i", path, "-af", f"silencedetect=noise=-35dB:d={d}",
             "-f", "null", "-", ok=False).stderr
    return [float(x) for x in re.findall(r"silence_duration: ([0-9.]+)", log)]


# ── fixtures ──────────────────────────────────────────────────────────────
SPEAK = "between(t,12,20)+between(t,22,30)+between(t,45,50)+between(t,58,65)+between(t,75,78)"
VTT = """WEBVTT

00:00:12.500 --> 00:00:19.000
Всем привет, начинаем

00:00:22.500 --> 00:00:29.500
Теперь попробуйте сами, напишите в чат свою задачу

00:00:45.500 --> 00:00:49.500
Так, запускаю агента, смотрите

00:00:58.500 --> 00:01:04.000
Отлично, идём дальше

00:01:15.500 --> 00:01:17.000
Конец
"""


def lesson_clip(t):
    """78 s: 12 s lead, 2 s pause, 15 s exercise, 8 s demo, 10 s dead air on webcam.

    Visuals mimic real lab footage (measured on GDA 01): the demo is a STILL
    screen with a discrete update every 2 s (screen share); 60-75 s has constant
    small motion everywhere (a person on webcam). A continuously moving pattern
    would read as a webcam, not a demo."""
    v = t / "lesson.mp4"
    if not v.exists():
        sh("ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
           "-f", "lavfi", "-i", "color=gray:s=320x240:d=78:r=25",
           "-f", "lavfi", "-i", "testsrc2=s=200x150:d=78:r=0.5",
           "-f", "lavfi", "-i", f"aevalsrc='0.4*sin(2*PI*220*t)*({SPEAK})':s=44100:d=78",
           # Game of Life: structured continuous motion, scene-score median ~0.015 like a
           # real face (0.010-0.014); grain noise and gradients score ~0 and fail.
           "-f", "lavfi", "-i", "life=s=320x240:r=25:ratio=0.3:mold=0",
           "-filter_complex",
           "[1]fps=25[upd];[0][upd]overlay=60:45:enable='between(t,50,58)'[s];"
           "[3]format=yuv420p[cam];[s][cam]overlay=0:0:enable='between(t,60,78)'[v]",
           "-map", "[v]", "-map", "2:a", "-t", "78", "-c:v", "libx264", "-pix_fmt", "yuv420p",
           "-c:a", "aac", v)
        (t / "lesson.vtt").write_text(VTT, encoding="utf-8")
    return v


def sync_clip(t):
    """60 s VFR: a white flash and a beep start together every 1.5 s — sync probe."""
    v = t / "sync.mp4"
    if not v.exists():
        on = "lt(mod({x}-0.5,1.5),0.2)*gte({x},0.5)"
        sh("ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
           "-f", "lavfi", "-i", "color=black:s=160x120:d=60:r=25",
           "-f", "lavfi", "-i", f"aevalsrc='0.5*sin(2*PI*440*t)*{on.format(x='t')}':s=48000:d=60",
           # drop every 7th frame -> variable frame rate, like Zoom screen-share
           # recordings (constant-rate fixtures hide frame-count timestamp drift)
           "-vf", f"geq=lum='if({on.format(x='T')},235,16)':cb=128:cr=128,select='not(eq(mod(n,7),3))'",
           "-fps_mode", "vfr", "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-c:a", "aac", "-shortest", v)
    return v


def onsets(path):
    log = sh("ffmpeg", "-hide_banner", "-i", path, "-af", "silencedetect=noise=-30dB:d=0.1",
             "-vf", "blackdetect=d=0.1:pix_th=0.3", "-f", "null", "-", ok=False).stderr
    beeps = [float(x) for x in re.findall(r"silence_end: ([0-9.]+)", log)]
    flashes = [float(x) for x in re.findall(r"black_end:([0-9.]+)", log)]
    return beeps, flashes


# ── edit ──────────────────────────────────────────────────────────────────
def _analyze(t, *extra):
    edl = t / "lesson.edl.json"
    sh(PY, S / "edit_video.py", "analyze", lesson_clip(t), "--transcript", t / "lesson.vtt", *extra, "-o", edl)
    return json.loads(edl.read_text())


def case_edit_classifies_context(t):
    acts = [a for a in _analyze(t)["actions"] if a["class"] != "tech"]
    got = [(round(a["start"]), a["class"], a["approved"]) for a in acts]
    want = [(0, "lead", True), (20, "pause", True), (30, "exercise", True),
            (50, "demo", False), (65, "dead_air", True)]
    assert got == want, f"got {got}"


def case_edit_frozen_dead_air_not_demo(t):
    """Regression: a demo announced 20 s earlier must not mark a later silence as demo."""
    a = next(x for x in _analyze(t)["actions"] if round(x["start"]) == 65)
    assert a["class"] == "dead_air", a


def case_edit_visual_states(t):
    """Regression (GDA 01): freezedetect called every webcam pause 'screen active' and kept
    all 183 silences (0% removed). Webcam = constant motion, demo = still + updates."""
    acts = {round(x["start"]): x.get("visual") for x in _analyze(t)["actions"] if x["class"] != "tech"}
    assert acts[50] == "screen_activity", acts
    assert acts[65] == "webcam", acts
    assert acts[30] == "static", acts


def case_edit_offset_auto(t):
    def shift(m):
        mm, ss = divmod(int(m[2]) * 60 + int(m[3]) + 7, 60)
        return f"00:{mm:02d}:{ss:02d}.{m[4]}"
    shifted = re.sub(r"(\d\d):(\d\d):(\d\d)\.(\d+)", shift, VTT)
    (t / "shifted.vtt").write_text(shifted, encoding="utf-8")
    edl = t / "shifted.edl.json"
    sh(PY, S / "edit_video.py", "analyze", lesson_clip(t), "--transcript", t / "shifted.vtt", "-o", edl)
    off = json.loads(edl.read_text())["offset"]
    # cues start 0.5 s after audio onsets, so -7.5 (cue snapped to onset) is also correct
    assert -7.6 <= off <= -6.9, f"offset {off}, want -7..-7.5"


def case_edit_apply_leaves_intended_pauses(t):
    _analyze(t)
    out = t / "lesson.edited.mp4"
    sh(PY, S / "edit_video.py", "apply", lesson_clip(t), t / "lesson.edl.json", "-o", out, "--max-remove", "0.5")
    got = silences(out)
    want = [2.0, 0.5, 2.0, 8.0, 0.5]
    assert len(got) == len(want) and all(abs(g - w) < 0.15 for g, w in zip(got, want)), f"pauses {got}"


def case_edit_report_counts_overlap_once(t):
    """GDA 01: directive + break-demo cuts overlapped; the report summed them (15.8 min)
    while apply removes their union."""
    import edit_video
    edl = {"duration": 600.0, "actions": [
        {"class": "directive", "remove": [100.0, 400.0], "approved": True, "review": False, "start": 100, "end": 400, "before": ""},
        {"class": "demo", "remove": [104.0, 350.0], "approved": True, "review": False, "start": 100, "end": 352, "before": ""}]}
    assert "removes 5.0 min" in edit_video.report(edl), edit_video.report(edl)[:80]


def case_edit_safety_cap_refuses(t):
    _analyze(t)
    r = sh(PY, S / "edit_video.py", "apply", lesson_clip(t), t / "lesson.edl.json",
           "-o", t / "x.mp4", "--max-remove", "0.2", ok=False)
    assert r.returncode != 0 and "REFUSED" in r.stderr, r.stderr[-300:]


def case_edit_many_cuts_keep_av_sync(t):
    """40 cuts in single-pass mode: every flash must still start with its beep."""
    v = sync_clip(t)
    spans = [{"start": 1.0 + i * 1.5, "end": 1.6 + i * 1.5} for i in range(38)]  # between events
    (t / "sync.spans.json").write_text(json.dumps(spans))
    out = t / "sync.cut.mp4"
    sh(PY, S / "cut_spans.py", v, "--spans-json", t / "sync.spans.json", "--max-remove", "0.5", "-o", out)
    d = durations(out)
    assert abs(d["video"] - d["audio"]) < 0.06, f"stream length drift {d}"
    # VFR sources already jitter by a frame or two (events on dropped frames);
    # judge the cut against the source, and check there is no accumulating trend.
    sb, sf = onsets(v)
    src_worst = max(abs(b - f) for b, f in zip(sb, sf))
    beeps, flashes = onsets(out)
    assert len(beeps) >= 30 and len(flashes) >= 30, (len(beeps), len(flashes))
    err = [b - f for b, f in zip(beeps, flashes)]
    worst = max(map(abs, err))
    trend = abs(sum(err[-10:]) / 10 - sum(err[:10]) / 10)
    assert trend < 0.03, f"A/V drift accumulates: {trend:.3f}s first→last"
    assert worst < src_worst + 0.04, f"A/V offset {worst:.3f}s vs source {src_worst:.3f}s"


def case_edit_lesson_start_is_hosts(t):
    """Regression (GDA 01): a participant's «Всем привет» at 16:31 became lesson_start;
    trim-to-start would have removed the recording notice. Only the host counts, and a
    late start is review-only."""
    r = json.loads(sh(PY, S / "detect_lesson_start.py", FIX / "lesson-start-gda01.json", "--json").stdout)
    assert r["host_only"] and r["lesson_start_s"] != 991.0, r
    assert r["lesson_start_s"] is None or r["lesson_start_s"] < 600 or r["lesson_start_review"], r


def case_edit_hundreds_of_cuts(t):
    """Regression (GDA 01): 145 pause cuts in ONE select expression -> ffmpeg 'Cannot allocate
    memory'. Real lessons produce 100-300 cuts; must work at that scale and stay in sync."""
    v = sync_clip(t)
    spans = [{"start": 0.75 + i * 0.3, "end": 0.8 + i * 0.3} for i in range(190)]  # 190 cuts, 9.5 s
    (t / "many.json").write_text(json.dumps(spans))
    out = t / "many190.mp4"
    r = sh(PY, S / "cut_spans.py", v, "--spans-json", t / "many.json", "--max-remove", "0.5", "-o", out, ok=False)
    assert r.returncode == 0, r.stderr[-500:]
    d = durations(out)
    assert abs(d["video"] - (60 - 9.5)) < 0.3 and abs(d["video"] - d["audio"]) < 0.08, d


def case_edit_whisper_hallucination_filter(t):
    """GDA 01: Groq Whisper emitted a bare 'DimaTorzok' (no_speech_prob 0.07, so a probability
    filter misses it); 'накладывать текст субтитров' at 1:25:36 is real speech and must stay."""
    from transcribe_cut import is_hallucination
    for bad in ["DimaTorzok", " Субтитры сделал DimaTorzok", "Продолжение следует...", "Спасибо за просмотр!"]:
        assert is_hallucination(bad), bad
    # GDA 01 #02: English fillers invented over 8 min of pre-meeting silence
    for bad in ["Thank you for watching!", "The following is a video from the recording of the event."]:
        assert is_hallucination(bad), bad
    assert is_hallucination("Thank you.", 0.8) and not is_hallucination("Thank you.", 0.05)
    for good in ["И как видите, здесь можно накладывать текст субтитров с вашим дизайном.",
                 "Продолжение следует в следующей встрече, где мы разберём MCP."]:
        assert not is_hallucination(good), good


def case_edit_transcribe_skips_leading_silence(t):
    """GDA 01 #02: 8 min of silence at the start of chunk 1 flipped Whisper to English."""
    from transcribe_cut import first_speech
    s = first_speech(lesson_clip(t))  # fixture: 12 s silence, then speech
    assert 10.5 <= s <= 11.5, s


def case_edit_cut_drops_stale_chapters(t):
    """GDA 01 #02: the Zoom source had a chapter text track; the cut file kept it with the
    original 2:35:37 duration while video/audio were 2:16:19."""
    src = t / "chap.mp4"
    meta = t / "chap.txt"
    meta.write_text(";FFMETADATA1\n[CHAPTER]\nTIMEBASE=1/1\nSTART=0\nEND=78\ntitle=all\n")
    sh("ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", lesson_clip(t), "-i", meta,
       "-map_metadata", "1", "-map_chapters", "1", "-c", "copy", src)
    out = t / "chap.cut.mp4"
    sh(PY, S / "cut_spans.py", src, "--remove", "20-30", "-o", out)
    probe = sh("ffprobe", "-v", "error", "-show_chapters", "-show_entries", "stream=codec_type",
               "-of", "compact", out).stdout
    assert "chapter" not in probe and "data" not in probe, probe


def case_edit_tech_spans_need_approval(t):
    vtt = VTT + "\n00:01:05.000 --> 00:01:06.000\nвидно мой экран? меня слышно?\n"
    (t / "tech.vtt").write_text(vtt, encoding="utf-8")
    edl = t / "tech.edl.json"
    sh(PY, S / "edit_video.py", "analyze", lesson_clip(t), "--transcript", t / "tech.vtt", "--no-screen", "-o", edl)
    tech = [a for a in json.loads(edl.read_text())["actions"] if a["class"] == "tech"]
    assert tech and not any(a["approved"] for a in tech), tech


def case_edit_offset_noise_falls_back_to_zero(t):
    """Regression (GDA 01 #02): a transcript of the SAME video got offset +199.5 s because the
    alignment landscape was flat noise. No clear peak -> 0 + warning, never a random shift."""
    import random
    import edit_video
    rnd = random.Random(3)
    sil = sorted((x, x + 1.5) for x in (rnd.uniform(0, 9000) for _ in range(460)))
    segs = sorted((rnd.uniform(0, 9000), "x") for _ in range(1000))   # unrelated to the pauses
    assert edit_video.offset_peak_z(segs, sil) < 4.0
    # and a genuinely aligned transcript (cues right after pauses, shifted 30 s) has a sharp peak
    al = [(e - 30.0, "x") for _, e in sil[:300]]
    assert edit_video.offset_peak_z(al, sil) >= 4.0


def case_edit_same_source_offset_zero(t):
    import edit_video
    v = lesson_clip(t)
    tr = t / "same.json"
    tr.write_text(json.dumps({"transcript": [{"timestamp": 12.4, "text": "x"}], "source": str(v.resolve())}))
    assert edit_video.same_source(tr, v) and not edit_video.same_source(tr, t / "other.mp4")


def case_edit_warns_on_wispr_clock(t):
    """GDA 01: Wispr Flow's live.ndjson clock is recording_active_ms (pauses skipped);
    analyze must say so instead of silently using it to place cuts."""
    r = sh(PY, S / "edit_video.py", "analyze", lesson_clip(t), "--transcript", FIX / "wispr-live.ndjson",
           "--no-screen", "-o", t / "w.edl.json")
    assert "recording_active_ms" in r.stderr, r.stderr[-400:]
    assert json.loads((t / "w.edl.json").read_text())["offset_drift"]


def case_edit_compare_detects_clock_step(t):
    """Text-aligned drift (what found Wispr's +59 s step on GDA 01; onset matching could not)."""
    from compare_transcripts import clock_steps
    pairs = [(tb, tb + 66) for tb in range(0, 6000, 60)] + [(tb, tb + 125) for tb in range(6000, 9000, 60)]
    _, steps = clock_steps(pairs)
    assert len(steps) == 1 and steps[0][0] == 6000 and abs(steps[0][1] - 59) < 1, steps
    _, none = clock_steps([(tb, tb + 66 + (tb % 7) * 0.5) for tb in range(0, 9000, 60)])
    assert none == [], none
    # one noisy bucket that returns to the level is not a step (GDA 01, 60-70 min: n=5, -31 s)
    blip = [(tb, tb + (37 if 3600 <= tb < 4200 else 66)) for tb in range(0, 9000, 60)]
    _, none = clock_steps(blip)
    assert none == [], none


def case_edit_loads_wispr_ndjson(t):
    from detect_lesson_start import load_segments
    live = load_segments(FIX / "wispr-live.ndjson")
    ref = load_segments(FIX / "wispr-refined.ndjson")
    assert live == [(0.952, "Давно в Германии."), (9697.0, "Тоже хочу не заморачиваться.")], live
    assert ref[1][0] == 161 * 60 + 37, ref  # minutes > 59 in MM:SS


def case_edit_compare_transcripts_terms(t):
    from compare_transcripts import term_table
    rows = dict(term_table(["Клод и кодекс", "Claude и Codex"], {"Claude": r"клод\w*", "Codex": r"кодекс\w*"}))
    assert rows == {"Claude": ["0 / 1", "1 / 0"], "Codex": ["0 / 1", "1 / 0"]}, rows


def case_edit_spoken_directives(t):
    """Regression (GDA 01, 71 min): «агент, это конец паузы. | Пожалуйста, вырежи паузу.» spans
    two segments; «агент» is also the lab's topic noun (false positives everywhere)."""
    import edit_video
    from detect_lesson_start import load_segments
    segs = load_segments(FIX / "directives-gda01.json")
    brk = (66 * 60 + 41, 71 * 60 + 15)
    cuts, notes = edit_video.directives(segs, [brk, (40 * 60, 40 * 60 + 3)])
    assert len(cuts) == 1, [c["before"] for c in cuts]
    c = cuts[0]
    assert c["remove"][0] == brk[0] and 71 * 60 + 22 <= c["remove"][1] <= 71 * 60 + 26, c["remove"]
    assert not c["approved"] and c["review"], "directive cuts must be review-only"
    assert [round(n["at"]) for n in notes] == [82 * 60 + 5], notes


# ── merge ─────────────────────────────────────────────────────────────────
from merge_meeting_doc import merge  # noqa: E402

BLOCKS = {"recording": '<iframe src="https://www.youtube.com/embed/abc"></iframe>',
          "summary": "## Что разобрали\n\n- пункт", "transcript": "[Транскрипт](/t.md)"}


def case_merge_keeps_curated_content(t):
    src = (FIX / "curated-meeting.mdx").read_text(encoding="utf-8")
    out, _ = merge(src, BLOCKS, {"title": "Новое"}, "ru")
    managed = re.compile(r"\{/\* agency:(\w+) \*/\}.*?\{/\* /agency:\1 \*/\}", re.S)
    rest = managed.sub("", out)
    from merge_meeting_doc import PENDING_RE
    missing = [l for l in src.splitlines() if l.strip() and l not in rest and not PENDING_RE.match(l)]
    assert not missing, f"curated lines lost: {missing[:3]}"
    assert "Новое" not in out, "curated title overwritten"
    assert "появятся здесь после встречи" not in out, "pending note survived publication (GDA 01 live page)"


def case_merge_idempotent(t):
    src = (FIX / "curated-meeting.mdx").read_text(encoding="utf-8")
    once, _ = merge(src, BLOCKS)
    twice, changes = merge(once, BLOCKS)
    assert once == twice, "second merge changed the page"
    assert all("replaced managed block" in c for c in changes), changes


def case_merge_takes_over_section_and_drops_pending(t):
    src = ("---\ntitle: \"Встреча 02: [Название встречи]\"\ntoolkit: [a, b]\n---\n\n"
           "**Дата:** 17 октября\n\n## Видео\n\nЗапись появится после встречи.\n\n## Материалы\n\n- x\n")
    out, _ = merge(src, BLOCKS, {"title": "Встреча 02: Агенты"})
    assert out.count("## Запись") == 1 and "## Видео" not in out, out
    assert "появится" not in out
    assert 'title: "Встреча 02: Агенты"' in out and "toolkit: [a, b]" in out
    assert out.index("## Запись") < out.index("## Материалы")
    assert "### Что разобрали" in out, "summary headings not nested"


def case_merge_scaffold_placeholders(t):
    """GDA 01 #02: scaffold wrote title "Встреча 02", a generic description, and
    «Запись, слайды и материалы появятся здесь после встречи.» — none were recognised,
    so the real title was never set and the pending note stayed after publication."""
    src = ('---\ntitle: "Встреча 02"\ndescription: "Встреча 02 лаборатории Goal-Driven AI."\n---\n\n'
           "**Дата:** 17 октября 2026 (Сб) · 10:00 по Берлину | **Длительность:** ~2 часа\n\n"
           "Запись, слайды и материалы появятся здесь после встречи.\n")
    out, _ = merge(src, BLOCKS, {"title": "Встреча 02: Obsidian для агентов", "description": "Новое"})
    assert 'title: "Встреча 02: Obsidian для агентов"' in out and 'description: "Новое"' in out, out[:200]
    assert "появятся" not in out, out
    # curated values and real prose must survive
    keep = '---\ntitle: "Встреча 01: Знакомство"\n---\n\nМатериалы к практике будут полезны всем.\n'
    out2, _ = merge(keep, BLOCKS, {"title": "X"})
    assert "Знакомство" in out2 and "X" not in out2.split("---")[1], out2
    assert "Материалы к практике будут полезны всем." in out2, "real prose removed as pending note"


def case_merge_without_fathom(t):
    """GDA 01 #02: no Fathom recording (Zoom + Wispr only) -> update_meeting_doc exited.
    It must merge into the existing page without a Fathom URL."""
    import os
    sess = t / "20261017-goal-driven-ai-01.md"
    sess.write_text('---\ntitle: "Goal-Driven AI 01"\ndate: 2026-10-17\nsource: zoom\n---\n\nтекст\n', encoding="utf-8")
    docs = t / "docs"; (docs / "meetings").mkdir(parents=True)
    (docs / "meetings" / "02.mdx").write_text('---\ntitle: "Встреча 02"\n---\n\n**Дата:** 17 октября 2026\n', encoding="utf-8")
    summ = t / "s.md"; summ.write_text("## Итоги\n\n- пункт\n", encoding="utf-8")
    r = subprocess.run([PY, str(S / "update_meeting_doc.py"), str(sess), "https://youtu.be/abcdefghijk", str(summ),
                        str(docs), "-n", "02", "--lab", "01", "--title", "Встреча 02: Тест"],
                       capture_output=True, text=True, env={**os.environ, "LAB_SLUG": "goal-driven-ai"})
    assert r.returncode == 0, (r.stdout + r.stderr)[-500:]
    page = (docs / "meetings" / "02.mdx").read_text(encoding="utf-8")
    assert "embed/abcdefghijk" in page and "Встреча 02: Тест" in page and "Fathom" not in page, page[:400]


def case_merge_english_headings(t):
    out, _ = merge("**Date:** Oct 10\n\n## Plan\n\n- a\n", BLOCKS, lang="en")
    assert "## Recording" in out and "## Summary" in out and "## Plan" in out


# ── cover ─────────────────────────────────────────────────────────────────
import brand_cover  # noqa: E402


def case_cover_composition_choice(t):
    b = brand_cover.load_brand("goal-driven-ai")
    got = {s: brand_cover.pick_composition(s, b)
           for s in ("Сравниваем модели", "Знакомство и первая практика", "Автоматизация процесса", "")}
    assert got == {"Сравниваем модели": "pricing", "Знакомство и первая практика": "portrait",
                   "Автоматизация процесса": "program", "": "hero"}, got


def case_cover_headline_outweighs_topic(t):
    """Regression (GDA 01): topic 'Знакомство участников, инструменты, демо' tied
    portrait/pricing and the declared order picked pricing; the headline says Знакомство."""
    b = brand_cover.load_brand("goal-driven-ai")
    got = brand_cover.pick_composition("Знакомство участников, инструменты, демо", b,
                                       "Знакомство и первая практика с ИИ-агентами")
    assert got == "portrait", got


def case_cover_label_override(t):
    """GDA 01 Sunday group: the brand's «Встреча {meeting}» made the advanced session's cover
    read «Встреча 01», colliding with Saturday meeting 01."""
    if FAST:
        return "skipped (--fast)"
    sh(PY, S / "brand_cover.py", "render", "goal-driven-ai", "--meeting", "01", "--hero", "Тест",
       "--label", "Продвинутая группа · {meeting}", "--formats", "youtube", "--out-prefix", t / "lbl")
    html = (t / "lbl.youtube.html").read_text(encoding="utf-8")
    assert "Продвинутая группа · 01" in html and "Встреча 01" not in html


def case_cover_copy_rules(t):
    f = {"hero": "Знакомство и практика.", "emphasis": "на задаче"}
    brand_cover.apply_copy_rules(f, {"strip_heading_full_stop": True})
    assert f["hero"] == "Знакомство и практика"


def case_cover_tokens_resolve(t):
    b = brand_cover.load_brand("goal-driven-ai")
    css = brand_cover.css_vars(b["_tokens"])
    for var in ("--color-primary: #d01920", "--font-editorial:", "--illustration-hero-serif-size-adjust: 0.54"):
        assert var in css, var


def case_cover_render_sizes(t):
    if FAST:
        return "skipped (--fast)"
    sh(PY, S / "brand_cover.py", "render", "goal-driven-ai", "--hero", "Тест", "--emphasis", "обложки",
       "--formats", "youtube,og", "--out-prefix", t / "cov")
    for f, wh in (("cov.youtube.jpg", "1280x720"), ("cov.og.png", "1200x630")):
        got = sh("magick", "identify", "-format", "%wx%h", t / f).stdout
        assert got == wh, f"{f}: {got}"


def case_cover_transforms(t):
    from image_transforms import run_pipeline
    src = brand_cover.load_brand("goal-driven-ai")["assets"]["red-triangle"]
    out = t / "tri.png"
    run_pipeline(src, out, [{"op": "trim"}, {"op": "resize", "width": 200}, {"op": "key_out", "color": "#ffffff"}])
    assert sh("magick", "identify", "-format", "%w %[channels]", out).stdout.startswith("200 srgba")
    r = sh(PY, S / "image_transforms.py", src, t / "x.png", "--pipeline", '[{"op":"nope"}]', ok=False)
    assert r.returncode and "unknown transform op" in (r.stdout + r.stderr)


# ── layout ────────────────────────────────────────────────────────────────
def case_layout_goal_driven_ai(t):
    import lab_layout
    r = lab_layout.resolve("goal-driven-ai", "01", "03")
    assert r["page_url"] == "/goal-driven-ai-01/meetings/03" and r["brand"] == "goal-driven-ai"
    assert r["thumbnail_style"] == "brand" and r["registered"]
    assert lab_layout.resolve("claude-code", "05")["thumbnail_style"] == "claude-code"


def case_layout_find_transcript_in_sessions(t):
    """Regression (GDA 01): Step 1 globbed vault root for *-lab-NN.md; real file was
    Sessions/20261010-goal-driven-ai-01.md."""
    from find_transcript import find
    v = t / "vault"
    (v / "Sessions").mkdir(parents=True)
    for name in ("Sessions/20261010-goal-driven-ai-01.md", "Sessions/20260820-goal-driven-design.md",
                 "20260420-claude-code-lab-05.md", "Sessions/20261010-unrelated-call.md"):
        (v / name).write_text("---\n---\n")
    assert find("20261010", vault=v) == {"path": str(v / "Sessions/20261010-goal-driven-ai-01.md"),
                                         "slug": "goal-driven-ai", "lab": "01", "suffix": ""}
    assert find("20260820", vault=v)["slug"] == "ai-design"
    assert find("20260420", vault=v) == {"path": str(v / "20260420-claude-code-lab-05.md"),
                                         "slug": "claude-code", "lab": "05", "suffix": ""}
    # GDA 01 Sunday group: calendar title adds a descriptor after the lab number
    (v / "Sessions/20261018-goal-driven-ai-01-продвинутая-группа.md").write_text("---\n---\n")
    r = find("20261018", vault=v)
    assert r and r["slug"] == "goal-driven-ai-advanced" and r["lab"] == "01" and r["suffix"] == "", r
    # an unknown descriptor still resolves to the base lab, with the suffix reported
    (v / "Sessions/20261019-goal-driven-ai-01-доп-встреча.md").write_text("---\n---\n")
    r2 = find("20261019", vault=v)
    assert r2 and r2["slug"] == "goal-driven-ai" and r2["suffix"] == "доп-встреча", r2
    assert find("20261010", slug="claude-code", vault=v) is None


def case_layout_lab_number_from_real_names(t):
    import os
    import update_meeting_doc as u
    os.environ["LAB_SLUG"] = "goal-driven-ai"
    try:
        assert u.extract_lab_number("20261010-goal-driven-ai-01.md") == "01"
        assert u.extract_lab_number("20261017-goal-driven-ai-lab-02.md") == "02"
    finally:
        os.environ.pop("LAB_SLUG")
    assert u.extract_lab_number("20260420-claude-code-lab-05.md") == "05"


def case_layout_docs_resolve_paths_via_registry(t):
    """Regression (GDA 01): SKILL.md built /${LAB_SLUG}-lab-NN/ URLs and
    content/docs/${LAB_SLUG}-internal-NN paths by hand — 404 links in YouTube
    descriptions and an empty `git add` for registry-only labs."""
    bad = re.compile(r"\$\{LAB_SLUG\}-internal-|\$\{LAB_SLUG\}-lab-\$\{LAB_NUMBER\}/meetings|"
                     r"/docs/claude-code-internal-\$\{LAB_NUMBER\}|'Claude Code Lab \$\{LAB_NUMBER\}'")
    hits = []
    docs = [f for f in sorted((SKILL / "references").glob("*.md")) if f.name != "learnings.md"]  # history may quote the anti-pattern
    for f in [SKILL / "SKILL.md", *docs]:
        for n, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            if bad.search(line):
                hits.append(f"{f.name}:{n}")
    assert not hits, f"hand-built lab paths: {hits}"


def case_layout_aggregations_resolve_templated_dirs(t):
    """Regression (GDA 01): meetings_dir 'content/docs/goal-driven-ai-{lab}/meetings' never
    matched (literal substring test) -> glossary/index linked /claude-code-lab-??/meetings/01."""
    import rebuild_aggregations as ra
    d = t / "site" / "content" / "docs"
    for rel in ("goal-driven-ai-01/meetings/03.mdx", "goal-driven-design-ru/meetings/02.mdx",
                "claude-code-internal-05/meetings/07.mdx"):
        (d / rel).parent.mkdir(parents=True, exist_ok=True)
        (d / rel).write_text('---\ntitle: "T"\n---\n\n**Дата:** 1 октября 2026\n')
    urls = {Path(rec["path"]).parent.parent.name: rec["url"].split("glebkalinin.com")[-1]
            for rec in (ra.parse_meeting(d / x) for x in ("goal-driven-ai-01/meetings/03.mdx",
                        "goal-driven-design-ru/meetings/02.mdx", "claude-code-internal-05/meetings/07.mdx"))}
    assert urls == {"goal-driven-ai-01": "/goal-driven-ai-01/meetings/03",
                    "goal-driven-design-ru": "/goal-driven-design-ru/meetings/02",
                    "claude-code-internal-05": "/claude-code-lab-05/meetings/07"}, urls


def case_layout_publish_preflight_blocks_feature_branch(t):
    """Regression (GDA 01): the docs checkout was on codex/companion-t-shaped (22 commits ahead
    of origin/main, production deployed from it via CLI). Committing + pushing to main merged
    the branch without a PR. The preflight must refuse a non-main or ahead checkout."""
    g = lambda *a, cwd: subprocess.run(["git", *a], cwd=cwd, capture_output=True, text=True, check=True)
    origin, work = t / "origin.git", t / "work"
    g("init", "-q", "--bare", "-b", "main", str(origin), cwd=t)
    g("clone", "-q", str(origin), str(work), cwd=t)
    g("-c", "user.email=e@x", "-c", "user.name=n", "commit", "-q", "--allow-empty", "-m", "init", cwd=work)
    g("push", "-q", "origin", "HEAD:main", cwd=work)
    ok = sh("bash", S / "publish_preflight.sh", work, ok=False)
    assert ok.returncode == 0 and "safe to commit" in ok.stdout, ok.stdout
    g("checkout", "-q", "-b", "codex/feature", cwd=work)
    g("-c", "user.email=e@x", "-c", "user.name=n", "commit", "-q", "--allow-empty", "-m", "wip", cwd=work)
    bad = sh("bash", S / "publish_preflight.sh", work, ok=False)
    assert bad.returncode != 0 and "codex/feature" in bad.stdout and "ahead 1" in bad.stdout, bad.stdout


def case_layout_unregistered_lab_never_question_marks(t):
    """Regression (GDA 01 #02): goal-driven-ai-en appeared on main unregistered and its 6
    meetings were indexed as /claude-code-lab-??/meetings/NN."""
    import rebuild_aggregations as ra
    f = t / "site" / "content" / "docs" / "brand-new-lab-xyz" / "meetings" / "04.mdx"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text('---\ntitle: "T"\n---\n', encoding="utf-8")
    url = ra.parse_meeting(f)["url"]
    assert "??" not in url and url.endswith("/brand-new-lab-xyz/meetings/04"), url


def case_layout_announce_refuses_resend(t):
    """Step 10 duplicate prevention: an existing receipt (any status) stops the sender before
    it decrypts secrets or touches the network."""
    import os
    data = t / "pibot-data"; (data / "publication-receipts").mkdir(parents=True)
    (data / "publication-receipts" / "goal-driven-ai-01--02---1000000000001.json").write_text('{"status":"pending"}')
    # a second track keys receipts by its own feed, so Saturday 02's receipt must not block advanced 02
    adv = subprocess.run(["npx", "tsx", str(S / "announce_publication.ts"), "--meeting", "02", "--feed", "goal-driven-ai-01-advanced",
                          "--page", "/goal-driven-ai-01/advanced/02", "--chat", "-1000000000001", "--recording", "https://www.youtube.com/watch?v=GlVzeSrj4FY", "--lead", "x"],
                         cwd=Path.home() / "ai_projects" / "pibot", capture_output=True, text=True,
                         env={**os.environ, "PIBOT_DATA_DIR": str(data)}) if (Path.home() / "ai_projects" / "pibot" / "node_modules").exists() else None
    if adv is not None:
        assert "receipt exists" not in adv.stdout and adv.returncode == 5 and "publication gate" in adv.stdout, adv.stdout[-300:]
    pibot = Path.home() / "ai_projects" / "pibot"
    if not (pibot / "node_modules").exists():
        return "skipped (no pibot checkout)"
    r = subprocess.run(["npx", "tsx", str(S / "announce_publication.ts"), "--meeting", "02", "--chat", "-1000000000001",
                        "--recording", "https://www.youtube.com/watch?v=GlVzeSrj4FY", "--lead", "x"],
                       cwd=pibot, capture_output=True, text=True, env={**os.environ, "PIBOT_DATA_DIR": str(data)})
    assert r.returncode == 2 and "receipt exists" in r.stdout and "never resend" in r.stdout, r.stdout + r.stderr[-300:]


# ── upload (verify + trash gate) ──────────────────────────────────────────
import verify_upload  # noqa: E402


def _yt(upload="processed", processing="succeeded", duration="PT1H45M0S", rejection=None):
    status = {"uploadStatus": upload, "privacyStatus": "unlisted"}
    if rejection:
        status["rejectionReason"] = rejection
    return {"status": status, "processingDetails": {"processingStatus": processing},
            "contentDetails": {"duration": duration}}


def case_upload_iso_duration(t):
    p = verify_upload.parse_iso_duration
    assert (p("PT1H45M0S"), p("PT59S"), p("PT2H"), p("P0D")) == (6300, 59, 7200, 0)


def case_upload_trash_only_when_fully_verified(t):
    a = verify_upload.assess
    assert a(_yt(), 6300.3)[0] == "ok"
    assert a(None, 6300)[0] == "wait"                                    # not visible yet
    assert a(_yt(upload="uploaded", processing="processing"), 6300)[0] == "wait"
    assert a(_yt(upload="failed"), 6300)[0] == "fail"
    assert a(_yt(rejection="duplicate"), 6300)[0] == "fail"
    assert a(_yt(processing="failed"), 6300)[0] == "fail"


def case_upload_duration_mismatch_blocks_trash(t):
    """Regression (GDA 01 #05): only part 2 of a split recording was uploaded —
    'succeeded' on YouTube, but 1:34 against a 2:16 local file. Never trash then."""
    st, why = verify_upload.assess(_yt(duration="PT1H34M"), 8160)
    assert st == "fail" and "duration" in why, (st, why)
    assert verify_upload.assess(_yt(), None)[0] == "ok"                  # no local file to compare


def case_upload_trash_refuses_without_ok(t):
    f = t / "keep.mp4"
    f.write_bytes(b"x")
    trashed = verify_upload.trash_files([f], verified=False)
    assert trashed == [] and f.exists()


# ── runner ────────────────────────────────────────────────────────────────
FAST = "--fast" in sys.argv


def main():
    only = None
    if "--only" in sys.argv:
        only = set(sys.argv[sys.argv.index("--only") + 1].split(","))
    cases = [(n, f) for n, f in globals().items() if n.startswith("case_") and callable(f)]
    if only:
        cases = [(n, f) for n, f in cases if n.split("_")[1] in only]
    slow = {"case_edit_many_cuts_keep_av_sync", "case_edit_apply_leaves_intended_pauses"}
    failed = 0
    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        for name, fn in cases:
            if FAST and name in slow:
                print(f"SKIP  {name[5:]}")
                continue
            try:
                note = fn(t)
                print(f"PASS  {name[5:]}" + (f"  ({note})" if note else ""))
            except Exception as e:  # noqa: BLE001
                failed += 1
                msg = str(e) if isinstance(e, AssertionError) else traceback.format_exc(limit=2)
                print(f"FAIL  {name[5:]}\n      {msg.strip()[:600]}")
    print(f"\n{len(cases) - failed}/{len(cases)} passed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
