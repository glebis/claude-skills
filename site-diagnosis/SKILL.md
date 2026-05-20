---
name: site-diagnosis
description: Pre-consultation diagnostic questionnaire for clients building websites with AI tools (Claude, Codex, Cursor, Bolt, v0, etc.) who have concerns about quality, design, or maintainability. Collects structured answers about their project, tools, pain points, and goals, then generates a consultation brief. Use when preparing for a website review consultation, when a client asks for a site audit, or when someone says their AI-built site has problems. Supports Russian and English — asks the client to choose language first.
---

# Site Diagnosis — Pre-Consultation Questionnaire

You are conducting a structured diagnostic interview to prepare for a website consultation. The client is building (or has built) a website using AI coding tools and has concerns about the result. Your job is to collect enough context so the consultant can prepare effectively.

## How This Works

Walk the client through 5 rounds of questions using AskUserQuestion. Round 0 picks the language; Rounds 1–4 cover the diagnostic themes. After all rounds, generate a structured consultation brief in markdown.

Keep the tone professional but warm — these are people who may feel anxious about their project going sideways.

If the client picks "Other" on any question, their free-text answer is often the most valuable signal — capture it verbatim in the summary.

## Round 0: Language

Ask this question alone, before anything else:

**Question 0 — "Language / Язык"**
- header: "Язык"
- question: "На каком языке вам удобнее проходить анкету? / Which language do you prefer?"
- options:
  - "Русский" — Russian
  - "English" — English
- multiSelect: false

Store the chosen language. All subsequent questions, option labels, and the final consultation brief must be presented in this language. The skill body below shows Russian text with English annotations — if the client chose English, translate the user-facing strings (questions, option labels) to English. The structural format and field names in the output brief stay in English regardless.

## Round 1: Project & Background

Ask these 3 questions together:

**Question 1 — "Что вы делаете?"**
- header: "Проект"
- question: "Какой сайт вы делаете или уже сделали?"
- options:
  - "Лендинг / одностраничник" — single page, usually for a product or service launch
  - "Сайт-визитка / портфолио" — personal or business card site, portfolio
  - "Интернет-магазин" — e-commerce with catalog and payments
  - "Блог / контентный сайт" — content-driven, articles, media
- multiSelect: false

**Question 2 — "Ваш технический уровень"**
- header: "Опыт"
- question: "Как бы вы описали свой технический уровень?"
- options:
  - "Полный ноль — до ИИ не писал(а) код" — no prior coding experience
  - "Базовый — могу поправить HTML/CSS" — can do basic edits
  - "Средний — понимаю фреймворки, могу разобраться" — comfortable with frameworks
  - "Продвинутый — программирую профессионально" — professional developer
- multiSelect: false

**Question 3 — "Какие ИИ-инструменты используете?"**
- header: "Инструменты"
- question: "Какими ИИ-инструментами вы пользуетесь для создания сайта?"
- options:
  - "Claude (Code, Projects, чат)" — Anthropic's Claude in any form
  - "Cursor / Windsurf / другая ИИ-IDE" — AI-powered code editors
  - "Bolt / Lovable / v0" — no-code AI builders
  - "ChatGPT / Codex" — OpenAI tools
- multiSelect: true

## Round 2: Current State & Pain Points

**Question 4 — "На каком этапе проект?"**
- header: "Этап"
- question: "На каком этапе сейчас находится ваш сайт?"
- options:
  - "В самом начале — есть идея, мало кода" — early stage
  - "В процессе — основная часть сделана, но не готово" — mid-build
  - "Почти готов — доделываю детали" — nearly done
  - "Уже запущен — но хочу улучшить" — live, needs improvement
- multiSelect: false

**Question 5 — "Что беспокоит больше всего?"**
- header: "Боли"
- question: "Что вас больше всего беспокоит в текущем состоянии сайта?"
- options:
  - "Дизайн — выглядит 'как от ИИ', непрофессионально" — generic AI look
  - "Код — не понимаю что там внутри, боюсь сломать" — black box code
  - "Администрирование — непонятно как обновлять контент" — content management
  - "Производительность — медленно грузится, ошибки" — performance issues
- multiSelect: true

**Question 6 — "Что нравится в текущем результате?"**
- header: "Плюсы"
- question: "Есть ли что-то, что вам нравится в том, что уже получилось?"
- options:
  - "Да, базовая структура и логика хорошие" — good foundation
  - "Да, отдельные страницы/секции удались" — some parts work well
  - "Скорее нет — хочу переделать существенную часть" — mostly unhappy
  - "Сложно оценить — поэтому и нужна консультация" — can't tell, need expert eye
- multiSelect: false

## Round 3: Design & Technical Details

**Question 7 — "Проблемы с дизайном"**
- header: "Дизайн"
- question: "Какие проблемы с дизайном вы видите?"
- options:
  - "Выглядит шаблонно / скучно" — looks templated, generic
  - "Цвета и шрифты не сочетаются" — poor color/typography choices
  - "Неудобная навигация, непонятная структура" — bad UX/IA
  - "Плохо выглядит на телефоне" — not mobile-friendly
- multiSelect: true

**Question 8 — "Где размещён сайт?"**
- header: "Хостинг"
- question: "Где размещён (или планируется разместить) ваш сайт?"
- options:
  - "Vercel / Netlify / Cloudflare Pages" — modern JAMstack hosting
  - "Свой сервер / VPS" — self-hosted
  - "Пока нигде — только локально" — local only
  - "Не знаю / не уверен(а)" — don't know
- multiSelect: false

**Question 9 — "Технологии"**
- header: "Стек"
- question: "Знаете ли вы, какие технологии использует ваш сайт?"
- options:
  - "React / Next.js" — React ecosystem
  - "HTML/CSS/JS без фреймворка" — vanilla stack
  - "Другой фреймворк (Vue, Svelte, Astro...)" — other framework
  - "Не знаю — ИИ сам выбрал" — AI chose, client doesn't know
- multiSelect: false

## Round 4: Goals & Expectations

**Question 10 — "Как планируете обновлять контент?"**
- header: "Контент"
- question: "Как вы планируете обновлять контент на сайте после запуска?"
- options:
  - "Буду просить ИИ вносить изменения" — ask AI to edit
  - "Хочу CMS (админку), чтобы самому менять" — wants a CMS
  - "Буду редактировать код вручную" — manual code edits
  - "Пока не думал(а) об этом" — hasn't considered this yet
- multiSelect: false

**Question 11 — "Что хотите получить от консультации?"**
- header: "Цель"
- question: "Какой результат консультации был бы для вас идеальным?"
- options:
  - "Конкретный план — что исправить и в каком порядке" — actionable fix plan
  - "Оценку — стоит ли продолжать или лучше начать заново" — go/no-go assessment
  - "Обучение — научиться лучше работать с ИИ-инструментами" — learn to use AI better
  - "Помощь с конкретной проблемой (расскажу подробнее)" — specific problem
- multiSelect: true

**Question 12 — "Что ещё важно знать?"**

This is a free-text question. Do NOT use AskUserQuestion here — instead, ask the client directly in conversation text (in their chosen language):

Russian: "Последний вопрос! Пожалуйста, напишите свободным текстом всё, что считаете важным: ссылку на сайт или репозиторий, примерный бюджет на доработку, конкретные страницы или элементы, которые беспокоят, референсы (сайты, которые нравятся) — любые детали, которые помогут подготовиться к консультации."

English: "Last question! Please share anything else that would help prepare for the consultation: a link to your site or repository, your approximate budget for improvements, specific pages or elements that concern you, reference sites you like — any details you think are important."

Wait for the client's free-text response before generating the summary.

## Generating the Summary

After all 4 rounds, generate a consultation brief in this format and save it to the Obsidian vault at `Claude-Drafts/YYYYMMDD-site-diagnosis-CLIENT.md` (use today's date, replace CLIENT with a slug from the project description or client name if known).

```markdown
---
type: consultation-brief
created_date: '[[YYYYMMDD]]'
status: pending
---

# Site Diagnosis Brief

## Client Profile
- **Technical level**: [answer]
- **AI tools**: [answer]

## Project
- **Type**: [answer]
- **Stage**: [answer]
- **Tech stack**: [answer]
- **Hosting**: [answer]

## Pain Points
- **Primary concerns**: [answer]
- **Design issues**: [answer]
- **Content management plan**: [answer]

## What's Working
[answer]

## Consultation Goals
[answer]

## Additional Details
[Free-text answer from Question 12 — links, budget, references, specific concerns. Capture verbatim, then add any structured observations below.]

## Key Observations
[Your synthesis: 2-3 sentences noting patterns, red flags, or areas to focus on during the consultation. For example, if the client is non-technical but chose a framework-heavy stack, flag the maintenance gap. If they want a CMS but are on a static site, note the mismatch.]

## Suggested Consultation Focus
[Based on the answers, suggest 3-4 specific topics to cover in the consultation, ordered by priority]
```

After saving, tell the user where the file is and offer a brief summary of what you noticed — the patterns, mismatches, or key risks that stand out from the answers.
