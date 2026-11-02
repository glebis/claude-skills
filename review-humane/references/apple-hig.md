# Apple Human Interface Guidelines review lens

Use only for an explicitly requested Apple HIG/HCI lens. Check current official pages; these links are entry points, not a frozen policy copy.

- [Design principles](https://developer.apple.com/design/human-interface-guidelines/design-principles): hierarchy, recognizable controls, focused tasks.
- [Layout](https://developer.apple.com/design/human-interface-guidelines/layout): grouping, adaptation, progressive disclosure.
- [Disclosure controls](https://developer.apple.com/design/human-interface-guidelines/disclosure-controls): essential content visible, secondary details available when needed; distinguish general disclosure from native disclosure-button rules.
- [Buttons](https://developer.apple.com/design/human-interface-guidelines/buttons): action hierarchy, understandable labels, pending-action feedback.
- [Alerts](https://developer.apple.com/design/human-interface-guidelines/alerts): interruption proportional to consequence. Routine undoable actions should not acquire automatic confirmation alerts; uncommon irreversible destructive actions need protection.
- [Undo and redo](https://developer.apple.com/design/human-interface-guidelines/undo-and-redo): predictable, scoped recovery. Never promise undo or rollback that the implementation lacks.
- [Feedback](https://developer.apple.com/design/human-interface-guidelines/feedback): status and outcomes at the appropriate level of interruption.

For each actionable observation, record artifact evidence, applicable Apple guidance, user impact, and proposed change. Explicitly label reviewer inference and unbuilt-design risks. Do not infer native platform compliance from a web screenshot, apply point dimensions as universal CSS requirements, or recommend an Apple visual style merely to appear compliant. Do not copy Apple's documentation wholesale.

Apple and Humane recommendations may differ: explain the applicable context rather than erasing the difference. In particular, prefer recoverability for routine actions over a universal “confirm everything” rule. Keep any final verdict scoped to the evidence and disclose untested device, keyboard, assistive-technology, and error states.
