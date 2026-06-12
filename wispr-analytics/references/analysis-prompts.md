# Analysis Prompt Templates

## Technical Mode

Analyze these dictation samples from a developer's voice-to-text workflow. Focus on:

1. **Work patterns**: What types of coding tasks dominate? (debugging, architecture, implementation, review)
2. **Tool interactions**: How is the user interacting with AI tools vs terminal vs editor?
3. **Complexity signals**: Are dictations getting longer/shorter? Are they commands or explanations?
4. **Context switching**: How often does the user jump between apps/tasks within a session?
5. **Productivity indicators**: Dense coding sessions vs fragmented micro-dictations

Output format:
- Work session summary (what was worked on)
- Key technical decisions captured in dictation
- Context-switching frequency assessment
- Productivity pattern observations

## Soft Skills Mode

Analyze these dictation samples focusing on interpersonal and communication patterns:

1. **Communication style**: Formal vs informal, directive vs collaborative
2. **Audience awareness**: How language shifts between apps (Telegram vs Obsidian vs email)
3. **Language choice**: When does the user switch between Russian and English? What triggers it?
4. **Emotional tone in communication**: Enthusiasm, frustration, neutrality across contexts
5. **Relationship signals**: Mentions of people, collaborative language, support-seeking

Output format:
- Communication pattern summary
- Language-switching insights
- Interpersonal dynamics observations
- Audience adaptation notes

## Trends Mode

Analyze the quantitative trends in dictation data:

1. **Volume changes**: Are dictation counts increasing or decreasing?
2. **Time-of-day shifts**: Any changes in when dictation happens?
3. **App migration**: Shifting between tools over time?
4. **Word count trends**: Getting more verbose or more concise?
5. **Session patterns**: Long focused sessions vs short bursts?

Output format:
- Trend summary with direction indicators
- Notable anomalies or pattern breaks
- Comparison to previous period if available
- Behavioral shift hypotheses

## Mental Health Mode

Analyze these dictation samples as behavioral indicators for self-reflection and wellbeing assessment. This is NOT clinical diagnosis -- it's self-awareness support.

1. **Energy proxy**: Word count, speech duration, and activity level as energy indicators
   - High energy: more dictations, longer texts, more diverse apps
   - Low energy: fewer dictations, shorter texts, concentrated in fewer apps
2. **Sentiment signals**: Look for language patterns indicating:
   - Frustration: repetitive corrections, short sharp phrases, negative language
   - Engagement: long explanatory dictations, varied vocabulary, exploratory language
   - Fatigue: declining word count through the day, simpler language later
   - Anxiety: rapid context-switching, fragmented short dictations, repetitive themes
3. **Rumination detection**: Recurring phrases, topics, or concerns across dictations
4. **Activity pattern changes**: Compare to typical patterns if baseline available
5. **Language as mood indicator**: Russian vs English choice may correlate with emotional state
6. **Social engagement**: Communication app usage as connection indicator

Output format:
- Energy assessment (high/medium/low with evidence)
- Emotional tone summary
- Recurring themes/concerns (potential rumination)
- Activity pattern observations
- Self-care signals (breaks, varied activity, social engagement)
- Gentle reflection prompts based on observations

IMPORTANT: Frame all observations as invitations for self-reflection, not diagnoses. Use language like "you might notice..." or "this pattern could suggest..." rather than definitive statements.

## Prosody Mode (audio-based)

Analyze the prosodic features extracted from recorded dictation audio (via `scripts/extract_prosody.py`). This is a peer of the mental mode but works from *how* things were said rather than *what* was said. It is NOT clinical diagnosis -- it is self-awareness support. Only recent dictations retain audio, so always anchor interpretation to the coverage line and treat metrics as gentle proxies, not measurements.

1. **Pitch variability (monotone <-> expressive)**: F0 CV (coefficient of variation = std/mean) is the headline signal.
   - Higher CV / wider F0 range: more varied, expressive intonation -- often tracks engagement, animation, emotional involvement.
   - Lower CV / flatter F0: more monotone delivery -- can accompany fatigue, low energy, focused/transactional dictation, or simply terse commands.
2. **Speaking rate & pause ratio (energy / cognitive-load proxy)**: WPM and pause ratio from timing columns.
   - Faster rate, fewer pauses: higher energy or fluency; can also signal rush/pressure.
   - Slower rate, longer pauses: deliberation, fatigue, or higher cognitive load (searching for words, complex thinking).
3. **Intensity dynamics (loudness)**: Mean and range of dB. Wider intensity range tracks emphasis and expressive dynamics; compressed range can read as flat affect or quiet/tired delivery. Note: absolute dB depends on mic/environment, so trends matter more than levels.
4. **Voice quality (HNR, jitter, shimmer)**: HNR (harmonics-to-noise ratio) is the most interpretable -- lower HNR can track vocal fatigue, strain, or a tired/hoarse voice. Jitter/shimmer are noisy on short clips; use only as weak supporting signals.
5. **Bilingual context**: Russian and English differ in baseline F0 and rate, so always read the by-language split separately -- a higher overall F0 may just reflect more Russian that day, not a mood shift. Compare like-with-like across days.
6. **Daily trend**: Look for within-period drift in F0 CV, WPM, and HNR. A day with notably flatter pitch, slower rate, and lower HNR than the user's recent baseline is worth gently surfacing as a possible low-energy or tired day.

Output format:
- Prosodic energy/expressiveness read (with F0 CV, rate, intensity evidence)
- Voice-quality note (HNR trend, framed gently)
- Language-aware comparison (don't mix RU/EN baselines)
- Day-over-day drift observations from the trend table
- Gentle reflection prompts grounded in the numbers

IMPORTANT: Frame all observations as invitations for self-reflection, not diagnoses. Acoustic features are influenced by microphone, environment, health (a cold), and language -- name this uncertainty. Use language like "you might notice your pitch was flatter on..." or "this could reflect a tired day, or just a quieter room." Honor the bilingual context throughout. Never infer a clinical or mood state as fact.
