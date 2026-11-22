# Copy

## Budgets (880 px safe box)
| role | budget | why |
|---|---|---|
| hook line (`data-fill`) | the style's `type.fill_chars` (6 in `pop` … 12 in sentence-case serif; 10 for condensed caps) | above it a line drops under 140 px and stops reading as a headline — the budget is measured per font, case and language by `style.py calibrate` |
| caption plate | ≤ 15 chars/line, ≤ 4 lines (~60) | 90–150 px, readable in ~1 s |
| transcript / mono line | ≤ 22 chars/line | |
| CTA action | 2–4 words | see "CTA" below |

The audit fails with `REWRITE` instead of shrinking type. Shorten; don't override.

## Slide anatomy
- **hook**: 3 stacked lines (bold / light / light), red rule, then title (−1 step), `[date] venue` (−2), button (−2). Works as the cover frame too.
- **cta**: kicker ("<venue> показывает"), title (fill), big date (fill, capped), action line.
- **caption**: accent plate at the top of the safe zone + optional white label at the bottom ("режиссёр: …").

## Humor for silent footage
Silent rehearsal footage has no lines to quote, so humor comes from the edit and the text:
- **Juxtaposition**: action → reaction cut (grimace → deadpan partner).
- **Repetition**: the same gesture/shout three times, counter in a caption ("в 9-й раз").
- **Deadpan stage directions** in documentary style: "(пауза 14 секунд)", "(поёт. Слова неизвестны даже ей)".
- **Mislabeling with love**: "Актёр показывает, как понял задачу режиссёра".
Joke about the process (rehearsal, actors, director), not about the real people whose stories a documentary show tells. Check the show's tone with the user.

## CTA
Name, date, place, action — every reel. If time/link are unknown, use "ссылка в профиле" / "link in bio" and don't invent a time.

| kind | hook button | CTA action line |
|---|---|---|
| show, concert, screening | Купить билет · Get tickets | Билеты — в профиле → |
| workshop, course, lecture | Записаться · Sign up | Запись — ссылка в профиле → |
| free event, opening | Приходите · Join us | Вход свободный, регистрация в профиле → |
| product, drop, launch | Заказать · Shop now | В продаже с 16.11 → |
| fundraiser | Поддержать · Donate | Поддержать — ссылка в профиле → |

Humour and tone follow the event: the patterns below are for performance/rehearsal footage; for products and courses prefer before/after and "process" captions over jokes about people.

## Learned in use
<!-- appended by scripts/learn.py — newest last -->

- **2026-11-14 · error** — Configure slide motion separately from footage motion, and configure the CTA date color independently from the main theme ink; preserve static slides when the brief requires them.
  _Evidence:_ Static slides required a local build script adjustment; the CTA date required a separate theme to match the requested black.
