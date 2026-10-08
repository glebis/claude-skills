# Live sources and checkpoints

A new talk is a new subfolder and source document. Determine boundaries from the host/speaker introduction and source segment IDs, not just a reset timecode. Some feeds revise segments or reset their clocks mid-talk.

Before splitting, stop the old capture worker. Preserve its source/state snapshot. New capture baseline must include BOTH earlier talk IDs and the previous worker's baseline; otherwise earlier speeches will reappear in the new source. Inspect first and last segment and verify no earlier speaker leaked into the new range. Resume capture in the new folder.

Track reviewed IDs and revisions/digests, not only counts: a previously seen segment may have changed. Update claims derived from revised segments. Put runtime checkpoints outside a declared OKF bundle, or under a non-Markdown state directory; they are not concept notes.

Use a requested 30-second availability target for capture where the source allows it; measure and report delay rather than promise every utterance meets it. Capture may be automatic while model curation is request-driven. Report a frozen source cutoff for each summarisation. Do not mark unread future segments reviewed while a live feed grows.

Wispr/Granola capture adapters are separate integrations. This plugin does not supply a recorder, timer, background model service, or credentials. Use an available connector or the user's authorised local source. An unresolved speaker/tool name stays provisional. Non-source claims, questions, and experiments are explicitly interpretations or proposals.
