# Open Knowledge Vault

An agent plugin for portable knowledge work: create a bundle, curate source-grounded notes, keep links and indexes useful, and inspect basic OKF structure. Optional Obsidian setup and Dataview views sit on top of ordinary Markdown and YAML.

## Use

Install this local plugin through your agent's plugin workflow, or expose `skills/open-knowledge-vault` as an individual skill. Invoke `open-knowledge-vault` with a destination and a purpose: a meeting, learning goal, research corpus, or project.

```sh
python3 skills/open-knowledge-vault/scripts/vault.py init /path/to/bundle --title "Creative design" --profile meeting
python3 skills/open-knowledge-vault/scripts/vault.py audit /path/to/bundle
```

The helpers require Python 3.10+ and PyYAML. Install dependencies in your preferred isolated environment. Add `--obsidian --dataview` to setup for a dashboard with static navigation and query blocks. To install a chosen existing Dataview build:

```sh
python3 skills/open-knowledge-vault/scripts/vault.py dataview /path/to/bundle --from-plugin /path/to/dataview
```

Dataview is not bundled and is not required. New installations disable JavaScript queries, preserve the other plugin IDs, and require a rendered activation check in Obsidian. A plain bundle does not create `.obsidian` at all.

## Scope

Version 0.1.0 is a local agent plugin, not an Obsidian application plugin. It provides setup, maintenance instructions, and basic structural audit; it does not supply a recorder, unattended model worker, hosted service, payment system, full attestation validator, or automatic migration of existing originals.

`learning-vault` remains the study-specific entry point. Existing vaults are inspected before adaptation; conversion of wikilinks, lifecycle fields, templates, and tool instructions is an explicit migration step.

## Product direction

Keep the format open and charge for useful implementation: onboarding, migration, maintained team knowledge, source integrations, and training. Pricing and demand are not validated. No official Google affiliation or OKF certification is implied. See the product reference for the proposed service tiers.

## Specification

Target: [Open Knowledge Format v0.2](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md), checked 8 October 2026. The plugin follows the containing skills repository's licence for its own code; third-party components are separately licensed. No third-party runtime binaries are redistributed here.
