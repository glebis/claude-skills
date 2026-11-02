---
name: review-humane
description: Dedicated design-review subskill for a review workflow or direct invocation. Delegates evidence-based UI and document review to the installed Humane review pipeline; adds an Apple Human Interface Guidelines lens when requested. Use for Humane or holistic interaction review, not general code review or human annotation.
---

# Humane review subskill

Announce that you are using `review-humane`, identify the artifact and the requested review boundary, and keep review read-only unless fixes are separately requested. A parent review can invoke this subskill and consume its consolidated findings; it does not authorize implementation or external actions.

## Resolve the owning review skill

Locate the installed Humane review entrypoint: prefer an explicitly supplied skill path or the active `lab-coach:review` / `humane:review` installation. In Codex, search the installed lab-coach plugin's `skills/review/SKILL.md` beneath `~/.codex/plugins/cache/claude-code-lab-coach/`; use the active installation, not a hard-coded cache version or merely the highest directory name. Other hosts may expose it directly as a named skill. Read its entrypoint and the domain references it requires.

Do not confuse `human-review` (a browser annotation tool) with Humane design review. Do not copy or maintain a second set of Humane rules here. If the owner or a domain skill is unavailable, name the gap; do not substitute remembered rules or silently declare a pass. Do not install or change plugins merely to satisfy this dependency.

## Run and integrate

Follow the owning review skill's artifact routing, mode, browser evidence contract, domain order, severity, and output format. Preserve the task/actor and research provenance; distinguish live evidence, screenshots, source inspection, and unbuilt concepts. Label untested concept concerns as design risks, not observed failures.

When called by a parent review, return scope/coverage, one prioritized findings table with durable evidence locators and owning domains, verification gaps, considered-but-rejected candidates, and the scoped verdict. Consolidate duplicate root causes with the parent's findings. Keep Nielsen scores and the shared review severity distinct if both are reported.

## Optional Apple lens

When the user or parent requests Apple HIG/HCI review, read [references/apple-hig.md](references/apple-hig.md) and verify relevant guidance against Apple's current official documentation. Add source links to the affected claims. Treat this as a supplementary lens, not a replacement for the owning Humane domains, and consolidate overlap once.

For a web interface, distinguish transferable principles from native-platform requirements. Neither Apple HIG inspection nor Humane review establishes accessibility conformance or usability-test success. Read-only review does not require triggering live destructive or externally visible actions; report such verification gaps honestly.
