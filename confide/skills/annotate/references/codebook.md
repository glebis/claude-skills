# CONFIDE — PII annotation codebook (v1)

The rulebook for labelling personally-identifying information (PII) in therapy/counselling
transcripts, so that **independent annotators produce comparable gold** and we can measure
inter-annotator agreement (IAA) and adjudicate disagreements. Applies to RU and EN (and is
designed to extend to DE/FR/ES). Pairs with `HARM-TAXONOMY.md` (severity) and the schema in
`build_ru_dataset.py` (the fields each span carries). Unsure about a term (PII / ПДн,
quasi-identifier, span, IAA…)? See the bilingual EN↔RU **[GLOSSARY.md](GLOSSARY.md)**.

> **Why a codebook?** PII labelling is subjective at the edges ("is *a small gym in town* a
> location?"). Disagreement almost always traces to an unclear rule, not a careless
> annotator — so this document *is* the experiment. When you hit a case the codebook doesn't
> cover, **log it** (don't guess silently); it becomes a new rule at adjudication.

---

## 1. What you are doing

For each transcript, mark every **span** of text that is, or helps identify, a real person
(here: the client, or third parties they mention). For each span record: **type**,
**direct/quasi** class, **entity id** (which real-world person/thing it refers to),
**person role**, and **harm level**. You do **not** rewrite or redact — only label.

**Unit = the minimal text span** that carries the identifier, by character offsets.

## 2. The type taxonomy (10 types)

| Type | Mark when it is… | Examples (label the **bold**) |
|---|---|---|
| **PERSON** | any personal name / patronymic / surname / initials / unique nickname of a real individual | **Марина Волкова**, **Dr. Lee**, **my brother Alexey** (mark *Alexey*, not "my brother") |
| **LOCATION** | a place that narrows who someone is: city, district, street, venue, small institution-as-place | **Kostroma**, **Тверская**, **the gym on 5th** |
| **ORG** | a named employer, school, company, clinic | **Яндекс**, **gymnasium № 9**, **Acme Corp** |
| **PHONE** | a phone number, digits or spelled-out | **+7-916-555-21-43**, **"plus seven, nine one six…"** |
| **EMAIL** | an email address | **marina.volkova@example.ru** |
| **ID** | structured IDs: passport, SNILS/INN, policy/account/case numbers, usernames/handles | **7722-4455-8811**, **@handle**, spelled-out policy numbers |
| **DATE** | a date that ties to the person: birth date, a specific session/event date, **relative dates** | **15 января**, **"last Tuesday"**, **03.02.2026** |
| **MEDICATION** | a named drug (implies a diagnosis → sensitive) | **сертралин**, **fluoxetine** |
| **AGE** | the person's age, digits or spelled-out | **"тридцать четыре"**, **34**, **"I'm 41"** |
| **PROFESSION** | a specific job/role that narrows identity, incl. seniority | **маркетолог**, **backend tmlid**, **UX designer** |

If a span fits two types, pick the **more specific identifier** and log it (e.g. a username
that is also a name → ID if it's the login form, PERSON if it's the spoken name).

## 3. Direct vs quasi-identifier (the `identifier_class` field)

- **direct** — identifies a person *largely on its own*: full name, email, phone, ID, exact address.
- **quasi** — identifies only *in combination* with others: age, profession, city, employer, a single given name, a date. Most re-identification risk lives here — label diligently.

Rule of thumb: *Could a stranger find this one person from this span alone?* Yes → direct. Only-with-other-facts → quasi.

## 4. Span boundary rules

- Include **inflectional endings** (RU): label **Марин**у, **Калуг**е as the whole word.
- Include **titles/patronymics** when they're part of the reference: **Дмитрий Олегович**, **Dr. Lee** (include "Dr.").
- Multi-token names = **one span**: *Марина Волкова* is a single PERSON span.
- Do **not** include surrounding role words: in "my boss **Dmitry**", label only *Dmitry*.
- Spelled-out numbers (phone/policy/age) = label the **whole spoken sequence** as one span.
- Punctuation/`@`/domain are **part of** EMAIL/ID/handle spans.

## 5. Entity id & coreference (`entity_id`)

Every span gets an `entity_id` grouping **all mentions of the same real-world thing** across
the transcript (and the session series). "Marina", "Marina Volkova", "she" (if you label
pronouns — see §8) → same `entity_id`. Distinct people who share a first name get **distinct**
ids. This is what makes *entity-level recall* ("every mention masked") computable.

## 6. Person role (`person_role`)

Mark whose identity it is:
- **client** — the help-seeker (the protected person).
- **partner / relative / friend** — named third parties in the client's life.
- **clinician** — therapist/doctor named in the text.
- **third_party** — bosses, colleagues, acquaintances.
- **institution** — for ORG/LOCATION (employer, school, clinic).

## 7. Harm level (`harm`) — see `HARM-TAXONOMY.md`

Assign each span a coarse, qualitative severity. Default by type, escalate by context:
- **critical** — exposure endangers/re-traumatizes: abuser/perpetrator names; a survivor's
  location; identity tied to a stigmatised/illegal/safety-sensitive disclosure.
- **high** — MEDICATION, PERSON (the client, or a named third party + a sensitive disclosure).
- **medium** — quasi-identifiers: LOCATION, PROFESSION, ORG, AGE, DATE.
- **low** — EMAIL, PHONE, URL, ID/handle (strong linkers, low *content* harm, rare in speech).

When a span is on the boundary, **escalate and log it** for adjudication.

## 8. Edge-case rulings (the part that causes disagreement)

1. **Pronouns / definite descriptions** ("she", "my eldest"): **do NOT label** as PII spans —
   they're not identifiers on their own. (They matter for coreference but aren't masked.)
2. **Public figures / brands as references** ("like Putin", "works like at Google" as a simile,
   a book title): **not PII** unless it's actually *this* person's employer/identity.
3. **Generic role nouns** ("мама", "a colleague", "the doctor" with no name): **not PII**.
4. **Relative dates** ("last Tuesday", "two weeks ago" only if it pins a specific date in
   context): **label as DATE, quasi**. Vague durations ("for years") → not PII.
5. **Age**: label both spelled ("сорок один") and bare digit ("41") **when it's the age** —
   but a bare number that is a quantity ("41 tasks") or a timestamp (00:08:41) is **not** AGE.
6. **Spelled-out structured values** (policy/phone read aloud): label as ID/PHONE — these are
   real PII the regex layer can't catch, so human labelling matters most here.
7. **Nested values** (name inside an email, `timur` in `timur.kh@…`): label the **outer
   structured span only** (the EMAIL); do not also mark the substring as PERSON.
8. **Third-party vs client**: label named third parties too (they're identifiable people), with
   the right `person_role`; harm rises when a third party is named *with* a disclosure about them.
9. **Locations at different granularity**: city = quasi; a specific street/venue = direct-ish
   (escalate). A country alone ("Russia") is usually too broad → not labelled unless it narrows.
10. **Sensitive disclosures that aren't a PII type** (trauma, orientation, substance use,
    diagnosis-as-text): **do NOT force a PII type.** Flag them in the `note` field as
    `sensitive-disclosure` for human review — this is a known gap (`HARM-TAXONOMY.md`), not a
    labelling target yet.

## 9. What is NOT PII (do not label)

Pronouns, generic role nouns, common words that happen to match a name, public figures used as
references, vague time spans, round non-identifying quantities, the therapist's clinical
boilerplate. **When unsure, label-and-log** rather than drop silently — adjudication decides.

## 10. Workflow

1. Read the whole transcript once before labelling (context disambiguates).
2. Annotate spans in the provided tool (offsets auto-captured). Set type, class, role, harm,
   and `entity_id` (reuse the id for repeat mentions).
3. Put anything the codebook doesn't cover in the **`note`** field with `QUESTION:`.
4. Work **independently** — do not consult other annotators or any existing gold. Blindness is
   what makes the agreement number meaningful.

## 11. Agreement & adjudication (what happens with your labels)

- We compute **pairwise Cohen's κ** (or **Fleiss' κ** for 3+ annotators) and span/entity-level
  F1 **before** any reconciliation, on the shared sample.
- A senior adjudicator resolves every disagreement into the final **adjudicated gold**, writing
  the ruling back into this codebook (so v2 is sharper). We report **post-adjudication** κ too.
- Target: **κ ≥ 0.8** on the shared sample = a defensible gold standard.

## 12. Privacy for annotators

You only ever see **synthetic** transcripts or **consented** real ones that have been handled
per `ETHICS.md` / `THREE-LOCKS.md`. Do not copy, screenshot, or re-share transcript text.
Raw data stays in the provided environment; only your span labels leave it.

---

*v1 — living document. Every adjudicated edge case is appended here. Cite the version used to
produce a given gold release.*
