# EU / Germany compliance for repos

Practical, repo-level additions for a maintainer **based in Germany / operating
under EU law**. Scope here is what belongs *in a repository*; it does not cover
company-level obligations.

> **Not legal advice.** General principles as of 2026. Most obligations are
> **conditional** — they bite only for commercial activity, personal-data
> processing, AI-facing behaviour, or an operated website. Ask the gating
> questions below and only add what applies. Recommend counsel for anything
> load-bearing.

## Gating questions (ask before adding anything)

1. **Commercial?** Is the software provided in the course of a business activity,
   for a fee, *or in exchange for personal data*? (Donations/sponsorship and
   "free but monetised" are gray — flag them.)
2. **Personal data?** Does the software or its website collect/process any
   personal data (telemetry, analytics, accounts, logs with PII)?
3. **AI-facing?** Does it interact with users *as* an AI, or generate synthetic
   text/image/audio/video?
4. **Operated website?** Is there a project site / landing page / docs site you
   run (not just the GitHub repo)?

Most personal/non-commercial OSS with no data collection needs **none** of the
heavy items — just LICENSE, NOTICE, SECURITY.md, and a clear non-commercial framing.

## 1. Cyber Resilience Act (CRA) — Regulation (EU) 2024/2557

- In force Dec 2024. **Vulnerability/incident reporting from 11 Sep 2026**; full
  compliance **11 Dec 2027**. Penalties up to €15M / 2.5% turnover (commercial).
- **Open-source carve-outs:** software developed/supplied *outside* a commercial
  activity is largely out of scope; a lighter "**open-source software steward**"
  category exists for foundations/orgs supporting projects they don't monetise.
  **Article 64: administrative fines don't apply to OSS stewards** — but
  vulnerability-reporting duties still start Sep 2026.
- **What to add to a repo (good practice for everyone, required for commercial
  "products with digital elements"):**
  - `SECURITY.md` with a private vulnerability-reporting channel and SLA.
  - A **machine-readable SBOM** (SPDX or CycloneDX), covering at least direct
    dependencies. Generate in CI (e.g. `syft`, `cyclonedx`, `cargo-cyclonedx`,
    `npm sbom`). Retain security docs ~10 years for commercial products.
  - Dependency/supply-chain audit in CI (e.g. `cargo-audit`/`cargo-deny`,
    `npm audit`, `pip-audit`) and Dependabot.
  - Coordinated vulnerability-disclosure policy; GitHub "Private vulnerability
    reporting" enabled.

## 2. AI Act — Regulation (EU) 2024/1689 (Article 50 transparency)

- **Article 50 transparency applies 2 Aug 2026.**
- Applies **only if the software is AI-facing**:
  - Systems that interact with people **must disclose they are AI** (unless
    obvious).
  - Generators of **synthetic audio/image/video/text must mark output** as
    artificially generated in a **machine-readable** format.
- Limited open-source exemption exists for some GPAI documentation duties.
- **What to add (only if AI-facing):** an "AI transparency" note in README/docs
  stating the system is AI and how outputs are marked; implement output marking
  (e.g. C2PA / metadata) where you generate synthetic media.

## 3. Impressum — German DDG (ex-TMG)

- The Telemediengesetz was renamed **Digitale-Dienste-Gesetz (DDG)** (DSA
  alignment, 2024). It requires an **Impressum** (imprint) for *geschäftsmäßige*
  (business-like) telemedia — name, postal address, email, and where applicable
  registry/VAT details.
- A bare GitHub repo is generally not "geschäftsmäßig"; the obligation typically
  attaches to an **operated project website**, or when the project is commercial
  / monetised / donation-driven.
- **What to add (if you run a project site or it's commercial):** an `IMPRESSUM`
  (in repo as `IMPRESSUM.md` and/or on the site) with the required identity
  details. Several community templates exist (search "Impressum GitHub template").

## 4. GDPR — Regulation (EU) 2016/679

- Applies **only when personal data is processed** (incl. via a website with
  analytics, accounts, telemetry, or server logs with PII).
- **What to add (only if data is collected):**
  - `PRIVACY.md` / privacy policy in clear language: what's collected, why, legal
    basis, retention, user rights, contact.
  - A **data-flow description** (what leaves the device, to whom).
  - For local-first/no-collection software, a short explicit statement —
    *"collects no personal data; nothing is sent off-device"* — is valuable and
    low-cost.
  - Contributions: a DCO (`Signed-off-by`) or CLA is part of a clean posture.

## 5. Product Liability Directive — (EU) 2024/2853

- Software is now explicitly a **"product."** In force Nov 2024; Member-State
  transposition by **9 Dec 2026**.
- **OSS exemption:** software "developed or supplied **outside a commercial
  activity**" is exempt from strict liability. **But** a chargeable service —
  *or a service in exchange for personal data* — revives product status, and
  **commercial products built on your OSS are fully covered.**
- **What to add:** keep the **non-commercial framing explicit** in LICENSE/NOTICE;
  for anything commercial, pair with security docs and threat modelling.

## 6. European Accessibility Act (EAA) — Directive (EU) 2019/882

- Applies from **28 Jun 2025** to certain **consumer-facing products/services**
  (e-commerce, consumer apps) placed on the market commercially. Likely
  irrelevant to a dev tool / library; **flag it only for consumer-facing
  commercial software** and recommend an accessibility review then.

## Suggested repo artifacts by trigger

| Trigger | Add |
|---|---|
| Always (EU maintainer) | `LICENSE`, `NOTICE`, `SECURITY.md`, clear non-commercial framing |
| Commercial / "product with digital elements" | SBOM in CI, supply-chain audit, CRA vuln-reporting process, 10-yr doc retention |
| AI-facing | AI-transparency note + machine-readable output marking |
| Operated website or commercial | `IMPRESSUM.md` (DDG) |
| Processes personal data | `PRIVACY.md` + data-flow description |
| Local-first, no data | One-line "collects no data" statement |
| Consumer-facing commercial | Accessibility (EAA) review |

## Sources

- CRA: [OpenSSF](https://openssf.org/category/policy/cra/) · [Red Hat](https://www.redhat.com/en/blog/eu-cyber-resilience-acts-impact-open-source-security) · [BCLP](https://www.bclplaw.com/en-US/events-insights-news/the-cyber-resilience-acts-obligations-for-open-source-software.html)
- SBOM/CRA: [Anchore](https://anchore.com/sbom/eu-cra/) · [OPSWAT](https://www.opswat.com/blog/eu-cyber-resilience-act-cra-a-roadmap-to-software-supply-chain-and-sbom-compliance)
- AI Act: [Linux Foundation Europe](https://linuxfoundation.eu/newsroom/ai-act-explainer) · [Article 50](https://artificialintelligenceact.eu/article/50/)
- Impressum/DDG: [Wikipedia: Impressum](https://en.wikipedia.org/wiki/Impressum) · [Win With Words (2024 update)](https://www.winwithwords.nl/blog/update-your-german-impressum-2024)
- GDPR + OSS: [TermsFeed](https://www.termsfeed.com/blog/gdpr-open-source/) · [FreePrivacyPolicy](https://www.freeprivacypolicy.com/blog/open-source-projects-gdpr/)
- Product Liability: [Hogan Lovells](https://www.hoganlovells.com/en/publications/eu-introduces-comprehensive-digitalera-product-liability-directive) · [Cycode](https://cycode.com/blog/new-eu-product-liability-directive/)
