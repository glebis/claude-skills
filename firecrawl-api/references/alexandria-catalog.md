# Firecrawl Alexandria catalog

Snapshot 2026-10-18T19:41:28+02:00 · catalogue `sha256:7aa4b94397c0…` · 30 categories · 302 providers · 1850 tools.

Built with `scripts/build_catalog.py` from free find-tools listings. Prices are the listed `creditsCost` at snapshot time; check `contract` before running. A listed tool is not proof that it covers your market or inputs.

## Categories

| Category | Providers | Tools | What it covers |
| --- | --- | --- | --- |
| [agriculture](#agriculture) | 2 | 11 | Agriculture and food statistics: crop and livestock production, producer prices, trade, food balances, food s… |
| [ai-models](#ai-models) | 7 | 44 | Machine-learning models and datasets: cards, licenses, downloads, tasks, tags and files. |
| [apps](#apps) | 6 | 38 | Mobile apps on the Apple App Store and Google Play: listings, ratings, review counts, charts, reviews and ver… |
| [automotive](#automotive) | 2 | 11 | Cars for sale: dealer and private-seller inventory, listing details and book values. |
| [companies](#companies) | 63 | 458 | Company records, filings, funding and firmographics. |
| [developer](#developer) | 1 | 1 | Developer documentation, repositories, code and agent skills. |
| [digital-intelligence](#digital-intelligence) | 1 | 8 | Website traffic, audience, search marketing and competitive digital intelligence. |
| [energy](#energy) | 1 | 7 | Energy statistics: official supply, demand, generation, emissions and price series from agencies such as the … |
| [entertainment](#entertainment) | 8 | 39 | Films, TV shows, books and games: ratings, cast, release dates, reading lists. |
| [finance](#finance) | 35 | 347 | Market prices, financial statements, ownership and macro rates. |
| [government](#government) | 115 | 660 | Government programs and records: federal funding and procurement opportunities, eligibility, who is buying wh… |
| [health](#health) | 6 | 18 | Population health statistics: life expectancy, mortality, disease burden, immunization coverage, risk factors… |
| [healthcare](#healthcare) | 2 | 12 | Healthcare providers and facilities: identifiers, specialties, licenses, practice locations and official regi… |
| [jobs](#jobs) | 11 | 41 | Job postings: who is hiring for which roles, where, and since when. |
| [knowledge](#knowledge) | 1 | 7 | Encyclopedic and reference knowledge: articles, facts about entities, definitions and their sources. |
| [marketing](#marketing) | 7 | 144 | Marketing research: website traffic, search interest and trends, audience insights, creator discovery and pod… |
| [news](#news) | 8 | 57 | Reported news: articles, wires and the archives behind them. |
| [people](#people) | 10 | 156 | The people at companies: who they are, what they do, and how to reach them. |
| [places](#places) | 24 | 127 | Local businesses and places: what is near an address, with hours, phone, address, website, rating and review … |
| [podcasts](#podcasts) | 1 | 105 | What was said on a podcast: episodes, transcripts, guests and sponsors. |
| [political-science](#political-science) | 1 | 7 | Political-science research data: democracy and regime indices per country-year, their codebooks, uncertainty … |
| [real-estate](#real-estate) | 12 | 68 | Property records and home valuation comparables. |
| [research](#research) | 1 | 4 | Scientific papers, abstracts, relevant full-text passages and citation relationships. |
| [restaurants](#restaurants) | 9 | 56 | Restaurant locations, opening hours, menus, prices and product options. |
| [shopping](#shopping) | 54 | 287 | Products, prices, sizes, availability and customer reviews. |
| [skills](#skills) | 3 | 13 | Website instructions and source files for agents and browser interactions. |
| [social](#social) | 7 | 44 | Public social media accounts: profiles, follower counts, posts, hashtags, boards and pins. |
| [software](#software) | 5 | 23 | Open-source packages: registry metadata, versions, licences, download counts and dependents on npm, PyPI, cra… |
| [sports](#sports) | 14 | 78 | Sports federations and circuits: tournament calendars, match results and player rankings. |
| [travel](#travel) | 21 | 114 | Travel: hotels, their guest ratings, rankings in a destination and public reviews. |

## agriculture

Agriculture and food statistics: crop and livestock production, producer prices, trade, food balances, food security, land use, fertilizers and agrifood emissions.

<a id="p-afcd-foodstandards-gov-au"></a>

### Australian Food Composition Database (AFCD, FSANZ) (`afcd-foodstandards-gov-au`)

Food Standards Australia New Zealand's Australian Food Composition Database (AFCD Release 3.0, December 2025), the reference nutrient database for Australia: about 1,600 foods with up to 268 nutrients each (proximates, minerals, vitamins, fatty acids, amino acids, organic acids) per 100 g, with derivation and sampling notes, AUSNUT classification and food groups. Food search by name, letter or gr…

| Capability | Credits | Use |
| --- | --- | --- |
| `foods/foods_by_nutrient` | 5 | To rank or compare foods by a nutrient, e.g. iron (FE) across ready-to-eat breakfast cereals (sub_food_group_id 30), sodium (NA) in cheeses… |
| `foods/get_food` | 5 | After search_foods, list_foods_in_group or foods_by_nutrient returned a pfk, or when the user pastes an AFCD food URL. Answers 'nutrients i… |
| `foods/list_food_groups` | 5 | To discover the group and sub group ids before filtering or listing foods by category (e.g. find 'Breakfast cereals, ready to eat'). |
| `foods/list_foods_in_group` | 5 | To enumerate every food in a category with its provenance notes, e.g. all yeast extract spreads (2/11) or all ready-to-eat breakfast cereal… |
| `foods/list_nutrients` | 5 | To find the nutrient code for foods_by_nutrient (e.g. 'iron' -> FE, 'sodium' -> NA, 'energy' -> ENERGY-04) or to read how AFCD defines a nu… |
| `foods/search_foods` | 5 | To find the AFCD Public Food Key of a food by name (e.g. 'vegemite', 'weet-bix', 'lamb chop'), to list all foods in a group, or to browse f… |

<a id="p-food-nutrition-canada-ca"></a>

### Canadian Nutrient File, Health Canada (food-nutrition.canada.ca) (`food-nutrition-canada-ca`)

Health Canada's Canadian Nutrient File (CNF), the reference food-composition table for Canada: 5,690 foods with up to 152 nutrients per 100 g, Canadian fortification values, serving measures with gram weights, refuse and yield factors, in English or French. Food search by name, the full nutrient record of one food (optionally converted to a chosen measure such as 250ml), the nutrient, nutrient-gr…

| Capability | Credits | Use |
| --- | --- | --- |
| `foods/get_food` | 5 | After `search_foods` or `search_foods_by_nutrient` returned a food code, or when the user pastes a food-nutrition.canada.ca serving-portion… |
| `foods/list_food_groups` | 5 | To pick a `food_group_id` before `search_foods_by_nutrient`, or to list the CNF food groups. |
| `foods/list_nutrients` | 5 | To pick `nutrient_ids` for `get_food` or the `nutrient_id` for `search_foods_by_nutrient`, or to decode unit, group and source codes. |
| `foods/search_foods` | 5 | Start here to find CNF food codes by name, in English or French; then call `get_food` for nutrients and measures. |
| `foods/search_foods_by_nutrient` | 5 | To compare foods on one nutrient ('protein across cheeses': nutrient 203, food group 1), or to list the foods of a food group ranked by a n… |

## ai-models

Machine-learning models and datasets: cards, licenses, downloads, tasks, tags and files.

<a id="p-artificialanalysis-ai"></a>

### Artificial Analysis (`artificialanalysis-ai`)

Artificial Analysis LLM benchmarks: model and reasoning-effort records with Intelligence Index, benchmark scores, cost per task, list prices, output speed and latency, plus per-model and leaderboard-wide API provider endpoint benchmarks.

| Capability | Credits | Use |
| --- | --- | --- |
| `benchmarks/get_model` | 5 | When you have a model slug from search_models (or a pasted /models/{slug} URL) and need the full benchmark record. |
| `benchmarks/list_model_providers` | 5 | To compare where to run a given model: prices and measured speed per provider. Needs a model slug from search_models. |
| `benchmarks/search_models` | 5 | Start here to find a model slug (e.g. `claude-fable-5-1-high`) for get_model or list_model_providers, to rank models by intelligence, price… |
| `benchmarks/search_provider_endpoints` | 5 | To find the fastest or cheapest endpoint for a model, or all models a provider hosts. Use list_model_providers for one model's percentile d… |

<a id="p-arxiv-org"></a>

### arXiv (`arxiv-org`)

arXiv e-print repository: paper search and per-paper metadata through the export.arxiv.org Atom API, category and archive listings, BibTeX export, OAI-PMH metadata harvesting by date window and set, and the list of harvestable sets. Anonymous, no session.

| Capability | Credits | Use |
| --- | --- | --- |
| `papers/get_bibtex` | 5 | Cite a paper found with `search_papers`, `list_category` or `get_paper`. |
| `papers/get_paper` | 5 | Look up one paper by identifier or URL. Use `get_bibtex` for a citation entry and `harvest_records` for the license. |
| `papers/harvest_records` | 5 | Bulk or incremental synchronisation of arXiv metadata by date window, or the only surface that states a paper's license. For topical search… |
| `papers/list_category` | 5 | Browse what was announced in a category, or walk a month's submissions. Identifiers feed `get_paper` and `get_bibtex`. |
| `papers/list_sets` | 5 | Discover valid `set` values for `harvest_records` and category codes for `list_category`. |
| `papers/search_papers` | 5 | Find papers by topic, title, author or category, or find the arXiv identifier that `get_paper`, `get_bibtex` and the listing functions take… |

<a id="p-huggingface-co"></a>

### Hugging Face (`huggingface-co`)

Search Hugging Face models and datasets, inspect repository metadata, and read public model and dataset cards.

| Capability | Credits | Use |
| --- | --- | --- |
| `hub/card` | 5 | The README model or dataset card of one repository at a revision: raw YAML front matter, markdown body, section headings, word count and th… |
| `hub/dataset` | 5 | One dataset repository: canonical id, author, license(s), task categories, languages, size categories, 30-day and all-time downloads, likes… |
| `hub/datasets` | 5 | Search and list datasets by free text, author, task category, language, license, size category and tags, sorted by downloads, likes, trendi… |
| `hub/model` | 5 | One model repository: canonical id, author, license(s), pipeline tag, library, 30-day and all-time downloads, likes, trending score, gating… |
| `hub/models` | 5 | Search and list models by free text, author, task (pipeline tag), library, language, license and tags, sorted by downloads, likes, trending… |

<a id="p-ollama-com"></a>

### Ollama model library (`ollama-com`)

Ollama's public model library at ollama.com: search and browse official and community models, read model pages, tags with download size and context window, per-tag layers with exact byte sizes from the Ollama registry manifest, and GGUF layer metadata (context_length, embedding_length).

| Capability | Credits | Use |
| --- | --- | --- |
| `models/layer_metadata` | 5 | Compare embedding models on true context length and vector dimension, or inspect quantisation per tensor; the `layer_digest` is a model lay… |
| `models/library_models` | 5 | Enumerate official models (about 240) or filter them by a substring such as `embed`; community models are only reachable through search_mod… |
| `models/model` | 5 | Read a model found by search_models or library_models; use model_tags for every tag and tag for one tag's layers and exact byte sizes. |
| `models/model_tags` | 5 | Compare a model's variants (quantisations, parameter sizes) or pick the tag to pass to tag / layer_metadata. |
| `models/namespace_models` | 5 | List what a publisher has uploaded; the namespace comes from a search card's `namespace`. |
| `models/search_models` | 5 | Start here to find official and community models; take `namespace` and `model` from a card into model, model_tags and tag. |
| `models/tag` | 5 | Get exact download bytes and layer digests for a tag; pass a model layer's `short_digest` to layer_metadata for GGUF metadata such as conte… |

<a id="p-openreview-net"></a>

### OpenReview (`openreview-net`)

OpenReview (openreview.net): full-text search over public submissions (title, abstract, authors, venue, PDF/HTML links, BibTeX) and over public reviews, meta-reviews, decisions and comments, the catalog of venues hosted on OpenReview and one venue's public configuration, all through the anonymous, stateless api2.openreview.net (v2) and api.openreview.net (v1) JSON endpoints. Browsing a venue's fu…

| Capability | Credits | Use |
| --- | --- | --- |
| `papers/get_venue` | 5 | Resolve a venue id from list_venues or a `venue_id` from search results into its name, dates and public-submission policy, or check which v… |
| `papers/list_venues` | 5 | Discover the venue group id to pass as `venue` to the search functions or to get_venue, e.g. every ICLR venue with filter `ICLR.cc`. Titles… |
| `papers/search_replies` | 5 | Find public reviews or discussion that mention a topic, or read how a venue's reviewers rated papers on a subject. Review visibility is ven… |
| `papers/search_submissions` | 5 | Find papers by topic, title, author or keyword, or find the forum id and venue id behind a paper. Matching is full-text term matching, not … |

<a id="p-openrouter-ai"></a>

### OpenRouter (`openrouter-ai`)

OpenRouter model catalog and marketplace data: search models by modality, author, provider and price; per-model provider endpoints with pricing, limits, data policy and uptime; effective and listed price history; usage and availability stats; the provider directory; author lineups; and documentation pages such as the Decisions API reference and the Jev decision-model guide. Anonymous public endpo…

| Capability | Credits | Use |
| --- | --- | --- |
| `model-marketplace/get_docs_page` | 5 | To read the typed Decisions API contract, confidence interpretation or any other OpenRouter guide without an API key. The index of all page… |
| `model-marketplace/get_model` | 5 | Verify that a model exists and see which providers serve it at what price; take `canonical_slug` from here into the permaslug-keyed functio… |
| `model-marketplace/get_model_endpoints` | 5 | After get_model, when you need endpoint UUIDs, rate limits, data policy or latency percentiles per provider. |
| `model-marketplace/get_model_pricing` | 5 | To answer 'what does this model cost today and has it changed' for a permaslug from search_models/get_model. |
| `model-marketplace/get_model_stats` | 5 | To judge whether a model is actively used and reliably available before building on it. |
| `model-marketplace/list_author_models` | 5 | To enumerate a vendor's whole lineup (e.g. everything by `typesafe` or `openai`) with permaslugs for the stats functions. |
| `model-marketplace/list_providers` | 5 | To resolve a provider slug for search_models `providers=` or to review data policies across providers. |
| `model-marketplace/search_models` | 5 | Start here to find a model slug and permaslug, e.g. `q=jev, output_modalities=decisions` to check whether the TypeSafe Jev decision model i… |

<a id="p-semanticscholar-org"></a>

### Semantic Scholar (`semanticscholar-org`)

Semantic Scholar's scholarly search and citation graph through its public Academic Graph API: keyword paper search with filters, title matching, paper details by S2 id, DOI, arXiv, PubMed or other identifiers, batch lookups, citations and references with contexts and intents, recommendations, and author search, profiles and publication lists. Anonymous public endpoints only.

| Capability | Credits | Use |
| --- | --- | --- |
| `papers/get_author` | 5 | Author metrics for an author id from a paper's author list or search_authors. |
| `papers/get_author_papers` | 5 | List what an author published; follow with get_paper or get_citations per paper. |
| `papers/get_citations` | 5 | Forward citation expansion: who built on this paper. Newest citing papers come first. |
| `papers/get_paper` | 5 | Details for a paper found through search_papers, match_paper, citations, references, recommendations or an author's list; or to resolve a D… |
| `papers/get_papers` | 5 | Hydrate a list of paper ids, DOIs or arXiv ids (for example the references of several papers) in one request. |
| `papers/get_recommendations` | 5 | Related-work expansion beyond the citation graph. Give `paper_id` for one seed or `positive_paper_ids` (with optional `negative_paper_ids`)… |
| `papers/get_references` | 5 | Backward expansion: the bibliography of a paper with the sentences that cite each entry. |
| `papers/match_paper` | 5 | Resolve a citation string or a title to a Semantic Scholar paper id. |
| `papers/search_authors` | 5 | Find an author id by name before get_author or get_author_papers. Names are ambiguous: check affiliations and counts. |
| `papers/search_papers` | 5 | Discover papers on a topic before calling get_paper, get_citations or get_references. For one known title use match_paper instead. |

## apps

Mobile apps on the Apple App Store and Google Play: listings, ratings, review counts, charts, reviews and version history.

<a id="p-alternativeto-net"></a>

### AlternativeTo (`alternativeto-net`)

AlternativeTo (alternativeto.net): crowd-sourced software catalog. Search apps, list alternatives to an app with platform/license/feature filters, browse the catalog by tag, and read an app's full public record (license, pricing, platforms, features, links, GitHub and App Store stats, ratings and reviews). Anonymous, read-only, English.

| Capability | Credits | Use |
| --- | --- | --- |
| `apps/browse_software` | 5 | Explore a category or feature across the catalog rather than alternatives to one product. |
| `apps/get_alternatives` | 5 | When the user asks for alternatives to a known product; chain from search_software's url_name. |
| `apps/get_software` | 5 | After search_software or get_alternatives returned a url_name, or when the user pastes an alternativeto.net/software/... URL. |
| `apps/search_software` | 5 | Start here to resolve a product name to its url_name, then call get_software for details (structured license, pricing, rating, links) or ge… |

<a id="p-apps-apple-com"></a>

### Apple App Store (`apps-apple-com`)

Apple App Store listings from Apple's own catalog and iTunes APIs: app detail with per-device compatibility (iPhone, iPad, Mac, Apple Watch, Apple Vision), prices and in-app purchase/subscription prices, version history and ratings; paginated customer reviews; keyword search; top charts by genre; a developer's apps.

| Capability | Credits | Use |
| --- | --- | --- |
| `apps/app` | 5 | Verify device or watchOS compatibility, subscription and in-app purchase prices, the current version or release notes of a specific app. |
| `apps/developer_apps` | 5 | List everything one publisher offers, given the developer id from `app`, `search` or a developer page URL. |
| `apps/reviews` | 5 | Read what users say about an app; page with `offset` from `next_offset`. |
| `apps/search` | 5 | Find candidate apps by name or topic before calling `app` for compatibility and subscription detail. |
| `apps/top_charts` | 5 | Rankings: what is popular now in a category or overall on a storefront. |

<a id="p-aptoide-com"></a>

### Aptoide (`aptoide-com`)

Android app metadata from Aptoide: search packages, inspect app permissions, downloads, ratings and signing certificates, and read version history.

| Capability | Credits | Use |
| --- | --- | --- |
| `apps/app` | 5 | Metadata for one Android package on Aptoide: latest APK (version name/code, size, md5, min SDK, signing certificate, malware scan), declare… |
| `apps/search` | 5 | Search Aptoide's Android APK catalog by keyword (app name, developer or package fragment). Returns up to `limit` listings with package name… |
| `apps/versions` | 5 | Version history for one Android package: the APK uploads Aptoide holds across its stores, newest first, each with version name/code, size, … |

<a id="p-github-com"></a>

### GitHub (`github-com`)

Public GitHub repositories, releases, issues, labels, contributors and raw file contents.

| Capability | Credits | Use |
| --- | --- | --- |
| `repositories/contributors` | 5 | One page of a repository's contributors ordered by commit count on the default branch, with login, account type and contribution count. Ano… |
| `repositories/file` | 1 | The text of one file in a public GitHub repository at a branch, tag or commit, given as a raw.githubusercontent.com URL, a github.com blob … |
| `repositories/issue_counts` | 5 | Exact issue counts for a repository (pull requests excluded, unlike the repository's open_issues_count): the total for the given state plus… |
| `repositories/issues` | 5 | One page of a repository's issues filtered by state and labels (all given labels must match), sorted by created/updated/comments. Pull requ… |
| `repositories/labels` | 5 | The labels defined in a repository (name, color, description, whether GitHub-default), one page of up to 100. Use the names with issues and… |
| `repositories/latest_release` | 5 | The latest published, non-prerelease, non-draft release of a repository with its release notes (Markdown body), tag, publish date, author a… |
| `repositories/releases` | 5 | One page of a repository's releases, newest first, including pre-releases and drafts visible to the public, each with tag, name, notes body… |
| `repositories/repo` | 5 | One GitHub repository by owner/name or URL: stars, forks, watchers, open issue+PR count, creation/last-push dates, primary language, topics… |
| `repositories/search_repos` | 5 | Search public GitHub repositories with GitHub's search syntax (free text plus qualifiers such as language:rust, stars:>1000, topic:llm, org… |

<a id="p-npmjs-com"></a>

### npm (`npmjs-com`)

npm, the JavaScript package registry: full-text and typeahead package search, package documents with dist-tags and version history, per-version dependencies and tarballs, download counts (totals, daily series, per version), dependents and packages by user or organization.

| Capability | Credits | Use |
| --- | --- | --- |
| `packages/get_download_range` | 5 | Chart or trend a package's downloads day by day; periods up to 18 months per request. |
| `packages/get_downloads` | 5 | Compare popularity of a few packages or get the weekly/monthly/yearly download total of one; use `get_download_range` for a daily series. |
| `packages/get_package` | 5 | Look up an npm package by name or pasted npmjs.com URL: what it is, who maintains it, which versions exist and which tag points where. Use … |
| `packages/get_package_version` | 5 | Resolve exactly what `name@version` (or `name@latest`, `name@next`) installs: its dependencies, engines, tarball and integrity hash. |
| `packages/get_version_downloads` | 5 | See which versions of a package are actually installed this week (major-version adoption, whether a deprecated line is still in use). |
| `packages/list_dependents` | 5 | Find who uses a package (recent adopters, plugins, wrappers); the total dependents count is in `search_packages` results. |
| `packages/list_owner_packages` | 5 | List everything a maintainer or an organization publishes; provide exactly one of `user` or `org`. |
| `packages/search_packages` | 5 | Find npm packages by words, keyword, author or scope before looking one up by name; the registry returns up to 250 hits per page and report… |
| `packages/suggest_packages` | 5 | Resolve a partial or misspelled package name to real package names quickly; use `search_packages` for full result pages. |

<a id="p-pypi-org"></a>

### PyPI (`pypi-org`)

Python Package Index: project and release metadata, dependencies and Python compatibility, distribution files with hashes, PEP 740 provenance, release feeds, the global change log, a user's projects and site statistics.

| Capability | Credits | Use |
| --- | --- | --- |
| `packages/changelog` | 5 | Incrementally track everything that changes on PyPI: poll with the last seen serial. Upstream serves up to 50 000 events per call; `limit` … |
| `packages/files` | 5 | Enumerate all files across all versions of a package (for mirroring, hash pinning or compatibility scans), or get the complete version list… |
| `packages/project` | 5 | Look up a Python package by name or pasted pypi.org URL: what it is, who publishes it, which Python versions and dependencies it needs, whi… |
| `packages/provenance` | 5 | Verify where a specific wheel or sdist was built and published from (GitHub/GitLab Trusted Publishing) before trusting it. |
| `packages/recent_releases` | 5 | Watch for new versions of a package, or discover what was just released or created on PyPI. Fixed windows; no history beyond the feed. |
| `packages/release` | 5 | Check a specific version: dependency pins, Python compatibility, wheels/sdist available with hashes, whether it was yanked, and advisories … |
| `packages/stats` | 5 | Size PyPI as a whole or see which projects dominate its storage. |
| `packages/user_projects` | 5 | Find every package published or maintained by a given PyPI username (from a project's ownership or maintainer links). |

## automotive

Cars for sale: dealer and private-seller inventory, listing details and book values.

<a id="p-auctiontime-com"></a>

### AuctionTime (`auctiontime-com`)

AuctionTime.com (Sandhills Global) online equipment auctions: search upcoming lots and auction results by keyword, category, manufacturer, model and state; one lot's specs, photos, seller and live bid snapshot; the upcoming auction calendar; one sale's catalog; the category directory.

| Capability | Credits | Use |
| --- | --- | --- |
| `equipment-auctions/get_auction_lot` | 5 | Full detail for a lot found with `search_auction_lots` or `get_sale_catalog`. |
| `equipment-auctions/get_sale_catalog` | 5 | List everything in one auctioneer's sale. |
| `equipment-auctions/list_auction_events` | 5 | Discover auction dates and standalone sales; take `event_id` into `get_sale_catalog`. |
| `equipment-auctions/list_categories` | 5 | Find a category id before searching by category. |
| `equipment-auctions/search_auction_lots` | 5 | Find equipment lots to bid on or to look up; take `listing_id` into `get_auction_lot`. Use `list_categories` for category ids. |

<a id="p-carsandbids-com"></a>

### Cars & Bids (`carsandbids-com`)

Cars & Bids (carsandbids.com) online car auctions: search live and past auctions, one auction's full listing with bids, photos and seller, its comments and bid history, search suggestions, member profiles with auction and bid histories, and similar auctions. Read-only, anonymous, via the site's own signed JSON API.

| Capability | Credits | Use |
| --- | --- | --- |
| `car-auctions/auction` | 5 | Full detail for an auction id from `search_auctions`, a sitemap or a pasted https://carsandbids.com/auctions/{id}/{slug} URL. |
| `car-auctions/auction_comments` | 5 | Bid history (`filter: bids`) or the discussion for an auction id from `search_auctions` or `auction`. |
| `car-auctions/search_auctions` | 5 | Find auctions or past results; take `auctions[].id` into `auction` and `auction_comments`, `seller_username` into `user_profile`. |
| `car-auctions/similar_auctions` | 5 | Comparable listings and recent results for an auction id. |
| `car-auctions/suggest` | 5 | Resolve a loose car name to the search phrases the site itself proposes before calling `search_auctions`. |
| `car-auctions/user_profile` | 5 | Seller or bidder background for a `seller_username` from `search_auctions` / `auction` or a `username` from `auction_comments`. |

## companies

Company records, filings, funding and firmographics.

<a id="p-adstransparency-google-com"></a>

### Google Ads Transparency Center (`adstransparency-google-com`)

Google Ads Transparency Center: resolve advertisers, list their ads by region, format, platform and date, read creative details (dates, previews, EU DSA and political impression/spend ranges, targeting), advertiser profiles, political ads insights and geo criterion lookups, from the site's own anonymous RPC endpoints.

| Capability | Credits | Use |
| --- | --- | --- |
| `ad-transparency/get_ad` | 5 | Use with ids from list_ads. The same creative shows more fields under topic=political or an EU region than under the US all-ads context. An… |
| `ad-transparency/get_advertiser` | 5 | Use with an advertiser_id from suggest, search_advertisers or list_ads. An unknown id is not_found. |
| `ad-transparency/list_ads` | 5 | Use after suggest/search_advertisers resolved an advertiser_id or domain, or with a pasted advertiser page URL. For topic=political the adv… |
| `ad-transparency/political_stats` | 5 | Use for election-ad aggregates. Shares are fractions of the regional total as published by the site (labels inferred from the Insights UI).… |
| `ad-transparency/resolve_locations` | 5 | Use to label criterion ids such as 21162 (Nebraska). Unknown ids are reported in missing_ids; if none resolves the call is not_found. |
| `ad-transparency/search_advertisers` | 5 | Use when you need a paged, exhaustive advertiser list (suggest caps at 20) or political advertiser metadata. Pass `continuation` back with … |
| `ad-transparency/suggest` | 5 | Start here to turn a brand or company name into an advertiser_id (for list_ads / get_advertiser) or a domain (for list_ads). A query with n… |

<a id="p-alibaba"></a>

### Alibaba wholesale products (`alibaba`)

Public wholesale product and supplier discovery, quantity pricing and specifications. Advertised facts, not live inventory or landed-cost quotes.

| Capability | Credits | Use |
| --- | --- | --- |
| `retail/price_tiers` | 5 | Read advertised quantity-based unit prices in USD from source dollarPrice fields. Excludes shipping, tax and customization; localized displ… |
| `retail/product` | 5 | Read an Alibaba wholesale product title, MOQ, quantity unit and supplier identity. Source-advertised facts; availability remains unknown. |
| `retail/search` | 5 | Find wholesale products and suppliers in Alibaba's public keyword listing (/premium/<keyword>.html), which is mostly sponsored placements. … |
| `retail/specifications` | 5 | Read supplier-advertised product specifications as name/value pairs. Preserves duplicate attribute labels and makes no independent certific… |
| `retail/supplier` | 5 | Read the supplier summary attached to an Alibaba product: identity, country, business type, platform tenure and source-reported response/de… |

<a id="p-answerthepublic-com"></a>

### AnswerThePublic (`answerthepublic-com`)

AnswerThePublic (answerthepublic.com) Free Market Research: the public catalog of brand keyword collections and, for every keyword in it, the pre-computed questions, prepositions, comparisons, alphabetical, number and related search suggestions with Google search volume and cost per click, from the site's own public JSON API. Ad-hoc keyword search is not covered: it needs a Cloudflare Turnstile t…

| Capability | Credits | Use |
| --- | --- | --- |
| `search-suggestions/get_keyword_research` | 5 | The core research call: pass a keyword slug from list_collection_keywords (or the keyword text / research page URL). Filter sources or cap … |
| `search-suggestions/list_collection_keywords` | 5 | Browse a collection from list_collections to find the keyword slug to pass to get_keyword_research. |
| `search-suggestions/list_collections` | 5 | Start here to discover collection slugs for list_collection_keywords, or to see how many brand keyword reports the free catalog holds. |

<a id="p-apollo"></a>

### Apollo (`apollo`)

Person and company enrichment: find people by title and company, resolve them to verified work emails, and enrich companies from a domain with funding, headcount and technologies.

| Capability | Credits | Use |
| --- | --- | --- |
| `companies/bulk-enrich` | 30/record | Enrich up to ten companies in one call, billed 30 Firecrawl credits per matched company; unmatched records are free. |
| `companies/enrich` | 30 | Use when you have a domain or LinkedIn company URL and need the company behind it. For a company you can only name, search first. |
| `companies/info` | 30 | Look up a company by its Apollo ID; use companies/enrich when you have a domain instead. |
| `companies/job-postings` | 30 | Find current hiring activity at a known company. Each requested page costs 30 Firecrawl credits. |
| `companies/news` | 30 | Find news about known Apollo companies, optionally filtered by category and dates. Each requested page costs 30 Firecrawl credits. |
| `companies/search` | 30 | Use to build a list from a shape: size, location, industry, technology. It bills per page, so ask for the page size you need rather than pa… |
| `people/bulk-match` | 30/record | Enrich up to ten identified people in one call, billed 30 Firecrawl credits per matched person; unmatched records are free. |
| `people/info` | 30 | Retrieve a known Apollo person by ID. Use people/match to unlock contact information. |
| `people/match` | 30 | Use to resolve one person you have already found. Prefer the id from people/search, then a LinkedIn URL, then email; a bare name needs a do… |
| `people/search` | 0 | Always start here. It is free and it tells you who exists before anything is spent. Never match a list of guesses: search, read the preview… |

<a id="p-apps-fcc-gov"></a>

### FCC OET Equipment Authorization System (apps.fcc.gov) (`apps-fcc-gov`)

The FCC Office of Engineering and Technology's Equipment Authorization System (EAS) public reports at apps.fcc.gov/oetcf: equipment authorization search by FCC ID, grantee, applicant, grant date and technical filters; the exhibits (test reports, photos, manuals, with confidentiality flags and attachment ids) and the Form 731 grant of one filing; grantee registration search; the TCB list and the a…

| Capability | Credits | Use |
| --- | --- | --- |
| `equipment-authorizations/get_application_exhibits` | 5 | After search_authorizations or lookup_fcc_id, with a row's application_id and fcc_id, to list test reports, photos, manuals and other exhib… |
| `equipment-authorizations/get_application_grant` | 5 | After search_authorizations or lookup_fcc_id, with a row's application_id and fcc_id, for the authorized technical parameters and condition… |
| `equipment-authorizations/list_tcbs` | 5 | To list or look up the certification bodies (TCBs) that issue grants, e.g. to resolve a tcb_code filter for search_authorizations. |
| `equipment-authorizations/list_test_firms` | 5 | To find accredited test laboratories recognized by the FCC, by name or city. |
| `equipment-authorizations/lookup_fcc_id` | 5 | When you have an FCC ID (from a device label) and want its filings and their application_id for exhibits and grant detail. |
| `equipment-authorizations/search_authorizations` | 5 | To find FCC equipment authorization filings by grantee, applicant, date range or technical filters; use lookup_fcc_id for one exact FCC ID. |
| `equipment-authorizations/search_grantees` | 5 | To resolve a company to its grantee code(s) before an FCC ID search, or to look up who holds a grantee code. |

<a id="p-azroc-my-site-com"></a>

### Arizona Registrar of Contractors license register (azroc.my.site.com) (`azroc-my-site-com`)

Public contractor license register of the Arizona Registrar of Contractors (ROC), served by the AZRoc Salesforce Experience Cloud site at azroc.my.site.com/AZRoc/s/contractor-search. Search licensed contractors by business or person name, ROC license number, license classification and city; read a license record with its personnel, surety bonds and public complaint history; list the classificatio…

| Capability | Credits | Use |
| --- | --- | --- |
| `licenses/get_classification_description` | 5 | After search_contractors or get_license, to explain what work a license's classification permits. |
| `licenses/get_license` | 5 | After search_contractors, with a license's license_id, to verify status, bonding and complaint history. |
| `licenses/list_classifications` | 5 | To pick the exact classification spelling before a filtered search_contractors call. |
| `licenses/search_contractors` | 5 | Start here to find a contractor and the `license_id` of each of its licenses; then call get_license for the full record, bonds and complain… |

<a id="p-b3-com-br"></a>

### B3 listed companies and indices (`b3-com-br`)

B3 (Brasil, Bolsa, Balcão), the São Paulo exchange: listed-company registry search and enumeration, company detail with sector classification and financial summary, corporate actions, cash dividend history, CVM filings, index portfolios (IBOV, IBRX, SMLL, IDIV, IFIX...), stock-to-index membership, delayed quotes and the sector taxonomy. Public data, no credentials; Portuguese labels as B3 publish…

| Capability | Credits | Use |
| --- | --- | --- |
| `companies/cash_dividends` | 5 | When the `trading_name` (e.g. PETROBRAS) is known from `search_companies` or `company`. |
| `companies/company` | 5 | After `search_companies` returned a `code_cvm`, or when the CVM code is known. |
| `companies/company_filings` | 5 | For a company's regulatory disclosures; filter by `category` id (1 Assembleia, 2 Reunião da Administração, 3 Aviso aos Acionistas, 4 Fato R… |
| `companies/corporate_actions` | 5 | When the four-letter issuer code (`issuing_company`, e.g. PETR) is known, typically from `search_companies` or `company`. |
| `companies/index_portfolio` | 5 | To get an index's composition; page through with `page` (default 120 rows covers IBOV in one call). |
| `companies/industry_classification` | 5 | To interpret or filter the `segment` and classification labels returned by the company functions. |
| `companies/quote` | 5 | For a ticker such as PETR4, VALE3, BOVA11. Quotes are delayed per B3 policy. |
| `companies/search_companies` | 5 | First step to find a company's CVM code (`code_cvm`), issuer code and trading name for the detail functions. |
| `companies/stock_indices` | 5 | To learn the indices a company (e.g. PETR) is a member of. |

<a id="p-bbb-business-profiles-ratings-complaint"></a>

### BBB business profiles (`bbb-business-profiles-ratings-complaint`)

Better Business Bureau (bbb.org) business search, profiles with BBB letter grade and accreditation, complaint histories and customer reviews for the US and Canada.

| Capability | Credits | Use |
| --- | --- | --- |
| `businesses/complaints` | 1 | One page (10) of the public complaint history for a BBB business identified by profile URL or bbb_id + business_id: complaint type, status,… |
| `businesses/profile` | 1 | One BBB business profile identified by its bbb.org profile URL or by bbb_id + business_id (from search): BBB letter grade with reasons, acc… |
| `businesses/reviews` | 1 | One page (10) of BBB customer reviews for a business identified by profile URL or bbb_id + business_id: star rating, reviewer display name,… |
| `businesses/search` | 1 | Find BBB business profiles by business name or category near a place (US or Canada). Returns one page of 15 results with each business's BB… |

<a id="p-bbb-org"></a>

### Better Business Bureau (`bbb-org`)

bbb.org business directory: search businesses by name/category and location across the US and Canada with rating and accreditation filters; read a full business profile with BBB letter grade, accreditation status and dates, complaint and review summaries, alerts and licences; list published complaints with business responses; resolve a pasted bbb.org URL or id to its canonical identity. Reads the…

| Capability | Credits | Use |
| --- | --- | --- |
| `businesses/complaints` | 5 | You need the complaint detail behind a business's complaint counts, filtered by status (answered, resolved, unanswered) or type. |
| `businesses/profile` | 5 | You have a BBB `id` (from search or resolve) or a pasted bbb.org profile URL and need ratings, accreditation and complaint summary figures. |
| `businesses/resolve` | 5 | Normalise a bbb.org link an agent found elsewhere, or confirm an `id` exists, before calling profile or complaints. |
| `businesses/search` | 5 | Start here to find a business and its `id` for profile / complaints / resolve, or to list businesses in a category and place. |

<a id="p-benzinga"></a>

### Benzinga (`benzinga`)

Real-time financial newswire and analyst coverage for US-listed companies: market-moving headlines, why-is-it-moving notes, press releases, ratings changes and consensus, announced deals, and unusual options activity.

| Capability | Credits | Use |
| --- | --- | --- |
| `calendar/consensus-ratings` | 30 | Use for where analysts stand in aggregate right now on one company. For the individual changes that moved the consensus, use calendar/ratin… |
| `calendar/mergers-acquisitions` | 15 | Use for who is buying whom, at what price, and whether the deal is pending or closed. For the coverage and commentary around a deal use new… |
| `calendar/ratings` | 30 | Use for how analysts have moved on a stock: upgrades, downgrades, initiations and target changes. Filter by parameters[analyst_id] or param… |
| `calendar/ratings-analysts` | 30 | Use to resolve an analyst by name, or to judge how accurate a particular analyst has been, and to get the id you then pass to calendar/rati… |
| `calendar/ratings-firms` | 30 | Use to enumerate the covering firms or to turn a firm name into the id that calendar/ratings filters on as parameters[firm_id]. For an indi… |
| `calendar/removed` | 0 | Use when you keep a copy of the ratings or M&A calendar and need to know which previously returned events have since been withdrawn, which … |
| `news/press-releases` | 15 | Use this for company-issued announcements distributed over the wires, the primary-source wording behind a story. For Benzinga editorial cov… |
| `news/removed` | 0 | Use this when you keep a copy of Benzinga news and need to know which stories have been withdrawn so you can delete them, which Schedule C.… |
| `news/search` | 30 | Use for what was reported about a company or subject, and when. Scope it to tickers or a date range: unscoped it returns the whole newswire… |
| `news/wiims` | 45 | Use this to answer why a stock moved: WIIMs are the short attributed explanations Benzinga files against a ticker's price action. For the u… |
| `signals/options-activity` | 45 | Use for positioning: large directional bets before a catalyst. It reports orders, not outcomes, and a sweep filled at or above the ask (exe… |

<a id="p-bing-com"></a>

### Bing Maps (`bing-com`)

Public Bing Maps local business search and structured business details.

| Capability | Credits | Use |
| --- | --- | --- |
| `businesses/business` | 5 | One local business by its Bing ypid (from `search`): name, structured address, display and E.164 phone, website, coordinates, categories, a… |
| `businesses/search` | 5 | Local businesses matching a category or a business name near a street address, city/state or postal code (US and other Bing Maps markets). … |

<a id="p-branddb-wipo-int"></a>

### WIPO Global Brand Database (`branddb-wipo-int`)

WIPO Global Brand Database (branddb.wipo.int): search trademarks across 89 IP offices by brand name, owner, number, goods and services, Nice class, office, designation and status; read one record by its ST.13 number; goods and services term suggestions; per-office coverage and database-wide statistics. Public JSON API, no login.

| Capability | Credits | Use |
| --- | --- | --- |
| `intellectual-property/get_coverage` | 5 | To list the office codes accepted by search_trademarks and see how fresh each collection is. |
| `intellectual-property/get_database_stats` | 5 | For the size of the database and the distribution of records by office or country. |
| `intellectual-property/get_trademark` | 5 | After search_trademarks, with a result's st13. |
| `intellectual-property/search_trademarks` | 5 | Start here to find trademark records and their st13 identifiers; pass an st13 to get_trademark for the full record. |
| `intellectual-property/suggest_terms` | 5 | To expand a goods/services keyword before search_trademarks. |

<a id="p-brevets-patents-ic-gc-ca"></a>

### Canadian Patents Database (CIPO) (`brevets-patents-ic-gc-ca`)

Canadian Intellectual Property Office patent database: keyword, fielded and date-range search over Canadian patents and applications, and the full bibliographic summary of one patent (titles, status, IPC, parties, dates, PCT and priority data, abstracts, claims and description text, event and fee history, owners on record, document list).

| Capability | Credits | Use |
| --- | --- | --- |
| `intellectual-property/get_patent` | 5 | You have a CA patent or application number (from search_patents or a CPD URL) and need its bibliographic data, status, abstract, history or… |
| `intellectual-property/search_patents` | 5 | Start here to find patent numbers by keyword, title, inventor, applicant or owner name, IPC class, PCT or international publication number,… |

<a id="p-bsd-sos-mo-gov"></a>

### Missouri Secretary of State business registry (`bsd-sos-mo-gov`)

Missouri Secretary of State Business Services (bsd.sos.mo.gov) public business entity registry: search entities by business name or charter number, read an entity's registration record (names, type, charter number, domesticity, home state, status, formation date, duration, registered agent, filed documents with their public document links, principal office addresses, officers/owners/stock/contact…

| Capability | Credits | Use |
| --- | --- | --- |
| `entities/get_entity` | 5 | You have a business_entity_id from search_entities or get_registered_agent and need the full registration record, filing history or documen… |
| `entities/get_registered_agent` | 5 | You have a reg_agent_id from search_entities or get_entity and need the agent's address or the list of entities it represents. |
| `entities/search_entities` | 5 | You know (part of) a Missouri business name or a charter number (LC1041362, LP0013885, FL001415560, 00123456 ...) and need the entity's int… |

<a id="p-builtin-com"></a>

### Built In (`builtin-com`)

Technology job search, public role details and company profiles from Built In.

| Capability | Credits | Use |
| --- | --- | --- |
| `jobs/company` | 5 | Read one company profile by returned slug: description, website, logo, source employee count and industries. Headcount is a public source o… |
| `jobs/job` | 5 | Read one canonical Built In job URL: description, employer, source salary range/currency/unit, posting/expiry dates, locations, benefits an… |
| `jobs/search` | 5 | Search Built In public technology jobs by keyword, with pages1–100 and source ordering. Returns job URLs and company slugs for detail looku… |

<a id="p-businessregistration-utah-gov"></a>

### Utah business registry (`businessregistration-utah-gov`)

Utah Division of Corporations and Commercial Code public business registry (businessregistration.utah.gov): search registered entities, DBAs and name reservations by name, entity number, principal or registered agent with status, type and formation-date filters; read an entity's registration record (identity, status, dates, registered agent, principals, addresses), its filing history, check a pro…

| Capability | Credits | Use |
| --- | --- | --- |
| `entities/check_name_availability` | 5 | Check whether a proposed Utah business name is already taken or close to an existing registration. |
| `entities/get_entity` | 5 | You have a business_id (and reservation_id for a Name Reservation row) from search_entities and need the registration record, registered ag… |
| `entities/get_filing_history` | 5 | You have a business_id from search_entities and need the chronological filings of the entity (formation, annual reports, amendments, dissol… |
| `entities/list_lookup_values` | 5 | You need the entity_type key for a search_entities filter or want to know which statuses and status details the registry uses. |
| `entities/search_entities` | 5 | Find Utah entities by name, entity number, principal or registered agent and get their business_id for the detail functions. |

<a id="p-cis-scc-virginia-gov"></a>

### Virginia SCC Clerk's Information System (business entity registry) (`cis-scc-virginia-gov`)

Virginia State Corporation Commission Clerk's Information System public business entity search at cis.scc.virginia.gov: entity search by name or SCC entity id with entity type, status and jurisdiction filters; entity detail with status, formation and status dates, jurisdiction, industry code, registered agent, principal office, principals and shares; filing history with document ids; registered a…

| Capability | Credits | Use |
| --- | --- | --- |
| `entities/get_entity` | 5 | After search_entities, to read the full record and current status of one entity. |
| `entities/get_entity_agent_history` | 5 | To see past and current registered agents of an entity. |
| `entities/get_entity_filings` | 5 | To list an entity's filings and their document ids after search_entities or get_entity. |
| `entities/get_entity_name_history` | 5 | To see former and fictitious names of an entity. |
| `entities/search_entities` | 5 | Start here to find an entity's business_id and SCC entity id; use get_entity for the full record. |

<a id="p-cslb-ca-gov"></a>

### California CSLB contractor license lookup (`cslb-ca-gov`)

California Contractors State License Board (www.cslb.ca.gov) public Check a License service: read a contractor license record by license number (business information, entity, dates, status, classifications, bonds, workers' compensation, miscellaneous actions), search business names with cursor pagination, find currently licensed contractors by ZIP code or city and classification, list the personn…

| Capability | Credits | Use |
| --- | --- | --- |
| `licenses/find_contractors_by_location` | 5 | You need licensed contractors of a given classification (B, C-10, C-53 ...) near a California ZIP code or in a city. |
| `licenses/get_complaint_disclosure` | 5 | You have a license number (typically one whose get_license output carries complaint_disclosure_url) and need its disciplinary cases. |
| `licenses/get_license` | 5 | You have a CSLB license number (from search_contractors_by_name, find_contractors_by_location, list_license_personnel or a pasted LicenseDe… |
| `licenses/list_license_personnel` | 5 | You have a license number and need its qualifying individuals, officers or owners. |
| `licenses/search_contractors_by_name` | 5 | You know (the start of) a California contractor's business name and need the license number(s) to look up. |

<a id="p-data-inpi-fr"></a>

### INPI data.inpi.fr (`data-inpi-fr`)

INPI's open data portal for French intellectual property and company records: trademarks with effect in France (INPI, EUIPO and WIPO/Madrid), patents published in France (FR, EP, WO, CCP), industrial designs (FR and Hague) and the French company register (RNE), through the JSON search and detail-by-id API behind the site's results page.

| Capability | Credits | Use |
| --- | --- | --- |
| `intellectual-property-registers/get_company` | 5 | When the 9-digit SIREN is known (from search_companies or a trademark holder's identifier). |
| `intellectual-property-registers/get_design` | 5 | When a design id from search_designs is known. |
| `intellectual-property-registers/get_patent` | 5 | When the publication number with its country prefix is known. |
| `intellectual-property-registers/get_trademarks` | 5 | After search_trademarks, or when the office code + application number is known. |
| `intellectual-property-registers/search_companies` | 5 | Find a French company's SIREN and registration facts; chain `items[].siren` into get_company. |
| `intellectual-property-registers/search_designs` | 5 | Find designs by product name or applicant; chain `items[].id` into get_design. |
| `intellectual-property-registers/search_patents` | 5 | Find patents by keyword, applicant or inventor; chain `items[].id` into get_patent. |
| `intellectual-property-registers/search_trademarks` | 5 | Find trademarks by name, owner or Nice class, e.g. all FR/EM/WO marks named 'chanel' in class 3. Chain the returned `items[].id` into get_t… |

<a id="p-datalegion"></a>

### Data Legion (`datalegion`)

Person and company enrichment with separate tier and contact products.

| Capability | Credits | Use |
| --- | --- | --- |
| `companies/enrich-base` | 10 | Match a known company using identifiers with the base product. Contact entitlement comes from the dedicated credential, never from field pr… |
| `companies/enrich-premium` | 40 | Match a known company using identifiers with the premium product. Contact entitlement comes from the dedicated credential, never from field… |
| `people/enrich-base-no-contact` | 10 | Match a known person using identifiers with the base-no-contact product. Contact entitlement comes from the dedicated credential, never fro… |
| `people/enrich-base-with-contact` | 50 | Match a known person using identifiers with the base-with-contact product. Contact entitlement comes from the dedicated credential, never f… |
| `people/enrich-premium-no-contact` | 40 | Match a known person using identifiers with the premium-no-contact product. Contact entitlement comes from the dedicated credential, never … |
| `people/enrich-premium-with-contact` | 80 | Match a known person using identifiers with the premium-with-contact product. Contact entitlement comes from the dedicated credential, neve… |

<a id="p-dataprivacyframework-gov"></a>

### Data Privacy Framework participant list (`dataprivacyframework-gov`)

U.S. Department of Commerce Data Privacy Framework (DPF) program: search the public list of self-certified participants (EU-U.S. DPF, UK Extension, Swiss-U.S. DPF), filter by status, state, framework, data covered, industry, recourse mechanism and verification method, read one organization's full certification record, and look up the reference lists behind the filters. Read-only, anonymous, from …

| Capability | Credits | Use |
| --- | --- | --- |
| `companies/get_participant` | 5 | After search_participants, with the organization_id of a row (or the pasted https://www.dataprivacyframework.gov/participant/{id} URL), for… |
| `companies/list_reference_data` | 5 | To turn an industry name into industry_ids or to see the exact recourse mechanism names before calling search_participants. |
| `companies/search_participants` | 5 | Start here to find an organization_id and its current status per framework; use get_participant for the full certification record. Filter v… |
| `companies/search_site_content` | 5 | For questions about the program's rules and procedures rather than about a specific participant. |

<a id="p-delaware-gov"></a>

### Delaware Division of Corporations (`delaware-gov`)

Delaware Division of Corporations public records: the ICIS entity search (icis.corp.delaware.gov) by entity name or file number, the free entity details (formation date, kind, type, residency, registered agent) and the Division's list of Delaware registered agents (corp.delaware.gov/agents/). Paid status, franchise tax and filing history are not included.

| Capability | Credits | Use |
| --- | --- | --- |
| `entities/entity` | 5 | You have a Delaware file number (from `search` or a filing) and need the registration record and registered agent. |
| `entities/registered_agents` | 5 | You need the contact details of a Delaware registered agent named on an entity record, or the full list of agents the Division publishes. |
| `entities/search` | 5 | You know an entity name or a Delaware file number and need the matching registrations and their file numbers; follow up with `entity` for t… |

<a id="p-ecorp-sos-ga-gov"></a>

### Georgia Secretary of State business registry (eCorp) (`ecorp-sos-ga-gov`)

Georgia Secretary of State Corporations Division public registry at ecorp.sos.ga.gov (PCC Technology Group eCorp): business entity search by name, control number, registered agent, officer or designated agent; entity detail with status, type, formation date, jurisdiction, principal office, registered agent and officers; filing history and name change history keyed by the site's internal business …

| Capability | Credits | Use |
| --- | --- | --- |
| `entities/get_business` | 5 | After search_businesses, with the business_id of a row, for the full registry record of one entity. |
| `entities/get_filing_history` | 5 | With a business_id from search_businesses, to list an entity's filings and annual registrations. |
| `entities/get_name_history` | 5 | With a business_id from search_businesses, to see the entity's former names. |
| `entities/search_businesses` | 5 | Start here to find an entity's business_id and control number; use `get_business` for the full record. |
| `entities/search_service_of_process` | 5 | To find lawsuits served on the Secretary of State as agent for a Georgia entity, by defendant or plaintiff name. |
| `entities/search_trademarks` | 5 | To find Georgia state (not federal USPTO) trademark registrations by mark text or registrant. |

<a id="p-fcia-org"></a>

### FCIA member directory (`fcia-org`)

Firestop Contractors International Association (fcia.org) member directory: search firestop contractors, special inspection agencies, manufacturers, distributors and other members by service area (US state, Canadian province, Middle East country), region, accreditation (FM 4991, UL Qualified, IAS AC 291), member type and barrier-management service; search by company name; read one member's detail…

| Capability | Credits | Use |
| --- | --- | --- |
| `businesses/get_member` | 5 | After search_members or search_members_by_name, to read the full record (service areas, telephone, member since) for one location_id. |
| `businesses/search_members` | 5 | Start here to find firestop contractors, inspection agencies or suppliers by where they work and what they are accredited for; take locatio… |
| `businesses/search_members_by_name` | 5 | When you know (part of) the company name and want its location_id, accreditation badges or contacts. |

<a id="p-finance-yahoo-com"></a>

### Yahoo Finance (`finance-yahoo-com`)

Yahoo Finance public quotes, earnings estimates, ticker discovery, dividend history and historical OHLCV price bars.

| Capability | Credits | Use |
| --- | --- | --- |
| `equities/dividends` | 5 | Cash dividend history for one ticker over a range (default 10y): each payout's ex-dividend date and per-share amount, newest first, plus an… |
| `equities/earnings` | 5 | Earnings calendar and estimates for one ticker: the next earnings date (with an is_estimate flag and, when Yahoo gives a window, its end), … |
| `equities/history` | 5 | Historical OHLCV price bars for one symbol (stock, ETF, cash index such as ^GSPC, future such as NQ=F, or exchange-suffixed listing such as… |
| `equities/quote` | 5 | Live quote and key fundamentals for one symbol (stock, ETF, cash index such as ^GSPC, future such as NQ=F, or exchange-suffixed listing suc… |
| `equities/search` | 5 | Resolve a company name or partial ticker to Yahoo Finance symbols. Returns up to `count` matches with symbol, name, quote type (EQUITY, ETF… |

<a id="p-find-and-update-company-information-service-gov-uk"></a>

### Companies House (`find-and-update-company-information-service-gov-uk`)

Public UK company searches, profiles, filings, officers, ownership, charges and historic records from the Companies House website.

| Capability | Credits | Use |
| --- | --- | --- |
| `companies/advanced_search` | 5 | Search companies by name, free-text registered-office address, dates, status, type and one SIC code. Returns one page; source limits access… |
| `companies/alphabetical_search` | 5 | Read an alphabetical window of company names with opaque previous/next cursors. This is not a substring search. |
| `companies/charge` | 5 | Read a returned charge identifier, dates, status, entitled parties, particulars and filing links. |
| `companies/charges` | 5 | Read one company-charge page, optionally outstanding charges only. |
| `companies/company` | 5 | Read a company overview, deadlines, SICs, former names and available sections. Preserve different date/address meanings and partial profile… |
| `companies/disqualification` | 5 | Read a returned natural-person or corporate disqualification record, preserving the published sanction/order/undertaking classification. |
| `companies/dissolved_search` | 5 | Search the historic 1989–2009 dissolved-company index by name, previous name or alphabetical window. Report downloads can be unavailable or… |
| `companies/filing_document` | 5 | Return a stable public PDF filing link; optionally retrieve PDF bytes through validated redirects, capped at 5 MiB. Signed URLs are not ret… |
| `companies/filings` | 5 | Read one filing-history page, optionally filtered by category, with annotations and stable document links. |
| `companies/insolvency` | 5 | Read published insolvency cases for a company with an available insolvency page. An unavailable route is not evidence of no cases. |
| `companies/name_availability` | 5 | Read the source name-conflict check. No exact match does not guarantee registration. |
| `companies/officer_appointments` | 5 | Read one page of appointments for an officer identifier returned by the website, optionally current appointments only. |
| `companies/officers` | 5 | Read one company-officer page, including public appointment details; optionally current officers only. |
| `companies/persons_with_significant_control` | 5 | Read public PSC records, statements or explicit exemption information for a company. |
| `companies/search` | 5 | Search one page of public company, officer or disqualification results. Defaults to companies. |

<a id="p-firecrawl-maps"></a>

### Maps (`firecrawl-maps`)

Business search, public reviews, monthly rating trends and directions for driving, walking, cycling and transit.

| Capability | Credits | Use |
| --- | --- | --- |
| `businesses/directions` | 5 | Routes between two addresses, place names, or coordinate pairs. Modes: driving (default), walking, bicycling, transit. Returns route altern… |
| `businesses/rating_trend` | 5 | Monthly rating trend for one business from its newest 60 reviews (one request): per calendar month the review count, average rating and own… |
| `businesses/reviews` | 5 | Public reviews for one business identified by its Maps feature_id (0x..:0x.., from search or a Maps URL). One request returns 1 to 60 revie… |
| `businesses/search` | 5 | Find businesses on Maps by free-text query (name and/or 'category in city'). Returns up to 20 places with feature_id (input for reviews/rat… |

<a id="p-fireround"></a>

### Fireround (`fireround`)

Startup funding rounds: venture capital (VC funding) of private companies from across the open web, pre-seed to growth, with amounts, valuations, stages, lead and other investors, certainty and sources, each read back against the pages it came from; the funded companies with their headquarters, sector, what they do and total raised; the investors behind them and the news that reported them.

| Capability | Credits | Use |
| --- | --- | --- |
| `companies/profile` | 5 | One startup or private company's profile and venture funding: its headquarters (location), its sector, what the company does, its total rai… |
| `companies/rounds` | 5 | Every funding round on record for one company as full round records, newest first: each with amount, valuation, investors, certainty, the s… |
| `companies/search` | 5 | Find startups and other venture-backed private companies by sector, stage, location (headquarters city or country), what the company does, … |
| `investors/profile` | 5 | One investor's track record on Fireround: the rounds it led and joined, the sectors and stages it backs, the investors it co-invests with, … |
| `investors/search` | 5 | Find a venture investor or fund by name, or list the investors with the most rounds on record: how many rounds a firm led and joined and it… |
| `investors/top` | 5 | Rank the investors that led the most startup funding rounds this week, this month or this quarter, overall or in one sector or stage: which… |
| `news/latest` | 5 | The latest startup funding news: articles from press and newswires about the rounds Fireround tracks, newest first, each with its publisher… |
| `rounds/search` | 5 | Search startup funding rounds: the latest rounds, the biggest rounds, and rounds by stage, sector, investor, date or size across venture ca… |
| `rounds/trending` | 5 | The funding rounds first seen in the last three days that are being discussed most, ranked by distinct people posting about them on X, pres… |

<a id="p-fiscal-ai"></a>

### Fiscal.ai (`fiscal-ai`)

Company fundamentals with the record around them: standardized and as-reported statements, ratios, ownership, prices, earnings call transcripts, and what fund letters say about a company.

| Capability | Credits | Use |
| --- | --- | --- |
| `company/list` | 0 | Call to discover what is covered, or to resolve names to identifiers when you do not already have a ticker. Check the per-company dataset l… |
| `company/profile` | 30 | Call first when starting from a company name or ticker: it returns every other identifier, so one call here makes the rest of this provider… |
| `company/segments-and-kpis` | 30 | Call for the numbers a business is actually run on - segment revenue, units, subscribers - which never reach the three statements. Coverage… |
| `company/shares-outstanding` | 30 | Call when a per-share figure has to be computed, or when a dual-class structure means the headline share count is misleading. Point-in-time… |
| `events/calendar` | 15 | Call to answer who reports when. Omit every company identifier for the whole calendar, which is what makes this the one capability here tha… |
| `events/ir-events` | 30 | Call to find what exists for a quarter before asking for any of it - the deck, the release, the report, the transcript. Rows sharing a fisc… |
| `events/transcript` | 30 | Call for what was said on the call, attributed and timed. The speaker mapping is what makes it worth more than the raw text: management's p… |
| `filings/list` | 15 | Call to find out what exists and when it was filed, and to get the document links. The filing bytes themselves are not retrievable through … |
| `financials/adjusted-metrics` | 30 | Call when comparing against analyst estimates or consensus, which are quoted on an adjusted basis rather than a GAAP one. Not a substitute … |
| `financials/balance-sheet` | 15 | Call when comparing companies, screening, or computing anything that has to mean the same thing across two filers. The mapping is visible: … |
| `financials/balance-sheet-as-reported` | 30 | Call when fidelity to the filing matters more than comparability: the labels and groupings are the company's own, so two companies cannot b… |
| `financials/cash-flow-statement` | 15 | Call when comparing companies, screening, or computing anything that has to mean the same thing across two filers. The mapping is visible: … |
| `financials/cash-flow-statement-as-reported` | 30 | Call when fidelity to the filing matters more than comparability: the labels and groupings are the company's own, so two companies cannot b… |
| `financials/income-statement` | 15 | Call when comparing companies, screening, or computing anything that has to mean the same thing across two filers. The mapping is visible: … |
| `financials/income-statement-as-reported` | 30 | Call when fidelity to the filing matters more than comparability: the labels and groupings are the company's own, so two companies cannot b… |
| `fund-letters/companies` | 15 | Call to find which companies professional investors are actually writing about, and how heavily, before asking what they said. |
| `fund-letters/company` | 15 | Call for the qualitative case on a company as professional investors put it, with the stance and conviction attached. The one capability he… |
| `fund-letters/detail` | 15 | Call for what one letter actually argued. The narrative sections are the investor's own words; the theses are the extraction, and each name… |
| `fund-letters/investor` | 15 | Call to understand how a firm invests before weighting what it says about a company. The profile is derived from its own letters rather tha… |
| `fund-letters/investors` | 15 | Call to find the investorId for a firm, or to pick firms by style or sector focus before reading any letters. Sorted by coverage, so the mo… |
| `fund-letters/list` | 15 | Call to see what was published in a quarter. Returns the letter index rather than the letters - take a letterId to fund-letters/detail for … |
| `metrics/ratios-list` | 0 | Call to find a ratio id before requesting a series, and to check `hasDailyData` before asking for a daily one - not every ratio has it. |
| `metrics/standardized` | 0 | Call to find the standardized metric id for a concept before requesting statements, rather than guessing at a name. Free, and takes no comp… |
| `metrics/standardized-by-template` | 0 | Call rather than the full list when the template is already known - it is the only place the prose definition and the sub-component breakdo… |
| `ownership/holder-holdings` | 15 | Call to read ownership from the investor's end rather than the company's - what a fund holds and how it is weighted. The counterpart to ins… |
| `ownership/holders-list` | 0 | Call to resolve an institution's name to the holder id that ownership/holder-holdings needs. Free, and takes no company. |
| `ownership/insider-holders` | 15 | Call for the current standing position of officers and directors, including holdings held through trusts and other vehicles. Use insider-tr… |
| `ownership/insider-transactions` | 15 | Call to see insider activity over time. Read `transactionType` before drawing conclusions: an option exercise or a tax withholding is not a… |
| `ownership/institutional-holders` | 15 | Call to see who institutionally owns a company and who moved last quarter. 13F data lags: the report date is the quarter end, the filing da… |
| `prices/daily` | 15 | Call for a daily close series. Prices are split-adjusted already, so no correction against prices/splits is needed; the series is per listi… |
| `prices/intraday` | 15 | Call when the question is about movement within a session - a reaction to an announcement, say. Rounded to two decimals, so it is not a tic… |
| `prices/splits` | 15 | Call to explain a discontinuity, or to reconcile against a price series from elsewhere that is not split-adjusted. The series returned by p… |
| `ratios/daily` | 15 | Call when the question is how a ratio moved between reporting dates rather than what it was at them. Each day is recomputed against that da… |
| `ratios/series` | 15 | Call for valuation, margin and leverage ratios already computed against the reported statements, rather than recomputing them from financia… |

<a id="p-fullenrich"></a>

### FullEnrich (`fullenrich`)

People and company search, profile lookups, firmographics, and verified contact data.

| Capability | Credits | Use |
| --- | --- | --- |
| `companies/lookup` | 5/record | Resolve one company from its domain, LinkedIn company URL, or LinkedIn company ID. Returns firmographics, technologies, social profiles, an… |
| `companies/match` | 5/record | Match an exact LinkedIn company URL. Use companies/lookup to resolve a domain, or companies/search to build a shortlist. |
| `companies/search` | 5/record | Find companies by industry, size, location, technologies, or founding year. Combine filters and page through the results. Use companies/loo… |
| `contacts/mobile` | 175/record | Find a person's mobile phone number from a LinkedIn URL, or from their name and employer. The most expensive line by far: ask for it only w… |
| `contacts/personal-email` | 55/record | Find a person's personal email from a LinkedIn URL, or from their name and employer. Schedule A bars marketing to personal addresses; use c… |
| `contacts/reverse-email` | 20/record | Identify the person and company behind a work or personal email address. Returns a professional profile; use people/lookup when a name or L… |
| `contacts/work-email` | 20/record | Find a person's verified work email from a LinkedIn URL, or from their name and employer. Use contacts/mobile for a phone number and people… |
| `people/lookup` | 5/record | Resolve a person from a LinkedIn URL or ID, or a full name combined with a company domain, LinkedIn URL, or ID. Returns a profile, not veri… |
| `people/match` | 5/record | Match an exact LinkedIn profile URL. Use people/lookup for additional identifiers, or people/search to build a shortlist. |
| `people/search` | 5/record | Find people by role, employer, location, skills, or work history. Combine filters and page through the results. Use people/lookup when you … |

<a id="p-gartner-com"></a>

### Gartner (`gartner-com`)

Gartner's public marketing site: upcoming and on-demand webinars (listing servlet and detail pages with speakers, times and registration URL), the conference calendar, and public content lists (articles, newsroom press releases, experts). Anonymous, English (www.gartner.com/en).

| Capability | Credits | Use |
| --- | --- | --- |
| `events/conferences_list` | 5 | Find Gartner conferences by region, audience or format, or get the detail URL and event code for a conference. |
| `events/content_list` | 5 | Browse Gartner's latest articles or press releases, or list Gartner analysts for a function such as cybersecurity. |
| `events/webinar_detail` | 5 | After webinars_search, to get speakers and the complete description for one webinar, or when a Gartner webinar URL is pasted. |
| `events/webinars_search` | 5 | Find upcoming webinars on a topic or in a date range, or browse the on-demand library. Follow with webinar_detail for speakers and the full… |

<a id="p-gleif-org"></a>

### GLEIF (`gleif-org`)

Global LEI search, identity and reported direct/ultimate accounting-consolidation parents and children. Preserves reporting exceptions.

| Capability | Credits | Use |
| --- | --- | --- |
| `entities/direct_children` | 5 | Page through reported direct accounting-consolidated children for an LEI. This excludes unreported ownership relationships. |
| `entities/direct_parent` | 5 | Retrieve the reported direct accounting-consolidating parent, or its reporting-exception record and reason. This is not a complete benefici… |
| `entities/entity` | 5 | Resolve an exact 20-character LEI to source identity, registration, mapped identifiers and relationship links. Unknown LEIs fail as upstrea… |
| `entities/search` | 5 | Search global registered entities by name: current legal name, previous legal and other names, and ASCII-transliterated names, with optiona… |
| `entities/ultimate_children` | 5 | Page through reported ultimate accounting-consolidated children for an LEI. This excludes unreported ownership relationships. |
| `entities/ultimate_parent` | 5 | Retrieve the reported ultimate accounting-consolidating parent, or its reporting-exception record and reason. Preserve exceptions rather th… |

<a id="p-houzz-com"></a>

### Houzz (`houzz-com`)

Public professional discovery, service profiles and portfolio summaries.

| Capability | Credits | Use |
| --- | --- | --- |
| `professionals/profile` | 5 | Read a public Houzz professional profile, source review aggregate, advertised services and service areas. No review text, contact actions o… |
| `professionals/projects` | 5 | Read the initial portfolio project summaries embedded in a public professional profile, with photo counts and source location. This is a pa… |
| `professionals/search` | 5 | Read one page of Houzz professionals from an explicit location directory URL. Results may include sponsored or nonlocal providers. Follow n… |

<a id="p-indeed-com"></a>

### Indeed (`indeed-com`)

Indeed job search, full job postings and employer profiles (rating, review category scores, size, revenue, industry, addresses, CEO, links) from Indeed's own GraphQL API for the US and 25 other country sites, with the public company page as fallback and salary and location normalised.

| Capability | Credits | Use |
| --- | --- | --- |
| `jobs/employer` | 5 | Employer research after search or job returned an employer key or url. Prefer employer_key (solver-free, one GraphQL call); unknown keys an… |
| `jobs/job` | 5 | After search, or when you hold a viewjob?jk= or rc/clk?jk= URL. Removed postings return not_found. |
| `jobs/search` | 5 | Start here to find job_key values; pass the same filters plus next_cursor to page. No total count is exposed by Indeed; next_cursor=null is… |

<a id="p-justwatch-com"></a>

### JustWatch (`justwatch-com`)

JustWatch streaming availability: search movies and shows, per-country streaming/rent/buy offers with provider links and prices, title details with IMDb/TMDB ids, episodes, catalog browsing, new arrivals and provider lists from JustWatch's public GraphQL API.

| Capability | Credits | Use |
| --- | --- | --- |
| `streaming-availability/browse_titles` | 5 | Catalog questions such as 'top Netflix movies in Germany' or 'what is streaming free in the UK'. Provider short names come from `providers`. |
| `streaming-availability/new_titles` | 5 | 'What came to Netflix in the US today', 'what arrives on Apple TV next week'. Dates are the catalog dates JustWatch publishes; page through… |
| `streaming-availability/providers` | 5 | To pick provider short names for browse_titles and new_titles, or to list a country's streaming services. |
| `streaming-availability/search_titles` | 5 | Start here to find a title id (tm…/ts…) or to check IMDb/TMDB ids; use title_offers for several countries at once and title_detail for the … |
| `streaming-availability/season_episodes` | 5 | With a tss… season id from title_detail `seasons`. Paginate with `offset` when a season has more than `limit` episodes. |
| `streaming-availability/title_detail` | 5 | After search_titles, or with a pasted justwatch.com URL. For offers in several countries use title_offers; for episodes use season_episodes… |
| `streaming-availability/title_offers` | 5 | The issue's core question: where can this movie or show be watched, per country. Pass `countries` for a multi-market comparison; one reques… |

<a id="p-kickstarter-com"></a>

### Kickstarter (`kickstarter-com`)

Kickstarter (www.kickstarter.com) crowdfunding projects: search and browse the public discover catalogue by term, category, location, tag, state and sort with seeded pagination; search-box suggestions; location lookup for the location filter; one project's full record with funding progress and reward tiers from its public page; lightweight live funding counters; the category tree and featured tag…

| Capability | Credits | Use |
| --- | --- | --- |
| `crowdfunding-projects/get_project` | 5 | Full detail, reward tiers and add-ons for a project found with search_projects or suggest_projects, or from a pasted kickstarter.com/projec… |
| `crowdfunding-projects/get_project_stats` | 5 | Refresh backers and pledged totals for a known project without re-reading the full page. |
| `crowdfunding-projects/list_categories` | 5 | Find category ids and tag slugs for search_projects. |
| `crowdfunding-projects/search_locations` | 5 | Turn a city or region name into a `woe_id` before filtering search_projects by location. |
| `crowdfunding-projects/search_projects` | 5 | Discover projects before fetching one with get_project. Use list_categories for category ids and search_locations for woe_ids. |
| `crowdfunding-projects/suggest_projects` | 5 | Resolve a project name to its id, creator and slug quickly; prefer search_projects for filtered, paginated discovery. |

<a id="p-lda-gov"></a>

### Lobbying Disclosure Act filings (lda.gov) (`lda-gov`)

U.S. federal lobbying disclosures from the Senate Office of Public Records' Lobbying Disclosure Act REST API (lda.gov): LD-1 registrations and LD-2 quarterly activity reports (client, registrant, income or expenses, general issue codes, specific issues, lobbyists, government entities contacted, foreign entities), LD-203 contribution reports (FECA contributions and honorary, meeting, library and i…

| Capability | Credits | Use |
| --- | --- | --- |
| `lobbying-disclosures/get_client` | 5 | You have a client_id and need that client record and its registrant. |
| `lobbying-disclosures/get_contribution_report` | 5 | You have an LD-203 report UUID or link and need its itemized contributions. |
| `lobbying-disclosures/get_filing` | 5 | You have a filing UUID or an lda.gov filing link and need its full contents. |
| `lobbying-disclosures/get_registrant` | 5 | You have a registrant_id and need the registrant's record. |
| `lobbying-disclosures/search_clients` | 5 | Find which firms lobby for a company, or resolve a client to client_id values for search_filings. |
| `lobbying-disclosures/search_contributions` | 5 | Which members of Congress a lobbyist or firm gave to, contributions to a campaign committee by registered lobbyists, a firm's PAC giving. |
| `lobbying-disclosures/search_filings` | 5 | Who lobbies for a company or on an issue, how much a client paid a firm in a year, which firms or lobbyists worked a bill topic. |
| `lobbying-disclosures/search_registrants` | 5 | Resolve a lobbying firm or in-house organization to its registrant_id before searching filings or contributions. |

<a id="p-msc-com"></a>

### MSC shipment tracking and schedules (`msc-com`)

MSC (Mediterranean Shipping Company) public tools on msc.com: container, bill-of-lading and booking tracking with milestone events, point-to-point sailing schedules, vessel port-call schedules, port arrivals and departures, the port and vessel reference lists, first-EU-port arrivals and the customer advisories newsroom. Anonymous JSON endpoints behind the site's Sitecore pages.

| Capability | Credits | Use |
| --- | --- | --- |
| `shipment-tracking/eu_first_port_arrivals` | 5 | EU customs pre-arrival work: which MSC vessel/voyage enters the EU where and when, and the customs office code. |
| `shipment-tracking/list_advisories` | 5 | Surcharges, service changes, port congestion notices and rate announcements MSC has published; paginate with `page` while `next_page` is no… |
| `shipment-tracking/list_ports` | 5 | Before search_sailing_schedule or port_arrivals_departures when you have a port name and need its MSC port id or UN/LOCODE. |
| `shipment-tracking/list_vessels` | 5 | Find the IMO number for vessel_schedule from a vessel name, or check that a vessel is in MSC's schedule system. |
| `shipment-tracking/port_arrivals_departures` | 5 | What MSC vessels are due at a port in the coming days; port codes come from list_ports or tracking events. |
| `shipment-tracking/search_sailing_schedule` | 5 | Planning a shipment: which MSC sailings connect two ports from a date, how long they take and when cargo must be at the terminal. |
| `shipment-tracking/track_shipment` | 5 | Any 'where is my container / B/L' question. A container lookup returns its bill of lading number; look that up to get every sibling contain… |
| `shipment-tracking/vessel_schedule` | 5 | Where a vessel is and where it calls next; IMO numbers come from list_vessels, tracking events or sailing schedules. |

<a id="p-msheritage-access-preservica-com"></a>

### M&S Heritage digital archive (Preservica Universal Access) (`msheritage-access-preservica-com`)

The Marks & Spencer Company Archive's public digital catalogue ('M&S Heritage', msheritage.access.preservica.com, a Preservica Universal Access tenant): keyword search of the catalogue with collection, format and reference-number filters, browsing of the collection hierarchy (Browse Collections root -> folders -> items) and the metadata of a single record (title, description, date, reference numb…

| Capability | Credits | Use |
| --- | --- | --- |
| `archive-records/get_record` | 5 | You have an id from search_records or list_folder and need the record's full header metadata, its reference number or its place in the hier… |
| `archive-records/list_folder` | 5 | Enumerate the archive top-down (root -> collection -> sub-folders -> items) or list what sits inside a folder found by search_records or ge… |
| `archive-records/search_records` | 5 | Find archive records (magazines, photographs, reports, adverts, catalogues) by keyword, or list everything of one file format or reference … |

<a id="p-myfloridalicense-com"></a>

### Florida DBPR licensing registry (myfloridalicense.com) (`myfloridalicense-com`)

Florida Department of Business and Professional Regulation public license verification at myfloridalicense.com (the ASP.NET MVC `portalsearches/VerifyLicensee` application that the legacy wl11.asp search now redirects to): search professional and business licensees by name or license number with board, license type, county, city and state filters and historic-license inclusion; the licensee detai…

| Capability | Credits | Use |
| --- | --- | --- |
| `licenses/get_license_complaints` | 5 | With a detail_id from search_licenses, to check for published complaints or discipline before the licensee detail. |
| `licenses/get_license_detail` | 5 | After search_licenses, with a row's detail_id, for the full license record and current status. |
| `licenses/get_license_relations` | 5 | With a detail_id from search_licenses, to see which business a contractor qualifies or who qualifies a business. |
| `licenses/search_licenses` | 5 | Start here to find a licensee and its detail_id; then call get_license_detail for the full record. Use license_number when you have it (fas… |

<a id="p-namecheap-com"></a>

### Namecheap domain search (`namecheap-com`)

Public, anonymous domain availability, premium and aftermarket status, TLD pricing, marketplace listings and auctions behind namecheap.com's domain search. Read-only; no cart, account or purchase actions.

| Capability | Credits | Use |
| --- | --- | --- |
| `domains/auctions` | 5 | List currently running Namecheap Market auctions; optionally filter by TLD. |
| `domains/check_domains` | 5 | You already know the exact names to check. For a keyword plus a set of extensions use search_domains. |
| `domains/marketplace_listings` | 5 | See which registered names on a keyword are for sale and at what asking price. An empty list is a valid answer. |
| `domains/search_domains` | 5 | Start here with a brand or keyword to see which extensions are free and what Namecheap displays for them. |
| `domains/tld_pricing` | 5 | Compare extension prices or look up renewal/transfer cost for a TLD. |

<a id="p-opensanctions-org"></a>

### OpenSanctions (`opensanctions-org`)

OpenSanctions sanctions, PEP and persons-of-interest database: entity search with facets and filters, full entity profiles with properties, sanctions programs, relationships and data sources from the public website, and the dataset catalogue from the public data mirror.

| Capability | Credits | Use |
| --- | --- | --- |
| `sanctions-screening/get_dataset` | 5 | With a dataset name from list_datasets, search facets or an entity's data sources. |
| `sanctions-screening/get_entity` | 5 | After search_entities, with an entity_id. Accepts canonical ids (Q7747, NK-..., addr-...) and source identifiers (ofac-35096), which the si… |
| `sanctions-screening/list_datasets` | 5 | To discover dataset names for search_entities (datasets / scope) and get_dataset. |
| `sanctions-screening/search_entities` | 5 | Start here to find an entity_id for get_entity, or to browse a dataset or program with filters only (no q). |

<a id="p-particle"></a>

### Particle (`particle`)

Podcast intelligence: speaker-labelled transcripts, episode and show search, the people who appear, the sponsors and companies advertising, chart rankings, and bias and brand-suitability analysis.

| Capability | Credits | Use |
| --- | --- | --- |
| `advertising/co-occurrence` | 25 | Use for who a sponsor shares ad breaks with: the advertisers that buy the same inventory. |
| `advertising/company` | 5 | Use for the company record behind a sponsor, an entity or a companies/search hit. For its podcast advertising footprint use advertising/com… |
| `advertising/company/overview` | 25 | Use for a company's podcast advertising footprint in one call, across all its brands. For the show list use advertising/company/shows. |
| `advertising/company/placements` | 25 | Use for the feed of a company's actual ad reads, episode by episode, to read or audit them. |
| `advertising/company/prospects` | 25 | Use as a buy-side prospect list: where an advertiser could go next, with the shows it already buys as the reason. |
| `advertising/company/shows` | 25 | Use for where a company advertises, ranked by volume, with the reads to sample. Pages are at most 24 rows. |
| `advertising/episode` | 25 | Use for exactly who advertised in one episode, with the offer and where in the episode the read sits. |
| `advertising/leaderboard` | 25 | Use for the biggest podcast advertisers overall, in a period, or on one network. For the top-ten snapshot use advertising/leaderboard/previ… |
| `advertising/leaderboard/preview` | 25 | Use for a quick read of who is spending most on podcasts this week and who is climbing. For deeper pages, other windows or filters use adve… |
| `advertising/publisher` | 25 | Use for how a network is monetised and who buys across it. For its shows ranked by ad volume use advertising/publisher/shows. |
| `advertising/publisher/shows` | 25 | Use for which of a network's shows carry the advertising. For the same catalogue by popularity use podcasts/publisher/shows. |
| `advertising/publisher/sponsors` | 25 | Use for who buys a network, and which of them buy it as a bundle: sort by podcast_coverage with a minimum. |
| `advertising/publishers/leaderboard` | 25 | Use for which networks carry the most advertising, or monetise their catalogue most densely. |
| `advertising/show` | 25 | Use for who sponsors a show and how heavily it is monetised. For the full per-sponsor list use advertising/show/sponsors. |
| `advertising/show/prospects` | 25 | Use as a prospecting list for a show selling its own inventory: who buys shows like mine and has not bought me. |
| `advertising/show/sponsors` | 25 | Use for every advertiser on one show with counts and recency, or one company's brands on it. Set since and until on shows with extensive ad… |
| `advertising/sponsor` | 25 | Use to find who is buying advertising, or to go from a sponsor back to the company paying for it. For where it runs use advertising/sponsor… |
| `advertising/sponsor/publishers` | 25 | Use to tell network buys from per-show buys: a sponsor at 60 to 100 percent coverage of several publishers is buying bundles. |
| `advertising/sponsor/segments` | 25 | Use to read the actual ad reads for a sponsor, then podcasts/segment/transcript for the words of one. |
| `advertising/sponsor/shows` | 25 | Use for where an advertiser buys: the canonical footprint of one sponsor, or of a whole company across its brands. |
| `advertising/sponsors` | 25 | Use to find a sponsor by name or by company and pick up its id. For the biggest spenders use advertising/leaderboard. |
| `advertising/sponsors/trending` | 25 | Use for which advertisers are ramping podcast spend right now, by airdate. |
| `advertising/timeseries` | 25 | Use for how an advertiser's podcast spend trends by week or month, optionally on one show or network, and its host-read mix. |
| `bias/publisher` | 25 | Use for a network's political profile as a whole: how political its catalogue is and which way it leans. |
| `bias/publisher/shows` | 25 | Use to list a network's shows by political lean, or only the ones in a bucket. |
| `bias/publishers-by-bucket` | 25 | Use for which publishers carry the most shows of one lean: the flip of a publisher's own bias profile. |
| `bias/publishers/leaderboard` | 25 | Use for which networks lean furthest left or right, are most political, or most ideologically diverse. |
| `bias/show` | 25 | Use for where a show sits politically and why, with the evidence to quote. The bucket alone rides on every show record as bias. |
| `charts/chart` | 50 | Use for what podcasts are talking about most this week in one domain: the most-mentioned shows, films, games, teams or players, or the most… |
| `charts/list` | 50 | Use to see which charts exist (all, tv-series, movies, video-games, nfl, nba, guests and so on) and who leads each, before fetching one wit… |
| `companies/competitors` | 25 | Use for a company's competitive set with the reason each one is on it, before comparing their podcast presence or advertising. |
| `companies/external-links` | 15 | Use to get a company's handles, domain, CIK or ticker. The reverse, identifier to company, is entities/lookup. |
| `companies/people` | 25 | Use to find executives and role holders at a company, or the marketing, brand and partnerships contacts a sponsorship conversation would go… |
| `companies/products` | 25 | Use to see what a company sells, structured by segment and product line, for example to match an ad read's offer to a product. |
| `companies/search` | 5 | Use to resolve a company by name, ticker, domain, CIK or Wikidata QID to the slug every company capability takes. The record itself is adve… |
| `entities/list` | 5 | Use for the most-discussed entities overall, in one show, or of one kind, or to fetch several entities by slug at once. Takes no free text;… |
| `entities/lookup` | 5 | Use when you hold a LinkedIn slug, a handle, a domain, a ticker or a CIK and need the Particle person or company: the reverse of the extern… |
| `entities/mentions` | 5 | Use to resolve an entity slug to its record and its linked company or person. For where it was mentioned use podcasts/mentions (dialogue li… |
| `entities/search` | 5 | Use to turn what someone typed into a specific person, company or entity and its slug, before asking what was said about it with podcasts/m… |
| `entities/topic` | 5 | Use to place a topic in the taxonomy and see its neighbours. For the shows in it use podcasts/list with topic_id; for episodes, podcasts/ep… |
| `entities/topics` | 15 | Use to find the topic_id that podcasts/search, podcasts/list and the guest capabilities filter on. Walk down from the roots by passing pare… |
| `entities/types` | 15 | Use to see what the type filter on entities/list can take. Skip it when listing without a filter. |
| `people/external-links` | 15 | Use to get a person's LinkedIn or social handles. The reverse, handle to person, is entities/lookup. |
| `people/guest` | 15 | Use when the question is about someone as a podcast guest: how often they appear, where, and since when. For the episode list use people/gu… |
| `people/guest/appearances` | 15 | Use for where someone has appeared, episode by episode, to read what they said: take episode.id to podcasts/transcript with speaker set to … |
| `people/guest/pitch-list` | 25 | Use to build a pitch list for a guest: the shows most like the ones that already booked them, with the venues to cite. |
| `people/guest/shows` | 15 | Use for the set of shows behind a guest rather than the episodes: which shows book them and how often. |
| `people/guests` | 15 | Use to find guests by name, by show, by topic or by how often they appear, and pick up the person slug. For who is currently making the rou… |
| `people/guests/trending` | 25 | Use for who is doing the podcast circuit right now: a book launch, a product unveil, a news moment, or someone new. For a steady-state dire… |
| `people/profile` | 5 | Use to go from a name on an episode to the person: who they are, where they work and worked, and their profile links. For their podcast app… |
| `people/show-guests` | 15 | Use for who has been on a show and how often. For who it could book next use people/show-recommended-guests. |
| `people/show-recommended-guests` | 25 | Use as a booking pipeline for a show: guests its peers chose that it has not had yet. |
| `podcasts/clip` | 15 | Use when a segment needs to be cited as a playable range rather than as text. For its words call podcasts/clip/transcript. |
| `podcasts/clip/transcript` | 15 | Use to quote a clip verbatim with speaker labels, or export it as subtitles with format srt. |
| `podcasts/clips` | 15 | Use to browse quotable moments by show, speaker or kind. For clips about a subject, search episodes: matching clips ride inside each search… |
| `podcasts/episode` | 5 | Use episode.id from a search match to get the full record and, when available, its web URL or direct audio stream. Neither link is guarante… |
| `podcasts/episode/clips` | 5 | Use for the quotable moments of an episode as bounded, playable ranges with a kind and a speaker. |
| `podcasts/episode/entities` | 15 | Use for what an episode was about in named things: the companies, people and products it discussed, ranked by salience. For where each one … |
| `podcasts/episode/related` | 15 | Use for who else covered this: the same story or subject on other shows, optionally within a week of the episode. |
| `podcasts/episode/segments` | 15 | Use to see the structure of an episode and pick the section to read: which time ranges are ads to skip, where the interview starts, what ea… |
| `podcasts/episode/speakers` | 15 | Use to find who was on an episode and in what role, with the person slug to follow into people/profile or people/guest. Ask for the adverti… |
| `podcasts/episode/topics` | 15 | Use to classify an episode by subject area, or to pick up a topic_id for filtering shows and episodes. |
| `podcasts/episodes/feed` | 5 | Use to poll for new episodes of a set of shows or topics as they are transcribed: a resumable, strictly ordered pull. A filter is required.… |
| `podcasts/episodes/list` | 5 | Use for episode-level filtering without dialogue: every episode a person spoke on, every episode featuring a company, a show's episodes in … |
| `podcasts/episodes/lookup` | 5 | Use when you hold a Spotify, Apple Podcasts or YouTube episode link, a platform episode id, or an RSS guid and need the Particle episode id… |
| `podcasts/episodes/search` | 15 | Use to find episodes that discussed something. This is the entry point: it returns ids the other podcast capabilities take. For every line … |
| `podcasts/episodes/timeseries` | 5 | Use for a trend rather than a list: how often a person appeared by month, how a show's output changed, how many episodes discussed a term e… |
| `podcasts/list` | 5 | Use to browse shows by attribute rather than by name: a topic, a language, a brand-suitability tier, a length band, a cadence, an ad-free o… |
| `podcasts/lookup` | 5 | Use when you already hold an Apple collection id, Spotify show id, YouTube channel id or RSS feed URL and need the Particle podcast determi… |
| `podcasts/mentions` | 15 | Use for every line of dialogue about one person or company across podcasts: the read-everything-about-X call. Resolve the subject with enti… |
| `podcasts/mentions/timeseries` | 15 | Use for how mentions of a person or company trend by day, week or month, optionally within one show or network. One call instead of paging … |
| `podcasts/publisher` | 15 | Use to go from a show's publisher reference to the network record. For the network's shows call podcasts/publisher/shows; for its advertisi… |
| `podcasts/publisher/shows` | 15 | Use to walk a network's catalogue by audience. For the same catalogue ranked by ad volume use advertising/publisher/shows. |
| `podcasts/publishers` | 15 | Use to find a network's slug by name before asking about its shows, advertising, bias or suitability. |
| `podcasts/search` | 5 | Use to turn a show name into its slug and record. To find what was said inside one, search episodes instead: this matches show metadata, no… |
| `podcasts/segment` | 5 | Use to see what a matched segment is (an interview, a topic discussion, an ad) and its time range. For its text call podcasts/segment/trans… |
| `podcasts/segment/transcript` | 15 | Use to read the words of one segment in full and in order, at the price of a segment rather than an episode. |
| `podcasts/segments` | 5 | Use to pull one kind of section across a show: every interview, every ad read, every topic discussion in a date range. For one episode's st… |
| `podcasts/show` | 5 | Use when a search or an episode record gave you a podcast id and the full show record is needed, including the publisher to go up to and th… |
| `podcasts/show/episodes` | 15 | Use to get from a show to its episodes and their ids: the latest episode, an episode by title, or the run of episodes in a date range. A po… |
| `podcasts/show/external-links` | 15 | Use to get a show's Apple, Spotify or YouTube ids and links, its social handles, or its website. The reverse direction, platform id to show… |
| `podcasts/show/format` | 15 | Use for the exact rates and distributions behind a show's format: how often it has guests, how long episodes run, how often it publishes an… |
| `podcasts/show/mentions` | 15 | Use for how much one show talks about a person or company: an episode-level roll-up inside one podcast. For the dialogue lines themselves, … |
| `podcasts/show/ratings` | 5 | Use to read what listeners wrote about a show. For the averages and histogram use podcasts/show/ratings-summary. |
| `podcasts/show/ratings-summary` | 15 | Use for a show's average rating and count per storefront, plus the combined figure and what recent reviews say in aggregate. |
| `podcasts/show/related` | 15 | Use for shows like this one: competitive sets, a listener's next show, or the peer set a sponsor or guest pitch cites. Branch on band rathe… |
| `podcasts/topics` | 15 | Use to see which subject areas have the most shows. For the full taxonomy tree use entities/topics; for the shows in one topic use podcasts… |
| `podcasts/transcript` | 15 | Use to read a whole episode rather than the excerpt a search returned. For one passage, podcasts/segment/transcript is smaller and cheaper;… |
| `podcasts/transcript/mentions` | 15 | Use to see exactly where and how a company, person or product was discussed within one episode, with the dialogue around each mention. Acro… |
| `podcasts/transcript/preview` | 15 | Use to read what was being said at a timestamp, or the opening of an episode, at a fifth of the full transcript's price. For a whole episod… |
| `rankings/categories` | 15 | Use to find the category_slug the chart capabilities take. |
| `rankings/charts` | 25 | Use for today's chart: the US Apple overall top podcasts with no arguments, or a country and category. Use rankings/categories and rankings… |
| `rankings/countries` | 15 | Use to find the country codes the chart capabilities take. |
| `rankings/history` | 25 | Use for how a chart looked on past days, or how one show moved within it. For one show across every chart use rankings/show/history. |
| `rankings/movers` | 25 | Use for what debuted, climbed, fell or dropped off a chart since yesterday or over a window. |
| `rankings/show` | 25 | Use for where a show charts today, everywhere it charts. For a one-number summary use rankings/show/summary. |
| `rankings/show/history` | 25 | Use for a show's chart trajectory over time. |
| `rankings/show/summary` | 25 | Use for how big a show is on the charts in one call: its best rank and how widely it charts. |
| `rankings/sources` | 15 | Use to check which chart sources exist and how fresh the snapshot is. |
| `suitability/category-publishers` | 25 | Use to pivot on one category for a regulated or family brand: which networks carry the most, or least, alcohol, weapons, adult or hate-spee… |
| `suitability/guest` | 25 | Use for what kind of shows a guest tends to appear on, in brand-safety terms. |
| `suitability/publisher` | 25 | Use for how brand-safe a network's catalogue is as a whole and where its exposure sits. |
| `suitability/publisher/shows` | 25 | Use to build an inclusion or exclusion list inside one network: its shows by tier, or the ones exposed in a category. |
| `suitability/publishers/leaderboard` | 25 | Use for the safest or riskiest networks to buy, or the most broadly placeable. |
| `suitability/show` | 25 | Use for whether a show is safe to advertise on and in which categories it is exposed, with the evidence. The tier alone rides on every show… |

<a id="p-patentscope-wipo-int"></a>

### WIPO PATENTSCOPE patent search (`patentscope-wipo-int`)

WIPO PATENTSCOPE (patentscope.wipo.int): full-text and fielded search over the PCT collection and 85 national and regional patent collections, bibliographic records of one PCT or national document (titles and abstracts per language, parties, classifications, priorities, designated states, family links), and the reference lists behind the query language (search field codes, office codes, IPC symbo…

| Capability | Credits | Use |
| --- | --- | --- |
| `intellectual-property/patent` | 5 | You have a PATENTSCOPE doc_id (WO2024001234, CN190116616) and need the full bibliographic data. |
| `intellectual-property/reference` | 5 | Before composing a `search` query: to find the right field code, office code or IPC symbol. |
| `intellectual-property/search` | 5 | You need patent documents matching keywords, a title, an applicant or inventor, a publication or application number, or a date range, optio… |

<a id="p-peerspot-com"></a>

### PeerSpot (`peerspot-com`)

Public PeerSpot software products, customer reviews, ratings and comparisons.

| Capability | Credits | Use |
| --- | --- | --- |
| `software-reviews/compare` | 5 | PeerSpot head-to-head comparison of two products: category ranking, average rating (out of 10), reviews sentiment and review count per prod… |
| `software-reviews/product` | 5 | One PeerSpot product page: average rating and review count, willingness to recommend, category ranking and mindshare, editorial review-them… |
| `software-reviews/reviews` | 5 | One page (10 reviews) of full-text PeerSpot reviews for a product: star rating, title, date, reviewer role and labels, company size, indust… |
| `software-reviews/search` | 5 | Find PeerSpot product pages for a vendor or product name. Returns up to 10 matching products with the slug needed by product, reviews and c… |

<a id="p-people-data-labs"></a>

### People Data Labs (`people-data-labs`)

Company identity resolution, enrichment and search from a domain, ticker, name or company profile.

| Capability | Credits | Use |
| --- | --- | --- |
| `company/enrich` | 50 | Use when you have one company and want its firmographics, funding and headcount. Give it a domain, ticker or social profile if you possibly… |
| `company/search` | 50/record | Use to find companies by attribute - industry, headcount, funding stage, location - rather than to look one up you can already name. Each r… |

<a id="p-purchasing-alberta-ca"></a>

### Alberta Purchasing Connection (`purchasing-alberta-ca`)

Alberta Purchasing Connection (purchasing.alberta.ca), the Government of Alberta's public procurement portal: search tender postings by text, status, organization, region, category, solicitation and opportunity type, UNSPSC code and post/close dates; one posting's full public record (dates, submission details, contact, documents metadata, plan holders, bidders, awards); the contracting-organizati…

| Capability | Credits | Use |
| --- | --- | --- |
| `public-tenders/get_posting` | 5 | After search_postings, or when a user pastes a https://purchasing.alberta.ca/posting/AB-YYYY-NNNNN link. |
| `public-tenders/list_codes` | 5 | Translate a code seen in a posting (e.g. TA-01, RFQual, OPEN-COMPETITIVE) or find valid filter values for search_postings. |
| `public-tenders/list_organizations` | 5 | Find the exact organization name or id to filter search_postings, or to resolve a posting's contracting_organization_id. |
| `public-tenders/search_postings` | 5 | Discover tenders, notices and awards; take `reference_number` into `get_posting`. Use `list_codes`, `list_organizations` and `search_unspsc… |
| `public-tenders/search_unspsc_codes` | 5 | Find UNSPSC codes for a product or service area before filtering search_postings, or expand a code seen in a posting. |

<a id="p-quickstart-sos-nh-gov"></a>

### New Hampshire business registry (QuickStart) (`quickstart-sos-nh-gov`)

New Hampshire Secretary of State QuickStart business registry (quickstart.sos.nh.gov/online/businessinquire): search businesses by name, Business ID or filing number, read a business record (type, status, dates, addresses, principals, registered agent, NAICS purpose, trade names, trademarks) and its filing history. Anonymous public access only; no certificates, documents, orders or filings. Every…

| Capability | Credits | Use |
| --- | --- | --- |
| `entities/get_business` | 5 | You have a business_id_token or Business ID (from search_businesses or a pasted BusinessInformation URL) and need the full registration rec… |
| `entities/get_filing_history` | 5 | You have a business_id_token or Business ID and need the chronological list of filings (annual reports, amendments, agent changes, formatio… |
| `entities/search_businesses` | 5 | You know (part of) a New Hampshire business name, a Business ID (270916, B55208 ...) or a filing number and need the business's status, typ… |

<a id="p-recherche-entreprises-api-gouv-fr"></a>

### API Recherche d'entreprises (annuaire-entreprises.data.gouv.fr) (`recherche-entreprises-api-gouv-fr`)

The French state's open company search (API Recherche d'entreprises, run by DINUM for annuaire-entreprises.data.gouv.fr): every diffusible French legal unit from INSEE Sirene and INPI's national company register (RNE) with legal form, NAF activity, salaried headcount band, INSEE size category, head office with address and coordinates, executives (dirigeants) as published, latest published revenue…

| Capability | Credits | Use |
| --- | --- | --- |
| `companies/get_company` | 5 | Due diligence or M&A screening on one French company: SIREN, headcount band, revenue and executives in one call. Use search_companies first… |
| `companies/search_companies` | 5 | Screening and prospect lists of French companies: e.g. software publishers (58.29C) or IT consultancies (62.02A) in Île-de-France with 50-2… |
| `companies/search_near_point` | 5 | Local market mapping: which companies operate establishments around an address or coordinates, e.g. restaurant companies (56.10A) within 1 … |

<a id="p-reclameaqui-com-br"></a>

### Reclame Aqui (`reclameaqui-com-br`)

Reclame Aqui (reclameaqui.com.br), Brazil's consumer complaints platform: company reputation profiles (score, RA1000/Otimo/Bom/Regular/Ruim/Nao recomendada status, response and solution rates), company search by name or CNPJ, a company's complaints with tabs and pagination, full-text complaint search, single complaint text with the company reply and consumer evaluation, segment tree and best/wors…

| Capability | Credits | Use |
| --- | --- | --- |
| `complaints/company` | 5 | Look up a company's reputation and identity when you know its shortname (from search_companies or a pasted profile URL). |
| `complaints/company_complaints` | 5 | List or paginate a company's complaints. Pass company_id from search_companies or company (or shortname). Use page for the next page while … |
| `complaints/complaint` | 5 | Read one complaint's text, the company reply and the consumer's evaluation. Ids and URLs come from company_complaints or search_complaints. |
| `complaints/search_companies` | 5 | Start here to resolve a company's shortname and numeric id from a name or CNPJ before calling company, company_complaints or search_complai… |
| `complaints/search_complaints` | 5 | Find complaints about a topic ('reembolso', a product name) across Reclame Aqui or within one company. Use company_complaints to browse a c… |
| `complaints/segment_ranking` | 5 | Rank companies in a category, e.g. the best marketplaces (varejo/marketplaces) or the worst online courses. |
| `complaints/segments` | 5 | Discover the main_segment/sub_segment pair for segment_ranking or browse Reclame Aqui's category taxonomy. |

<a id="p-register-fca-org-uk"></a>

### UK Financial Services Register (FCA) (`register-fca-org-uk`)

The FCA's Financial Services Register (register.fca.org.uk): search authorised and registered firms by name or firm reference number, read a firm's record (status, permissions and their conditions, requirements, disciplinary history, waivers, appointed representatives, regulators, names, addresses, individuals), search approved individuals and read an individual's controlled functions, search and…

| Capability | Credits | Use |
| --- | --- | --- |
| `entities/get_firm` | 5 | You have a firm_id or FRN (from search_firms, a controlled function or a register URL) and need the full regulatory record. |
| `entities/get_fund` | 5 | You have a fund_id (from search_funds, a sub-fund list or a register URL) and need the full record. |
| `entities/get_individual` | 5 | You have an individual_id (from search_individuals, a firm's individuals or a register URL) and need the full record. |
| `entities/list_downloads` | 5 | You want a whole register extract (investment firms, PSD/EMD agents, appointed representatives ...) rather than per-record calls. |
| `entities/list_register` | 5 | You need the complete list of registered cryptoasset firms or of unregistered cryptoasset businesses the FCA warns about. |
| `entities/search_firms` | 5 | You know (part of) a firm's name or its FRN and need its status, sectors, permission categories or the `firm_id` that get_firm takes. |
| `entities/search_funds` | 5 | You know (part of) a fund or umbrella name or a PRN and need its status, structure or the `fund_id` that get_fund takes. |
| `entities/search_individuals` | 5 | You know an individual's name (or IRN) and need their status, roles, the firms they are approved at or the `individual_id` that get_individ… |

<a id="p-safer-fmcsa-dot-gov"></a>

### FMCSA SAFER and SMS carrier registry (`safer-fmcsa-dot-gov`)

FMCSA's public motor carrier safety data: the SAFER Company Snapshot system (safer.fmcsa.dot.gov: carrier name search, Company Snapshot by USDOT or MC/MX number with identity, authority, fleet size, drivers, cargo, 24-month inspection/out-of-service/crash counts and safety rating) and the Safety Measurement System (ai.fmcsa.dot.gov/SMS: paginated carrier search with power units, inspection and cr…

| Capability | Credits | Use |
| --- | --- | --- |
| `carriers/get_carrier_snapshot` | 5 | You have a USDOT or MC/MX number (from search_carriers, search_sms_carriers or elsewhere) and need the carrier's registration, fleet and sa… |
| `carriers/get_sms_overview` | 5 | You have a USDOT number and need the SMS safety performance view (BASICs, investigations, inspection and crash breakdown) rather than SAFER… |
| `carriers/get_sms_safety_records` | 5 | You need the individual inspections, violations or crashes behind a carrier's SMS totals. |
| `carriers/search_carriers` | 5 | You know (part of) a motor carrier's name and need its USDOT number before calling get_carrier_snapshot, get_sms_overview or get_sms_safety… |
| `carriers/search_sms_carriers` | 5 | You want a listing with fleet size and safety totals per carrier, or more than SAFER's 500-match cap allows, and want to page through it. |
| `carriers/suggest_sms_carrier_names` | 5 | You have a partial carrier name and want the spellings SMS knows before searching. |

<a id="p-sanctionssearch-ofac-treas-gov"></a>

### OFAC Sanctions List Search (`sanctionssearch-ofac-treas-gov`)

U.S. Treasury OFAC Sanctions List Search (sanctionssearch.ofac.treas.gov) and the Sanctions List Service REST API (sanctionslistservice.ofac.treas.gov): fuzzy name / ID-number / address search across the SDN and Non-SDN lists with program, country, type and list filters and a minimum match score; the Details page of one record (identifications, aliases, addresses); the structured Enhanced XML ent…

| Capability | Credits | Use |
| --- | --- | --- |
| `sanctions/entity` | 5 | You have an OFAC entity id (from `search`, `record` or elsewhere) and want the structured, machine-readable record instead of the HTML deta… |
| `sanctions/publications` | 5 | Track when OFAC published list changes, or find the publication id of a change to fetch its delta. |
| `sanctions/record` | 5 | You have an entity_id from `search` (or an SLS entity id) and want the human-readable record as OFAC's search tool shows it. |
| `sanctions/reference_lists` | 5 | Before filtering by program, or to map a program code or list name seen in a record. |
| `sanctions/search` | 5 | Screen a name, ID number, digital currency address or address against OFAC's lists, or list the records of a program / country / type, and … |

<a id="p-search-ipaustralia-gov-au"></a>

### IP Australia trade mark search (`search-ipaustralia-gov-au`)

Australian Trade Mark Search (search.ipaustralia.gov.au), IP Australia's public trade mark register: quick search by words, owner name or number; advanced search with word, image, class, status, date, kind, party, attorney, ACN and number filters; 100-per-page pagination and sorting; and the full public record of a trade mark (words, image, status, dates, owners and addresses for service, goods a…

| Capability | Credits | Use |
| --- | --- | --- |
| `intellectual-property/get_trademark` | 5 | After a search returned a trade mark number, or with a pasted /trademarks/search/view/{number} URL. |
| `intellectual-property/search_trademarks` | 5 | Start here with a word, brand, owner name or trade mark number. Use search_trademarks_advanced for class, status, date, kind or party filte… |
| `intellectual-property/search_trademarks_advanced` | 5 | When the search needs filters beyond a free-text term. Pass the returned search_record with page to page through the same result set withou… |

<a id="p-search-sunbiz-org"></a>

### Florida Sunbiz (`search-sunbiz-org`)

Florida official entity name lists and business registration records, including source-labelled officers, registered agents and filing links.

| Capability | Credits | Use |
| --- | --- | --- |
| `entities/entity` | 5 | Look up a Florida corporate registration by document number. Returns filing attributes, source-labelled officer and registered-agent sectio… |
| `entities/search` | 5 | Browse the official alphabetical entity name list from a query. Results can include nearby names, historical registrations and trademarks, … |

<a id="p-sos-state-co-us"></a>

### Colorado Secretary of State business database (`sos-state-co-us`)

Colorado Secretary of State business database (the live registry at www.sos.state.co.us/biz): business name, ID and document-number search, entity summary with periodic report month and registered agent, and the filing history with document links and periodic-report due dates.

| Capability | Credits | Use |
| --- | --- | --- |
| `entities/entity` | 3 | You have an entity_id from `search` (or a Colorado SOS ID number) and need the current record. |
| `entities/filings` | 5 | You need due dates, filed documents or the event timeline for an entity_id from `search` or `entity`. |
| `entities/search` | 5 | Start here to find the 11-digit entity_id for `entity` and `filings`. |

<a id="p-tenders-gov-au"></a>

### AusTender (`tenders-gov-au`)

AusTender, the Australian Government procurement portal: current and closed approaches to market (ATMs) with closing times in ACT local time and UTC, full ATM notices including the free-text instructions where mandatory briefings are announced, and Commonwealth contract notices from the public OCDS API by publication, modification, start or end date, or by CN id.

| Capability | Credits | Use |
| --- | --- | --- |
| `public-tenders/atm_detail` | 5 | Pass `guid` or `url` from an atm_search row, or an `atm_id` such as `NS1333` (resolved through the list's id filter, so only open ATMs reso… |
| `public-tenders/atm_search` | 5 | Start here to find open procurement opportunities by keyword (e.g. `cleaning`); pass a row's `guid` or `atm_id` to atm_detail for the full … |
| `public-tenders/contract_detail` | 5 | Pass a `cn_id` such as `CN4279555` (amendments like `CN4111658-A1` are their own ids). An unknown id is not_found (the API answers 400 erro… |
| `public-tenders/contracts_by_date` | 5 | Use for 'what was published/started/ends between X and Y'. The API pages 100 releases at a time behind an opaque cursor; `limit` trims a pa… |

<a id="p-trademarks-ipo-gov-uk"></a>

### UK IPO trade mark register (`trademarks-ipo-gov-uk`)

UK Intellectual Property Office trade mark register: search owners by name or UK postcode, list the UK national marks an owner holds, and read a trade mark's case detail (status, dates, goods and services, owners, representatives, publications) and case history (status, event and goods history).

| Capability | Credits | Use |
| --- | --- | --- |
| `trade-marks/get_trade_mark` | 5 | When you have a trade mark number (UK000..., or UK009... for a comparable mark derived from an EU trade mark, domain 23). An unknown number… |
| `trade-marks/get_trade_mark_history` | 5 | For assignment, ownership-change and status timelines of a known trade mark number. |
| `trade-marks/list_owner_marks` | 5 | After search_owners returned a client_id, or from the owner link on a case detail. Follow up with get_trade_mark for the full record. |
| `trade-marks/search_owners` | 5 | Start here when you know a company or person name but not a trade mark number. An owner name that matches nothing returns zero owners, not … |

<a id="p-txsmartbuy-gov"></a>

### Texas SmartBuy ESBD (`txsmartbuy-gov`)

Texas Electronic State Business Daily (ESBD) on txsmartbuy.gov: search and read public solicitation notices, pre-solicitation notices, awards posted without a solicitation and grant opportunities, with attachments, from the Texas Comptroller's anonymous SuiteCommerce JSON services.

| Capability | Credits | Use |
| --- | --- | --- |
| `public-tenders/get_award` | 5 | Reading a purchase-order award returned by search_awards. |
| `public-tenders/get_grant` | 5 | Reading a grant opportunity returned by search_grants. |
| `public-tenders/get_solicitation` | 5 | Reading the full notice and attachment links for an id returned by search_solicitations or found in an ESBD URL. |
| `public-tenders/list_agencies` | 5 | Resolving an agency name to the agency_number search_solicitations and search_awards take. |
| `public-tenders/list_nigp_codes` | 5 | Validating or completing a NIGP code for the nigp_code filter. |
| `public-tenders/search_awards` | 5 | Finding Texas agency purchase-order awards and vendors; follow with get_award for notes and attachments. |
| `public-tenders/search_grants` | 5 | Finding Texas state grant opportunities and their grant numbers before calling get_grant; the facets in the output give the ids the filters… |
| `public-tenders/search_solicitations` | 5 | Finding Texas state procurement opportunities and their public ids before calling get_solicitation. Pass notice_type 'presolicitation' for … |

<a id="p-ungm-org"></a>

### UN Global Marketplace (`ungm-org`)

UN Global Marketplace (ungm.org), the procurement portal of the United Nations system: public procurement notices (tenders, RFPs, RFQs, EOIs) with deadlines, publishing agency, beneficiary country, reference, contacts, links and UNSPSC codes; published contract awards with supplier, award date and agency; and the UNSPSC category taxonomy used by both searches. Anonymous, read-only.

| Capability | Credits | Use |
| --- | --- | --- |
| `public-tenders/get_contract_award` | 5 | After search_contract_awards, with a row's `contract_award_id`, or when given a `https://www.ungm.org/Public/ContractAward/<id>` URL. An un… |
| `public-tenders/get_notice` | 5 | After search_notices, with a row's `notice_id`, or when given a `https://www.ungm.org/Public/Notice/<id>` URL. An unknown id is not_found. |
| `public-tenders/search_contract_awards` | 5 | To find who won UN contracts, by supplier name, agency, country or award window; pass a row's `contract_award_id` to get_contract_award for… |
| `public-tenders/search_notices` | 5 | Start here to find open UN tenders by keyword, agency (e.g. `UNDP`), country or deadline window; pass a row's `notice_id` to get_notice for… |
| `public-tenders/search_unspsc` | 5 | To turn a product or service keyword (`solar`, `vaccines`, `consulting`) into UNSPSC node ids before filtering search_notices. Only rows wi… |

<a id="p-usaspending-gov"></a>

### USAspending (`usaspending-gov`)

Federal awards, transactions, recipients and agencies from USAspending.gov.

| Capability | Credits | Use |
| --- | --- | --- |
| `agencies/agency` | 5 | Toptier agency overview for a fiscal year by CGAC/FREC code (097 Department of Defense, 075 Health and Human Services, 036 Veterans Affairs… |
| `awards/award` | 5 | One USAspending prime award by generated_unique_award_id (CONT_AWD_…, CONT_IDV_…, ASST_NON_…, ASST_AGG_…) or numeric internal id: identifie… |
| `awards/award_search` | 5 | Search USAspending prime awards by keyword, awarding/funding agency, recipient name or UEI, action-date window, place of performance, NAICS… |
| `awards/idv_children` | 5 | Awards issued under an indefinite delivery vehicle: child awards (orders), child IDVs or grandchild awards, newest period start first, with… |
| `awards/subawards` | 5 | Subawards reported under one prime award (FSRS data), newest first: subaward number, sub-recipient name, amount, action date and descriptio… |
| `awards/transactions` | 5 | Transactions (individual actions and modifications) of one award, newest action first: obligation per action (negative for de-obligations),… |
| `recipients/recipient` | 5 | Recipient profile by USAspending recipient_id (hash with -C/-P/-R level) or 12-character UEI: names, identifiers, parent, business types, l… |

<a id="p-uspto-gov"></a>

### USPTO patents, trademarks and assignments (`uspto-gov`)

United States Patent and Trademark Office public records: Patent Public Search (full-text patent and pre-grant publication search and bibliographic documents), Trademark Search (word-mark search), TSDR trademark status records by serial or registration number, and Assignment Center ownership records for patents and trademarks. Anonymous, stateless JSON APIs behind the USPTO web applications; US c…

| Capability | Credits | Use |
| --- | --- | --- |
| `intellectual-property/assignments` | 5 | You need who owns or has a security interest in a patent or trademark, or the reel/frame of a recorded assignment. |
| `intellectual-property/patent_document` | 5 | You have a patent number, publication number or ppubs guid and need the record itself. |
| `intellectual-property/patent_search` | 5 | Start here to find patents or publications by title, number, assignee, inventor or classification; pass `patents[].guid` to `patent_documen… |
| `intellectual-property/trademark_search` | 5 | Find trademark serial numbers by mark text; pass `hits[].serial_number` to `trademark_status` or `assignments`. |
| `intellectual-property/trademark_status` | 5 | You have a serial or registration number and need the current status and parties of the mark. |

<a id="p-ycombinator-com"></a>

### Y Combinator (`ycombinator-com`)

Public YC startup directory: browse or search companies by batch and filters, list batches, read company profiles and advertised jobs.

| Capability | Credits | Use |
| --- | --- | --- |
| `companies/batches` | 5 | List every batch label published in the public YC directory with its company count, newest first. Use a returned batch label as the search … |
| `companies/company` | 5 | Read a public YC company profile: description, batch, location, team size, source-reported status and the founders listed on the profile (n… |
| `companies/jobs` | 5 | List public jobs advertised on a YC company profile, including source salary text, location, role and requirements. Each record adds best-e… |
| `companies/search` | 5 | Browse or search the public YC company directory. Query is optional: omit it to list every company matching the exact source labels for bat… |

## developer

Developer documentation, repositories, code and agent skills.

<a id="p-firecrawl-developer-index"></a>

### Developer Index (`firecrawl-developer-index`)

Search developer documentation, repositories, issues and agent skills with matched passages.

| Capability | Credits | Use |
| --- | --- | --- |
| `search` | 2/record | Find code examples, official documentation, repository discussions or agent skills for a development task. |

## digital-intelligence

Website traffic, audience, search marketing and competitive digital intelligence.

<a id="p-similarweb"></a>

### Similarweb (`similarweb`)

Website traffic, audiences and search intelligence from Similarweb.

| Capability | Credits | Use |
| --- | --- | --- |
| `channels/share` | 550 | Use for marketing channel shares for one complete month. Subscription availability applies. The Similarweb-only monthly credit allowance ap… |
| `channels/traffic` | 550 | Use for marketing channel traffic for one complete month. Subscription availability applies. The Similarweb-only monthly credit allowance a… |
| `web/geography` | 110 | Use for traffic geography for one complete month. Subscription availability applies. The Similarweb-only monthly credit allowance applies. |
| `web/incoming-referrals` | 330 | Use for incoming referral domains for one complete month. Subscription availability applies. The Similarweb-only monthly credit allowance a… |
| `web/ppc-spend` | 110 | Use for paid search spend for one complete month. Subscription availability applies. The Similarweb-only monthly credit allowance applies. |
| `web/referrals` | 330 | Use for referral traffic for one complete month. Subscription availability applies. The Similarweb-only monthly credit allowance applies. |
| `web/traffic` | 110 | Use for traffic and engagement for one complete month. Subscription availability applies. The Similarweb-only monthly credit allowance appl… |
| `web/website-referrals/outgoing-referrals` | 330 | Outgoing referrals. Subscription availability applies. The Similarweb-only monthly credit allowance applies. Reference: https://docs.simila… |

## energy

Energy statistics: official supply, demand, generation, emissions and price series from agencies such as the IEA.

<a id="p-auc-ab-ca"></a>

### Alberta Utilities Commission (`auc-ab-ca`)

Alberta Utilities Commission (auc.ab.ca) public regulatory record: the decisions, recent updates, notices, facility approvals, gas pipeline licence and monthly rate approval tables with eFiling document ids, the public PDF of any decision or notice with its extracted text, proceedings currently under review, featured (high-profile) applications, the hearing and events calendar, and the site's ful…

| Capability | Credits | Use |
| --- | --- | --- |
| `regulatory-decision/get_document` | 5 | Read the full text of a decision or notice found through `list_documents`, `search` or a featured application. Not for eFiling exhibits, wh… |
| `regulatory-decision/get_featured_application` | 5 | Get the official numbers and overview of a high-profile proceeding and the links to its application and decision PDFs. |
| `regulatory-decision/list_current_applications` | 5 | Check whether a proceeding or applicant has an application under review and get its application number. |
| `regulatory-decision/list_documents` | 5 | Find decisions, notices or approvals by proceeding, applicant, date or type; feed `get_document` with `efiling_document_id`. Not for procee… |
| `regulatory-decision/list_events` | 5 | See which hearings are scheduled in a date window and for which proceedings. |
| `regulatory-decision/list_featured_applications` | 5 | Discover which proceedings the AUC presents as featured, then call `get_featured_application` for the proceeding, application and decision … |
| `regulatory-decision/search` | 5 | Find decisions or pages by topic, facility type, place or applicant when you do not have a proceeding id; verify any hit through `get_docum… |

## entertainment

Films, TV shows, books and games: ratings, cast, release dates, reading lists.

<a id="p-collections-search-bfi-org-uk"></a>

### BFI Collections Search (`collections-search-bfi-org-uk`)

BFI Collections Search (collections-search.bfi.org.uk), the British Film Institute's public catalogue of the BFI National Archive and BFI Reuben Library (Axiell Internet Server): expert search of any of its 12 databases (film and television works, film/video items, books, serials, articles, press cuttings, scripts and documents, posters, stills, special collections, library, persons and instituti…

| Capability | Credits | Use |
| --- | --- | --- |
| `records/get_record` | 5 | Read the full record behind a `search_records` row or a pasted /web/Details/{database}/{priref} URL. |
| `records/list_search_fields` | 5 | Before `search_records` on a database whose field names you do not know. |
| `records/lookup_terms` | 5 | Find the exact genre, subject, work type or other authority term spelling before searching on it. |
| `records/search_records` | 5 | Find BFI catalogue records (films, TV programmes, archive items, books, articles, posters, stills, people) matching field conditions, then … |

<a id="p-forever-codex-com"></a>

### Forever Codex (`forever-codex-com`)

Forever Codex, a World of Warcraft: Forever fan site built from the game files: a one-page overview of every class spec (stat values, racials that matter, the calculated pre-raid best in slot, consumables and crafted Tier 1), every class's talent trees with each talent's ranks, requirements and what changed since Classic Era, the dungeon finder (every dungeon and raid by level with its best drops…

| Capability | Credits | Use |
| --- | --- | --- |
| `video-game-gear/dungeon` | 5 | Read one instance found through `dungeons` (pass its `slug`, like `deadmines` or `the-hall-of-thanes`). An unknown slug is `not_found`. |
| `video-game-gear/dungeons` | 5 | Answer which dungeons a WoW Forever character should run at its level and what they drop for its class. Chain `slug` into `dungeon` for bos… |
| `video-game-gear/spec` | 5 | Answer what stats a WoW Forever spec wants, which race helps it, what to aim for at 60 and which consumables to bring. For gear at a lower … |
| `video-game-gear/talents` | 5 | Answer which talents a WoW Forever character can take or should consider at its level (one point per level from 10; row N needs 5*(N-1) poi… |

<a id="p-foreverdb-net"></a>

### ForeverDB (`foreverdb-net`)

ForeverDB, a World of Warcraft: Forever database built from the game client: best-in-slot gear for every class and spec at any level from 1 to 60 for PvE, PvP or leveling (best item per slot with its score, stats, the next two picks, where it comes from and the best enchant, plus the stat weights used), item details (stats, effects, levels, what is new in Forever and where to get it), DPS simulat…

| Capability | Credits | Use |
| --- | --- | --- |
| `video-game-gear/bis` | 5 | Answer what gear a WoW Forever character should wear or aim for at its level: pass class, spec, level and mode. Chain an item id into `item… |
| `video-game-gear/dungeon` | 5 | Answer what drops in a WoW Forever dungeon or raid, how its bosses work, or where it is. Take the `id` from `dungeons`; an unknown id is `n… |
| `video-game-gear/dungeons` | 5 | Answer which dungeons or raids a WoW Forever character should run at its level, or what instances exist. Chain an `id` into `dungeon` for b… |
| `video-game-gear/item` | 5 | Look up an item from a `bis` pick or alternative, or any game item id (ids are shared with Wowhead). An unknown id is `not_found`. |
| `video-game-gear/sim` | 5 | Answer how much damage a WoW Forever DPS spec does, which stats are worth most for it, or what rotation and gear the sim assumes. Healer an… |
| `video-game-gear/talent_builds` | 5 | Answer what talents a WoW Forever character should take: pass class, and spec and level when known. With level, only the builds for the hig… |

<a id="p-talentsforever-com"></a>

### Talents Forever (`talentsforever-com`)

Talents Forever, a World of Warcraft: Forever talent calculator built from the beta client: every class's talent trees with each rank's text, prerequisites and what changed from Classic, decoding of the site's build links into ranks per talent (CC BY 4.0 data from its JSON export), the most popular level 60 and level 30 builds per class and spec, and the order players place talent points in while…

| Capability | Credits | Use |
| --- | --- | --- |
| `video-game-talents/builds` | 5 | Answer which talent build a WoW Forever class or spec should take at 60 or at the level 30 cap. Pass a row's `calculator_url` to `talents` … |
| `video-game-talents/leveling` | 5 | Answer which talents a leveling WoW Forever character should have at its level ("level 20 Arms warrior"): pass class, spec and level and re… |
| `video-game-talents/talents` | 5 | Answer what a WoW Forever talent does, what a class's trees hold, or exactly which talents a shared build link takes. Pass `calculator_url`… |

<a id="p-themoviedb-org"></a>

### TMDB (The Movie Database) (`themoviedb-org`)

The Movie Database (themoviedb.org) from the public website, no API key and no login: title search with TMDB ids, movie and TV show details (overview, release dates, genres, user score, top-billed cast, keywords, facts), full cast and crew, streaming / rent / buy availability per country (JustWatch-sourced offers as the TMDB watch page shows them), per-country theatrical and digital release dates…

| Capability | Credits | Use |
| --- | --- | --- |
| `films/get_credits` | 5 | Who is in a film or show and who made it, beyond the top-billed strip get_title returns. |
| `films/get_person` | 5 | Who someone is and what they have been in or worked on. |
| `films/get_release_dates` | 5 | Is a film out yet, where and when it was or will be released, and with which rating. |
| `films/get_season` | 5 | Episode list and air dates of a season; is a new episode out yet. |
| `films/get_title` | 5 | Details of a known movie or show: when it came out, what it is about, who is in it, how it is rated, and whether TMDB shows it as streaming. |
| `films/get_watch_providers` | 5 | Streaming availability: where to stream, rent or buy a title in a given country (ISO 3166-1 alpha-2, default US). |
| `films/search` | 5 | Resolve a title or person name to a TMDB id and media type before calling get_title, get_credits, get_watch_providers, get_release_dates, g… |

<a id="p-www-60-tools"></a>

### 60.tools (`www-60-tools`)

60.tools, a World of Warcraft: Forever database and gear planner: curated best-in-slot lists per class and role at the beta level cap (30) and a level-20 archive, with ranked items per slot, Alliance and Horde picks, sources, crafting materials, enchants, consumables and the talent build that goes with the gear; every class talent with its Forever change versus Classic; and item details with Clas…

| Capability | Credits | Use |
| --- | --- | --- |
| `video-game-gear/bis` | 5 | Answer what gear, enchants, consumables and talents a WoW Forever character should use, e.g. a level 20 warrior: pass class, list slug (fro… |
| `video-game-gear/item` | 5 | Look up an item from a BiS list or a user's question; ids are the game's ids, shared with Wowhead and ForeverDB. |
| `video-game-gear/lists` | 5 | Find the right list slug for `bis`, e.g. which warrior list is Arms or Fury at a level. |
| `video-game-gear/talents` | 5 | Explain a WoW Forever class's talents or what changed from Classic; pair with the builds from `bis`. |

<a id="p-zockify-com"></a>

### Zockify (`zockify-com`)

Zockify's World of Warcraft: Forever tools (zockify.com/forever/): the talent calculator's full talent trees per class, the gear planner's stat weight presets (stat priorities and hit caps per role) and ranked item lists per class, slot and level, and the class guides with what changed in Forever and which talents are new or removed. Read from the static data files the planners load and the serve…

| Capability | Credits | Use |
| --- | --- | --- |
| `video-game-gear/class_guide` | 5 | Answer what changed for a class in WoW Forever, which talents are new or gone, or whether Zockify has published builds for it yet. |
| `video-game-gear/gear_items` | 5 | Answer which items are best for a WoW Forever character's slot at its level (for example `level 20 warrior head`), or list upgrade options.… |
| `video-game-gear/stat_weights` | 5 | Answer which stats matter most for a WoW Forever class or role (stat priority), or pick a `preset` id for `gear_items`. Pass a class to get… |
| `video-game-gear/talents` | 5 | Answer what talents a WoW Forever class has, what a talent does at each rank, or plan a build (one point per level from 10, every 5 points … |

Also in this category: [JustWatch](#p-justwatch-com)

## finance

Market prices, financial statements, ownership and macro rates.

<a id="p-api-exchange-coinbase-com"></a>

### Coinbase Exchange (`api-exchange-coinbase-com`)

Public market data from the Coinbase Exchange REST API (api.exchange.coinbase.com): trading pairs, tickers with 24h stats, aggregated order books, tick-level trades with cursor pagination, historical OHLCV candles from 1 minute to 1 day walked in 300-bucket windows, exchange-wide volume summary, currencies with networks, and wrapped-asset conversion rates. Anonymous endpoints only; no trading or …

| Capability | Credits | Use |
| --- | --- | --- |
| `markets/get_candles` | 5 | Backtests and price history, e.g. 1-minute BTC-USD candles between two dates: call with `granularity: 60`, `start`, `end`, `max_candles: 30… |
| `markets/get_currency` | 5 | Networks and precision of an asset before interpreting sizes or addresses. |
| `markets/get_order_book` | 5 | Liquidity and spread at a point in time; use `depth` to bound the payload. |
| `markets/get_product` | 5 | Validate a product id or read its tick sizes before interpreting prices and sizes. |
| `markets/get_ticker` | 5 | Current price and 24h range of a pair; poll it instead of the order book when you only need best bid/ask. |
| `markets/get_wrapped_asset` | 5 | The cbETH:ETH conversion rate, APY and circulating supply. |
| `markets/list_currencies` | 5 | Find a currency id, or list every online crypto or fiat currency. |
| `markets/list_products` | 5 | Find the `product_id` (e.g. `BTC-USD`) for tickers, order books, trades and candles, or list every market quoted in a currency. |
| `markets/list_trades` | 5 | Tick-level trade history; walk `next_after` backwards for a backfill, or poll with `before` set to the newest trade id you have. |
| `markets/list_volume_summary` | 5 | Rank or screen markets by volume, or check whether a pair trades on the spot book, RFQ or conversions. |

<a id="p-banks-data-fdic-gov"></a>

### FDIC BankFind Suite (`banks-data-fdic-gov`)

FDIC BankFind Suite (banks.data.fdic.gov), from its public keyless API at api.fdic.gov/banks: every FDIC-insured institution since 1934, current branch locations, quarterly Call Report financials since 1984, bank failures and assistance transactions since 1934, structure-change history, annual state and national banking aggregates, and the annual Summary of Deposits by branch since 1994. Filters,…

| Capability | Credits | Use |
| --- | --- | --- |
| `bank-data/deposits` | 5 | Deposit market share: how much each bank holds in a city, county, state or MSA, or where one bank's deposits sit. Filter by `cert`, `year`,… |
| `bank-data/failures` | 5 | Which banks failed in a period or state, who acquired them, how large they were and what they cost the Deposit Insurance Fund. Filter with … |
| `bank-data/financials` | 5 | A bank's balance sheet, earnings, capital and asset quality over time, or every bank in one quarter. Filter by `cert` for one institution's… |
| `bank-data/history` | 5 | What happened to a bank or its branches over time: when it opened, merged, changed its name or charter, or opened and closed branches. Filt… |
| `bank-data/institutions` | 5 | Find a US bank or savings institution and its FDIC certificate number (CERT), which every other function filters on, or list banks by state… |
| `bank-data/locations` | 5 | Where a bank has branches, or which banks have offices in a city, ZIP or state. Filter by `cert` (from `institutions`) for one bank's netwo… |
| `bank-data/summary` | 5 | State or national banking totals by year: how many banks a state had, total industry assets or deposits, net income, new charters or failur… |

<a id="p-bcb-gov-br"></a>

### Banco Central do Brasil open data (`bcb-gov-br`)

Banco Central do Brasil open data: SGS time series (Selic, CDI, IPCA, IGP-M, IBC-Br, USD/BRL and ~3,600 more series by code), PTAX official exchange rates (USD and other currencies, by date or date range), Focus market expectations (IPCA, Selic, PIB, cambio: median, mean, standard deviation, respondents), PIX statistics (by municipality, aggregate, registered keys, DICT users), retail credit rate…

| Capability | Credits | Use |
| --- | --- | --- |
| `economic-data/credit_rates` | 5 | Compare bank lending rates (mortgage, payroll loans, vehicle, credit card, ...) for a month. |
| `economic-data/datasets_search` | 5 | Find an SGS series code or an Olinda service name before calling `sgs_series` or `olinda_service`. |
| `economic-data/focus_expectations` | 5 | Market consensus for inflation, policy rate, GDP or FX by reference month/year or Copom meeting. |
| `economic-data/olinda_service` | 5 | See which entity sets and functions an Olinda service exposes before querying it. |
| `economic-data/payment_statistics` | 5 | SPI settlement volumes, payment-instrument mix, cash in circulation. |
| `economic-data/pix_statistics` | 5 | PIX volumes by municipality or segment, registered keys, DICT users. |
| `economic-data/ptax_currencies` | 5 | Discover which currency symbols `ptax_currency` accepts. |
| `economic-data/ptax_currency` | 5 | Rates for EUR, GBP, JPY, ... against BRL. Take `moeda` from `ptax_currencies`. |
| `economic-data/ptax_usd` | 5 | USD/BRL PTAX for a day or a range. Use `ptax_currency` for other currencies. |
| `economic-data/sgs_series` | 5 | Get the numbers for a known SGS code. Find codes with `datasets_search` (CKAN `codigo_sgs`). |

<a id="p-bls-gov"></a>

### BLS labor statistics (`bls-gov`)

US Bureau of Labor Statistics time series: list surveys, discover series ids (curated Top Picks and full flat-file catalogs), read a series catalog page, and retrieve employment, wage, price and inflation observations from the keyless public API.

| Capability | Credits | Use |
| --- | --- | --- |
| `economic-statistics/bls_cpi` | 5 | A direct inflation lookup by category; for other CPI items or percent changes use bls_series_search on survey cu and bls_series. |
| `economic-statistics/bls_series` | 5 | Retrieving the numbers once the series ids are known (from bls_top_picks, bls_series_search or the id conventions). The unregistered API al… |
| `economic-statistics/bls_series_detail` | 5 | To learn what a series id means (its labels) without an API key, or to read history older than the API's 10-year window. For many series at… |
| `economic-statistics/bls_series_search` | 5 | Free-text series discovery (the site's own Data Finder is reCAPTCHA-gated). Pick the survey first with bls_surveys or bls_top_picks; catalo… |
| `economic-statistics/bls_surveys` | 5 | To learn which survey abbreviation covers a topic (CU consumer prices, LA local unemployment, CE payroll employment, SM state employment, L… |
| `economic-statistics/bls_top_picks` | 5 | The cheapest way to find well-known series ids for a survey before calling bls_series; use bls_series_search for anything not in the curate… |
| `economic-statistics/bls_unemployment_rate` | 5 | A direct answer to 'what is the unemployment rate in X'; the resolved series id is returned for follow-up calls. |

<a id="p-cftc"></a>

### CFTC (`cftc`)

Commitments of Traders: weekly futures and options positioning by trader category - speculators, hedgers, managed money, dealers, leveraged funds, index traders - for every reportable US futures market, from the CFTC.

| Capability | Credits | Use |
| --- | --- | --- |
| `disaggregated/combined` | 1 | The disaggregated split with options included. Prefer it for crude, natural gas and gold, where a large share of managed-money exposure is … |
| `disaggregated/futures-only` | 1 | Physical commodities - agriculture, energy, metals - when the question is which kind of participant is positioned, not just speculator vers… |
| `financial/combined` | 1 | The financial split with options included, which matters most for equity index and Treasury futures, where options open interest is a large… |
| `financial/futures-only` | 1 | Currencies, Treasury and SOFR futures, equity index futures, VIX: who is long the dollar, how short leveraged funds are in ten-year notes, … |
| `legacy/combined` | 1 | The legacy split with options included, which is the fuller picture of a group's exposure in markets where options are liquid - energy, met… |
| `legacy/futures-only` | 1 | The report most commentary means by 'the COT': speculators versus hedgers, futures positions only, back to 1986 for every market. Filter by… |
| `supplemental/index-traders` | 1 | Thirteen agricultural markets - corn, wheat, soybeans, sugar, coffee, cocoa, cotton, cattle, hogs - when the question is how much of the le… |

<a id="p-cftc-gov"></a>

### CFTC Commitments of Traders (`cftc-gov`)

US Commodity Futures Trading Commission Commitments of Traders (COT) reports from the public reporting SODA API (publicreporting.cftc.gov): the seven weekly datasets (Legacy, Disaggregated and Traders in Financial Futures, each futures-only and combined, plus the Supplemental commodity index report) with filters, column projection, deterministic recent-first order and offset pagination, and a con…

| Capability | Credits | Use |
| --- | --- | --- |
| `commitments-of-traders/disaggregated_combined` | 5 | Positions and open interest from the CFTC Disaggregated - Combined report for one or many markets and weeks. Use `markets` first to find co… |
| `commitments-of-traders/disaggregated_futures_only` | 5 | Positions and open interest from the CFTC Disaggregated - Futures Only report for one or many markets and weeks. Use `markets` first to fin… |
| `commitments-of-traders/legacy_combined` | 5 | Positions and open interest from the CFTC Legacy - Combined report for one or many markets and weeks. Use `markets` first to find contract_… |
| `commitments-of-traders/legacy_futures_only` | 5 | Positions and open interest from the CFTC Legacy - Futures Only report for one or many markets and weeks. Use `markets` first to find contr… |
| `commitments-of-traders/markets` | 5 | Start here to find the contract_market_code (and exchange_code / commodity names) to pass to a report function, or to see which markets a d… |
| `commitments-of-traders/supplemental` | 5 | Positions and open interest from the CFTC Supplemental Commodity Index report for one or many markets and weeks. Use `markets` first to fin… |
| `commitments-of-traders/tff_combined` | 5 | Positions and open interest from the CFTC Traders in Financial Futures - Combined report for one or many markets and weeks. Use `markets` f… |
| `commitments-of-traders/tff_futures_only` | 5 | Positions and open interest from the CFTC Traders in Financial Futures - Futures Only report for one or many markets and weeks. Use `market… |

<a id="p-cmegroup-com"></a>

### CME Group FedWatch and market data (`cmegroup-com`)

CME FedWatch market-implied FOMC rate probabilities (the QuikStrike tool embedded on cmegroup.com: current view and per-meeting daily probability history) and CME Group's public CmeWS market data JSON: delayed futures quotes, daily settlements, volume and open interest, contract specifications, product search, and CME Term SOFR / SOFR average rates.

| Capability | Credits | Use |
| --- | --- | --- |
| `fomc-rate-probabilities/contract_specs` | 5 | Use to understand a product found with product_search before reading its quotes or settlements. |
| `fomc-rate-probabilities/fedwatch_meetings` | 5 | Start here for market-implied probabilities of the next FOMC rate decision and the list of meeting dates to pass to fedwatch_probability_hi… |
| `fomc-rate-probabilities/fedwatch_probability_history` | 5 | Use for the probabilities of a specific meeting (take latest) or for how they evolved over time. Meeting dates come from fedwatch_meetings. |
| `fomc-rate-probabilities/futures_quotes` | 5 | Use for the current futures strip behind FedWatch (product 305, 30 Day Fed Funds) or any other CME futures product id from product_search. |
| `fomc-rate-probabilities/futures_settlements` | 5 | Use for official daily settlement prices of the Fed Funds or SOFR futures strip, or any CME futures product. |
| `fomc-rate-probabilities/futures_volume` | 5 | Use for liquidity and positioning in the Fed Funds or SOFR futures contracts FedWatch is derived from. |
| `fomc-rate-probabilities/product_search` | 5 | Start here to find the product_id for futures_quotes, futures_settlements, futures_volume and contract_specs. |
| `fomc-rate-probabilities/sofr_rates` | 5 | Use for the SOFR benchmark levels alongside FedWatch probabilities. |

<a id="p-data-imf-org"></a>

### IMF Data (`data-imf-org`)

IMF SDMX dataflows, structures, observations and World Economic Outlook editions.

| Capability | Credits | Use |
| --- | --- | --- |
| `datasets/data` | 5 | Retrieve observations from any IMF dataflow (BOP current account, ER exchange rates, IL reserves, IMTS bilateral trade, CPI, GFS, FM, WEO) … |
| `datasets/dataflows` | 5 | List IMF Data portal dataflows (WEO, BOP, ER, IMTS, CPI, GFS_*, FM and 200+ more, including frozen vintages) filtered by a free-text query … |
| `datasets/structure` | 5 | Describe one dataflow: its dimensions in SDMX key order, the concept/codelist each one uses, the codes that currently carry data, attribute… |
| `datasets/weo` | 5 | World Economic Outlook observations for one edition (2026-04 current, 2025-10, 2025-04, or `latest`), given WEO subject codes (NGDP_RPCH, P… |

<a id="p-data-worldbank-org"></a>

### World Bank Data (`data-worldbank-org`)

World Bank Indicators API v2: database catalog, indicator discovery, economies and aggregates, reference lists, observations (classic and dimension paths including International Debt Statistics) and extended series/economy metadata. Keyless public API.

| Capability | Credits | Use |
| --- | --- | --- |
| `indicators/concept_values` | 5 | Enumerate what a source can be queried by, e.g. IDS creditor codes for `source_data`. |
| `indicators/countries` | 5 | Resolve country codes for `data`, or enumerate the members of a region or income group. |
| `indicators/country` | 5 | Confirm a code and read its region, income level and lending type before querying data. |
| `indicators/data` | 5 | Fetch the actual numbers once you know the indicator id(s) and country code(s). |
| `indicators/indicator` | 5 | You have an indicator id and need its definition or its source before calling `data`. |
| `indicators/indicators` | 5 | Discover indicator ids for `indicator` and `data`; browse a topic (see `reference` kind topic) or a database. |
| `indicators/metadata` | 5 | Read the definition, license or methodology notes behind a series, or an economy's statistical profile. |
| `indicators/reference` | 5 | Find valid `topic_id`, `region`, `income_level` or `lending_type` codes. |
| `indicators/source_concepts` | 5 | Before `concept_values` or `source_data` on an unfamiliar source. |
| `indicators/source_data` | 5 | Use for IDS (source 6) series, or when you want the dimension-keyed form of a series from any source. |
| `indicators/sources` | 5 | Start here to find the source id of a database (2 WDI, 6 IDS, 15 GEM) or to read its vintage. |

<a id="p-defillama-com"></a>

### DeFiLlama (`defillama-com`)

DeFiLlama analytics from the free llama.fi JSON APIs behind defillama.com: stablecoin supply and history, protocol and chain TVL, fees/revenue and DEX/options volume, yield pools, token prices and the hacks dataset.

| Capability | Credits | Use |
| --- | --- | --- |
| `crypto/chain_tvl_history` | 5 | TVL trend of a chain or of DeFi overall. |
| `crypto/chains` | 5 | Ranking chains by TVL or finding the exact chain name for `chain_tvl_history`, `stablecoin_history` and the chain filters. |
| `crypto/hacks` | 5 | Researching exploits of a protocol, on a chain, or the largest recent hacks. |
| `crypto/metrics_overview` | 5 | Which protocols earn the most fees or trade the most volume, overall or on one chain. |
| `crypto/price_chart` | 5 | A token's price over a window (daily or hourly candles as points). |
| `crypto/prices` | 5 | Spot or point-in-time USD prices for tokens by CoinGecko id or chain:address. |
| `crypto/protocol` | 5 | Details and TVL history for a protocol whose slug you know (from `protocols`, or from a defillama.com/protocol/{slug} URL). |
| `crypto/protocol_metrics` | 5 | Fee, revenue or volume figures and history for a protocol whose slug you know. |
| `crypto/protocols` | 5 | Finding a protocol slug for `protocol`/`protocol_metrics`, ranking protocols by TVL, or listing protocols in a category or on a chain. |
| `crypto/stablecoin_chains` | 5 | Comparing chains by stablecoin liquidity or checking how much stablecoin value sits on one chain. |
| `crypto/stablecoin_history` | 5 | The issue's named example: historical stablecoin supply for one asset (e.g. Tether id `1`), overall or on a chain like `Ethereum`. |
| `crypto/stablecoins` | 5 | Finding a stablecoin's id for `stablecoin_history`, ranking stablecoins by supply, or listing the stablecoins on one chain or with one peg. |
| `crypto/yield_pool_history` | 5 | APY/TVL trend of a pool whose uuid you have from `yield_pools`. |
| `crypto/yield_pools` | 5 | Finding yield opportunities by chain/project/asset, or a pool id for `yield_pool_history`. |

<a id="p-ec-europa-eu"></a>

### Eurostat (ec.europa.eu) (`ec-europa-eu`)

Eurostat's public dissemination API on ec.europa.eu: search the dataset catalogue, read a dataset's metadata card and dimension code lists, run filtered JSON-stat data queries on any of the ~8,000 datasets, and typed wrappers for country price level indices (EU27=100) and the semi-annual purchasing power parities of EU capital and duty-station cities (Brussels=1). Anonymous, keyless.

| Capability | Credits | Use |
| --- | --- | --- |
| `indicators/city_price_parities` | 5 | The 'how expensive is EU city X relative to Brussels' question at half-year granularity. Omit cities for all 33; use since/until for a peri… |
| `indicators/get_dataset` | 5 | After search_datasets, to learn which dimensions and codes a dataset accepts before calling query_data. |
| `indicators/price_level_indices` | 5 | The 'how expensive is country X relative to the EU' question. Pass geo codes to restrict; omit year for the whole series. |
| `indicators/query_data` | 5 | Any dataset code from search_datasets once get_dataset has shown its dimensions and codes. For country price level indices or city purchasi… |
| `indicators/search_datasets` | 5 | Start here to find a dataset code (for example 'price level indices' -> prc_ppp_ind_1, tec00120) before calling get_dataset or query_data. |

<a id="p-ecb-europa-eu"></a>

### European Central Bank (ECB Data Portal) (`ecb-europa-eu`)

Official European Central Bank statistics from the ECB Data Portal's keyless SDMX API: euro foreign exchange reference rates (latest, one day or a range, with derived cross rates between two non-euro currencies), any ECB time series by dataflow and key (euro short-term rate €STR, key policy rates, HICP inflation, M3 and other monetary aggregates, bank interest rates, yield curves, balance of paym…

| Capability | Credits | Use |
| --- | --- | --- |
| `economic-data/fx_rates` | 5 | Official ECB EUR exchange rates (e.g. EUR/USD reference rate on a date, latest EUR/JPY, a month of EUR/GBP), or a cross rate such as USD/JP… |
| `economic-data/search_dataflows` | 5 | Finding which ECB dataflow holds a statistic, or which dimension codes make up a series key, before calling series. |
| `economic-data/series` | 5 | Euro area statistics from the ECB: €STR (EST B.EU000A2X2A25.WT), key ECB interest rates (FM B.U2.EUR.4F.KR.MRR_FR.LEV, DFR, MLFR), HICP inf… |

<a id="p-efdsearch-senate-gov"></a>

### US Senate financial disclosures (eFD) (`efdsearch-senate-gov`)

United States Senate electronic Financial Disclosure search (efdsearch.senate.gov): search public financial disclosure filings of Senators, former Senators and Senate candidates by name, filer type, report type, state and date received, then read one filing: an electronic periodic transaction report (transactions table), an electronic annual report (Parts 1-10 with their tables), a scanned paper …

| Capability | Credits | Use |
| --- | --- | --- |
| `financial-disclosures/get_report` | 5 | You have a report_id and report_kind from search_reports (or a pasted /search/view/ URL) and need the filing's contents: PTR transactions, … |
| `financial-disclosures/search_reports` | 5 | Find Senate financial disclosure filings (PTRs, annual reports, extensions, blind trusts, paper filings) by Senator or candidate name, stat… |

<a id="p-eia-gov"></a>

### US Energy Information Administration (`eia-gov`)

Discover EIA energy data routes, enumerate facet values and retrieve energy observations with source units and labels.

| Capability | Credits | Use |
| --- | --- | --- |
| `energy-data/data` | 5 | One page of observations from an EIA route (`<route>/data`) at a frequency, filtered by facet codes and a period range, sorted, with offset… |
| `energy-data/facet_values` | 5 | List every value of one facet on a route (for example `sectorid` on `electricity/retail-sales`, or `series` on `petroleum/pri/spt`) with it… |
| `energy-data/routes` | 5 | Navigate the EIA API v2 route hierarchy. Given a route path (or none for the root) returns that route's metadata: child routes, frequencies… |

<a id="p-federalreserve-gov"></a>

### Federal Reserve Board (`federalreserve-gov`)

Board of Governors of the Federal Reserve System (federalreserve.gov): press releases, speeches and testimony with full text, the events calendar, FOMC meeting materials (statements, minutes, projections) and Data Download Program statistical packages (H.15 interest rates, H.10 exchange rates and other releases), from the site's own listing JSON, server-rendered pages and CSV endpoints. Anonymous…

| Capability | Credits | Use |
| --- | --- | --- |
| `central-bank-communications/calendar` | 5 | See what the Federal Reserve Board has scheduled (or held) in a given month: upcoming speeches, the next FOMC meeting, release dates. |
| `central-bank-communications/data_series` | 5 | Pull Federal Reserve statistical release data (H.15 interest rates, H.10 exchange rates, G.19 consumer credit, Z.1 financial accounts...) a… |
| `central-bank-communications/fomc_meetings` | 5 | Find FOMC meeting dates and the statement, minutes or projections documents for a meeting; pass a statement URL's slug to `press_release`. |
| `central-bank-communications/press_release` | 5 | Read the text of an FOMC statement, enforcement action or other announcement whose slug came from `press_releases`, `fomc_meetings` or a pa… |
| `central-bank-communications/press_releases` | 5 | Find recent Federal Reserve Board announcements (FOMC statements, enforcement actions, banking orders, regulatory policy) and the slug to p… |
| `central-bank-communications/speech` | 5 | Read the full text of a speech or testimony whose slug came from `speeches`, `calendar` or a pasted URL. |
| `central-bank-communications/speeches` | 5 | List recent policy speeches or testimony by a given official or in a date range and get the slug to pass to `speech`. |

<a id="p-fiscaldata-treasury-gov"></a>

### US Treasury Fiscal Data (`fiscaldata-treasury-gov`)

US Treasury Fiscal Data (fiscaldata.treasury.gov): the dataset catalog, filtered rows from any of the ~180 API tables (Debt to the Penny, Daily and Monthly Treasury Statements, auctions, average interest rates, interest expense, gold reserve, rates of exchange, MSPD, ...), latest observations of the headline tables, the release calendar and published report files.

| Capability | Credits | Use |
| --- | --- | --- |
| `fiscal-data/data` | 5 | Any question that needs the actual numbers from a Fiscal Data table. Use `datasets` first when the endpoint path is unknown; use `latest` f… |
| `fiscal-data/datasets` | 5 | Start here to find the `endpoint` for `data` or the `dataset_id` for `release_calendar` and `published_reports`. |
| `fiscal-data/latest` | 5 | Current values without knowing the endpoint path: today's national debt, the latest cash balance, the last auctions, the current exchange r… |
| `fiscal-data/published_reports` | 5 | To get the official PDF/XLS of a statement for a given date rather than the table rows. |
| `fiscal-data/release_calendar` | 5 | When a dataset will next be updated, or whether today's release is already out. |

<a id="p-forexfactory-com"></a>

### Forex Factory economic calendar (`forexfactory-com`)

Forex Factory's economic calendar (www.forexfactory.com/calendar): scheduled releases by day, week, month or custom range with impact, currency and event-type filters; per-event details, release history, numeric history series and indicator name search. Public, anonymous, read-only.

| Capability | Credits | Use |
| --- | --- | --- |
| `economic-calendar/event_detail` | 5 | After list_events gave an event_id; for the full history use event_history (paged) or event_graph (numeric series). |
| `economic-calendar/event_graph` | 5 | For charting or computing over an indicator's history; event_history gives the same releases as paged strings with links. |
| `economic-calendar/event_history` | 5 | To read an indicator's release history further back than the five rows event_detail returns; event_graph gives the same values as numbers f… |
| `economic-calendar/list_events` | 5 | To see what is scheduled or was released in a date window, or to find an event_id to pass to event_detail, event_history or event_graph. |
| `economic-calendar/search_events` | 5 | To find an indicator series (e.g. `cpi`, `nonfarm`) before listing its releases; the result has no per-release event_id, use list_events fo… |

<a id="p-fred"></a>

### FRED (`fred`)

US and international economic time series from the Federal Reserve Bank of St. Louis: rates, prices, employment, output and money, with the full revision history behind each figure.

| Capability | Credits | Use |
| --- | --- | --- |
| `categories/category` | 0 | Call to confirm what a category id is before walking down from it, or with no argument to land on the root. The only category endpoint that… |
| `categories/children` | 0 | The rung of the walk from the root to a series list. It descends one level per call, so getting from the root to a leaf takes several. Noth… |
| `categories/related` | 0 | Call for the cross-links the hierarchy cannot express. Most categories have none, so an empty array is the normal answer here and not a sig… |
| `categories/related-tags` | 0 | Call to narrow a category further once you already have one tag: it returns the tags that co-occur with `tag_names` inside this category. I… |
| `categories/series` | 1 | The bottom of the category walk: turns a category id into series ids. `limit` defaults to its maximum of 1000, so narrow with `tag_names` o… |
| `categories/tags` | 0 | Call to see what the series in a category are labelled with before filtering them. `series_count` on each tag counts only series in this ca… |
| `releases/dates` | 0 | Call for the economic calendar across all releases at once. Not symmetric with `releases/release-dates` despite the near-identical name: th… |
| `releases/related-tags` | 0 | Call to narrow within a release once you have one tag. Two independently required arguments here, `release_id` and `tag_names`; the second … |
| `releases/release` | 0 | Call to resolve a release id into a name and link. Widening the real-time period makes this single-release call return more than one record… |
| `releases/release-dates` | 0 | Call for one release's publication history. It defaults to the whole span back to 1776-07-04 rather than the current year, has no `order_by… |
| `releases/releases` | 0 | The entry point for every other release capability: it is where a release name becomes the `release_id` they take. There are only a few hun… |
| `releases/series` | 1 | The bridge from a release to series ids: every series that arrives with this publication. A large release runs to thousands of series, so f… |
| `releases/sources` | 0 | Call when the question is who publishes a release rather than what is in it. A release can have more than one source agency. |
| `releases/tables` | 1 | Call when the layout matters - which line of a published table a series sits on, and what nests under what. This is the only capability her… |
| `releases/tags` | 0 | Call to see how a release's series are labelled before filtering `releases/series` by tag. `tag_names` is optional here and required on `re… |
| `series/categories` | 0 | Call to walk back up from a series you already have to the part of the tree it lives in, and from there to its peers. A series can sit in s… |
| `series/observations` | 1 | The only capability in this provider that returns numbers; everything else exists to find the id it takes. Two independent time axes: `obse… |
| `series/release` | 0 | Call to find which publication a series arrives in, then use that `release_id` for its calendar or its sibling series. Answering `when is t… |
| `series/search` | 0 | The way in when all you have is words. Set `search_type` to series_id when the query is an id fragment rather than a description; the defau… |
| `series/search-related-tags` | 0 | The second step of narrowing a search: given words and one tag already applied, the tags that co-occur on what is left. Two required argume… |
| `series/search-tags` | 0 | Call after a broad `series/search` to see what would narrow it, then feed a name back as `tag_names` there. Two search-text parameters on o… |
| `series/series` | 1 | Call before charting or comparing: `units`, `seasonal_adjustment` and `frequency` are what decide whether two series are comparable, and no… |
| `series/tags` | 0 | Call to read one series' labels - its geography, frequency, publisher and subject - and to get the tag names that would find its peers thro… |
| `series/updates` | 1 | Call to find what has changed rather than what exists - the only capability here that takes no series id. FRED caps it at series updated in… |
| `series/vintage-dates` | 1 | Call to find out when a series was actually revised, then pass one or more of these dates to `series/observations` as `vintage_dates` to se… |
| `sources/releases` | 0 | The middle rung of the provenance walk: agency to release to series. Call when the question starts from a publisher - everything the BEA pu… |
| `sources/source` | 0 | Call to resolve a source id to an agency name and site. Widening the real-time period makes this single-source call return several records,… |
| `sources/sources` | 0 | Where a `source_id` comes from. There are only about a hundred agencies and `limit` defaults to 1000, so one call is the whole list and pag… |
| `tags/related` | 0 | Call to narrow a tag search: given tags already chosen, the tags that co-occur with them. The one required argument is the one that is opti… |
| `tags/series` | 1 | The non-hierarchical route to series ids: every series carrying all of `tag_names` at once, without walking the category tree. Tags interse… |
| `tags/tags` | 0 | The full vocabulary - roughly 4,800 tags against a `limit` cap of 1000, so this is the one tag capability that genuinely needs paging. `ser… |

<a id="p-fred-stlouisfed-org"></a>

### FRED (Federal Reserve Economic Data) (`fred-stlouisfed-org`)

FRED (Federal Reserve Economic Data), the St. Louis Fed's database of US and international economic time series: headline US indicators such as the monthly unemployment rate (UNRATE), CPI inflation (CPIAUCSL), GDP (GDP, GDPC1), nonfarm payrolls (PAYEMS), the federal funds rate (FEDFUNDS) and Treasury yields (DGS10), plus 800,000+ other series. Search series by text, browse categories, releases, s…

| Capability | Credits | Use |
| --- | --- | --- |
| `economic-data/category` | 5 | Discover series by topic instead of by text: start at the root, follow `children[].category_id`, then read `series[].series_id` for `series… |
| `economic-data/release` | 5 | Browse the series a release publishes (e.g. release 53 = Gross Domestic Product) and hand `series[].series_id` to `series` / `series_observ… |
| `economic-data/releases` | 5 | Find a `release_id` for `release`; releases group the series a statistical agency publishes together. |
| `economic-data/series` | 5 | Confirm what a `series_id` (or a pasted fred.stlouisfed.org/series/{id} page URL) measures and which `units`/`frequency` values `series_obs… |
| `economic-data/series_observations` | 5 | Get the historical values of a known `series_id` or a pasted fred.stlouisfed.org/series/{id} page URL (monthly US unemployment rate = UNRAT… |
| `economic-data/series_search` | 5 | Start here to find a `series_id` (e.g. UNRATE, CPIAUCSL) for `series` and `series_observations`. |
| `economic-data/source` | 5 | See what an agency publishes (e.g. source 18 = U.S. Bureau of Economic Analysis) and hand `releases[].release_id` to `release`. |
| `economic-data/sources` | 5 | Find a `source_id` for `source`. |
| `economic-data/tag_series` | 5 | Find series by tag combination, e.g. gdp;quarterly or usa;monthly;nsa, then read them with `series` / `series_observations`. |
| `economic-data/tags` | 5 | Discover tag names to combine in `tag_series`. |

<a id="p-gmgn-ai"></a>

### GMGN (`gmgn-ai`)

GMGN (gmgn.ai) memecoin terminal data from its anonymous JSON API: trending tokens and new launches per chain, token detail with security and creator statistics, candles, trades, holders, top traders, first buyers and community posts, plus the smart-money wallet leaderboard, wallet statistics and developer launch history. Chains: sol, eth, base, bsc, tron, monad.

| Capability | Credits | Use |
| --- | --- | --- |
| `crypto/community_messages` | 5 | Sentiment and chatter around a token. |
| `crypto/dev_created_tokens` | 5 | Developer history: what else a token's creator (token_detail.creator_address) has launched. |
| `crypto/new_pairs` | 5 | Discover tokens launched in the last minutes or hours. Snapshot listing (no pagination). |
| `crypto/search` | 5 | Find a token's address from its name or ticker before calling token_detail, token_trades or token_holders; or find tracked wallets by Twitt… |
| `crypto/token_candles` | 5 | Price or market-cap history of a token at 1s to 1d resolution. |
| `crypto/token_detail` | 5 | Details for a token address from search, trending_tokens or new_pairs, or a pasted gmgn.ai token page URL. Up to 20 addresses per call. |
| `crypto/token_holders` | 5 | Holder concentration and who holds a token. |
| `crypto/token_traders` | 5 | Who made (or lost) the most on a token. |
| `crypto/token_trades` | 5 | Trading activity and signals for a token: who is buying and selling, in what size. |
| `crypto/top_buyers` | 5 | Sniper/early-buyer analysis for a token. |
| `crypto/trending_tokens` | 5 | Token discovery: what is trading most right now on sol, bsc, base, eth, monad or tron. Take `address` into token_detail, token_trades, toke… |
| `crypto/wallet_profile` | 5 | Profile a wallet from wallet_rank, token_holders, token_trades or a gmgn.ai address URL. |
| `crypto/wallet_rank` | 5 | Find top-performing wallets to inspect with wallet_profile or dev_created_tokens. |

<a id="p-hyperliquid-xyz"></a>

### Hyperliquid (`hyperliquid-xyz`)

Hyperliquid perpetual markets: live funding and open interest, historical funding, candles, order books, trades, per-address positions, fills (with liquidations), funding payments and ledger, plus vault details, from Hyperliquid's public info API.

| Capability | Credits | Use |
| --- | --- | --- |
| `markets/account` | 5 | Positions and liquidation prices for a trader, sub-account or vault address (from recent_trades users, account_fills or a vault). An addres… |
| `markets/account_fills` | 5 | Trade and liquidation history for an address. Give start_time (unix ms) and optionally end_time; follow next_cursor as cursor. This is the … |
| `markets/account_funding` | 5 | Realized funding for a trader or vault. Give start_time and optionally end_time; follow next_cursor as cursor. |
| `markets/account_ledger` | 5 | Money movements and liquidation ledger entries for an address. Give start_time and optionally end_time; follow next_cursor as cursor. |
| `markets/candles` | 5 | Price history for a coin from markets. Intervals: 1m 3m 5m 15m 30m 1h 2h 4h 8h 12h 1d 3d 1w 1M. Follow next_cursor as cursor for more. |
| `markets/exchange_stats` | 5 | A quick health and size read of the exchange; the at-cap list tells which markets cannot take new open interest right now. |
| `markets/funding_history` | 5 | Historical funding for a coin from markets. Give start_time (unix ms) and optionally end_time; follow next_cursor as cursor until page.cont… |
| `markets/markets` | 5 | Start here to discover coin identifiers and read live funding and open interest. Pass dex for a HIP-3 builder dex (from a dex-prefixed coin… |
| `markets/order_book` | 5 | Current liquidity for a coin from markets. n_sig_figs (2-5) aggregates levels to fewer significant figures. |
| `markets/predicted_fundings` | 5 | Compare upcoming funding across venues or fetch the next Hyperliquid funding for all coins in one call. Pass coin to filter to one market. |
| `markets/recent_trades` | 5 | Latest prints for a coin from markets. For a user's own fills use account_fills. |
| `markets/vault` | 5 | Look up a vault such as HLP by its address. Set include_followers for the depositor list. |

<a id="p-mempool-space"></a>

### mempool.space (`mempool-space`)

Bitcoin mainnet explorer data from the open-source mempool.space REST API: transactions with inputs, outputs, fees and confirmations, which transaction spent each output, address balances, histories and UTXOs, blocks by hash or height with mining pool and fees, recent blocks, fee estimates and the mempool backlog.

| Capability | Credits | Use |
| --- | --- | --- |
| `crypto/address_transactions` | 5 | Listing payments into or out of an address, finding when it first or last moved funds, or paging through its full history. Use `get_transac… |
| `crypto/address_utxos` | 5 | Seeing which coins an address can still spend, their sizes and ages. Use `get_address` for just the balance (it works for addresses of any … |
| `crypto/block_transactions` | 5 | Listing what a block contains or finding its coinbase transaction. Use `get_transaction` for a row's full inputs and outputs. |
| `crypto/blocks` | 5 | Seeing the latest blocks and current chain height, who mined recent blocks, or scanning a height range. Use `get_block` for one block's ful… |
| `crypto/fees` | 5 | Choosing a fee rate for a new transaction or judging whether a pending transaction's fee rate will confirm soon. |
| `crypto/get_address` | 5 | Checking an address's balance or whether it has received or spent anything. Use `address_transactions` for its history and `address_utxos` … |
| `crypto/get_block` | 5 | Looking up a block's time, miner pool, fees or confirmations, or resolving a height to its hash. Use `block_transactions` for the transacti… |
| `crypto/get_transaction` | 5 | Checking whether a payment confirmed and how deeply, who paid whom and how much, or the fee a transaction paid. Use `transaction_outspends`… |
| `crypto/mempool` | 5 | Gauging congestion: how many vbytes are queued above a given fee rate, or how large the backlog is. |
| `crypto/transaction_outspends` | 5 | Following funds forward: which transaction spent a given output, whether a payment's coins have moved, or which outputs of a transaction ar… |

<a id="p-nasdaq-com"></a>

### Nasdaq.com news feeds and articles (`nasdaq-com`)

Nasdaq.com's public news surfaces: ticker news, press releases, market-wide and topic feeds (JSON), the RSS feeds that carry publish times, and the full text and exact publish instant of a Nasdaq article or press release page.

| Capability | Credits | Use |
| --- | --- | --- |
| `news/article` | 1 | Full text and the exact publish time of a story listed by any feed function. Costs one ~180 KB page fetch. |
| `news/feed` | 1 | Publish times for the newest stories on a ticker or topic in one request. For older stories or more than 15 rows use `ticker_news` / `topic… |
| `news/latest_headlines` | 1 | What is being published right now across the market, with no ticker or topic filter. |
| `news/press_releases` | 1 | Company announcements for one ticker (earnings dates, product launches, filings) rather than third-party coverage. |
| `news/ticker_news` | 1 | Latest third-party coverage of one stock or ETF. Official company announcements (deals, partnerships, earnings, launches) are press release… |
| `news/topic_news` | 1 | Coverage of a theme (Markets, Stocks, Technology, Investing) rather than a ticker. |

<a id="p-nfa-futures-org"></a>

### NFA BASIC (`nfa-futures-org`)

National Futures Association BASIC registry: firm, individual and commodity pool search, registration profiles, regulatory actions, arbitration awards, CFTC reparations, FCM financial reports and CPO pools, over BASIC's own JSON-RPC handlers.

| Capability | Credits | Use |
| --- | --- | --- |
| `regulatory-registry/get_arbitration_award` | 5 | Read an award returned by list_arbitration_awards. |
| `regulatory-registry/get_fcm_financials` | 5 | Track an FCM's adjusted net capital or customer segregated/secured/swap funds over time. |
| `regulatory-registry/get_profile` | 5 | Get the registration record behind an NFA ID returned by a search or lookup. |
| `regulatory-registry/get_regulatory_action` | 5 | Read the detail of an action returned by list_regulatory_actions (nfa_id + case_ref + contributor). |
| `regulatory-registry/list_arbitration_awards` | 5 | List arbitration awards for a firm before reading one with get_arbitration_award. |
| `regulatory-registry/list_pools` | 5 | List the pools a CPO found via search or profile operates. |
| `regulatory-registry/list_regulatory_actions` | 5 | List NFA, CFTC, exchange and foreign-regulator disciplinary actions against a firm or individual. |
| `regulatory-registry/list_reparations` | 5 | List CFTC reparations cases naming a firm or individual. |
| `regulatory-registry/lookup_id` | 5 | You already have an NFA ID or pool id and want the name, status summary and profile URL, or need the encrypted id for a BASIC page link. |
| `regulatory-registry/search_firms` | 5 | Find a futures firm's NFA ID from its name, optionally narrowed by membership status, registration type or whether it has regulatory action… |
| `regulatory-registry/search_individuals` | 5 | Find an associated person, principal or other registered individual and their NFA ID by name. |
| `regulatory-registry/search_pools` | 5 | Find a commodity pool and its CPO; optionally only current or only ceased pools. |

<a id="p-polymarket"></a>

### Polymarket (`polymarket`)

Prediction markets, outcome prices, events, topic tags, recurring series and sports metadata from Polymarket's Gamma API.

| Capability | Credits | Use |
| --- | --- | --- |
| `events/by-slug` | 0 | Read an event and its markets using the exact event slug from a Polymarket event URL. |
| `events/get` | 0 | Read an event and its markets using the Gamma event ID returned by events/list or search/query. |
| `events/list` | 0 | Browse events and their constituent markets. Use active=true and closed=false for open active events; advance offset to read another page. |
| `markets/by-slug` | 0 | Read a market using its exact market slug. Event slugs belong to events/by-slug. |
| `markets/get` | 0 | Read a market by its Gamma numeric ID, obtained from markets/list. This is not a condition ID or CLOB token ID. |
| `markets/list` | 0 | Browse prediction markets by slug, condition ID, token ID, tag, closing status or volume. Read outcomePrices alongside outcomes; both are J… |
| `search/query` | 0 | Search events, tags and public profiles by text. Markets are nested inside matching events; follow event IDs or slugs for full detail. Sear… |
| `series/get` | 0 | Read a recurring series and its events using a series ID from series/list or sports/list. |
| `series/list` | 0 | Browse recurring event series. Use exclude_events=true for a smaller metadata-only response. |
| `sports/list` | 0 | Find sport identifiers, resolution sources, tag IDs and series IDs for browsing sports prediction markets. |
| `sports/market-types` | 0 | List the valid sports market type names. |
| `tags/get` | 0 | Resolve one topic tag using its numeric Gamma tag ID. |
| `tags/list` | 0 | Find topic tags and their IDs before filtering markets or events by tag_id. |

<a id="p-sec-gov"></a>

### SEC EDGAR (`sec-gov`)

Official SEC company profiles, filings, filing sections, 13F holdings and XBRL concept facts, plus bulk collection of companies, XBRL facts and the daily filings index.

| Capability | Credits | Use |
| --- | --- | --- |
| `filings/companies_get` | 5 | A single filer's profile or its complete filing history page by page. |
| `filings/companies_list` | 5 | Bulk collection of every listed filer's profile. Use companies_get for one CIK. |
| `filings/companies_status` | 5 | Before a bulk run of companies_list, or to detect that the ticker index changed. |
| `filings/company` | 5 | Resolve a ticker, CIK or company name to its EDGAR filer profile: CIK, name, tickers, exchanges, SIC, filer category, state of incorporatio… |
| `filings/concept` | 5 | Every reported value of one XBRL concept for a filer (Revenues, NetIncomeLoss, Assets, EarningsPerShareDiluted ...) straight from the SEC's… |
| `filings/daily_index_changes` | 5 | Incremental collection of new filings since a date; filter forms and 8-K items for M&A events. |
| `filings/daily_index_get` | 5 | Details of one accession seen in daily_index_list or daily_index_changes. |
| `filings/daily_index_list` | 5 | Collect every filing of a business day, or the day's 8-Ks with given items. |
| `filings/daily_index_status` | 5 | To learn which day's index exists before daily_index_list, or to pin a publication. |
| `filings/facts_list` | 5 | Bulk collection of a filer's financial facts. Use concept for one tag. |
| `filings/facts_status` | 5 | Before paging facts_list for a CIK, or to detect that a filer's facts changed. |
| `filings/filing` | 5 | One filing by accession number: its submission metadata (form, dates, 8-K items) and every document in the filing folder with size and dire… |
| `filings/filings` | 5 | List a filer's EDGAR filings newest first, filtered by form type (10-K, 10-Q, 8-K, S-1, 13F-HR, 4, DEF 14A ...) and filing date. Each recor… |
| `filings/holdings_13f` | 5 | Form 13F-HR holdings of an institutional investment manager: every position from the XML information table (issuer, class, CUSIP, value, sh… |
| `filings/search` | 5 | EDGAR full-text search across every filer since 2001: filter by phrase, form types, filing-date range and CIK. Returns 100 hits per page wi… |
| `filings/sections` | 5 | Item sections of a 10-K or 10-Q as plain text: Item 1 Business, 1A Risk Factors, 7 MD&A, 8 Financial Statements and so on (10-Q items carry… |

<a id="p-servicodados-ibge-gov-br"></a>

### IBGE service data API (`servicodados-ibge-gov-br`)

Brazil's national statistics institute (IBGE) open JSON API at servicodados.ibge.gov.br: territorial codes (localidades), SIDRA aggregated statistics (agregados: official municipal / state / national population and household counts from the 2022 Census and the yearly population estimates, IPCA, PNAD, GDP and ~8,000 other tables), 2010 Census first-name frequencies and rankings, IBGE news/releases…

| Capability | Credits | Use |
| --- | --- | --- |
| `official-statistics/agregado_dados` | 5 | Official population or household count of a Brazilian municipality, state or the country (Census 2022: 4709/93 population, 4712/381 occupie… |
| `official-statistics/agregado_metadados` | 5 | Pick the variavel ids, classificacao/categoria ids, nivel and periods to pass to agregado_dados. Unknown table ids are not_found. |
| `official-statistics/agregados` | 5 | Find the agregado id (and then, with agregado_metadados, the variable and classification ids) before calling agregado_dados. Pass a query o… |
| `official-statistics/calendario` | 5 | When the next IPCA / PNAD / PIB release is scheduled, or the release history of a product. |
| `official-statistics/cnae` | 5 | Decode a CNAE code from a company registry (7-digit subclasse 0111301, 5-digit classe 01113) or browse the hierarchy. |
| `official-statistics/localidade` | 5 | Turn a municipality or state code into its name and hierarchy (microrregiao, mesorregiao, regiao imediata/intermediaria, UF, regiao), e.g. … |
| `official-statistics/localidades` | 5 | Resolve IBGE codes before querying agregados (N3 = estado id, N6 = municipio id), enumerate the municipalities of a state, or find a munici… |
| `official-statistics/malha` | 5 | Draw or geo-join a Brazilian state, municipality or region; get its centroid and area in km2. Use qualidade=minima unless you need detailed… |
| `official-statistics/nomes` | 5 | How common a Brazilian first name is, how its popularity changed by decade, or where in Brazil it concentrates. |
| `official-statistics/nomes_ranking` | 5 | Most common names in Brazil or a state, by decade or sex. |
| `official-statistics/noticias` | 5 | Recent IBGE releases (IPCA, PNAD, PIB...), news about a product or matching a keyword. Follow next_page until null. |
| `official-statistics/paises` | 5 | A country fact sheet or a UN-sourced indicator series (GDP per capita, population, life expectancy...) as IBGE republishes them, for Brazil… |

<a id="p-treasury-fiscal-data"></a>

### Treasury Fiscal Data (`treasury-fiscal-data`)

US Treasury Fiscal Data: the national debt to the penny, daily cash balances and tax receipts, monthly receipts and outlays, Treasury auction and buyback results, interest rates and expense on the debt, the gold reserve and official exchange rates.

| Capability | Credits | Use |
| --- | --- | --- |
| `auctions/results` | 1 | How an auction went: filter `security_type:eq:Note,security_term:eq:10-Year` and sort `-auction_date` for the last ten-year, then read `hig… |
| `auctions/upcoming` | 1 | What the Treasury is about to sell: the auction calendar for the coming days with sizes. No history here - once an auction settles it moves… |
| `buybacks/operations` | 1 | How much the Treasury bought back and when: sort `-operation_date` for the latest operation or the one just announced. Filter by program wi… |
| `buybacks/securities` | 1 | Which securities a buyback took and at what price: filter `operation_date:eq:<date>` for one operation's CUSIPs, adding `par_amt_accepted:g… |
| `daily-statement/deposits-and-withdrawals` | 1 | Where the government's cash came from and went each day: withheld income taxes, corporate taxes, Social Security benefits, Medicare, defenc… |
| `daily-statement/operating-cash-balance` | 1 | The Treasury General Account balance - the government's cash on hand - which is what debt-ceiling coverage tracks day by day. For the curre… |
| `daily-statement/public-debt-transactions` | 1 | Gross issuance and redemption of Treasury securities by day: how much in bills was issued and how much rolled off. Net issuance is issues m… |
| `debt/average-interest-rates` | 1 | What the government is paying on its debt, by kind of security: the average coupon on outstanding notes, the rate on bills, the blended rat… |
| `debt/historical-outstanding` | 1 | The long series: one figure per year from the first Treasury report in 1790. Use it for anything before 1993 or for a year-end comparison, … |
| `debt/interest-expense` | 1 | How much interest the debt costs in dollars, monthly, by kind of security. The fiscal-year-to-date column is the one quoted when interest i… |
| `debt/to-the-penny` | 1 | The headline national debt figure: total public debt outstanding on a given day, to the cent. Sort `-record_date` with `page[size]=1` for t… |
| `monthly-statement/receipts-and-outlays` | 1 | The monthly deficit: filter `record_date:eq:2026-07-31,classification_desc:eq:July` and read `current_month_dfct_sur_amt` on the row with t… |
| `rates/exchange` | 1 | The official rate a US agency reports a foreign balance at, per quarter. Filter `country_currency_desc:eq:Euro Zone-Euro` or `country:eq:Ja… |
| `reserves/gold` | 1 | How much gold the Treasury holds and where. The book value is the statutory price, not the market price, so a market valuation is the ounce… |

<a id="p-xe-com"></a>

### XE currency data (`xe-com`)

XE (xe.com) mid-market foreign exchange data read from the public site: convert an amount between two currencies with 7/30/90-day statistics, the full live rate table for a base currency, the historical rate table for any past date, a decoded chart series over 1 day to 10 years, the currency encyclopedia profile of one currency, and the list of every currency XE covers. Anonymous, read-only; mone…

| Capability | Credits | Use |
| --- | --- | --- |
| `exchange-rates/convert` | 5 | A single pair's current rate or a converted amount. For many quotes against one base use live_rates; for a past date use historical_table. |
| `exchange-rates/currency_profile` | 5 | Reference facts about a currency. For rates use convert, live_rates or historical_table. |
| `exchange-rates/historical_table` | 5 | What a rate was on a given day, or a whole day's table. For a time series of one pair use rate_history. |
| `exchange-rates/list_currencies` | 5 | Discover valid codes and slugs before calling the other functions. |
| `exchange-rates/live_rates` | 5 | Many rates against one base in one call. For one pair with statistics use convert. |
| `exchange-rates/rate_history` | 5 | Charting or trend analysis of one pair. For a single past date across all currencies use historical_table. |

Also in this category: [B3 listed companies and indices](#p-b3-com-br), [Benzinga](#p-benzinga), [Yahoo Finance](#p-finance-yahoo-com), [Fireround](#p-fireround), [Fiscal.ai](#p-fiscal-ai), [UK Financial Services Register (FCA)](#p-register-fca-org-uk)

## government

Government programs and records: federal funding and procurement opportunities, eligibility, who is buying what and when responses are due.

<a id="p-aer-ca"></a>

### Alberta Energy Regulator (aer.ca) (`aer-ca`)

Alberta Energy Regulator public site: paginated listings of directives, bulletins, hearing / regulatory appeal / procedural decisions, notices, statistical (ST) reports and news releases (Drupal views tables with keyword filter), directive and bulletin detail pages (release and effective dates, PDF, body text, cross-references), Public Notice of Application and Publication of Decision records by …

| Capability | Credits | Use |
| --- | --- | --- |
| `energy-regulator-decisions-directives-notices/get_bulletin` | 5 | When you know the bulletin number (directive pages name the bulletin they were released with) and want its text and the directives it annou… |
| `energy-regulator-decisions-directives-notices/get_directive` | 5 | When you know the directive number and want its current edition's dates, PDF and summary. Use list_publications with collection=directives … |
| `energy-regulator-decisions-directives-notices/get_public_notice` | 5 | When you have an application number from the PNoA listing, a notice or a decision and want the notice record as published. |
| `energy-regulator-decisions-directives-notices/get_published_decision` | 5 | When you have an application number and want to confirm whether and when the AER decided it. For the notice before the decision call get_pu… |
| `energy-regulator-decisions-directives-notices/list_publications` | 5 | To browse or filter AER publications of one type by date or keyword, and to find the directive / bulletin numbers, decision numbers and PDF… |
| `energy-regulator-decisions-directives-notices/site_search` | 5 | To find pages and PDFs about a topic, directive, company or decision anywhere on aer.ca when you do not know which listing holds it. |

<a id="p-api-weather-gov"></a>

### National Weather Service API (api.weather.gov) (`api-weather-gov`)

NWS watches, warnings and advisories (active and last ~7 days) and daily/hourly forecasts for a GeoJSON geometry in the United States: the land contract shared with the other land programs (geometry in; spatial_precision, sources, missing and a location echo out).

| Capability | Credits | Use |
| --- | --- | --- |
| `weather/alert` | 5 | Read the full text of an alert returned by alerts_active or alerts_history. |
| `weather/alerts_active` | 5 | Which watches, warnings and advisories (red flag, fire weather, flood, heat, severe storms) are in effect right now for this paddock, parce… |
| `weather/alerts_history` | 5 | Which alerts affected this parcel or paddock in the last week (start/end as YYYY-MM-DD). Pass `continuation` from the previous page to cont… |
| `weather/forecast_daily` | 5 | How much rain is forecast per day over the next 7 days for this field, with highs, lows, wind and minimum humidity. Hourly detail: forecast… |
| `weather/forecast_hourly` | 5 | Hourly temperature and humidity for the next two days (default 48 hours, up to 156) at this paddock or parcel. |

<a id="p-arcgis-com"></a>

### ArcGIS public GIS layers (`arcgis-com`)

Public government GIS data published on Esri ArcGIS (parcels, zoning, flood zones, permits, addresses, boundaries, parks, utilities and similar layers) through the documented, keyless ArcGIS REST APIs every ArcGIS web map uses: ArcGIS Online / Hub catalog search, FeatureServer and MapServer service and layer metadata, and attribute and spatial queries. Works with layers hosted on ArcGIS Online (s…

| Capability | Credits | Use |
| --- | --- | --- |
| `gis-layers/describe_layer` | 5 | Before query_layer: find the right layer id in a service and the exact field names and codes for a where clause (zoning codes, flood zone v… |
| `gis-layers/query_layer` | 5 | Look up the parcel, zoning district, flood zone, permit, address point or boundary at a location or matching an id (e.g. an assessor parcel… |
| `gis-layers/search_datasets` | 5 | Find which public ArcGIS layer holds the data (a county's parcels or zoning, FEMA flood zones, a park's trails, a city's permits) and get i… |

<a id="p-assembly-ab-ca"></a>

### Legislative Assembly of Alberta (`assembly-ab-ca`)

Legislative Assembly of Alberta (assembly.ab.ca): bills and their reading history with Hansard page references, Hansard and Votes and Proceedings sitting lists with the official PDF links, committee meeting transcripts, the Hansard speaker and subject indexes, and MLAs. Server-rendered public pages, no login.

| Capability | Credits | Use |
| --- | --- | --- |
| `legislative-records/get_bill` | 5 | Bill status and legislative history for one bill. Get the billinfoid from list_bills. Unknown ids answer not_found (the site renders an emp… |
| `legislative-records/get_member` | 5 | Member profile; the mid comes from list_members or from get_bill.sponsor.mid. |
| `legislative-records/hansard_index` | 5 | Find where a member spoke, or where a subject was debated, without reading the PDFs: this is the Assembly's own index. Letter A of a busy s… |
| `legislative-records/list_bills` | 5 | Start here to find a bill's billinfoid for get_bill, or to enumerate a session's bills. Legislature 31 is the current one (session 2 opened… |
| `legislative-records/list_committee_transcripts` | 5 | Committee transcripts by committee code: PA (Public Accounts), EF (Alberta's Economic Future), RS (Resource Stewardship), FC (Families and … |
| `legislative-records/list_members` | 5 | Roster of MLAs for a legislature; the mid keys get_member and matches the sponsor id on bills. |
| `legislative-records/list_sitting_documents` | 5 | To find the Hansard or Votes and Proceedings PDF for a date, or the docid of the session's speaker/subject index. The PDFs are static files… |

<a id="p-bidnetdirect-com"></a>

### BidNet Direct (`bidnetdirect-com`)

BidNet Direct (www.bidnetdirect.com), the US government bid portal of BidNet / mdf commerce: public solicitation search (keywords, state, NAICS-sector category, content group, publish window, sort, 25 rows per page) over open and closed bids, solicitation and statewide-notice detail pages (full public notice for closed BidNet-hosted solicitations including NIGP categories; open bids expose only t…

| Capability | Credits | Use |
| --- | --- | --- |
| `public-tenders/get_solicitation` | 5 | Read the detail of a solicitation found through `search_solicitations`, or of a pasted bidnetdirect.com solicitation URL. |
| `public-tenders/list_agencies` | 5 | Enumerate the buyers (school districts, cities, counties, utilities) that publish through a state purchasing group. |
| `public-tenders/list_categories` | 5 | Look up a sector's `category_id` or compare open-bid volume across sectors. |
| `public-tenders/list_locations` | 5 | Look up a state's `location_id` or compare open-bid volume across states. |
| `public-tenders/search_solicitations` | 5 | Find solicitations by keyword, state or category; pass a row's `id` and `kind` (or `detail_url`) to `get_solicitation`. |

<a id="p-california-dca-license"></a>

### California DCA physician licenses (`california-dca-license`)

Look up an exact California physician-and-surgeon license type, rank and number in the official DCA iServices API.

| Capability | Credits | Use |
| --- | --- | --- |
| `licenses/physician` | 5 | Check the DCA status code and expiry for an exact California physician-and-surgeon license rank and number; a status alone does not establi… |

<a id="p-cbc-ca"></a>

### CBC News (cbc.ca) (`cbc-ca`)

CBC News, Canada's public broadcaster: keyword search across cbc.ca (GraphQL allSearchItems), section and region listings with a publish-date range (aggregate_api/v1/items), the full text of an article with its headline, byline, exact publish and last-updated instants and any correction or clarification notice (GraphQL contentItem), and a Canadian place lookup that resolves a city name to CBC's t…

| Capability | Credits | Use |
| --- | --- | --- |
| `news/get_article` | 5 | Full text, exact timestamps and correction history of a story found by search_articles or list_articles, or of a pasted cbc.ca article URL. |
| `news/list_articles` | 5 | Browse a section or region, optionally within a date range (for example everything CBC Edmonton published last week). Category slugs come f… |
| `news/lookup_region` | 5 | Turn a user's city or region name into CBC's taxonomy path and the candidate category slug for list_articles. |
| `news/search_articles` | 5 | Find CBC stories by keyword, optionally within a section, then call get_article with a hit's source_id for the full text. For a region or s… |

<a id="p-census-gov"></a>

### US Census Bureau (`census-gov`)

Discover Census datasets, variables and geography codes, then retrieve published estimates, margins of error and counts with source annotations.

| Capability | Credits | Use |
| --- | --- | --- |
| `census/data` | 5 | Retrieve estimates. Input: dataset path (acs/acs5, acs/acs1, acs/acs5/subject, acs/acs5/profile, dec/pl, dec/dhc, pep/population, cbp ...),… |
| `census/datasets` | 5 | Search the Census Data API catalog. Input: free-text query over dataset path, title and description plus an optional vintage (year). Return… |
| `census/geographies` | 5 | Geography resolver. Input: a place, county, state, tract or other geography name (e.g. 'Travis County, Texas'). Returns matching Census geo… |
| `census/variables` | 5 | List variables of one dataset vintage. Input: dataset path and vintage, plus a group (table id such as B01003 or DP05) and/or a free-text q… |

<a id="p-clerk-house-gov"></a>

### U.S. House Clerk roll call votes and members (`clerk-house-gov`)

Office of the Clerk, U.S. House of Representatives (clerk.house.gov): roll call vote results for a congress, session and roll number with every member's position keyed by Bioguide ID, the votes listing with roll/bill/vote-type filters, a member's recent votes, and the current member roster.

| Capability | Credits | Use |
| --- | --- | --- |
| `legislative-votes/member` | 5 | You have a Bioguide ID (from `vote`, `member_vote` or a congress.gov URL) and want the member's current profile. Former members are not cov… |
| `legislative-votes/member_vote` | 5 | Answering 'how did member X vote on roll call N of session S of the Cth Congress'. |
| `legislative-votes/member_votes` | 5 | Listing how a current member has been voting recently. For a specific historical roll call use `member_vote`. |
| `legislative-votes/members` | 5 | Finding a member's Bioguide ID by state or party, or enumerating a delegation. Use `member` for one known Bioguide ID. |
| `legislative-votes/vote` | 5 | You know the congress, session and roll call number (for example from `votes` or from a clerk.house.gov/Votes/{year}{roll} URL) and want th… |
| `legislative-votes/votes` | 5 | Finding roll call numbers (to pass to `vote` or `member_vote`) for a bill, a date range or a session; browsing what the House voted on. |

<a id="p-clinicaltrials-gov"></a>

### ClinicalTrials.gov (`clinicaltrials-gov`)

ClinicalTrials.gov study registry via the public v2 REST API: search studies by condition, intervention, sponsor, location, status or Essie expression with page-token pagination; fetch one study record by NCT number; batch-resolve the raw ACTUAL/ESTIMATED start, primary-completion and completion dates for known NCT numbers; autocomplete conditions, interventions, sponsors and facilities; and read…

| Capability | Credits | Use |
| --- | --- | --- |
| `clinical-trials/field_values` | 5 | You need the valid values of a registry field or the distribution of a field across all studies. |
| `clinical-trials/search` | 5 | Discover NCT numbers for a topic before calling study or study_dates; list trials by sponsor, status or location. |
| `clinical-trials/study` | 5 | You have an NCT number (from search, a pasted clinicaltrials.gov/study URL or elsewhere) and need the full protocol, eligibility, locations… |
| `clinical-trials/study_dates` | 5 | You already have NCT numbers and need to know whether their start and primary completion dates are actual or estimated, or their current st… |
| `clinical-trials/suggest` | 5 | Normalize a drug, condition, sponsor or facility name to the spelling the registry uses before searching. |

<a id="p-commbuys-com"></a>

### COMMBUYS (`commbuys-com`)

COMMBUYS (www.commbuys.com), the Commonwealth of Massachusetts' public procurement portal on Periscope BuySpeed Online: keyword and filtered bid solicitation search (organization, buyer, NIGP class, type, status, UNSPSC category, opening-date window) with the site's fixed 25-row pagination, the current Open Bids list, full bid solicitation detail pages with header fields, addresses, stateless att…

| Capability | Credits | Use |
| --- | --- | --- |
| `public-tenders/get_bid` | 5 | After search_bids or list_open_bids, to read a solicitation in full or to get its attachment download URLs. An unknown bid number is `not_f… |
| `public-tenders/get_blanket` | 5 | After search_bids returns a `blanket_number`, or with a statewide contract number such as `C14597-vCurrent`, to read the awarded contract's… |
| `public-tenders/list_open_bids` | 5 | Enumerate everything currently open for responses without choosing a filter; follow `next_cursor` for later pages and pass a row's `bid_num… |
| `public-tenders/search_bids` | 5 | Find solicitations by keyword (description; with `match: any` also item description, bid number and alternate id), organization (agency), b… |

<a id="p-courtlistener-com"></a>

### CourtListener (`courtlistener-com`)

Public CourtListener opinions, federal dockets, entries and court metadata.

| Capability | Credits | Use |
| --- | --- | --- |
| `courts/courts` | 5 | List the courts CourtListener indexes, with their ids for the court filter of the search functions. Filter by jurisdiction code (S = state … |
| `dockets/docket_entries` | 5 | List the docket entries and filed documents of one federal PACER docket identified by its CourtListener docket_id (from search_dockets), ol… |
| `dockets/search_dockets` | 5 | Search federal PACER dockets (RECAP archive) on CourtListener by party name, attorney, case name, docket number, judge, nature of suit, cau… |
| `opinions/search_opinions` | 5 | Search published case law (opinions) from federal and state courts on CourtListener by full text, citation, case name, judge, docket number… |

<a id="p-courts-ca-gov"></a>

### California Courts (courts.ca.gov) (`courts-ca-gov`)

Judicial Branch of California public site: California Rules of Court by rule number and title index, Judicial Council court forms (search, catalog, form detail), slip opinions of the Supreme Court and Courts of Appeal (last 120 days, list and detail) and the site-wide search. Everything is read from the anonymous server-rendered Drupal pages of courts.ca.gov and selfhelp.courts.ca.gov; no login o…

| Capability | Credits | Use |
| --- | --- | --- |
| `court-rules-forms-opinions/form` | 5 | After forms_search or forms_list, or when you already know the form number. |
| `court-rules-forms-opinions/forms_list` | 5 | To enumerate every court form. Prefer forms_search when you have a topic or number. |
| `court-rules-forms-opinions/forms_search` | 5 | To find a court form when you know a topic (`discovery`, `custody`) or a form number prefix. Use forms_list to walk the whole catalog and f… |
| `court-rules-forms-opinions/opinion` | 5 | After opinions_search, to get the DOCX link and confirm the record. Pass the formats_url as case_number, or kind + date + case_number. |
| `court-rules-forms-opinions/opinions_search` | 5 | To list recent opinions or to locate one by case number (the case-number filter returns the row with its filing date, which opinion needs).… |
| `court-rules-forms-opinions/rule` | 5 | When you know the rule number and need the current text of a California Rule of Court (not a statute: the Code of Civil Procedure lives on … |
| `court-rules-forms-opinions/rules_index` | 5 | To find rule numbers on a subject before calling rule, or to list a whole title. Titles: one (all courts), two (trial court), three (civil)… |
| `court-rules-forms-opinions/site_search` | 5 | When you do not know whether the answer is a rule, a form page or a program page. For rule text call rule; for forms call forms_search. |

<a id="p-data-cityofnewyork-us"></a>

### NYC Open Data property records (ACRIS, PLUTO, DOB) (`data-cityofnewyork-us`)

New York City property records through NYC Open Data's Socrata SODA API and the Department of City Planning GeoSearch geocoder: resolve an address to BBL/BIN, read the MapPLUTO lot record (owner of record, building class, assessed value, zoning), list and read ACRIS recorded documents (deeds, mortgages, parties), and list DOB permits and DOB/ECB violations by building. Anonymous; no app token.

| Capability | Credits | Use |
| --- | --- | --- |
| `property-records/acris_document` | 5 | Who sold to whom, for how much, on which lots, for a document id returned by `acris_documents`. |
| `property-records/acris_documents` | 5 | Sales and deed history, mortgages and other recorded instruments for a parcel by BBL. Follow with `acris_document` for parties (grantor/gra… |
| `property-records/dob_permits` | 5 | Construction, alteration, plumbing or demolition permit history for a building once you have its BIN (from `resolve_address`). |
| `property-records/dob_violations` | 5 | Open or resolved DOB violations, ECB/OATH summonses and outstanding penalties for a building by BIN. |
| `property-records/property` | 5 | Owner of record, lot and building facts, assessed value or zoning for a parcel once you have its BBL (from `resolve_address`). |
| `property-records/resolve_address` | 5 | First step for any 'who owns / what was filed at <address>' question: turn the address into a BBL (for `property`, `acris_documents`) and a… |

<a id="p-data-cms-gov"></a>

### CMS Provider Data Catalog (`data-cms-gov`)

CMS Provider Data Catalog datasets: NPI-keyed clinician procedure volume, plus Care Compare search and detail for hospitals (overall star rating), nursing homes (five-star ratings, staffing, inspections, penalties), home health agencies (quality star rating and measures) and dialysis facilities (star rating and standardized outcomes).

| Capability | Credits | Use |
| --- | --- | --- |
| `clinician-procedure-volume/dialysis_facilities` | 5 | Find Medicare-certified dialysis facilities and their CMS star ratings and modalities. Use dialysis_facility with a CCN for standardized ou… |
| `clinician-procedure-volume/dialysis_facility` | 5 | Look up a dialysis facility's CMS star rating and patient outcomes versus expected. Get the CCN from dialysis_facilities. |
| `clinician-procedure-volume/home_health_agencies` | 5 | Find Medicare-certified home health agencies and their CMS quality star ratings. Use home_health_agency with a CCN for services offered and… |
| `clinician-procedure-volume/home_health_agency` | 5 | Look up a home health agency's CMS star rating, services and quality measures. Get the CCN from home_health_agencies. |
| `clinician-procedure-volume/hospital` | 5 | Look up a hospital's CMS star rating and how many of its measures are better, no different or worse than national rates. Get the CCN from h… |
| `clinician-procedure-volume/hospitals` | 5 | Find Medicare-certified hospitals and their CMS overall star ratings. Use hospital with a CCN for measure-group detail. Star ratings summar… |
| `clinician-procedure-volume/nursing_home` | 5 | Look up a nursing home's CMS ratings, staffing, inspections and penalties. Get the CCN from nursing_homes. Penalties cover the last three y… |
| `clinician-procedure-volume/nursing_homes` | 5 | Find Medicare/Medicaid nursing homes and compare their CMS five-star ratings. Use nursing_home with a CCN for staffing, inspection, penalty… |
| `clinician-procedure-volume/utilization` | 5 | Look up a clinician's reported Medicare procedure occurrences, not unique patients, quality or outcomes. Check displayed_on_profile before … |

<a id="p-data-gov-au"></a>

### data.gov.au open data catalogue (`data-gov-au`)

Australia's national open data catalogue (data.gov.au, CKAN 2.11): search ~100k datasets from federal, state and local agencies with facets and filters, read a dataset's metadata and resources, read a resource and its DataStore schema, query DataStore tables row by row with filters and full-text search, and list or look up publishing organisations.

| Capability | Credits | Use |
| --- | --- | --- |
| `open-data/get_dataset` | 5 | After search_datasets, to read a dataset fully and pick a resource id for get_resource or query_datastore. |
| `open-data/get_resource` | 5 | Before query_datastore: confirm `datastore_active` and read the field ids and types; otherwise use `url` to fetch the file from the publish… |
| `open-data/list_organizations` | 5 | To find the organisation slug to filter search_datasets by (e.g. `q: "statistics"` for the Australian Bureau of Statistics). |
| `open-data/query_datastore` | 5 | For tabular data (population, income, business counts ...) once get_resource or a dataset card shows `datastore_active: true`. Field ids co… |
| `open-data/search_datasets` | 5 | Start here to find datasets and their resource ids. Use `organization` with a slug from list_organizations (ABS Census tables: `government-… |

<a id="p-data-sf-gov"></a>

### DataSF open data portal (`data-sf-gov`)

San Francisco's open data portal (data.sf.gov, a Socrata site): search the dataset catalog, read a dataset's metadata and columns, query and count rows of any dataset with SoQL ($select/$where/$order/$group/$q and bare field filters, including spatial functions), and list the portal's category and tag facets.

| Capability | Credits | Use |
| --- | --- | --- |
| `open-data/dataset` | 5 | Before `rows`: column field names and datatypes must come from here, not be guessed. Accepts a 4x4 id or any data.sf.gov / data.sfgov.org d… |
| `open-data/datasets` | 5 | Start here when the 4x4 dataset id is unknown: find the dataset, then call `dataset` for its columns and `rows` for its data. Only results … |
| `open-data/facets` | 5 | Discover how the portal organises its assets before searching by category or tag. |
| `open-data/row_count` | 5 | Size a `rows` query before paging, or answer a pure how-many question. |
| `open-data/rows` | 5 | Any question that needs actual records from a DataSF dataset. Get the 4x4 id from `datasets` and the column field names from `dataset` firs… |

<a id="p-databrowser-uis-unesco-org"></a>

### UNESCO UIS (`databrowser-uis-unesco-org`)

UNESCO UIS published versions, geographies, indicators and education observations.

| Capability | Credits | Use |
| --- | --- | --- |
| `statistics/data` | 5 | Retrieve observations for up to 20 indicator codes across ISO3 countries and/or UIS regional aggregates, optionally limited to a year range… |
| `statistics/geographies` | 5 | List UIS geo units of one type: countries (ISO 3166-1 alpha-3 ids) or regional aggregates (`GROUP: Name` ids such as `SDG: Sub-Saharan Afri… |
| `statistics/indicator` | 5 | Look up one indicator code and return its full metadata: name, theme, unit label, data availability, glossary definition and calculation me… |
| `statistics/indicators` | 5 | Search the full UIS indicator catalogue (about 5,000 codes including sex, wealth-quintile, location and parity-index disaggregations) by fr… |
| `statistics/versions` | 5 | List every published UIS data version (release) with its publication date, description, and per-theme last-update status, flagging the curr… |

<a id="p-dsld-od-nih-gov"></a>

### NIH Dietary Supplement Label Database (dsld.od.nih.gov) (`dsld-od-nih-gov`)

NIH Office of Dietary Supplements' Dietary Supplement Label Database: the full label content of 200k+ dietary supplements sold in the US. Label search with the site's filters, one label in full (every Supplement Facts row with amount, unit and %DV, other ingredients, statements, claims, contacts, label image and PDF URLs), a brand's labels, A-Z/keyword product and brand browsing, ingredient group…

| Capability | Credits | Use |
| --- | --- | --- |
| `dietary-supplement-labels/brand_products` | 5 | List a brand's catalogue after finding the exact `brand_name` in search_labels or browse_brands. |
| `dietary-supplement-labels/browse_brands` | 5 | Find how DSLD spells a brand before calling brand_products or search_labels with a `brand` filter. |
| `dietary-supplement-labels/browse_products` | 5 | Enumerate products alphabetically or by a word in the product name without full-text ranking; use search_labels for ingredient or brand fil… |
| `dietary-supplement-labels/ingredient_groups` | 5 | Resolve a user's ingredient term (e.g. `ashwagandha`) to DSLD's group name and synonyms before filtering search_labels by `ingredient_name`… |
| `dietary-supplement-labels/label` | 5 | You have a `dsld_id` (from search_labels, brand_products or browse_products) or a `https://dsld.od.nih.gov/label/{id}` URL and need ingredi… |
| `dietary-supplement-labels/search_labels` | 5 | Find supplements by name, brand, ingredient or UPC (quote the formatted UPC, e.g. `"0 15794 08124 1"`); page with `offset`/`next_offset`; t… |
| `dietary-supplement-labels/summary` | 5 | Discover the filter codes (product_type, supplement_form, target_group) and how many labels DSLD holds, or check data freshness. |

<a id="p-earth-search-aws-element84-com"></a>

### Element 84 Earth Search (Sentinel-2 L2A) (`earth-search-aws-element84-com`)

Sentinel-2 L2A scenes over a geometry from Element 84's Earth Search STAC API, with per-field vegetation indices (NDVI, EVI, NDMI) and true-colour/NDVI clips read straight from the Cloud Optimized GeoTIFFs on AWS Open Data by HTTP range request.

| Capability | Credits | Use |
| --- | --- | --- |
| `satellite-imagery/render_clip` | 5 | To show a field on a given date. Get the scene id from search_scenes. Sizes grow with the geometry: keep max_px small for large fields. |
| `satellite-imagery/scene_availability` | 5 | To see whether a period has usable imagery, or how dense the archive is for a place, before calling search_scenes or vegetation_indices. |
| `satellite-imagery/scene_detail` | 5 | When you need asset URLs or raster metadata for a scene id returned by search_scenes. |
| `satellite-imagery/search_scenes` | 5 | Start here to find scene ids and dates for a field, then pass them to vegetation_indices or render_clip. Percentages are per MGRS tile, not… |
| `satellite-imagery/vegetation_indices` | 5 | For a paddock, field or parcel: how green or moist is it per scene, how much of it was cloudy, and which zones lag. Pass scene_ids from sea… |

<a id="p-earthquake-usgs-gov"></a>

### USGS Earthquake Catalog (ComCat) (`earthquake-usgs-gov`)

Earthquake search and event detail from the USGS ANSS Comprehensive Earthquake Catalog (ComCat) via its public FDSN event web service: worldwide events with US coverage down to small magnitudes, PAGER alerts, ShakeMap intensities and Did You Feel It? reports. Public-domain US government data.

| Capability | Credits | Use |
| --- | --- | --- |
| `earthquakes/event` | 5 | Look up one known earthquake's authoritative parameters and impact estimates: how strong the shaking was, the PAGER alert and whether fatal… |
| `earthquakes/search` | 5 | Find earthquakes (or other seismic events) in a time window, region or magnitude range: recent significant quakes, a historical sequence, q… |

<a id="p-elections-ab-ca"></a>

### Elections Alberta results and political finance (`elections-ab-ca`)

Elections Alberta (elections.ab.ca): official election results by electoral division and by voting location for general elections and by-elections, the list of electoral events, registered candidates with their financial filings, registered parties and their disclosure records, the contributor search, and referendum third-party advertisers. Read from the officialresults and efpublic ColdFusion pa…

| Capability | Credits | Use |
| --- | --- | --- |
| `elections/division_results` | 5 | You know the EventId and the electoral division number (from `election_results`) and need results at voting-location level. |
| `elections/election_results` | 5 | You have a numeric EventId (from `list_events`) and want the division-level official count. Use `division_results` for the poll-by-poll det… |
| `elections/list_events` | 5 | Start here to find the EventId for `election_results`, `division_results` and `search_candidates`. |
| `elections/list_parties` | 5 | Find the party id for `party_detail` or for the `party_id` filters of `search_candidates` and `search_contributors`. |
| `elections/list_third_party_advertisers` | 5 | Who is registered to advertise in the referendum and how much they have raised; the ids feed `third_party_advertiser_detail`. |
| `elections/party_detail` | 5 | You have a party id from `list_parties` and want its filings and officers; pass `year` to get one financial year. |
| `elections/search_candidates` | 5 | You want the candidate list of a general election or by-election, or a candidate's financial account identifiers. At least one of `ed`, `pa… |
| `elections/search_contributors` | 5 | You want who gave how much to whom; `name` needs at least 3 characters. Narrow broad surnames by `year`, `party_id` or `ed`. |
| `elections/third_party_advertiser_detail` | 5 | You have a TPAID from `list_third_party_advertisers`. |

<a id="p-ema-europa-eu"></a>

### European Medicines Agency (`ema-europa-eu`)

EU centrally authorised medicines (EPAR medicine pages) and EMA-assessed medicine supply shortages from EMA's published JSON data files, with EMA attribution on every result.

| Capability | Credits | Use |
| --- | --- | --- |
| `records/medicines` | 5 | Search medicines evaluated through EMA's centralised procedure (EU EPAR medicine pages): name, EMA product number, status (Authorised, With… |
| `records/shortages` | 5 | Search medicine supply shortages assessed by EMA: medicine, INN, status (Shortage ongoing, Shortage resolved, Medicine discontinued), pharm… |

<a id="p-faa-gov"></a>

### FAA public records (`faa-gov`)

FAA public records from faa.gov: the aircraft registry (N-number detail, owner, serial and dealer searches, recorded documents), airworthiness directives and other regulatory documents from the Dynamic Regulatory System (DRS), and live NAS airport delay and closure status.

| Capability | Credits | Use |
| --- | --- | --- |
| `aviation-records/aircraft` | 5 | Look up who owns a US-registered aircraft or what a tail number is. Unassigned numbers are not_found; malformed numbers are invalid_input. |
| `aviation-records/aircraft_documents` | 5 | Check recorded liens, security agreements or bills of sale on an aircraft. Most current aircraft have none; an empty page is a valid answer… |
| `aviation-records/aircraft_search` | 5 | Find the tail numbers an operator owns or every aircraft with a given serial number, then call `aircraft` for the detail record. Owner name… |
| `aviation-records/airport_delays` | 5 | Check whether an airport has an active delay program or closure right now. Only airports with an event are listed; `found: false` for a req… |
| `aviation-records/airworthiness_directive` | 5 | Read the details of an airworthiness directive (or any DRS document) found with `airworthiness_directive_search`. Unknown keys are not_foun… |
| `aviation-records/airworthiness_directive_search` | 5 | Find the ADs and related documents for an aircraft make or model, a part or a topic. Filter with `status: Current` for in-force documents; … |
| `aviation-records/dealer_search` | 5 | Find whether a company holds (or held) an FAA dealer aircraft registration certificate. Names match as a prefix on the registry's upper-cas… |
| `aviation-records/make_model_lookup` | 5 | Fleet-size questions (`how many SR22s are registered in Florida?`), or to find the canonical registry manufacturer/model spelling and MMS c… |
| `aviation-records/n_number_availability` | 5 | Pick a tail number for a new registration or reservation, or check which numbers in a vanity pattern are free. Numbers listed are available… |

<a id="p-fda-gov"></a>

### FDA (`fda-gov`)

US FDA drug, food and device enforcement recalls, Drugs@FDA applications, structured labeling, device 510(k) decisions, FAERS drug adverse-event reports, the NDC directory and drug shortages via openFDA.

| Capability | Credits | Use |
| --- | --- | --- |
| `records/device_clearances` | 5 | Search device 510(k) submission decision records and resolve a k_number. Preserve decision_code and decision_date; do not equate every retu… |
| `records/device_recalls` | 5 | Search medical device enforcement recall records and resolve a recall_number. Preserve recall reason, status and classification; this is no… |
| `records/drug_applications` | 5 | Search Drugs@FDA applications and submission histories, or resolve an application_number. Inspect submission statuses: a returned record al… |
| `records/drug_events` | 5 | FAERS drug adverse event reports: patient reactions, suspect and concomitant drugs, seriousness and reporter qualification. Search e.g. pat… |
| `records/drug_labels` | 5 | Search structured drug labeling and resolve a source label id. Includes source warnings and indications where available. Label presence doe… |
| `records/drug_ndc` | 5 | NDC Directory product listings: product NDC, brand and generic names, labeler, dosage form, route, active ingredients, marketing category a… |
| `records/drug_recalls` | 5 | Search drug enforcement recall records, including classification, reason and recall status. Search product_description, recalling_firm or r… |
| `records/drug_shortages` | 5 | FDA drug shortage entries: generic name, company, presentation, status (Current, Resolved, To Be Discontinued), therapeutic category and po… |
| `records/food_recalls` | 5 | Search food enforcement recall records and resolve a recall_number. Source recall status and affected product descriptions are preserved. |

<a id="p-fdc-nal-usda-gov"></a>

### USDA FoodData Central (fdc.nal.usda.gov) (`fdc-nal-usda-gov`)

USDA Agricultural Research Service FoodData Central: the authoritative US food-composition database (Foundation Foods, SR Legacy, Survey/FNDDS, Branded Foods, Experimental Foods). Food search and listing by data type, the complete nutrient record of one food (per 100 g values, data points, min/max/median, derivation, portions, conversion factors, brand and label data), nutrient-centric search (wh…

| Capability | Credits | Use |
| --- | --- | --- |
| `foods/get_food` | 5 | After `search_foods` or `search_foods_by_nutrient` returned an FDC id, or when the user pastes a food-details URL. |
| `foods/list_food_categories` | 5 | To see how FoodData Central groups foods of a data type, or to resolve a category code. |
| `foods/list_nutrients` | 5 | To find a nutrient id or unit before `search_foods_by_nutrient`, or to see which nutrients the database tracks at all. |
| `foods/search_foods` | 5 | Start here to find FDC ids by name, brand, UPC or to enumerate a data type; then call `get_food` for the full record. |
| `foods/search_foods_by_nutrient` | 5 | To find which foods have data for a specific nutrient, or the richest sources of it; `get_food` then gives the full record. |

<a id="p-fec-gov"></a>

### FEC (`fec-gov`)

US Federal Election Commission campaign finance data from the openFEC API: federal candidates and committees, committee financial totals per cycle, filed reports, itemized disbursements (Schedule B), independent expenditures (Schedule E) and individual-contribution aggregates by size, state and employer. Committee, candidate and aggregate data only: itemized individual contributions (Schedule A r…

| Capability | Credits | Use |
| --- | --- | --- |
| `records/candidates` | 5 | Find a federal candidate's FEC candidate ID and principal campaign committee before asking for totals, filings or independent expenditures. |
| `records/committee_totals` | 5 | How much a campaign, PAC or party committee raised, spent and has on hand in a cycle. Use the candidate's principal committee ID for a cand… |
| `records/committees` | 5 | Resolve a campaign, PAC or party committee to its FEC committee ID, or list the committees linked to a candidate. |
| `records/disbursements` | 5 | See what a campaign, PAC or party committee spent money on, or which committees paid a vendor or another committee. |
| `records/filings` | 5 | List a committee's or candidate's FEC filings, find the latest quarterly report, or get links to the filed documents. |
| `records/independent_expenditures` | 5 | Who spent independently for or against a candidate and how much, or what a super PAC spent on which races. |
| `records/receipt_aggregates` | 5 | Where a committee's individual money comes from: small versus large donors, top states or top employers. |

<a id="p-firecrawl-gov-index"></a>

### Government Index (`firecrawl-gov-index`)

About 16 million pages from US federal, state, county and city government sites: statutes and code sections, regulations, zoning and municipal ordinances, permits, licences and fee schedules, court filings, tax forms, procurement and agency guidance, searched as one index, with the laws and cases each page cites.

| Capability | Credits | Use |
| --- | --- | --- |
| `search` | 0 | Use first for any US government, legal, tax, court, permit, statute, regulation, grant or procurement question, before web search: what a c… |

<a id="p-grants-gov"></a>

### Grants.gov (`grants-gov`)

Official federal funding opportunity search, detail and filter vocabularies.

| Capability | Credits | Use |
| --- | --- | --- |
| `opportunities/detail` | 5 | Full Grants.gov opportunity record by stable numeric ID: eligibility, funding amounts, deadlines, amendments, attachments. Always a live lo… |
| `opportunities/facets` | 5 | Filter vocabularies with live hit counts: statuses, agency codes (with sub-agencies), eligibility codes, funding categories and instruments. |
| `opportunities/search` | 5 | Search Grants.gov funding opportunities by keyword, agency, status, eligibility, funding category, assistance listing and posted-date windo… |

<a id="p-iea-org"></a>

### IEA (`iea-org`)

Public energy highlights, country metadata and observations; paid and account-gated non-CC datasets are refused.

| Capability | Credits | Use |
| --- | --- | --- |
| `energy/countries` | 5 | IEA country name to ISO3 crosswalk (from api.iea.org/countries) with aggregates flagged: World, OECD Total/Europe/Americas/Asia Oceania, IE… |
| `energy/data` | 5 | Observations from one free IEA dataset for the given countries (ISO3 or IEA names, required, up to 50), optionally filtered by products, fl… |
| `energy/dataset` | 5 | One dataset's metadata with a live probe of api.iea.org: year_min/year_max actually served, last_updated (MES latest published month or pri… |
| `energy/datasets` | 5 | Catalog of IEA datasets: every free CC BY 4.0 dataset served by api.iea.org (energy balances, electricity and heat, oil, gas, CO2 from fuel… |

<a id="p-kings-printer-alberta-ca"></a>

### Alberta King's Printer (`kings-printer-alberta-ca`)

Official consolidated Alberta acts and regulations (Laws Online catalogue and full text by section, with per-section amendment history and consolidation dates) and the Alberta Gazette (Part 1 and Part 2 issue lists and verbatim issue text) from kings-printer.alberta.ca.

| Capability | Credits | Use |
| --- | --- | --- |
| `legislation/get_gazette_issue` | 5 | After list_gazette_issues. Part 2 is the fastest signal of regulations filed after a consolidation date: compare the AR numbers with get_le… |
| `legislation/get_legislation` | 5 | After search_legislation. Use the ISBN of a '(Download Version)' record. Pass `section` (e.g. '25' or '23.1') for a single section; without… |
| `legislation/list_gazette_issues` | 5 | To find which Gazette issues exist for a year and their ordinals before get_gazette_issue, or to get the Index of Regulations URL for the y… |
| `legislation/search_legislation` | 5 | Start here to find the ISBN of an act or regulation. Pass `query` for title words (POST keyword search; the site matches title words, not f… |

<a id="p-leginfo-legislature-ca-gov"></a>

### California Legislative Information (leginfo.legislature.ca.gov) (`leginfo-legislature-ca-gov`)

California Legislative Information, the Legislature's official site for state law and bills: current text of any California code section or article, full code tables of contents, keyword search over bill text by session, and per bill the current text with digest and versions, status, complete history and roll-call votes. Server-rendered HTML; no API key.

| Capability | Credits | Use |
| --- | --- | --- |
| `legislation/bill` | 5 | You have a bill_id (from bill_search or the site) and need what the bill says. |
| `legislation/bill_history` | 5 | You have a bill_id and need the full procedural history rather than the last five actions bill_status returns. |
| `legislation/bill_search` | 5 | You need bills about a topic in a given session; take bill_id from a result into bill, bill_status, bill_history or bill_votes. |
| `legislation/bill_status` | 5 | You have a bill_id and need where the bill is now, who carries it, and how it is classified. |
| `legislation/bill_votes` | 5 | You have a bill_id and need who voted how. A bill with no recorded votes returns an empty list. |
| `legislation/code_article` | 5 | You have a hierarchy node from code_toc (or the hierarchy of a code_section) and need all sections under it. |
| `legislation/code_section` | 5 | You know the statute citation (e.g. Code of Civil Procedure section 2031.310) and need its current text. |
| `legislation/code_toc` | 5 | You need to browse or enumerate a code, or find the article that holds a section range before calling code_article. |

<a id="p-legislation-gov-uk"></a>

### legislation.gov.uk (`legislation-gov-uk`)

UK legislation from legislation.gov.uk (The National Archives): search and listing feeds across every legislation type (UK Public General Acts, Statutory Instruments, Scottish, Welsh and Northern Ireland legislation, retained EU law), title-to-identifier lookup, tables of contents, the text of one provision or structural division (section, article, regulation, part, chapter, schedule) in its curr…

| Capability | Credits | Use |
| --- | --- | --- |
| `legislation/get_contents` | 5 | To navigate an Act before `get_provision`: find the section numbers under a heading (e.g. the thresholds in Part 3 of the Planning Act 2008… |
| `legislation/get_provision` | 5 | To read statute text: e.g. Planning Act 2008 s.14 (nationally significant infrastructure project definitions) or ss.15-30 (thresholds), or … |
| `legislation/list_changes` | 5 | To see amendments, repeals and commencements touching an Act (e.g. what the Planning and Infrastructure Act 2025 changed in the Planning Ac… |
| `legislation/lookup_identifier` | 5 | When you have an exact or near-exact title and need the `type`/`year`/`number` key; use `search_legislation` for word searches and paging. |
| `legislation/search_legislation` | 5 | Start here to find the `type`/`year`/`number` of an Act or instrument by title or subject words before calling `get_contents`, `get_provisi… |

<a id="p-nevo-online-rivm-nl"></a>

### RIVM NEVO-online (`nevo-online-rivm-nl`)

NEVO-online, the Dutch national food composition database published by RIVM: about 2,300 foods with up to 140 nutrient values per 100 g or 100 ml. Search foods by Dutch or English name, synonym, NEVO code or food group; read one food's full nutrient table with source codes and recipe ingredients; compare nutrient columns across several foods; list the food groups and nutrient columns. Labels are …

| Capability | Credits | Use |
| --- | --- | --- |
| `foods/compare_foods` | 5 | To compare a few nutrients across foods whose NEVO codes are known. |
| `foods/get_food` | 5 | After search_foods returned a NEVO code, or when the code is known. |
| `foods/list_food_groups` | 5 | To find the exact food_group value for search_foods. |
| `foods/list_nutrients` | 5 | To find nutrient tags for search_foods or compare_foods. |
| `foods/search_foods` | 5 | Start here to find a NEVO code by food name or to list the foods of a group; pass the code to get_food for the full nutrient table or sever… |

<a id="p-newjersey-mylicense-com"></a>

### New Jersey license verification (DCA) (`newjersey-mylicense-com`)

New Jersey Division of Consumer Affairs public license verification (newjersey.mylicense.com/verification): the profession and license-type lists behind the search form, person and business licensee search by profession, license type, name, license number and city with the site's 40-row pages, and the License Information record (status, status change reason, issue and expiration dates, board acti…

| Capability | Credits | Use |
| --- | --- | --- |
| `licenses/get_license` | 5 | To verify a New Jersey license number: status, dates, status change reason and whether a public board action is on file. |
| `licenses/list_professions` | 5 | Before a filtered search, to discover the exact profession and license-type names (for example which 15 license types the Nursing board iss… |
| `licenses/search_licenses` | 5 | To find a New Jersey licensee's license number and status by name, or to list the licensees of a profession / license type in a city; follo… |

<a id="p-nhc-noaa-gov"></a>

### NOAA National Hurricane Center (nhc.noaa.gov) (`nhc-noaa-gov`)

Tropical cyclone data from NOAA's National Hurricane Center (Atlantic, eastern and central North Pacific): storms NHC is advising on now with position, intensity and GIS links; each season's storms with ATCF ids; every archived advisory product (public advisory, forecast/advisory, forecast discussion, wind speed probabilities) with parsed headline and summary; the Tropical Weather Outlook with 48…

| Capability | Credits | Use |
| --- | --- | --- |
| `weather/active_storms` | 5 | Which hurricanes or tropical storms are active right now, where they are and how strong; the starting point for a storm's advisories (storm… |
| `weather/best_track` | 5 | Where did a storm go and how strong was it over time; track points for mapping or analysing a hurricane. |
| `weather/season_storms` | 5 | Find a storm's ATCF id from its name and year (Helene 2024 is al092024), or list a season's storms. |
| `weather/storm_advisory` | 5 | Read what NHC says about a storm: its current or a past public advisory, the forecaster's discussion, the forecast/advisory with forecast p… |
| `weather/storm_products` | 5 | See which advisories exist for a storm before reading one with storm_advisory, or get links to its full advisory history. |
| `weather/tropical_outlook` | 5 | Will a tropical cyclone form in the next 2 or 7 days? Which areas is NHC watching, and with what chance? |

<a id="p-nhtsa-gov"></a>

### NHTSA (`nhtsa-gov`)

US vehicle safety data from NHTSA's public APIs: VIN decode to NHTSA vehicle records, safety recalls by VIN-decoded vehicle or year/make/model, recall campaign detail with affected products and documents, consumer complaints, NCAP safety ratings, year/make/model discovery lists and child car seat inspection stations.

| Capability | Credits | Use |
| --- | --- | --- |
| `recalls/car_seat_inspection_stations` | 5 | Find where a parent can have a child seat installation checked near a ZIP, or list a state's stations. |
| `recalls/complaint` | 5 | You have an odi_number from vehicle_complaints and need that single record. |
| `recalls/decode_vin` | 5 | You have a VIN and need the NHTSA vehicle_id(s) to pull recalls or complaints, or the decoded year/make/model. |
| `recalls/recall_campaign` | 5 | You have a campaign number (e.g. from vehicle_recalls) and need the affected product list or the documents. |
| `recalls/safety_ratings` | 5 | Crash-test ratings for a year/make/model, or for the ncap_id returned by search_vehicles or decode_vin. |
| `recalls/search_vehicles` | 5 | Find the NHTSA vehicle_id for a year/make/model when you do not have a VIN, or list every trim/series variant. |
| `recalls/vehicle_complaints` | 5 | Review owner-reported problems for a year/make/model; pass next_offset to continue. |
| `recalls/vehicle_options` | 5 | Build a valid model_year/make/model before calling the recall or complaint functions. |
| `recalls/vehicle_recalls` | 5 | Dealer service or compliance lookups of recall campaigns for a year/make/model or a vehicle_id from decode_vin or search_vehicles. |

<a id="p-npiregistry-cms-hhs-gov"></a>

### NPI Registry (`npiregistry-cms-hhs-gov`)

Public CMS healthcare provider business identities, taxonomy and practice locations.

| Capability | Credits | Use |
| --- | --- | --- |
| `providers/locations` | 5 | Practice locations for one 10-digit NPI: the primary practice location plus every secondary practice location NPPES lists, with phone/fax, … |
| `providers/provider` | 5 | Full NPPES record for one 10-digit NPI: entity type, name, credential, status, enumeration and update dates, all taxonomies (specialties) w… |
| `providers/search` | 5 | Search the CMS NPPES NPI Registry for healthcare providers (individuals or organizations) by name, organization, taxonomy/specialty, city, … |

<a id="p-nvd-nist-gov"></a>

### NIST National Vulnerability Database (NVD) (`nvd-nist-gov`)

CVE vulnerability records from the NIST National Vulnerability Database CVE API 2.0 (services.nvd.nist.gov): look up a CVE by id, search by keyword, CPE product, CWE weakness, CVSS severity, CISA KEV membership and publication or modification dates, and list CVEs published or changed in the last days. Each record carries CVSS v4.0/v3.x/v2 scores, CWEs, CPE applicability matches, the CISA Known Ex…

| Capability | Credits | Use |
| --- | --- | --- |
| `vulnerabilities/cve` | 5 | You have a CVE id (CVE-2021-44228) or an nvd.nist.gov/vuln/detail URL and need its severity, weakness, affected products, exploitation stat… |
| `vulnerabilities/recent` | 5 | Monitoring: what NVD published or changed recently, e.g. critical CVEs modified in the last day. Use `search` for fixed date ranges combine… |
| `vulnerabilities/search` | 5 | Find CVEs affecting a product or version (cpe_match cpe:2.3:a:apache:log4j:2.14.1), with a weakness (CWE-79), that are actively exploited (… |

<a id="p-oregonbuys-gov"></a>

### OregonBuys (`oregonbuys-gov`)

OregonBuys (oregonbuys.gov), the State of Oregon's public procurement portal on Periscope BuySpeed Online: keyword and filtered bid solicitation search with the site's fixed 25-row pagination, the current Open Bids list, and full bid solicitation detail pages with header fields, addresses, public attachment download URLs and line items. Anonymous public access only; bid holder lists, quotes and a…

| Capability | Credits | Use |
| --- | --- | --- |
| `public-tenders/get_bid` | 5 | After search_bids or list_open_bids, to read a solicitation in full or to get its attachment download URLs. An unknown bid number is `not_f… |
| `public-tenders/list_open_bids` | 5 | Enumerate everything currently open for responses without choosing a filter; follow `next_cursor` for later pages and pass a row's `bid_num… |
| `public-tenders/search_bids` | 5 | Find solicitations by keyword (description, item description, bid number, alternate id), organization, buyer, type code, status, category o… |

<a id="p-pennbid-bonfirehub-com"></a>

### PennBid (Bonfire) public procurement portal (`pennbid-bonfirehub-com`)

PennBid, the Pennsylvania public procurement portal hosted on Bonfire (pennbid.bonfirehub.com): the public lists of open and past (closed) opportunities and a lookup of one opportunity's listing record by ProjectID or detail URL. Read-only; no bidding, registration or vendor account surfaces. The opportunity detail page itself sits behind a Cloudflare managed challenge and is not read.

| Capability | Credits | Use |
| --- | --- | --- |
| `public-tenders/get_opportunity` | 5 | Resolve a PennBid ProjectID or a pasted https://pennbid.bonfirehub.com/opportunities/... URL to its listing record and learn whether it is … |
| `public-tenders/list_open_opportunities` | 5 | Find currently open bids/RFPs on PennBid by keyword (project name or awarding agency) or closing window, then pass `project_id` to `get_opp… |
| `public-tenders/list_past_opportunities` | 5 | Look up closed PennBid solicitations by keyword, closing window or public-award flag, for example to find awarded projects of an agency; pa… |

<a id="p-power-larc-nasa-gov"></a>

### NASA POWER (`power-larc-nasa-gov`)

NASA POWER (Prediction Of Worldwide Energy Resources) global weather history for a GeoJSON geometry: daily temperature, rainfall, solar radiation, humidity, wind and soil wetness since 1981, monthly and annual history, 2001-2020 climate normals, and the parameter catalog. Keyless public API; every value is for the 0.5 x 0.625 degree reanalysis grid cell containing the geometry's centroid.

| Capability | Credits | Use |
| --- | --- | --- |
| `weather-history/climate_normals` | 5 | The seasonal baseline to compare a `daily_weather` or `monthly_history` window against (is this season wetter or hotter than normal). |
| `weather-history/daily_weather` | 5 | Rainfall, temperature and radiation history anywhere in the world, including outside the contiguous US. For the US, a station or PRISM-base… |
| `weather-history/list_parameters` | 5 | Find the code for a quantity (soil wetness, dew point, growing degree days) before asking for its history. |
| `weather-history/monthly_history` | 5 | Multi-year seasonal context (how did the last three growing seasons compare) without pulling thousands of daily rows. |
| `weather-history/soil_moisture` | 5 | Root-zone soil wetness for a paddock or field over a season, anywhere in the world. Not a soil survey: it is model soil moisture at 0.5 deg… |

<a id="p-publicpurchase-com"></a>

### Public Purchase (`publicpurchase-com`)

Public Purchase (www.publicpurchase.com), The Public Group's e-procurement portal for US and Canadian public agencies: the region list, the per-region agency directory, each agency's public home page and the anonymous per-agency open-bid widget (title, short description, start/end dates, time left, addendum dates and the login-walled detail URL). Bid detail pages, documents, search and closed bid…

| Capability | Credits | Use |
| --- | --- | --- |
| `public-tenders/get_agency` | 5 | Resolve an agency id (or a pasted agency page URL) to the agency's identity and links. |
| `public-tenders/list_agencies` | 5 | Find an agency's `agency_id` for `list_agency_open_bids` or `get_agency`, or enumerate the agencies of a state or province. |
| `public-tenders/list_agency_open_bids` | 5 | Get the currently open solicitations of one agency found through `list_agencies`. |
| `public-tenders/list_regions` | 5 | Start here when you need the exact region codes; otherwise pass a known state or province code straight to `list_agencies`. |

<a id="p-pubmed-ncbi-nlm-nih-gov"></a>

### PubMed and PMC (`pubmed-ncbi-nlm-nih-gov`)

Biomedical literature from PubMed and PubMed Central (NIH National Library of Medicine): search with PubMed query syntax, document summaries, full article records with abstracts and MeSH indexing, PMID/PMCID/DOI resolution, similar and citing articles, and open-access full text. Uses NCBI's anonymous programmatic services (E-utilities, PMC ID Converter, BioC) only; the PubMed and PMC websites the…

| Capability | Credits | Use |
| --- | --- | --- |
| `publications/article` | 5 | After `search` or `resolve_ids`, to read the abstract, MeSH indexing, affiliations, funding or references of one article. |
| `publications/full_text` | 5 | Read the body of an open-access paper once you have its PMCID (from `search` with `db=pmc`, `summaries`, `article` identifiers or `resolve_… |
| `publications/related` | 5 | Expand from one paper to its neighbourhood: reviews on the same topic (`similar`), later work building on it (`cited_in`) or what it built … |
| `publications/resolve_ids` | 5 | Turn a DOI into a PMID before calling `article`, or a PMID into a PMCID before calling `full_text`. |
| `publications/search` | 5 | Start here to find PMIDs (or PMCIDs with `db=pmc`) for a topic, author or journal; then call `article` for the abstract and MeSH terms, `re… |
| `publications/summaries` | 5 | Batch lookup of bibliographic metadata for known ids (from `search`, `related`, a reference list or a DOI resolved with `resolve_ids`). Use… |

<a id="p-rcc-acis-org"></a>

### ACIS (NOAA Regional Climate Centers) (`rcc-acis-org`)

Observed weather history for a piece of ground in the contiguous United States from the Applied Climate Information System: PRISM gridded daily and monthly precipitation, temperature and growing degree days for a GeoJSON point or polygon, nearby observing stations and their daily records, and county / climate-division / basin / forecast-office lookups. Anonymous public data API; every result carr…

| Capability | Credits | Use |
| --- | --- | --- |
| `weather-history/area_lookup` | 5 | Which county, climate division, watershed and NWS office a field or parcel belongs to, to join with other land data. |
| `weather-history/daily_weather_history` | 5 | How much rain fell on this field between two dates, how many wet days, the longest dry spell; daily highs, lows and GDD for a paddock or pa… |
| `weather-history/monthly_climate_history` | 5 | Long-range context for a parcel: how wet or warm each month was compared with other years, seasonal rainfall by month. |
| `weather-history/nearby_stations` | 5 | Find the closest rain gauge or weather station to a field before asking for its observed daily record. |
| `weather-history/station_daily_history` | 5 | Actual gauge readings near a field rather than the gridded estimate; a rain total from the nearest CoCoRaHS or airport station. |

<a id="p-recreation-gov"></a>

### Recreation.gov (`recreation-gov`)

Recreation.gov (US federal recreation reservations) read-only: search campgrounds, rec areas and permits by text, place or coordinates and stay dates; campground detail with rules, booking windows, rates and ratings; month availability grids; campsite listings and detail with open nights; visitor reviews; daily permit quota availability. Public anonymous JSON API of www.recreation.gov; availabili…

| Capability | Credits | Use |
| --- | --- | --- |
| `camping-availability/campground` | 5 | Details, rules and prices for a campground_id from `search`. |
| `camping-availability/campground_availability` | 5 | Which nights and which sites are open at a campground in a given month; distinguish reserved from closed and not-yet-released. |
| `camping-availability/campsite` | 5 | Full detail and open nights for one campsite_id from `campsites` or `campground_availability`. |
| `camping-availability/campsites` | 5 | List the sites of a campground_id, optionally filtered to a stay; then `campsite` for one site's full detail. |
| `camping-availability/permit_availability` | 5 | Remaining permit quota per entry point/zone and date for a permit_id from `search` (entity_type permit). |
| `camping-availability/reviews` | 5 | Read what visitors said about a campground_id or campsite_id. |
| `camping-availability/search` | 5 | Start here to find a campground_id / permit_id / rec area id by name or place; then call `campground`, `campsites`, `campground_availabilit… |
| `camping-availability/suggest` | 5 | Resolve a partial or ambiguous name to an entity id or to coordinates before `search`. |

<a id="p-reporter-nih-gov"></a>

### NIH RePORTER (`reporter-nih-gov`)

NIH RePORTER research funding database via the public, keyless api.reporter.nih.gov v2 API: search NIH and other HHS-funded research projects by text, principal investigator, organization, state, fiscal year, agency and activity code; read one project with abstract, investigators, program officers, costs and study section; and list the PubMed IDs of publications linked to a project.

| Capability | Credits | Use |
| --- | --- | --- |
| `research-grants/project` | 5 | Read the abstract and funding detail of a grant found with search_projects, or resolve a pasted reporter.nih.gov project link. |
| `research-grants/publications` | 5 | List the papers a grant produced; fetch their titles and abstracts from PubMed with the PMIDs. |
| `research-grants/search_projects` | 5 | Find NIH grants for a topic, a researcher or an institution; get appl_id for project and core_project_num for publications. |

<a id="p-saferproducts-gov"></a>

### CPSC Recalls (SaferProducts.gov) (`saferproducts-gov`)

U.S. Consumer Product Safety Commission recalls from the public Recalls REST API on saferproducts.gov: search by title, product, category, firm, retailer and date, or read one recall's hazards, remedies, units, firms, countries, UPCs and images.

| Capability | Credits | Use |
| --- | --- | --- |
| `product-recalls/recall` | 5 | Read the full recall notice once you have its number (from search_recalls or the cpsc.gov notice). |
| `product-recalls/search_recalls` | 5 | Find recalls for a product, brand, retailer or period. Use recall for the full notice (remedies, units, firms, images). Covers CPSC-regulat… |

<a id="p-sam-gov"></a>

### SAM.gov (`sam-gov`)

US federal procurement notice search and detail, including agency, deadlines, attachments and amendment history.

| Capability | Credits | Use |
| --- | --- | --- |
| `opportunities/detail` | 5 | Fetch one SAM.gov contract opportunity by its 32-character notice id (the id in https://sam.gov/opp/{id}/view): full description, deadlines… |
| `opportunities/search` | 5 | Search SAM.gov contract opportunities by keyword, agency, notice status, publication date, NAICS, set-aside, notice type and response deadl… |

<a id="p-seattle-gov"></a>

### City of Seattle (`seattle-gov`)

City of Seattle (seattle.gov): the City Council roster with office phone, email, page ids and term dates, one councilmember's typed contact card with CMS provenance, the City Clerk's terms of office for every elected official, council district lookup by coordinates (ArcGIS), site search, generic CMS page content and Council Connection news. Anonymous throughout: the Ingeniux content API, the publ…

| Capability | Credits | Use |
| --- | --- | --- |
| `seattle-city-government/council_news` | 5 | Recent statements and news releases from the council or one councilmember. |
| `seattle-city-government/council_roster` | 5 | Who currently sits on the Seattle City Council, how to reach each office, and when each term ends. Use `councilmember` for one member's ful… |
| `seattle-city-government/councilmember` | 5 | Full published contact details and freshness evidence for a specific councilmember after `council_roster` identified the seat. |
| `seattle-city-government/find_district` | 5 | Map an address's coordinates to its council district and representative. Geocoding is not provided; supply lon/lat. |
| `seattle-city-government/page_content` | 5 | Read a page found by `search_pages`, or a component id from `council_roster` / `councilmember`, when the specialised functions do not cover… |
| `seattle-city-government/search_pages` | 5 | Find seattle.gov pages or documents about a topic, person or program, then read one with `page_content`. |
| `seattle-city-government/terms_of_office` | 5 | Term dates for Seattle's elected officials, including those outside the council (mayor, city attorney, judges). |

<a id="p-services-ecourts-gov-in"></a>

### India eCourts district court services (`services-ecourts-gov-in`)

India eCourts Services portal for district and taluka courts (services.ecourts.gov.in, ecourtindia_v6): the state -> district -> court complex -> court establishment reference cascade the portal's search forms are built on, and the public case status record of a case identified by its 16-character CNR (Case Number Record): case type, filing and registration numbers and dates, status, court and ju…

| Capability | Credits | Use |
| --- | --- | --- |
| `court-cases/get_case_by_cnr` | 5 | You know a case's CNR (e.g. DLND010000012024, printed on court notices, orders and cause lists) and need its current status, parties, heari… |
| `court-cases/list_court_complexes` | 5 | You have state_code and dist_code and need a court_complex_code for list_establishments or to scope a case. |
| `court-cases/list_districts` | 5 | You have a state_code from list_states and need a dist_code for list_court_complexes. |
| `court-cases/list_establishments` | 5 | You have state_code, dist_code and court_complex_code and need the establishments in the complex. |
| `court-cases/list_states` | 5 | You need a state_code for list_districts, or want to know which states/UTs the portal serves. |

<a id="p-socrata-com"></a>

### Socrata open-data portals (`socrata-com`)

Discover and query datasets on any public Socrata (Tyler Data & Insights) open-data portal: city, county and state portals such as data.cityofchicago.org, data.ny.gov, data.austintexas.gov, data.wa.gov and hundreds more. Search the cross-portal catalog (Socrata Discovery API), read a dataset's columns, row count, license and update details, and query rows with SoQL (select/where/order/group/full …

| Capability | Credits | Use |
| --- | --- | --- |
| `open-data/describe_dataset` | 5 | Before query_dataset, to learn the exact field names and types for select/where/order, and to size a dataset. Also answers 'how current is … |
| `open-data/query_dataset` | 5 | Any question that needs actual records or aggregates from an open-data dataset (permit lookups by address or number, inspection results, 31… |
| `open-data/search_datasets` | 5 | Start here for city, county or state open data (permits, inspections, 311, code violations, business licenses, crime, property) when the da… |

<a id="p-tenders-etimad-sa"></a>

### Etimad tenders (tenders.etimad.sa) (`tenders-etimad-sa`)

Saudi Arabia's government procurement portal Etimad (منصة اعتماد, National Center for Government Resources Systems): visitor tender search with keyword, reference number, type, activity, agency, region, status and publish-window filters; tender detail with the basic information, dates (Gregorian and Hijri) and classification/execution-place tabs; direct-purchase and limited-tender announcements; …

| Capability | Credits | Use |
| --- | --- | --- |
| `public-procurement-tenders/get_tender` | 5 | After search_tenders, to read one tender's full public notice. |
| `public-procurement-tenders/list_lookups` | 5 | To get valid ids for search_tenders, search_announcements, search_prequalifications and search_future_projects filters, or to map an id bac… |
| `public-procurement-tenders/search_announcements` | 5 | To list direct-purchase / limited-tender notices, which are not in search_tenders. |
| `public-procurement-tenders/search_future_projects` | 5 | To see procurement an agency plans to tender, before a tender is published. |
| `public-procurement-tenders/search_prequalifications` | 5 | To list pre-qualification invitations (a separate surface from tenders and announcements). |
| `public-procurement-tenders/search_tenders` | 5 | To find tenders by keyword/filters or to resolve a 12-digit reference number to its tender_id_string before calling get_tender. |

<a id="p-tenders-wa-gov-au"></a>

### Tenders WA (tenders.wa.gov.au) (`tenders-wa-gov-au`)

Western Australian Government procurement portal Tenders WA: open, new, closed, awarded, early-advice and DCSP tender notice listings, advanced tender search with keyword, state, type, agency, region and date filters, tender detail (status, UNSPSC, regions, closing time, specification document list, briefing/site visit and awarded contract link), recently awarded contracts, contract search, contr…

| Capability | Credits | Use |
| --- | --- | --- |
| `public-procurement-tenders-contracts/get_contract` | 5 | After list_contracts, search_contracts or get_tender (awarded), to read who won, for how much and for how long. |
| `public-procurement-tenders-contracts/get_tender` | 5 | After list_tenders or search_tenders, to read one notice in full: closing time, briefing requirement, documents, description. |
| `public-procurement-tenders-contracts/list_contracts` | 5 | To see recently awarded WA government contracts without a keyword. Use search_contracts for filters and get_contract for the full record. |
| `public-procurement-tenders-contracts/list_tenders` | 5 | To see what is currently open, new, recently closed or awarded across all WA agencies without a keyword. Use search_tenders for keyword, ag… |
| `public-procurement-tenders-contracts/lookups` | 5 | To resolve an agency or region name to the id search_tenders / search_contracts expect. |
| `public-procurement-tenders-contracts/search_contracts` | 5 | To find awarded contracts by keyword (e.g. cleaning), agency, region, value or award date. Ids come from lookups. |
| `public-procurement-tenders-contracts/search_tenders` | 5 | To find tenders by keyword (e.g. cleaning), agency, region, state or date range. Ids for public_authority_id, issuing_business_id, region_i… |

<a id="p-travel-state-gov"></a>

### U.S. State Department Travel Advisories (travel.state.gov) (`travel-state-gov`)

U.S. Department of State travel advisory levels (1-4) and advice for every destination it covers, plus the per-country travel information pages (entry requirements, safety, local laws, health, transportation, embassy contacts), from the Bureau of Consular Affairs public data API.

| Capability | Credits | Use |
| --- | --- | --- |
| `travel-advisories/advisories` | 5 | Which destinations are Level 4 Do Not Travel, or what the U.S. government currently advises about travel to a country found by name. For on… |
| `travel-advisories/advisory` | 5 | Look up the level and advice for one destination when you know its State Department code (GM, UK, MX) or have its travel.state.gov advisory… |
| `travel-advisories/country_information` | 5 | Passport, visa and vaccination requirements, emergency numbers, local-law warnings or U.S. embassy addresses for a destination. Use advisor… |

<a id="p-v-dem-net"></a>

### V-Dem (`v-dem-net`)

Official V-Dem democracy indices, codebook metadata, country crosswalk and regime transformation episodes.

| Capability | Credits | Use |
| --- | --- | --- |
| `democracy/countries` | 5 | V-Dem country crosswalk (183 countries served by the graphing API): country_id, country_text_id, name, ISO3 or null with historical/non-ISO… |
| `democracy/data` | 5 | Country-year observations for up to 5 variables and 50 countries (ISO3 or V-Dem country_text_id) from v-dem.net's official graphing API for… |
| `democracy/datasets` | 5 | Current V-Dem dataset releases read live from v-dem.net (Country-Year Core, Country-Year Full+Others, Country-Date, Coder-Level: version, p… |
| `democracy/ert` | 5 | Episodes of Regime Transformation (ERT v16) country-year records for up to 20 countries from the V-Dem Institute's official GitHub csv: reg… |
| `democracy/variable` | 5 | Live codebook entry for one V-Dem variable tag (question, clarification, scale, aggregation, source variables, data-release line) from v-de… |
| `democracy/variables` | 5 | Search the V-Dem codebook (404 variables served by v-dem.net's graphing API) by tag, name or question text, filtered by thematic section, i… |

<a id="p-vpic-nhtsa-dot-gov"></a>

### NHTSA vPIC vehicle decoder (`vpic-nhtsa-dot-gov`)

NHTSA's Product Information Catalog and Vehicle Listing (vPIC): decode a VIN or WMI into make, model, year, trim, plant and vehicle type; list makes, models, manufacturers and their WMIs; look up the decode variable dictionary. Public US federal data, no key.

| Capability | Credits | Use |
| --- | --- | --- |
| `vehicles/decode_vin` | 5 | Dealer inventory intake, title or listing checks: turn a 17-character VIN into structured vehicle identity. Pass model_year for partial VIN… |
| `vehicles/decode_vin_batch` | 5 | Bulk inventory or fleet intake. NHTSA asks that large batches run at night US Eastern time or on weekends. |
| `vehicles/decode_wmi` | 5 | Identify who built a vehicle from a VIN prefix without a full VIN, or check whether a WMI is registered with NHTSA. |
| `vehicles/get_manufacturer` | 5 | After decode_vin (manufacturer_id) or list_manufacturers, to see who a registrant is and where they are; or to search the registry by name. |
| `vehicles/list_makes` | 5 | Discovery before list_models: find the make ID or exact make name vPIC uses. Search mode is client-side filtering of GetAllMakes and return… |
| `vehicles/list_manufacturers` | 5 | Enumerate the registry page by page; use get_manufacturer to search by name instead. |
| `vehicles/list_models` | 5 | Enumerate what a make sold in a model year (1981+), or resolve a model ID. |
| `vehicles/list_variables` | 5 | Interpret decode_vin attributes and error codes, or enumerate the allowed values of a lookup variable. |
| `vehicles/list_wmis` | 5 | Map a manufacturer to the VIN prefixes it uses, or check which vehicle types a WMI covers. |

<a id="p-web-pcc-gov-tw"></a>

### Taiwan Government e-Procurement (web.pcc.gov.tw) (`web-pcc-gov-tw`)

Taiwan's Government e-Procurement System (政府電子採購網): search tender notices (招標公告) and award / failed-to-award notices (決標公告, 無法決標公告), read the full notice detail pages, and look up agency codes. Anonymous, server-rendered HTML; no login, no documents behind the member login.

| Capability | Credits | Use |
| --- | --- | --- |
| `public-procurement-notices/award_detail` | 5 | After search_awards, to read one award or failed-to-award notice by its base64 pk and kind (or a pasted QueryAtmAwardDetail / urlSelector a… |
| `public-procurement-notices/lookup_agency` | 5 | To find the org_id for search_tenders / search_awards when you know an agency's name, or to list the subordinate units of a parent code. |
| `public-procurement-notices/search_awards` | 5 | Finding who won Taiwan public contracts, by keyword, agency, vendor tax id or date window; then call award_detail with a result's pk and ki… |
| `public-procurement-notices/search_tenders` | 5 | Finding Taiwan public tenders by keyword, agency or case number, or listing notices published in a date window; then call tender_detail wit… |
| `public-procurement-notices/tender_detail` | 5 | After search_tenders, to read one tender notice by its base64 pk (or a pasted searchTenderDetail / urlSelector tpam URL). |

<a id="p-who-int"></a>

### WHO Global Health Observatory (`who-int`)

Official WHO indicator search, dimension codes and paginated observations with source licensing and attribution.

| Capability | Credits | Use |
| --- | --- | --- |
| `indicators/data` | 5 | Fetch one page of observations for a GHO indicator, filtered by spatial type (COUNTRY, REGION, WORLDBANKINCOMEGROUP, GLOBAL), ISO3/region c… |
| `indicators/dimensions` | 5 | List the values of one GHO dimension (COUNTRY, REGION, WORLDBANKINCOMEGROUP, SEX, AGEGROUP, ...): code, title and parent (countries carry t… |
| `indicators/indicators` | 5 | Search the GHO indicator catalogue by words in the indicator name or code (case-insensitive substring; empty query lists everything). Retur… |

<a id="p-wildfirerisk-org"></a>

### USFS Wildfire Risk to Communities (`wildfirerisk-org`)

USDA Forest Service Wildfire Risk to Communities (wildfirerisk.org): 30 m raster wildfire risk values (burn probability, risk to homes, wildfire consequence, hazard potential, exposure type, flame length) for a GeoJSON point or polygon, the containing county, community and tribal area with their percentile ranks, place search, per-place summaries and rankings within a county, state or the nation.…

| Capability | Credits | Use |
| --- | --- | --- |
| `wildfire-risk/compare_within_parent` | 5 | 'How does this county compare with the rest of the state/nation' or 'which communities in this county are most at risk'. |
| `wildfire-risk/place_summary` | 5 | After search_places or wildfire_risk_for_geometry returned an id, for the published classes and ranks of that place. |
| `wildfire-risk/search_places` | 5 | To find the WRC id of a named town, county or tribal area before place_summary or compare_within_parent. |
| `wildfire-risk/wildfire_risk_for_geometry` | 5 | Any 'what is the wildfire risk of this parcel / paddock / lot' question. Follow with place_summary on a returned county or community id for… |

<a id="p-worldhappiness-report"></a>

### World Happiness Report (`worldhappiness-report`)

Official WHR dashboard aggregate rankings, country-year indicators and edition appendix metadata; not Gallup respondent microdata.

| Capability | Credits | Use |
| --- | --- | --- |
| `happiness/countries` | 5 | List the dashboard's geographies as ISO 3166-1 alpha-3 codes with display names (164 entries incl. XKX Kosovo, TWN Taiwan Province of China… |
| `happiness/editions` | 5 | List every World Happiness Report edition (2012 onwards) with its appendix and data file downloads, the citation string and the licence not… |
| `happiness/panel` | 5 | Gallup World Poll country-year panel for up to 10 countries (ISO3) from the dashboard country view: annual life ladder, three-year average,… |
| `happiness/rankings` | 5 | One page of a World Happiness Report edition's ranking table (three-year average Cantril ladder score and rank) with the six explanatory-fa… |

Also in this category: [Australian Food Composition Database (AFCD, FSANZ)](#p-afcd-foodstandards-gov-au), [FCC OET Equipment Authorization System (apps.fcc.gov)](#p-apps-fcc-gov), [Alberta Utilities Commission](#p-auc-ab-ca), [Arizona Registrar of Contractors license register (azroc.my.site.com)](#p-azroc-my-site-com), [FDIC BankFind Suite](#p-banks-data-fdic-gov), [Banco Central do Brasil open data](#p-bcb-gov-br), [BLS labor statistics](#p-bls-gov), [WIPO Global Brand Database](#p-branddb-wipo-int), [Canadian Patents Database (CIPO)](#p-brevets-patents-ic-gc-ca), [Missouri Secretary of State business registry](#p-bsd-sos-mo-gov), [Utah business registry](#p-businessregistration-utah-gov), [CFTC](#p-cftc), [CFTC Commitments of Traders](#p-cftc-gov), [Virginia SCC Clerk's Information System (business entity registry)](#p-cis-scc-virginia-gov), [California CSLB contractor license lookup](#p-cslb-ca-gov), [INPI data.inpi.fr](#p-data-inpi-fr), [World Bank Data](#p-data-worldbank-org), [Data Privacy Framework participant list](#p-dataprivacyframework-gov), [Delaware Division of Corporations](#p-delaware-gov), [Eurostat (ec.europa.eu)](#p-ec-europa-eu), [European Central Bank (ECB Data Portal)](#p-ecb-europa-eu), [Georgia Secretary of State business registry (eCorp)](#p-ecorp-sos-ga-gov), [US Senate financial disclosures (eFD)](#p-efdsearch-senate-gov), [US Energy Information Administration](#p-eia-gov), [Federal Reserve Board](#p-federalreserve-gov), [Companies House](#p-find-and-update-company-information-service-gov-uk), [US Treasury Fiscal Data](#p-fiscaldata-treasury-gov), [Canadian Nutrient File, Health Canada (food-nutrition.canada.ca)](#p-food-nutrition-canada-ca), [FRED](#p-fred), [FRED (Federal Reserve Economic Data)](#p-fred-stlouisfed-org), [GLEIF](#p-gleif-org), [Lobbying Disclosure Act filings (lda.gov)](#p-lda-gov), [Florida DBPR licensing registry (myfloridalicense.com)](#p-myfloridalicense-com), [NFA BASIC](#p-nfa-futures-org), [OpenSanctions](#p-opensanctions-org), [WIPO PATENTSCOPE patent search](#p-patentscope-wipo-int), [Alberta Purchasing Connection](#p-purchasing-alberta-ca), [New Hampshire business registry (QuickStart)](#p-quickstart-sos-nh-gov), [API Recherche d'entreprises (annuaire-entreprises.data.gouv.fr)](#p-recherche-entreprises-api-gouv-fr), [UK Financial Services Register (FCA)](#p-register-fca-org-uk), [FMCSA SAFER and SMS carrier registry](#p-safer-fmcsa-dot-gov), [OFAC Sanctions List Search](#p-sanctionssearch-ofac-treas-gov), [IP Australia trade mark search](#p-search-ipaustralia-gov-au), [Florida Sunbiz](#p-search-sunbiz-org), [SEC EDGAR](#p-sec-gov), [IBGE service data API](#p-servicodados-ibge-gov-br), [Colorado Secretary of State business database](#p-sos-state-co-us), [AusTender](#p-tenders-gov-au), [UK IPO trade mark register](#p-trademarks-ipo-gov-uk), [Treasury Fiscal Data](#p-treasury-fiscal-data), [Texas SmartBuy ESBD](#p-txsmartbuy-gov), [UN Global Marketplace](#p-ungm-org), [USAspending](#p-usaspending-gov), [USPTO patents, trademarks and assignments](#p-uspto-gov)

## health

Population health statistics: life expectancy, mortality, disease burden, immunization coverage, risk factors, health systems and WASH by country, region and year.

<a id="p-ihme-gbd-results"></a>

### IHME GBD Results (`ihme-gbd-results`)

IHME Global Burden of Disease Results tool metadata: release versions and the full cause, location, age, sex, measure, metric and risk-factor (REI) hierarchies for GBD 2021 and GBD 2023.

| Capability | Credits | Use |
| --- | --- | --- |
| `gbd/children` | 1 | Traverse one level down a hierarchy: the direct children of a cause, location or rei node (e.g. GBD region Western Europe to its 24 countri… |
| `gbd/lookup` | 1 | Resolve one entity (cause, location, age, sex, measure, metric or rei) by GBD id in a GBD round: its hierarchy_node record plus ancestors (… |
| `gbd/metadata` | 1 | One page of hierarchy_node records for an entity type (cause, location, age, sex, measure, metric, rei) in a GBD round: id, name, parent_id… |
| `gbd/versions` | 1 | List the GBD Results tool release versions (version id, GBD round, release stamp, model description, exposed measure ids) for one or both s… |

<a id="p-world-openfoodfacts-org"></a>

### Open Food Facts (`world-openfoodfacts-org`)

Open Food Facts, the open database of packaged foods (world.openfoodfacts.org): product facts by barcode (name, brand, quantity, countries, ingredients, allergens, additives, Nutri-Score, NOVA, per-100g and per-serving nutrition, images), full-text and filtered product search over the Search-a-licious service, and taxonomy autocomplete for categories, brands, labels and countries. Anonymous read …

| Capability | Credits | Use |
| --- | --- | --- |
| `foods/product` | 5 | You have a barcode (or a world.openfoodfacts.org product URL) and want its nutrition facts, ingredients, allergens or scores. Use `search` … |
| `foods/search` | 5 | Find products by name, brand or category, e.g. 'oat milk' sold in France, then call `product` with a hit's barcode for the full record. Use… |
| `foods/suggest` | 5 | Resolve a category, brand, label or country name the user typed into the taxonomy id before filtering with `search`. |

Also in this category: [California DCA physician licenses](#p-california-dca-license), [European Medicines Agency](#p-ema-europa-eu), [RIVM NEVO-online](#p-nevo-online-rivm-nl), [NIH RePORTER](#p-reporter-nih-gov)

## healthcare

Healthcare providers and facilities: identifiers, specialties, licenses, practice locations and official registry records.

Also in this category: [CMS Provider Data Catalog](#p-data-cms-gov), [New Jersey license verification (DCA)](#p-newjersey-mylicense-com)

## jobs

Job postings: who is hiring for which roles, where, and since when.

<a id="p-glassdoor-com"></a>

### Glassdoor US jobs (`glassdoor-com`)

Glassdoor US job search: one page of 30 job cards per call for a keyword, optionally in a Glassdoor location (city, state or country id from suggest_locations) with the site's own filters (posting age, remote, Easy Apply, sort, minimum salary, minimum employer rating, seniority, radius, employer size, employer, industry), cursor continuation into the following pages, and the autocomplete services…

| Capability | Credits | Use |
| --- | --- | --- |
| `jobs/search_jobs` | 5 | Start here for job discovery and employer comparison by hiring activity. Resolve a city/state with suggest_locations first when you need a … |
| `jobs/suggest_employers` | 5 | Resolve an employer name to its Glassdoor employer id, e.g. to filter search_jobs by employer_id. Returns an empty list for an unknown term. |
| `jobs/suggest_keywords` | 5 | Normalize a free-text role to the job titles Glassdoor knows before search_jobs. Returns an empty list when the site has no suggestion. |
| `jobs/suggest_locations` | 5 | Resolve a place name to a Glassdoor location id before search_jobs. Returns an empty list for an unknown term. |

<a id="p-greenhouse-io"></a>

### Greenhouse job boards (`greenhouse-io`)

Employer job boards hosted by Greenhouse: list every opening on a board, search it with Greenhouse's own keyword, department and office filters, read one post with its description, pay ranges and application questions, and enumerate a board's departments and offices. Keyed by the employer's board token; there is no directory of boards.

| Capability | Credits | Use |
| --- | --- | --- |
| `jobs/board` | 5 | To confirm a board token exists on Greenhouse and read the employer's name and blurb before listing its openings with jobs or search. |
| `jobs/departments` | 5 | To discover department ids for search or to see how openings spread across departments. |
| `jobs/job` | 5 | When you have a job post id from jobs or search, or a pasted job page URL, and need the description, departments or application questions. |
| `jobs/jobs` | 5 | Start here with a board token to enumerate every opening with id, title, location, requisition id, dates and the public job URL. Pass next_… |
| `jobs/offices` | 5 | To discover office ids for search or to see where an employer is hiring. |
| `jobs/search` | 5 | When you need Greenhouse's own keyword search or a department/office filter, or the department of each post. Ids for department_id and offi… |

<a id="p-icims-com"></a>

### iCIMS (`icims-com`)

Employer career portals hosted by iCIMS at <portal>.icims.com: search and paginate openings with the portal's own filters, read one posting with its header fields, body sections and JobPosting metadata, and describe a portal's categories, locations and position types.

| Capability | Credits | Use |
| --- | --- | --- |
| `jobs/job` | 5 | When you have a posting id from search or a pasted https://<portal>.icims.com/jobs/<id>/... URL. |
| `jobs/portal` | 5 | To discover filter ids for search or to check that a portal exists and still serves listings on icims.com. |
| `jobs/search` | 5 | Start here with a portal subdomain (or a pasted .icims.com/jobs/search URL). Pass next_page back as page to paginate; use job for the full … |

<a id="p-join-com"></a>

### JOIN job ads (`join-com`)

Employer career pages hosted by JOIN (join.com): read an employer's profile with offices and benefits, list its online job ads with category and city filters, read one ad with description, salary, contract and working terms, and enumerate the employer's job categories. Keyed by the employer's join.com slug; JOIN publishes no cross-employer search or directory.

| Capability | Credits | Use |
| --- | --- | --- |
| `jobs/categories` | 5 | To find category ids for jobs, or to name the category ids in jobs aggregations. |
| `jobs/company` | 5 | To resolve an employer slug (the segment after join.com/companies/) to its numeric company id and city ids before listing jobs, or to read … |
| `jobs/job` | 5 | When you have a job id or last_id from jobs, or a pasted ad URL (join.com/companies/<slug>/<id_param> or join.com/jobs/<last_id>), and need… |
| `jobs/jobs` | 5 | Start here with an employer slug (or company_id from company) to enumerate its openings; pass next_page back as page. Use category_ids from… |

<a id="p-myworkdayjobs-com"></a>

### Workday career sites (`myworkdayjobs-com`)

Career sites of any employer on Workday Recruiting ({tenant}.wd{N}.myworkdayjobs.com and wd{N}.myworkdaysite.com): search a site's open requisitions with its own keyword search and facets (location, job category, time type, remote type and others as each site exposes them, with ids and counts), page through results, and read one posting with its full description, requisition id, locations, dates …

| Capability | Credits | Use |
| --- | --- | --- |
| `jobs/get_job` | 5 | With a pasted Workday posting URL, or career_site plus an external_path from search_jobs. |
| `jobs/search_jobs` | 5 | Start here with any Workday career-site URL. Read `facets` to filter by location, job category, time type or remote type (parameters differ… |

<a id="p-successfactors-com"></a>

### SAP SuccessFactors career sites (`successfactors-com`)

Career sites of any employer on SAP SuccessFactors Recruiting Marketing (Career Site Builder, formerly jobs2web), the platform behind many large European employers' job boards (Fraunhofer, EY, BASF, Boehringer Ingelheim, E.ON, Schaeffler, BMW, DLR and thousands more): search a site's open postings with its own keyword, location and facet filters and page through them, and read one posting with it…

| Capability | Credits | Use |
| --- | --- | --- |
| `jobs/get_job` | 5 | With a pasted SuccessFactors posting URL (https://{site}/[...]/job/{slug}/{id}/), or career_site plus a search_jobs job_id. |
| `jobs/search_jobs` | 5 | Start here with any career-site URL running on SAP SuccessFactors / jobs2web (rmkcdn.successfactors.com assets, /job/{slug}/{id}/ posting U… |

<a id="p-wayfair-com"></a>

### Wayfair Careers and Product Reviews (`wayfair-com`)

Wayfair job postings from the careers site's own JSON search endpoint and server-rendered job pages: filtered job search with the full employer-authored description available per job, one job's complete detail (JSON-LD JobPosting plus the page's inline job data), and the filter vocabularies (teams, categories, countries, states, locations, job types) with their ids. Also the storefront's customer…

| Capability | Credits | Use |
| --- | --- | --- |
| `job-postings/get_job` | 5 | You have a job_id (`2-16958`), a bare eid (`16958`) or a wayfair.com/careers/job/ URL and want the complete posting text. Use search_jobs t… |
| `job-postings/list_filters` | 5 | Before a filtered search_jobs call, to translate a team, category, country, state, city or job type name into its id. |
| `job-postings/reviews` | 5 | Collect every review of a Wayfair product (loop on next_cursor until it is null) or keep a copy current: poll with sort=newest and stop at … |
| `job-postings/search_jobs` | 5 | Discovery: find Wayfair jobs by title words or filters and get their job_id for get_job. Keywords match the job title only (not the descrip… |

<a id="p-ziprecruiter-com"></a>

### ZipRecruiter US (`ziprecruiter-com`)

ZipRecruiter US job marketplace: job search by title and city/state (the public /Jobs/ directory pages, 20 cards a page with pay, employment and location types, benefits and posting time), full job postings (JobPosting JSON-LD plus the page's job details), a company's open jobs near a city, salary percentiles for a title in a city, and title/location autocomplete.

| Capability | Credits | Use |
| --- | --- | --- |
| `jobs/company_jobs` | 5 | After search_jobs, with the company slug from a card's company_url (e.g. YO-AI-Labs from /co/YO-AI-Labs/Jobs) and a city. |
| `jobs/job` | 5 | After search_jobs or company_jobs, with a card's url. Any pasted ziprecruiter.com /c/.../Job/... URL with a jid works. |
| `jobs/salary` | 5 | Pay benchmark for a title and city; not a posting's pay (that is on the job card). |
| `jobs/search_jobs` | 5 | Start here to find job detail URLs and company slugs; pass page=next_page to continue. Filter by posting date (posted_within_days) and annu… |
| `jobs/suggest_locations` | 5 | Resolve a place name to the "City, ST" form that search_jobs, company_jobs and salary take. An unknown prefix returns an empty list. |
| `jobs/suggest_titles` | 5 | Normalize free text into a title ZipRecruiter knows before search_jobs or salary. An unknown prefix returns an empty list. |

Also in this category: [Built In](#p-builtin-com), [Indeed](#p-indeed-com), [Y Combinator](#p-ycombinator-com)

## knowledge

Encyclopedic and reference knowledge: articles, facts about entities, definitions and their sources.

<a id="p-wikipedia"></a>

### Wikipedia (`wikipedia`)

Wikipedia and its sister projects through Wikimedia Enterprise, the Wikimedia Foundation's official API: current articles by title, parsed infoboxes and sections, and Wikidata entities.

| Capability | Credits | Use |
| --- | --- | --- |
| `articles/lookup` | 1/record | Read the current revision of a Wikipedia (or sister-project) article by exact title: full wikitext (or HTML with body), abstract, categorie… |
| `articles/structured-contents` | 1/record | Read a Wikipedia article pre-parsed into JSON: one-line description, abstract, infobox fields, sections as paragraphs and lists with links,… |
| `reference/languages` | 0 | List the language codes Wikimedia projects use, with names and writing direction, to choose the language option or build a project identifi… |
| `reference/projects` | 0 | List the Wikimedia projects available for lookup, to find the project identifier for a language and project type, such as `ptwiki` for Port… |
| `wikidata/item` | 1 | Read a Wikidata item by QID: labels, descriptions and aliases in every language, all statements (property values with qualifiers and refere… |
| `wikidata/labels` | 1 | Get the name of a Wikidata item or property in every language, keyed by language code. Cheaper than wikidata/item when only names are neede… |
| `wikidata/property` | 1 | Read a Wikidata property by PID: its labels, descriptions, datatype and statements. Use to learn what a statement key in an item, such as P… |

## marketing

Marketing research: website traffic, search interest and trends, audience insights, creator discovery and podcast sponsorships.

<a id="p-branding"></a>

### Website Branding (`branding`)

Extract a website's logo, colors, fonts, typography and component styles through Firecrawl Scrape's branding format.

| Capability | Credits | Use |
| --- | --- | --- |
| `extract` | 1 | Extract a website's brand identity: logo, color palette, fonts and typography, spacing and button styles, from one public page URL. Use for… |

<a id="p-firecrawl-trends"></a>

### Trends (`firecrawl-trends`)

Search interest over time and by region, related and rising queries, keyword suggestions and what is trending now.

| Capability | Credits | Use |
| --- | --- | --- |
| `trends/interest_by_region` | 5 | Where a term is most popular: top states, countries, metros or cities. |
| `trends/interest_over_time` | 5 | Trend lines, seasonality, or comparing popularity of terms over a period. |
| `trends/related_queries` | 5 | Keyword research: what else people search alongside a term, and what is newly rising. |
| `trends/suggestions` | 0 | Disambiguate a term (Apple the company vs the fruit) before comparing interest. |
| `trends/trending_now` | 5 | What people are searching for right now in a country; news and breakout topics. |

<a id="p-icons-computer"></a>

### Icons Computer (`icons-computer`)

Find app icons by name, color, style, category and platform, with image links and source attribution.

| Capability | Credits | Use |
| --- | --- | --- |
| `icons/collection` | 5 | Get the collection's icon count, available categories and platforms with counts, methodology and rights notice. Each call costs 5 credits. |
| `icons/detail` | 5 | Read one icon using its ID from search, including image dimensions, source links and an agent-ready Markdown reference. Each call costs 5 c… |
| `icons/search` | 5 | Find app icons by app name or a description such as purple icons or animal icon. Filter by category or platform. Default sort ranks query m… |

<a id="p-oriane"></a>

### Oriane (`oriane`)

Search indexed Instagram and TikTok profiles and posts through Oriane, including bios, follower counts and content engagement. Empty results do not trigger live scraping.

| Capability | Credits | Use |
| --- | --- | --- |
| `instagram/post-lookup` | 30 | Resolve a canonical Instagram post/video URL against Oriane's index. Instagram uses the post shortcode; TikTok uses the numeric video ID. E… |
| `instagram/posts-search` | 30 | Search Oriane's indexed Instagram posts, captions and engagement. Platform is fixed to Instagram. Coverage and freshness depend on the exis… |
| `instagram/profile-lookup` | 30 | Pass a canonical Instagram profile URL to look up account details in Oriane's index. Returns profileUrl with each match. Short links and po… |
| `instagram/profiles-search` | 30 | Search Oriane's indexed Instagram profiles, bios and follower counts. Platform is fixed to Instagram. Coverage and freshness depend on the … |
| `tiktok/posts-search` | 30 | Search Oriane's indexed TikTok posts, captions and engagement. Platform is fixed to TikTok. Coverage and freshness depend on the existing i… |
| `tiktok/profile-lookup` | 30 | Pass a canonical TikTok profile URL to look up account details in Oriane's index. Returns profileUrl with each match. Short links and post … |
| `tiktok/profiles-search` | 30 | Search Oriane's indexed TikTok profiles, bios and follower counts. Platform is fixed to TikTok. Coverage and freshness depend on the existi… |
| `tiktok/video-lookup` | 30 | Resolve a canonical TikTok post/video URL against Oriane's index. Instagram uses the post shortcode; TikTok uses the numeric video ID. Empt… |

<a id="p-upspring"></a>

### Upspring (`upspring`)

Competitor ad intelligence from Upspring: Meta ads with their hooks, personas and offers, and the brands behind them.

| Capability | Credits | Use |
| --- | --- | --- |
| `ads/breakdown` | 50 | Use for how a market advertises: the share of hooks, personas, offers or formats across a vertical, brand or filter. Run it twice, once wit… |
| `ads/browse` | 50 | Use to list a brand's or a vertical's ads by filter: what an advertiser is running now (advertiser_id + is_active=true), or the winners in … |
| `ads/detail` | 100 | Use for everything about one ad: the hook, offer, landing page and whether the page delivers what the ad promises. Add include=full for sce… |
| `ads/search` | 50 | Use to find Meta ads matching a free-text idea, relevance-ranked across Upspring's competitor ad corpus. Re-rank the page by strength.impre… |
| `ads/similar` | 50 | Use to find ads creatively like one ad, from the same brand and from its competitors. |
| `advertisers/brief` | 100 | Use for a brand's ad strategy at a glance: size grades, Facebook and Instagram followers, Reddit sentiment, its creative fingerprint (perso… |
| `advertisers/by-domain` | 100 | Use when all you have is a company's website: resolves it to one advertiser and returns the same brief as advertisers/brief. Never 404s; a … |
| `advertisers/compare` | 100 | Use to put two brands' ad strategies side by side: where they overlap, where they differ, and what each leaves open. |
| `advertisers/peers` | 50 | Use for brands like this one: same category, vertical, geography or size band. For creative similarity instead use advertisers/similar. |
| `advertisers/request` | 0 | Use when advertisers/brief answers not found or status unavailable for an advertiser id you know exists: asks Upspring to source it, then p… |
| `advertisers/search` | 50 | Use to find a brand's advertiser id by name, website or Facebook page, or to list the advertisers in a vertical, category or size tier. For… |
| `advertisers/similar` | 50 | Use for a brand's closest competitors: advertisers going after the same audience with comparable creative strategies. |
| `taxonomy/vertical` | 0 | Use, free, before filtering ads by persona, hook or another dimension: lists the valid ids in one vertical. |
| `taxonomy/verticals` | 0 | Use first, free, to learn the vertical and category ids the ads and advertiser filters accept. |

Also in this category: [Particle](#p-particle), [Similarweb](#p-similarweb)

## news

Reported news: articles, wires and the archives behind them.

<a id="p-substack-com"></a>

### Substack (`substack-com`)

Public Substack archives, search and free posts or paid previews.

| Capability | Credits | Use |
| --- | --- | --- |
| `newsletters/archive` | 5 | One page of a Substack publication's archive, newest, top or pinned first. Each entry carries title, subtitle, URL, publish time, audience … |
| `newsletters/post` | 5 | One Substack post by URL, or by publication and slug: metadata plus body_html and body_text. Free posts (audience everyone) are complete; p… |
| `newsletters/search` | 5 | Search a Substack publication's archive for posts matching a query, using Substack's own archive search. Returns the same post entries as a… |

<a id="p-us-forums-blizzard-com"></a>

### Blizzard US Forums (`us-forums-blizzard-com`)

Blizzard Entertainment's US community forums (us.forums.blizzard.com, Discourse multisite): categories, latest/top topic listings, topics with their posts, full-text post search, single posts, public user profiles with activity, and the latest-posts feed, for every locale/site forum on the host (WoW, WoW: Forever, Diablo, Hearthstone, Overwatch, StarCraft, ...). Anonymous read-only JSON routes; n…

| Capability | Credits | Use |
| --- | --- | --- |
| `forum-discussions/get_post` | 5 | Fetch a single post found through search_posts, latest_posts or a user's activity. |
| `forum-discussions/get_topic` | 5 | Read a discussion found through list_topics or search_posts; page through long threads with `page` (and a smaller `page_size` when only the… |
| `forum-discussions/get_user` | 5 | Who is behind a post, and what else they wrote on this forum. |
| `forum-discussions/latest_posts` | 5 | A firehose of what is being said right now on a forum (news-style monitoring); filter by category_id or topic on the caller's side. |
| `forum-discussions/list_categories` | 5 | Discovery: find the category ids to pass to list_topics (for example the WoW: Forever categories on en/wow) or to read a site's structure. |
| `forum-discussions/list_topics` | 5 | Browse or monitor a forum or category, e.g. WoW: Forever discussions (en/wow category 347) newest first, or the week's top topics. |
| `forum-discussions/search_posts` | 5 | Find discussions about a subject (e.g. `WoW Forever` newest first, or posts in #housing after a date). Pair with get_topic for the full thr… |

<a id="p-wowhead-com"></a>

### Wowhead (`wowhead-com`)

Wowhead (World of Warcraft and Blizzard games): news RSS feeds and paged news lists with articles and comments, the Blizzard Blue Tracker (forum posts and news), search suggestions and database tooltips, all from the site's anonymous JSON, XML and server-rendered data islands. Public guide discovery (class, build, leveling and every other category, on retail and each Classic branch) and full guid…

| Capability | Credits | Use |
| --- | --- | --- |
| `news/blue_tracker` | 5 | Official Blizzard community communication (hotfixes, dev notes, forum replies). Chain `id` and `region` of a `topic` entry into `blue_track… |
| `news/blue_tracker_news` | 5 | Read a Blizzard news article mirrored by Wowhead Blue Tracker. Accepts kind=news identifiers from blue_tracker. Returns full body HTML and … |
| `news/blue_tracker_topic` | 5 | Read the full Blizzard replies of a topic listed by `blue_tracker` (kind `topic`). |
| `news/comment_replies` | 5 | Retrieve the complete public reply array for a comment from comments_list, including replies omitted from the page preview. Supply the orig… |
| `news/comments_list` | 5 | Read public comments from a Wowhead guide, news article or database page. Offset pagination preserves all embedded comments, sorted by id. … |
| `news/forum_topic` | 5 | Read a thread found through forum_topics, a pasted topic URL or a last_post link. |
| `news/forum_topics` | 5 | Browse or collect community discussion on a board, then read threads with forum_topic. |
| `news/guide_get` | 5 | Read a public Wowhead guide (class, build, leveling or any other category) with its complete authored body markup, author, publication/upda… |
| `news/guides_search` | 5 | Discover public WoW guides by branch, category, title query, class and specialization. Filters and offset pagination apply to the embedded … |
| `news/news_article` | 5 | Read a news post found through `news_feed`, `news_list` or `search_suggest` (type 162) in full. |
| `news/news_feed` | 5 | The quickest way to get recent Wowhead news for a game branch with exact timestamps and source links (for example WoW Forever news). Use `n… |
| `news/news_list` | 5 | Browse or page through Wowhead news beyond the RSS window, or filter by news type. Chain the returned `id` into `news_article`. |
| `news/search_suggest` | 5 | Resolve a name to Wowhead ids before `tooltip` or `news_article`, or discover related news and guides. An unknown term returns empty arrays… |
| `news/tooltip` | 5 | Look up a game entity's name and tooltip by id (ids come from `search_suggest`). An id the site does not know is `not_found`. |

Also in this category: [Benzinga](#p-benzinga), [CBC News (cbc.ca)](#p-cbc-ca), [Federal Reserve Board](#p-federalreserve-gov), [Trends](#p-firecrawl-trends), [Nasdaq.com news feeds and articles](#p-nasdaq-com)

## people

The people at companies: who they are, what they do, and how to reach them.

Also in this category: [Apollo](#p-apollo), [U.S. House Clerk roll call votes and members](#p-clerk-house-gov), [Data Legion](#p-datalegion), [US Senate financial disclosures (eFD)](#p-efdsearch-senate-gov), [FullEnrich](#p-fullenrich), [New Jersey license verification (DCA)](#p-newjersey-mylicense-com), [NPI Registry](#p-npiregistry-cms-hhs-gov), [OpenSanctions](#p-opensanctions-org), [Particle](#p-particle), [City of Seattle](#p-seattle-gov)

## places

Local businesses and places: what is near an address, with hours, phone, address, website, rating and review count.

<a id="p-campspot-com"></a>

### Campspot (`campspot-com`)

Campspot campground marketplace (www.campspot.com): destination and park suggestions, dated park search by coordinates or place name with guest, pet, site-type, amenity and rating filters, park details and policies, per-park site-type availability and pricing for a date range, and the full park catalogue from the sitemap. Anonymous, read-only; nothing here books, holds or signs in.

| Capability | Credits | Use |
| --- | --- | --- |
| `campsite-listings/get_park` | 5 | Details for a park found through search_parks, suggest_locations, list_parks' booking slugs or a pasted https://www.campspot.com/book/{slug… |
| `campsite-listings/get_park_availability` | 5 | After search_parks or get_park, to see which site types and campsites a park has free for given dates and what they cost. Prices are in the… |
| `campsite-listings/list_parks` | 5 | Enumerate every park on the marketplace or find a park by a word in its slug. Marketplace slugs are not booking slugs: use suggest_location… |
| `campsite-listings/search_parks` | 5 | Find parks near a place or coordinates, optionally for a date range and party. Follow with get_park for details and get_park_availability f… |
| `campsite-listings/suggest_locations` | 5 | Turn free text ('Austin', 'Yellowstone', a park name) into coordinates or a park_id before search_parks or get_park. search_parks also acce… |

<a id="p-classpass-com"></a>

### ClassPass (`classpass-com`)

ClassPass class discovery and availability: find studios and class occurrences near a point for a date, read studio details and class types, a studio's schedule for a day, a single class occurrence with its availability status and displayed credit price, resolve locations and list markets. Anonymous same-origin JSON API of classpass.com; read-only, no reservations. Prices are ClassPass credits as…

| Capability | Credits | Use |
| --- | --- | --- |
| `fitness-classes/location` | 5 | Turn a city or address into latitude/longitude for search_schedules / search_venues. |
| `fitness-classes/markets` | 5 | Coverage check and a starting coordinate for search_schedules / search_venues without a geocoder. |
| `fitness-classes/schedule` | 5 | Detail for an `id` from search_schedules or venue_schedule. |
| `fitness-classes/search_schedules` | 5 | Discovery of classes near a location on a date. Get coordinates from `location` or `markets`; pass a result's `id` to `schedule`, its `venu… |
| `fitness-classes/search_venues` | 5 | Discovery of studios near a location. Pass a result's `id` to `venue` or `venue_schedule`. |
| `fitness-classes/venue` | 5 | Details for a `venue.id` / `id` from search_schedules or search_venues. |
| `fitness-classes/venue_schedule` | 5 | The day's timetable of a known studio (`venue_id` from search_venues / search_schedules / venue). |

<a id="p-flooranddecor-com"></a>

### Floor & Decor (`flooranddecor-com`)

Floor & Decor US (flooranddecor.com): catalog search and category browse, product detail with per-store USD pricing, type-ahead suggestions, store locator and store pages, and customer Q&A. Anonymous, read-only.

| Capability | Credits | Use |
| --- | --- | --- |
| `products/find_stores` | 5 | Find a store id for get_store, or to price and filter products by store in search_products and get_product. |
| `products/get_product` | 5 | After search_products or suggest returned a product id, or when the id is known from a product URL (the trailing -{id}.html). |
| `products/get_store` | 5 | After find_stores, or when a store id is known from a /store/... URL or a product's store pricing. |
| `products/product_questions` | 5 | Read customer Q&A for a product id from search_products or get_product. |
| `products/search_products` | 5 | Start here to find product ids (and category slugs) for get_product and product_questions. Omit `query` to browse a category. |
| `products/suggest` | 5 | Resolve a partial or misspelled term to category slugs, product ids and canonical search phrases before search_products. |

<a id="p-fresha-com"></a>

### Fresha (`fresha-com`)

Fresha marketplace discovery without an account: find salons, spas and other venues near a geocode by treatment, filter by a date and time window to see available start times per service, read a venue's public service menu (advertised prices, durations, variants), team, hours and latest reviews, and find professionals and their profiles. Anonymous persisted GraphQL queries on www.fresha.com; read…

| Capability | Credits | Use |
| --- | --- | --- |
| `professionals/professional_detail` | 5 | Detail read after search_professionals or autocomplete, or for a pasted fresha.com/p/ link. |
| `professionals/search_professionals` | 5 | Find a stylist, therapist or barber near a place; then pass the slug to professional_detail. |
| `venues/autocomplete` | 5 | Resolve a treatment name to a taxonomy id before search_venues, or find a venue/professional slug by name. |
| `venues/search_venues` | 5 | Discovery: find venues offering a treatment near a place, or check which venues have openings on a date; then pass a venue slug to venue_de… |
| `venues/venue_detail` | 5 | Detail read after search_venues or autocomplete, or for a pasted fresha.com/a/ link. |

<a id="p-hipcamp-com"></a>

### Hipcamp (`hipcamp-com`)

Hipcamp campsite, cabin, glamping and RV listing discovery: dated search with location, group size and amenity filters, land details, per-site availability and displayed price quotes, blocked-date calendars, reviews, place autocomplete and public campground daily availability. Anonymous, read-only.

| Capability | Credits | Use |
| --- | --- | --- |
| `campsite-listings/autocomplete` | 5 | Turn a place name into coordinates for search_lands, or find a land or public campground by name. |
| `campsite-listings/land` | 5 | After search_lands or a pasted hipcamp.com/land URL. For dated availability and full quotes call land_sites. |
| `campsite-listings/land_calendar` | 5 | Calendar view of what is already booked or closed for a land or a single site. |
| `campsite-listings/land_reviews` | 5 | Read reviews for a land from search_lands or land; pass next_cursor to continue. |
| `campsite-listings/land_sites` | 5 | Dated availability check and price breakdown for a land found by search_lands or land. |
| `campsite-listings/public_campground_availability` | 5 | After autocomplete returns a campground_public result; pass its numeric id. |
| `campsite-listings/search_lands` | 5 | Start here to find lands near a place; use autocomplete first to turn a place name into coordinates. Feed masked_id into land, land_sites, … |

<a id="p-nissanusa-com"></a>

### Nissan USA dealer locator and inventory (`nissanusa-com`)

Nissan USA (nissanusa.com) dealer locator: dealers by ZIP, city or coordinates, dealer details with hours and services, and public new / certified pre-owned inventory by dealer or VIN. Anonymous, read-only; no leads, bookings or accounts.

| Capability | Credits | Use |
| --- | --- | --- |
| `vehicles/get_dealer` | 5 | You have a dealer_id from search_dealers, nearby_dealers or a nissanusa.com dealer URL. |
| `vehicles/get_inventory_vehicle` | 5 | You have a VIN from list_dealer_inventory (condition new). Certified pre-owned VINs are not served by this call. |
| `vehicles/list_dealer_inventory` | 5 | Browse a dealer's public inventory. Pass dealer_id from search_dealers/nearby_dealers plus the dealer's coordinates; omit dealer_id to list… |
| `vehicles/nearby_dealers` | 5 | You already have coordinates and want the locator's own record (including hours) in one call. The source caps a call at 100 dealers; there … |
| `vehicles/search_dealers` | 5 | The user supplies a place name or ZIP code. Returns dealer_id values for get_dealer and list_dealer_inventory. Sales hours are not in this … |

<a id="p-openstreetmap-org"></a>

### OpenStreetMap (`openstreetmap-org`)

OpenStreetMap data: Nominatim geocoding (forward and reverse), Overpass category search inside a bbox, radius, administrative area or polygon, and the OSM API v0.6 for element detail, batch fetch, bbox map dumps, element history, changesets and map notes.

| Capability | Credits | Use |
| --- | --- | --- |
| `places/changesets` | 5 | See who edited an area recently and with which tools; auditing a local copy. |
| `places/element_history` | 5 | Audit how an element changed over time, or find who last edited it. |
| `places/geocode` | 5 | Start here to turn a place name (city, neighbourhood, street, POI) into OSM ids, coordinates, a bbox or a boundary polygon. |
| `places/get_element` | 5 | Detail for an id returned by `search_elements`, `geocode` or `map_bbox`; `full` for a way or boundary geometry. |
| `places/get_elements` | 5 | Refresh or deduplicate a batch of known ids (e.g. from a local database) in one call. |
| `places/map_bbox` | 5 | A complete dump of a block or plaza for a local database; for category queries over a larger area use `search_elements`. |
| `places/notes` | 5 | Find open data-quality reports in an area before or after importing it. |
| `places/reverse_geocode` | 5 | You have a lat/lon and need the OSM object and address there. |
| `places/search_elements` | 5 | Category queries: all restaurants in a bbox, pharmacies inside a municipality relation, cafes within 500 m of a point, POIs inside a neighb… |

<a id="p-ra-co"></a>

### Resident Advisor (`ra-co`)

Resident Advisor (ra.co) electronic music and nightlife events worldwide, read from RA's own anonymous GraphQL API: resolve a city to its RA area, list events for an area and date range with genre and keyword filters, facets and pagination, read one event with lineup, venue and the public primary ticket tiers (price, booking fee, currency, sale status, on-sale window), search events, venues, arti…

| Capability | Credits | Use |
| --- | --- | --- |
| `events/areas` | 5 | First step of event discovery: you need the numeric `area_id` for `events`, or the time zone and currency of a city. |
| `events/artist` | 5 | You have an artist id (from `search` or an event's `artists[].id`), an RA slug, or a pasted `https://ra.co/dj/{slug}` URL and need the prof… |
| `events/event` | 5 | You have an RA event id (from `events`, `search`, `venue`, `artist`) or a pasted `https://ra.co/events/{id}` URL and need details or ticket… |
| `events/events` | 5 | Discover events by city and date; take `area_id` from `areas` and chain each `events[].id` into `event` for tickets. |
| `events/search` | 5 | You know a name (artist, club, party, promoter, city) and need its RA id to chain into `event`, `venue`, `artist` or `events`. |
| `events/venue` | 5 | You have a venue id (from `search`, `events[].venue.id`, or a pasted `https://ra.co/clubs/{id}` URL) and need the venue's details or its up… |

<a id="p-resy-com"></a>

### Resy (`resy-com`)

Resy restaurant discovery and reservation availability from Resy's own web API: city lookup, venue search with inline slots, venue details, per-day availability with booked-out vs closed distinction, availability calendars and slot deposit/cancellation conditions. Read-only: no bookings, holds or notifications.

| Capability | Credits | Use |
| --- | --- | --- |
| `restaurants/availability` | 5 | Given a venue_id (from search_venues or venue) and a date. One upstream availability call plus one calendar call. |
| `restaurants/calendar` | 5 | To find which days a venue has any table for a party size before calling availability, or to tell a closed day from a sold-out one. |
| `restaurants/locations` | 5 | First hop when you know a city name but not its Resy slug or coordinates. Returns the coordinates to pass to search_venues. |
| `restaurants/search_venues` | 5 | Discovery: find restaurants near a point (optionally by name or cuisine keyword) that have a table on a day. Follow with venue, availabilit… |
| `restaurants/slot_conditions` | 5 | After availability or search_venues returned a slot `config_token`. Alternatively give venue_id + day (+ optional start time and seating ty… |
| `restaurants/venue` | 5 | Detail hop after search_venues, or when given a resy.com/cities/{city}/venues/{slug} URL. Use availability for slots. |

<a id="p-rover-com"></a>

### Rover (`rover-com`)

Rover public pet-care discovery without an account: search sitters by service (boarding, house sitting, drop-in visits, dog walking, doggy day care), location, dates, dog size and price; read a sitter's public profile with every listed rate (sitter rate and the full price including Rover's owner-side service fee), acceptance rules and cancellation policy; read the sitter's public availability cal…

| Capability | Credits | Use |
| --- | --- | --- |
| `pet-care-services/get_sitter` | 5 | After `search_sitters`, to read a sitter's full profile and every listed rate. |
| `pet-care-services/get_sitter_availability` | 5 | Check which days a specific sitter lists as open for a service before contacting them on Rover. |
| `pet-care-services/list_sitter_reviews` | 5 | Read what pet owners wrote about a specific sitter. |
| `pet-care-services/search_sitters` | 5 | Find sitters for a service near a place, optionally for dates, dog size and budget; then chain `slug`/`opk` into the detail functions. |
| `pet-care-services/suggest_locations` | 5 | Turn a partial or ambiguous place name into a location string before `search_sitters`. |

<a id="p-seatgeek-com"></a>

### SeatGeek (`seatgeek-com`)

SeatGeek event discovery: search events by team, artist, venue, place, date and category; event, performer and venue detail; search-box suggestions; event-level ticket availability snapshots (listing and ticket counts, price range). Reads the anonymous SeatGeek Platform API (api.seatgeek.com/2) with the web app's public client id. Per-listing offers are behind DataDome and not covered.

| Capability | Credits | Use |
| --- | --- | --- |
| `events/event` | 5 | Detail for an event id from search_events, suggest or a pasted seatgeek.com event URL. |
| `events/performer` | 5 | Detail for a performer id or slug from search_performers, search_events or suggest. |
| `events/search_events` | 5 | Discovery: find events for a team, artist, venue, place or date range, then pass an event id to event. |
| `events/search_performers` | 5 | Resolve a team, artist or show name to a SeatGeek performer id/slug before listing its events. |
| `events/search_venues` | 5 | Find a venue id by name or list venues in a city before listing events at a venue. |
| `events/suggest` | 5 | Quickly resolve a partial name to SeatGeek ids across events, performers and venues in one call. |
| `events/venue` | 5 | Detail for a venue id from search_venues, search_events or suggest. |

<a id="p-spothero-com"></a>

### SpotHero parking (`spothero-com`)

SpotHero parking discovery and pricing for the US and Canada: hourly/daily, monthly and airport parking searches with itemised quotes for a time window, single-facility quotes, customer reviews, destinations (venue name search and per-id detail with typical price ranges), upcoming events, and the city and airport directories. Read-only: no holds, bookings or checkout.

| Capability | Credits | Use |
| --- | --- | --- |
| `parking/airports` | 5 | Look up an airport's IATA code or destination id before search_airport_parking or destination. |
| `parking/cities` | 5 | Check whether SpotHero covers a city and get a starting coordinate for search_parking or search_monthly_parking. |
| `parking/destination` | 5 | Resolve a destination id to coordinates before search_parking, or show a venue's typical price ranges. |
| `parking/destination_events` | 5 | Find event dates and SpotHero's event parking windows at a venue before pricing with search_parking. |
| `parking/facility_quote` | 5 | Re-price a facility found by a search for a different window, or read its full details. |
| `parking/facility_reviews` | 5 | Read what customers say about a facility found by a search. |
| `parking/search_airport_parking` | 5 | Compare off-airport and on-airport parking prices for a trip; airports and their codes come from `airports`. |
| `parking/search_destinations` | 5 | Turn a venue name into a SpotHero destination_id and coordinates, then follow it into destination_events (that venue's event parking window… |
| `parking/search_events` | 5 | Turn a team, artist or event title into destination coordinates and an event parking window for search_parking. Not for venue names: use se… |
| `parking/search_monthly_parking` | 5 | Find commuter or resident monthly parking near an address; coordinates come from `cities`, `destination` or `airports`. |
| `parking/search_parking` | 5 | Find parking near a place or venue for a specific arrival and departure time and compare quoted prices; follow `facility_id` into facility_… |

<a id="p-stubhub-com"></a>

### StubHub (`stubhub-com`)

Search StubHub events, read event details and retrieve paginated public resale offers with quantity restrictions and price/fee disclosures. Uses anonymous web pages and read-only inventory requests.

| Capability | Credits | Use |
| --- | --- | --- |
| `events/event` | 0 | Read event identity, venue, source status, performers and current inventory counts. Unconfirmed times are null; utc_offset_ms is the source… |
| `events/listings` | 0 | Read one page of public resale offers for an event and ticket quantity. Numeric price is per ticket; display_total_for_quantity is the sour… |
| `events/search` | 0 | Search public StubHub events by keywords such as an artist, team, venue or city. Returns one relevance-ranked page; pass next_page as page.… |

<a id="p-tickpick-com"></a>

### TickPick (`tickpick-com`)

TickPick (US resale ticket marketplace, all-in pricing): discover sports, concert, theater and comedy events by free text, performer, venue or location, and read event details with event-level listing statistics (count, min/max/average all-in per-ticket price) and daily/hourly price history from TickPick's own web API. Per-listing offers are not available (DataDome-protected).

| Capability | Credits | Use |
| --- | --- | --- |
| `events/categories` | 5 | Browse without a query: list leagues, teams, genres and shows and get performer slugs. Cached daily by the site. |
| `events/event` | 5 | After search, performer_events or venue_events returned an event_id, or when the user pastes a tickpick.com/buy-... URL. |
| `events/event_price_history` | 5 | To see how the cheapest ticket and the listing count moved over time for an event_id from search, performer_events or venue_events. |
| `events/nearby_events` | 5 | Location-first discovery: 'what is happening in Chicago'. Pass latitude/longitude; add the TickPick market slug (dma, for example washingto… |
| `events/performer_events` | 5 | Events for a performer whose slug and url_category came from search (performers[]) or categories (items[]). |
| `events/search` | 5 | Start here to resolve a team, artist, show, venue or event name to TickPick identifiers. For a full event list use performer_events or venu… |
| `events/venue_events` | 5 | Everything at a venue whose slug came from search or an event's venue. Page with offset = next_offset until it is null. |

<a id="p-todaytix-com"></a>

### TodayTix (`todaytix-com`)

TodayTix theatre discovery and availability: the cities the site sells in, show search by city, keyword, date, price and sort, show detail with event-level low prices and publicly disclosed Rush/Lottery information, per-performance ticket snapshots with price bands and seat counts, and venue profiles. Read-only; no holds, lotteries or checkout.

| Capability | Credits | Use |
| --- | --- | --- |
| `events/locations` | 5 | First hop of discovery: resolve a city name to a TodayTix location id, timezone and currency. |
| `events/search_shows` | 5 | Find shows by city, keyword or date, then pass a show id to show or showtimes. |
| `events/show` | 5 | Detail for a show id from search_shows, or for a pasted todaytix.com show URL. |
| `events/showtimes` | 5 | Availability and prices per performance for a show id; filter by date window to keep pages small. |
| `events/venue` | 5 | Where a show plays: pass venue.slug from a show card, or a todaytix.com venue URL. |

<a id="p-uhaul-com"></a>

### U-Haul (`uhaul-com`)

uhaul.com truck rental quotes and availability: search in-town (local) and one-way truck rates for a pickup location, optional drop-off location and pickup date, read the per-model rate basis (rental rate, mileage rate, extra day/mile, allowed days and distance, environmental fee) and the site's own availability text; autosuggest pickup/drop-off place names; list U-Haul locations in a city, read …

| Capability | Credits | Use |
| --- | --- | --- |
| `truck-rentals/get_location` | 5 | You have an `entity_id` from `list_locations` (or a pasted uhaul.com/Locations/.../{id}/ URL) and need the location's profile. |
| `truck-rentals/get_location_reviews` | 5 | You have a location `entity_id` and want its customer feedback. |
| `truck-rentals/list_locations` | 5 | Find location `entity_id`s in a place before `get_location` / `get_location_reviews`. |
| `truck-rentals/search_truck_rates` | 5 | The caller wants truck sizes, prices or availability for a move between two places or around one place on a date. Use `suggest_locations` f… |
| `truck-rentals/suggest_locations` | 5 | Normalise a free-text place into the exact `pickup_location` / `dropoff_location` string before calling `search_truck_rates`. |

Also in this category: [BBB business profiles](#p-bbb-business-profiles-ratings-complaint), [Better Business Bureau](#p-bbb-org), [Bing Maps](#p-bing-com), [FCIA member directory](#p-fcia-org), [Maps](#p-firecrawl-maps), [Gartner](#p-gartner-com), [Houzz](#p-houzz-com), [USFS Wildfire Risk to Communities](#p-wildfirerisk-org)

## podcasts

What was said on a podcast: episodes, transcripts, guests and sponsors.

Also in this category: [Particle](#p-particle)

## political-science

Political-science research data: democracy and regime indices per country-year, their codebooks, uncertainty bounds and dataset releases.

Also in this category: [Legislative Assembly of Alberta](#p-assembly-ab-ca)

## real-estate

Property records and home valuation comparables.

<a id="p-auction-com"></a>

### Auction.com (`auction-com`)

Auction.com residential real-estate auctions (US): search foreclosure, bank-owned and other auction listings by state, city, county or ZIP, read listing details, third-party valuation and comparables, live bid state, and location suggestions, from the site's own anonymous GraphQL API.

| Capability | Credits | Use |
| --- | --- | --- |
| `real-estate-auctions/get_auction_status` | 5 | Refreshing bid state for listings already known, or checking many listings cheaply. |
| `real-estate-auctions/get_listing` | 5 | Full detail for a listing found through search_listings or a pasted auction.com/details URL. |
| `real-estate-auctions/get_valuation` | 5 | Pricing context for a listing (AVM, comps, last sale prices, assessed and tax values). |
| `real-estate-auctions/search_listings` | 5 | Finding auction properties in an area; listing sold (closed) auctions with winning bids; locating a listing_id for get_listing, get_valuati… |
| `real-estate-auctions/suggest_locations` | 5 | Resolving a user's place name to the state/city/county/ZIP values search_listings expects, or finding the listing behind a street address. |

<a id="p-craigslist-org"></a>

### Craigslist (`craigslist-org`)

Craigslist housing rentals: every region worldwide, filtered search of apartments, rooms, sublets and swaps by rent, beds, baths, pets, type and keyword, and full postings with attributes, photos, map location and timestamps.

| Capability | Credits | Use |
| --- | --- | --- |
| `housing/posting` | 5 | Pass a card's `url` (or its posting_token as posting_id). A numeric post id also needs `region` (and optionally `category`). A deleted or u… |
| `housing/regions` | 5 | Find the `region` slug for search (sfbay, newyork, austin, london) or list all regions in a country. |
| `housing/search` | 5 | Search rentals in a region; narrow large regions with `subarea` (abbreviations come from `regions`, e.g. sfbay: sfc san francisco, eby east… |

<a id="p-redfin-com"></a>

### Redfin (`redfin-com`)

Read publicly advertised US rental listings, floor plans, amenities and policies. Preview pending runner validation.

| Capability | Credits | Use |
| --- | --- | --- |
| `properties/amenities` | 5 | Read published in-unit and community amenity names for a rental listing. |
| `properties/floor_plans` | 5 | Read published rental floor plans with names, rent, size/bath text and unit availability text. Unit counts are separate from building count… |
| `properties/policies` | 5 | Read published rental policy text, including pet restrictions and any displayed fees. Does not infer missing policies. |
| `properties/related_areas` | 5 | Discover linked nearby city rental search pages from an existing city rental page. This is not free-text location geocoding. |
| `properties/rental` | 5 | Read primary rental identity, rent, beds, baths, area, description and source attribution. Requires a current For rent listing; excludes ne… |
| `properties/search` | 5 | Read one rental search page with published rent, bedroom/bathroom text, listing URLs and availability facts. Accept city and neighborhood r… |

<a id="p-zillow-com"></a>

### Zillow (`zillow-com`)

US home search, property details, photos, schools, scores and valuation history, plus rental listings (apartments, houses, townhomes, condos, rooms) and apartment buildings with per-unit availability, and the Zillow Observed Rent Index (ZORI) market rent series by metro, city, county or ZIP from Zillow Research.

| Capability | Credits | Use |
| --- | --- | --- |
| `properties/building` | 5 | Details and unit availability for one building URL from rental_search (is_building = true). Single homes and units use rental. |
| `properties/comparables` | 5 | Zillow home valuation comparables, distinct from nearby homes. |
| `properties/locations` | 5 | Resolve text into region or other typed suggestions. Results vary by type and do not include a bounding box; pass region_id (or region_ids[… |
| `properties/map` | 5 | Property/building clusters in a small map viewport (at most 0.1 degrees per axis). Each card carries only what Zillow's safelisted map docu… |
| `properties/nearby` | 5 | Nearby property cards, including off-market homes. |
| `properties/price_history` | 5 | Public listing and sale price events, timestamps and changes. |
| `properties/property` | 5 | Property facts, original photos, price/tax history, schools and nearby homes; optionally fetch scores and valuation data in the same sessio… |
| `properties/rental` | 5 | Details for one rental identified by zpid or /homedetails/ URL from rental_search (is_building = false). For apartment communities use buil… |
| `properties/rental_search` | 5 | Discovery of rentals by area and filters; pass next_cursor back as cursor for later pages. Use rental for one listing and building for one … |
| `properties/schools` | 5 | Nearby and assigned schools remain distinct, with ratings, grade levels and distance in miles. |
| `properties/scores` | 5 | Walk, transit and bike scores; unavailable scores are null. |
| `properties/search` | 5 | Find for-sale listings in a region or a map box. Chain from locations: pass its region_id (or region_ids[0]) as region_id and its region_ty… |
| `properties/tax_history` | 5 | Tax payment and assessed-value history with provider timestamps. |
| `properties/value_history` | 5 | Named valuation chart series. Point timestamps are Unix milliseconds; null values remain null. |
| `properties/zori` | 5 | Market-level rent index questions (median asking rent over time, YoY rent change for a metro/city/county/ZIP). Not for individual listings:… |

Also in this category: [National Weather Service API (api.weather.gov)](#p-api-weather-gov), [ArcGIS public GIS layers](#p-arcgis-com), [NYC Open Data property records (ACRIS, PLUTO, DOB)](#p-data-cityofnewyork-us), [Element 84 Earth Search (Sentinel-2 L2A)](#p-earth-search-aws-element84-com), [NOAA National Hurricane Center (nhc.noaa.gov)](#p-nhc-noaa-gov), [NASA POWER](#p-power-larc-nasa-gov), [ACIS (NOAA Regional Climate Centers)](#p-rcc-acis-org), [USFS Wildfire Risk to Communities](#p-wildfirerisk-org)

## research

Scientific papers, abstracts, relevant full-text passages and citation relationships.

<a id="p-firecrawl-research-index"></a>

### Research Index (`firecrawl-research-index`)

Find scientific papers, inspect metadata, read relevant passages and follow citation relationships.

| Capability | Credits | Use |
| --- | --- | --- |
| `inspect` | 0 | Read a paper's metadata and abstract without retrieving full text. |
| `read` | 0 | Retrieve paper passages relevant to a question. Empty passages do not mean the full paper was read. |
| `related` | 0 | Find similar work, papers citing a seed or its references, ranked for your research question. |
| `search` | 0 | Find scientific papers about a research question, then use indexed paperIds for follow-up calls. |

## restaurants

Restaurant locations, opening hours, menus, prices and product options.

<a id="p-dominos-ca"></a>

### Domino's Canada (`dominos-ca`)

Public Canadian store directory, nearby locations, profiles and complete store-specific menus. Read-only; no order placement.

| Capability | Credits | Use |
| --- | --- | --- |
| `restaurants/categories` | 5 | Read the flattened menu category tree and coupon categories for a store. |
| `restaurants/category` | 5 | Read products and priced size/crust variants in a category and its direct subcategories. |
| `restaurants/directory` | 5 | List Canadian stores from the public national directory: store ID, city, province and page URL. |
| `restaurants/menu` | 5 | Read the whole structured store menu: categories, products, variants, modifier tables and coupons. |
| `restaurants/modifiers` | 5 | Read full sizes, crusts, toppings, sides, cooking instructions and priced variants for a product. |
| `restaurants/store` | 5 | Read one store profile, hours, payment methods, waits and service capabilities. |
| `restaurants/stores` | 5 | Find Canadian stores near latitude and longitude; returns address, hours, availability and waits. |

<a id="p-dominos-com"></a>

### Domino's US (`dominos-com`)

Public US store lookup, menus, product customization and published delivery fees.

| Capability | Credits | Use |
| --- | --- | --- |
| `restaurants/categories` | 5 | List menu categories for one US store. |
| `restaurants/category` | 5 | Read category products and direct subcategories for one store. |
| `restaurants/delivery_cost` | 5 | Read the published store delivery fee and minimum in USD. Does not validate an address or create an order. |
| `restaurants/menu` | 5 | Read the complete store menu, variants, modifiers, preconfigured (ready-made) SKUs and coupons in one request. Topping cost is in each vari… |
| `restaurants/modifiers` | 5 | Read product sizes, bases, toppings, sides and cooking options. |
| `restaurants/store` | 5 | Read public store details, availability and hours. |
| `restaurants/stores` | 5 | Find US stores near a postal code or city and state, nearest first with the distance in miles. Returns the fixed nearest set Domino's publi… |

<a id="p-littlecaesars-com"></a>

### Little Caesars US (`littlecaesars-com`)

Little Caesars (littlecaesars.com) US store finder, store details, store-scoped menus with prices, item modifiers and toppings, create-your-own pizza options, ordering time slots and national/market promo deals, from the anonymous ordering BFF the order.littlecaesars.com app uses.

| Capability | Credits | Use |
| --- | --- | --- |
| `restaurants/get_custom_pizza_options` | 5 | Build-your-own pricing and the complete topping catalogue for a store. Pass `crust_id` to keep the answer small; the whole menu is about 10… |
| `restaurants/get_deals` | 5 | Deals and promo codes; combine with `dma_code` from `search_stores`/`get_store` or pass `zip`. Not store-scoped menu prices: use `get_menu`… |
| `restaurants/get_menu` | 5 | Menu listing for a store from `search_stores`. Prices and the item set differ per store and per service method; there is no national menu. … |
| `restaurants/get_menu_item` | 5 | Modifiers for an `item_id` from `get_menu` (items with `has_customizations` true carry options or toppings). |
| `restaurants/get_ordering_hours` | 5 | Availability of a store for a service method; an empty day list for an existing store means it is not taking orders. |
| `restaurants/get_store` | 5 | After `search_stores`, or when the caller already knows the store number from a littlecaesars.com/en-us/store/{n}/ URL. |
| `restaurants/search_stores` | 5 | Start here to get a `location_number`; every menu function needs one. |

<a id="p-marcos-com"></a>

### Marco's Pizza (`marcos-com`)

Marco's Pizza (marcos.com) store finder and location-specific menus: categories, items, sizes and prices, toppings and modifiers, coupons and live wait times from the public ordering data files and API.

| Capability | Credits | Use |
| --- | --- | --- |
| `restaurants/deals` | 5 | For the Hot Deals / Value Menu / Catering Bundles categories, which menu lists without items. Defaults to the public, currently valid coupo… |
| `restaurants/item` | 5 | After menu, with an item_id from it, when the caller needs toppings and customization prices for one product. |
| `restaurants/menu` | 5 | After stores. Omit category for the whole menu (about 100 items), or pass a category id or name for a slice. Deal categories hold coupons, … |
| `restaurants/store` | 5 | One Marco's Pizza store by store key: identity, address, coordinates, weekly hours, order types with delivery charge and minimum, delivery … |
| `restaurants/stores` | 5 | Start here to find a store_key; menu, item, deals, store and wait_times need one. The source publishes the whole location list in one page,… |
| `restaurants/wait_times` | 5 | Live availability for one store_key; the menu itself does not change with it. |

<a id="p-pizzahut-ca"></a>

### Pizza Hut Canada (`pizzahut-ca`)

Canadian Pizza Hut store, menu, builder and promotion data from the public Yum storefront.

| Capability | Credits | Use |
| --- | --- | --- |
| `restaurants/bundles` | 5 | Read deal bundles, optionally selected by code. |
| `restaurants/categories` | 5 | Read the store menu category index. |
| `restaurants/category` | 5 | Read items in one category and optional subcategories. |
| `restaurants/directory` | 5 | List Pizza Hut Canada stores, optionally by province, walking the source connection. |
| `restaurants/menu` | 5 | Read the full menu query with deduplicated products, variants and bundles. Products and variants are paginated (default and maximum 10 each… |
| `restaurants/modifiers` | 5 | Read a product builder with variants, slots, modifiers and prices. |
| `restaurants/promotions` | 5 | Read public promotions and their requirements and effects. |
| `restaurants/store` | 5 | Read one store profile, address, occasions and service hours. |
| `restaurants/stores` | 5 | Find nearby and delivering Pizza Hut Canada stores by coordinates or postal anchor. |

<a id="p-pizzahut-com"></a>

### Pizza Hut US (`pizzahut-com`)

Discover Pizza Hut US stores and read menus, products, modifiers, bundles and the paginated store directory.

| Capability | Credits | Use |
| --- | --- | --- |
| `restaurants/bundles` | 5 | Read Pizza Hut US bundles and their choices; optionally filter by bundle codes. For online deals and prices, keep only bundles whose redeem… |
| `restaurants/categories` | 5 | List menu categories and subcategories for a Pizza Hut US store, with the first item in each. |
| `restaurants/category` | 5 | Read products, variants and bundles in a Pizza Hut US menu category. For online deals and prices, keep only bundles whose redeemable_online… |
| `restaurants/directory` | 5 | Page through the Pizza Hut US store directory, optionally filtered by state. Resume with next_cursor when has_more is true. |
| `restaurants/modifiers` | 5 | Read a Pizza Hut US product with variants, options, modifier slots, weights and prices. |
| `restaurants/store` | 5 | Read one Pizza Hut US store, including address, hours, order availability and tax configuration. |
| `restaurants/stores` | 5 | Discover nearby Pizza Hut stores and their store numbers, addresses, hours and supported occasions. |

<a id="p-sevenrooms"></a>

### SevenRooms reservations (`sevenrooms`)

Look up a public SevenRooms venue and observe bookable reservation slots. Never creates bookings or holds.

| Capability | Credits | Use |
| --- | --- | --- |
| `reservations/availability` | 5 | Observe bookable SevenRooms slots for one local service date and party size. Excludes request-only placeholders. Optional exact local time … |
| `reservations/venue` | 5 | Look up public venue identity, address, phone and IANA timezone by known venue URL key. Australia validated; other countries unverified. |

Also in this category: [USDA FoodData Central (fdc.nal.usda.gov)](#p-fdc-nal-usda-gov), [Resy](#p-resy-com)

## shopping

Products, prices, sizes, availability and customer reviews.

<a id="p-allbirds-com"></a>

### Allbirds (`allbirds-com`)

Explore Allbirds collections, product suggestions, size-level offers and published materials/care details.

| Capability | Credits | Use |
| --- | --- | --- |
| `products/collections` | 5 | List curated collection links from the Allbirds US homepage. Partial discovery, not every archived collection. |
| `products/details` | 5 | Read substantive product design, materials, sustainability and care sections. Unsupported layouts fail closed. |
| `products/product` | 5 | Read the canonical product profile and source-labelled offer currency; stock is a source snapshot. |
| `products/products` | 5 | Browse one Allbirds collection page. Follow next_page with the same collection and limit; prices are omitted until product details supply c… |
| `products/search` | 5 | Find predictive product suggestions for a query. Up to ten results; this is not exhaustive or paginated search. |
| `products/variants` | 5 | Compare published sizes, SKUs, color labels and size-level prices and stock for one product. |

<a id="p-amazon-com"></a>

### Amazon US (`amazon-com`)

Amazon US public product details, photos, specifications, variants, displayed review totals, individual customer reviews with rating distribution, search, suggestions, Best Sellers lists, featured offers, sellers, stock and batch prices.

| Capability | Credits | Use |
| --- | --- | --- |
| `products/bestsellers` | 5 | Rank products in an Amazon US category (top sellers in headphones, books, toys) without a search query. Pair with product or specifications… |
| `products/offer` | 5 | Get the featured buy-box offer for one Amazon.com ASIN or product URL: displayed price, list price and savings, boolean in-stock state with… |
| `products/photos` | 5 | Get the selected product image gallery. |
| `products/prices` | 5 | Check current buy-box price and stock state for up to five Amazon.com ASINs in one call. Each row carries price, list price, in-stock flag,… |
| `products/product` | 5 | Get public Amazon product details, displayed price, images, variants and review totals. |
| `products/review_summary` | 5 | Get the displayed rating and count; individual review text is not included. |
| `products/reviews` | 5 | What buyers say about a product or book: individual review text, stars, dates, verified purchase and the rating distribution, from the publ… |
| `products/search` | 5 | Fetch one search page. Next-page input is returned; blocked pages raise an error. |
| `products/specifications` | 5 | Get product specification tables (including detail-bullet lists for books and media), best sellers rank per category, and feature bullets. |
| `products/suggestions` | 5 | Get autocomplete suggestions for a search prefix. |
| `products/variants` | 5 | List the variant dimensions (color, size, style...) and sibling ASINs of an Amazon.com product, with the swatch availability flag Amazon re… |
| `products/variations` | 5 | List product variants and their attributes. Availability and prices require a separate lookup. |

<a id="p-arditicollection-com"></a>

### Arditi Collection (`arditicollection-com`)

Arditi Collection (arditicollection.com) luxury furniture catalogue: collections, product listings, product detail with USD prices and specifications, predictive search and recommendations from the public Shopify storefront JSON routes.

| Capability | Credits | Use |
| --- | --- | --- |
| `products/get_product` | 5 | Detail for a handle returned by any listing or search function, or a pasted product URL. A 0.00 price means the store sells on quote (price… |
| `products/get_recommendations` | 5 | After get_product or a listing supplied a numeric id. An unpublished or unknown id is not_found; an empty list is a legitimate 'no recommen… |
| `products/list_collection_products` | 5 | Browse a category by handle (from list_collections) or a pasted collection URL. Shopify throttles this feed per exit IP with 429/retry-afte… |
| `products/list_collections` | 5 | Start here to discover collection handles for list_collection_products; 219 collections fit in one page at limit 250. |
| `products/list_products` | 5 | Bulk catalogue pulls (about 930 products, 4 pages at limit 250). Never throttled in the capture; prefer it over collection feeds for full e… |
| `products/search_products` | 5 | Find products by keyword. Shopify pads a no-match query with unrelated fallback products; those are removed and counted in dropped. For exh… |

<a id="p-auctions-yahoo-co-jp"></a>

### Yahoo! Auctions Japan (`auctions-yahoo-co-jp`)

Yahoo! Auctions (ヤフオク!) open and closed listing search with sold-price statistics, item detail with shipping fees and related items, seller profiles, category/brand/price facets and keyword suggestions, from the site's own JSON API.

| Capability | Credits | Use |
| --- | --- | --- |
| `listings/category_facets` | 5 | To discover category ids to pass to search, or to see brand and price distribution for a category or keyword. |
| `listings/item` | 5 | Full detail for an auction id from search or a pasted auctions.yahoo.co.jp / page.auctions.yahoo.co.jp listing URL. |
| `listings/search` | 5 | Start here to find auction ids (then call item) or to get sold-price history for a keyword. Provide at least one of query, category_id or s… |
| `listings/seller` | 5 | After search or item returned a seller user_id and you need the seller's rating or profile. |
| `listings/suggest` | 5 | Before search when the exact Japanese term is unknown; an unknown prefix legitimately returns no keywords. |

<a id="p-authenticvintageposters-com"></a>

### Authentic Vintage Posters (`authenticvintageposters-com`)

Catalogue of original vintage posters, prints, labels and ads sold by Authentic Vintage Posters (Shopify storefront): product listing, search, collections and product detail with artist, size and condition.

| Capability | Credits | Use |
| --- | --- | --- |
| `products/get_collection` | 5 | Check that a collection handle exists and how many products it holds before paging through it. Unknown handles are not_found. |
| `products/get_product` | 5 | You have a product handle or URL (from list_products, search_products, list_collection_products or a pasted link) and want its full record.… |
| `products/list_collection_products` | 5 | Browse a decade (1930s), style (art-nouveau), price band (100-249) or subject collection; handles come from list_collections. Follow next_p… |
| `products/list_collections` | 5 | Discover collection handles before calling list_collection_products or get_collection. About 420 collections; page through with next_page. |
| `products/list_products` | 5 | Browse or export the full catalogue without a search term; follow next_page until it is null. For one known product use get_product; for a … |
| `products/search_products` | 5 | Find products by artist, subject, title words or keywords (e.g. mucha, cognac, ski). Zero matches is a legitimate empty result. Follow next… |

<a id="p-autotrader-com"></a>

### Autotrader (`autotrader-com`)

Autotrader.com (Cox Automotive) US vehicle marketplace: search new, used and certified listings by location, make/model, year, price, mileage or one dealership (by dealer id or dealer website domain, with the dealer's new/used/certified inventory counts); read one listing with pricing, specifications, features and seller; resolve make/model names to codes; facet counts by model year, trim and cit…

| Capability | Credits | Use |
| --- | --- | --- |
| `vehicles/get_listing` | 5 | After search_listings, or when the user pastes an autotrader.com/cars-for-sale/vehicle/{id} URL or a VIN. |
| `vehicles/listing_facets` | 5 | To see which years, trims or cities have inventory before searching, or to pick a trim_code for search_listings. |
| `vehicles/search_listings` | 5 | Discovering vehicles for sale in the US, or reading one dealership's Autotrader inventory and its new/used/certified counts by dealer_id or… |
| `vehicles/suggest_make_model` | 5 | Before search_listings or listing_facets when you have a make/model name rather than codes. |
| `vehicles/vehicle_specs` | 5 | After get_listing or search_listings, to read the manufacturer specifications behind a listing. |

<a id="p-bestbuy-com"></a>

### Best Buy US (`bestbuy-com`)

Public Best Buy US catalog, product details, prices, customer reviews and location-specific availability.

| Capability | Credits | Use |
| --- | --- | --- |
| `products/availability` | 5 | Get shipping, delivery and pickup promises for a SKU, ZIP code and store. pickup_summary gives each pickup record an explicit available, un… |
| `products/pricing` | 5 | Get displayed US pricing, condition and mobile-contract terms. |
| `products/product` | 5 | Get public Bestbuy product details, displayed price, images, variants and review totals. |
| `products/review_summary` | 5 | Get the displayed rating and count; individual review text is not included. |
| `products/reviews` | 5 | Page through all customer reviews of one Best Buy US product (SKU or product/review URL), 20 per source page, via the endpoint Best Buy's o… |
| `products/search` | 5 | Fetch one search page. Next-page input is returned; blocked pages raise an error. |
| `products/stores` | 5 | Find nearby open Best Buy stores by US ZIP code with names, street addresses, dated sales hours and distances in miles; use store_id for av… |
| `products/suggestions` | 5 | Get autocomplete suggestions for a search prefix. |
| `products/variations` | 5 | List product variants and their attributes. Availability and prices require a separate lookup. |

<a id="p-bid-cars"></a>

### bid.cars (`bid-cars`)

bid.cars, a public aggregator of US salvage and insurance auction lots from Copart and IAAI: active-lot search with the site's filters, sort and 50-per-page pagination, one lot's detail page (vehicle data, damage, documents, bidding state, sales history), the public sold comparables for a lot (the only anonymous source of final prices), and the make/model taxonomy with active lot counts. Anonymou…

| Capability | Credits | Use |
| --- | --- | --- |
| `vehicles/get_lot` | 5 | Read one lot in full after `search_lots`, or from a VIN or a bid.cars lot URL. |
| `vehicles/makes_models` | 5 | Discover valid `make` / `model` / `vehicle_type` values for `search_lots`, or count active lots per model. |
| `vehicles/search_lots` | 5 | Browse or filter lots currently at auction; find the lot id or VIN for `get_lot` and `similar_sold_lots`. |
| `vehicles/similar_sold_lots` | 5 | Price a lot against recent sales after `search_lots` or `get_lot`. |

<a id="p-cargurus-com"></a>

### CarGurus (`cargurus-com`)

CarGurus.com US used-car marketplace: search listings within a radius of a ZIP code (make/model/trim, price, year, mileage, body style, transmission, 11 sort orders, paginated), read one listing's full detail (price analysis, history, specifications, dealer), resolve free text to make/model/trim ontology ids, list makes and models, and read owner reviews for a model.

| Capability | Credits | Use |
| --- | --- | --- |
| `vehicles/get_listing` | 5 | After search_listings, to read the full record of one vehicle. Also accepts a pasted https://www.cargurus.com/details/{id} URL. |
| `vehicles/list_makes` | 5 | To enumerate makes or find a make's id for list_models and search_listings. |
| `vehicles/list_models` | 5 | After list_makes or suggest_vehicles, to pick the model entity_id for search_listings or model_owner_reviews. |
| `vehicles/model_owner_reviews` | 5 | Research on a model's owner satisfaction, keyed by the model_id of a search result or suggestion. |
| `vehicles/search_listings` | 5 | Finding used vehicles for sale near a US ZIP code, comparing prices against CarGurus' market value, or enumerating trims and counts for a m… |
| `vehicles/suggest_vehicles` | 5 | To turn a vehicle name typed by a user into the entity_id / make_model_trim_paths that search_listings and model_owner_reviews take. |

<a id="p-christies-com"></a>

### Christie's (`christies-com`)

Christie's auction lots and sales: keyword search of sold and upcoming lots with estimates and prices realised, sale search, sale headers with totals, full sale catalogues and lot detail pages, from christies.com's own anonymous APIs.

| Capability | Credits | Use |
| --- | --- | --- |
| `auction-lots/get_auction` | 5 | A known sale id (from search_lots `sale.sale_id`, get_lot `sale.sale_id`) or a christies.com/en/auction/ URL. |
| `auction-lots/get_lot` | 5 | Full record of a lot found through search_lots or list_auction_lots (numeric `object_id`), or a pasted christies.com/en/lot/lot-… URL. Onli… |
| `auction-lots/list_auction_lots` | 5 | Full catalogue or results of a sale whose sale_id, sale_number and sale_room_code you have (get_auction returns all three). |
| `auction-lots/search_auctions` | 5 | Find a sale by name, collection or keyword; then get_auction with the returned `url` for its header and lot count. |
| `auction-lots/search_lots` | 5 | Find lots by artist, title or keyword across all Christie's sales; refine with the `filter_groups` option ids. Use get_lot for full details… |

<a id="p-dell-com"></a>

### Dell (`dell-com`)

Dell.com storefront and support: keyword search of the shop (offer ids, platform codes, prices, ratings, hero specs), the exact configured tech specs of one offer id, the support product catalog, the manuals and documents list of a support product, and owner's manual chapters with their specification tables.

| Capability | Credits | Use |
| --- | --- | --- |
| `product-specifications/manual_chapter` | 5 | After support_documents gave you a book_id and a guid, read a chapter; use the returned toc to find the guid of 'Keyboard', 'External ports… |
| `product-specifications/search_products` | 5 | Find the offer_id (e.g. pb16250_fixed_20) and platform code for a model number or product name; then call tech_specs with the offer_id. Pas… |
| `product-specifications/support_documents` | 5 | Given a support product code (from support_search) or a shop platform code (from search_products, lowercased), list the owner's manual, set… |
| `product-specifications/support_search` | 5 | Turn a model number or product name (PB16250, XPS 13 9310, Latitude 5550) into a support product code such as dell-pro-pb16250-laptop. Zero… |
| `product-specifications/tech_specs` | 5 | You have an offer_id from search_products (or a Dell product URL ending in /spd/{platform}/{offer_id}) and need the manufacturer's current … |

<a id="p-discogs-com"></a>

### Discogs (`discogs-com`)

Public Discogs music releases, masters, artists and labels with search and paginated catalogs.

| Capability | Credits | Use |
| --- | --- | --- |
| `releases/artist` | 5 | One Discogs artist or group by artist ID: name, real name, profile text, name variations, aliases, members (for groups) or groups (for peop… |
| `releases/artist_releases` | 5 | Releases by an artist (their discography as Discogs credits it), one page at a time: masters and standalone releases with role (Main, Remix… |
| `releases/label` | 5 | One Discogs label by label ID: name, profile, contact info, parent label, sublabels, external URLs and images. |
| `releases/label_releases` | 5 | A label's catalog, one page at a time: every release on the label with its catalog number, artist, title, format and year, in Discogs' cata… |
| `releases/master` | 5 | One Discogs master release (the grouping of all pressings of the same album or single) by master ID: title, artists, original year, main an… |
| `releases/master_versions` | 5 | Pressing variants of a master release: every release (country, label, catalog number, format, year) grouped under the master, one page at a… |
| `releases/release` | 5 | One Discogs release (a specific pressing or edition) by release ID: artists, labels with catalog numbers, companies and pressing plants, fo… |
| `releases/search` | 5 | Search the Discogs database for releases, masters, artists or labels by free text, artist, release title, track, label, catalog number or b… |

<a id="p-ebay-com"></a>

### eBay listings (`ebay-com`)

eBay.com listings through the site's item-module JSON: item detail, variations, shipping and returns terms, and search autosuggest. Keyword search, sold listings and seller pages are HTML behind Akamai/orch and are not offered. Public US marketplace (www.ebay.com, USD), anonymous session, no bidding or purchases.

| Capability | Credits | Use |
| --- | --- | --- |
| `listings/item` | 5 | You have an item number or /itm/ URL and want its current listing data without loading the HTML page. |
| `listings/item_shipping` | 5 | You need the shipping service, delivery estimate, ships-to list or returns policy of a listing. |
| `listings/item_variations` | 5 | The item has variations (item.has_variations) and you need per-SKU prices and availability. |
| `listings/suggest` | 5 | Expand a partial product query into the keywords eBay proposes before searching. |

<a id="p-etsy-com"></a>

### Etsy (`etsy-com`)

Etsy marketplace listings: listing details and prices, per-variation pricing, similar listings, shop sections and search query suggestions from Etsy's public ajax JSON API. Keyword search, shop listing enumeration and reviews are DataDome-gated and not available.

| Capability | Credits | Use |
| --- | --- | --- |
| `listings/listing` | 5 | You have a listing id or an etsy.com/listing/{id}/ URL. Use similar_listings for discovery, listing_variations for option prices, shop_sect… |
| `listings/listing_variations` | 5 | A listing shows has_variation_pricing or you need the option values a buyer can pick. Needs a listing id from listing or similar_listings. |
| `listings/search_suggestions` | 5 | Expand or normalize a shopping query before looking for listings elsewhere. Keyword search itself is not available from this program. |
| `listings/shop_sections` | 5 | You have a shop_id from a listing and want the shop's catalog structure and active listing counts. |
| `listings/similar_listings` | 5 | Fan out from one known listing to related listings. Etsy keyword search is DataDome-gated and not available; use search_suggestions for que… |

<a id="p-fanatics-com"></a>

### Fanatics US (`fanatics-com`)

Fanatics US (www.fanatics.com) licensed sports merchandise: product search, league/team/department listings with facets, product detail with per-size stock and prices, and the team directory of a league, from the storefront's server-rendered page data and its Iris data API.

| Capability | Credits | Use |
| --- | --- | --- |
| `products/get_product` | 5 | Use after search_products or list_products with a result's product_id, or when the user pastes a www.fanatics.com product URL. Inventory co… |
| `products/list_products` | 5 | Use when the user wants a team's or league's gear or a department within it. league_id comes from a search facet (type o), team_id from lis… |
| `products/list_teams` | 5 | Use to turn a league into team ids for list_products. League ids come from the Leagues facet of search_products (23 = NBA, 25 = NFL, 19 = M… |
| `products/search_products` | 5 | Start here when the user names a product, player or team in free text. Follow a result's product_id into get_product for sizes and stock, o… |

<a id="p-hertzcarsales-com"></a>

### Hertz Car Sales (`hertzcarsales-com`)

Hertz Car Sales (hertzcarsales.com), the US used-car retail arm of Hertz: search the used and Rent2Buy inventories by make, model, body style, fuel, state, ZIP radius, year, mileage and price with pagination; read one vehicle by VIN, vehicle id or URL with full specifications; list facet values and counts for a filter set; natural-language inventory search; Buy Online availability and payment est…

| Capability | Credits | Use |
| --- | --- | --- |
| `vehicles/check_availability` | 5 | After search_inventory, to confirm a vehicle is still available before pointing a user at it, or to get a payment estimate. |
| `vehicles/get_vehicle` | 5 | After search_inventory or suggest_inventory, or when the user pastes a hertzcarsales.com/used/... or /rent2buy/... URL or a VIN. |
| `vehicles/list_facets` | 5 | To discover what exists before searching (which makes, which states have stores, the price range), or to narrow a large result set. |
| `vehicles/search_inventory` | 5 | Start here to find vehicles; pass next_cursor back as cursor for the following page. Use list_facets to see which makes, models, states and… |
| `vehicles/suggest_inventory` | 5 | To turn a user's phrase into make/model facets for search_inventory, or for a quick first look at matching cars. |

<a id="p-hibid-com"></a>

### HiBid (`hibid-com`)

HiBid (hibid.com), the North American online auction platform used by thousands of auction houses: search lots by keyword, auction, category, region or archive (hammer prices), read one lot with pictures and terms, its bid history and live bid state, search current and past auctions, read one auction's terms and bid increments, and look up auctioneers. Anonymous public GraphQL API; auctioneer sub…

| Capability | Credits | Use |
| --- | --- | --- |
| `online-auctions/auction` | 5 | After `search_auctions` or `search_lots`, or when given a hibid.com/catalog/{id} URL. Use `search_lots` with auction_id for the lots. |
| `online-auctions/auctioneers` | 5 | To find an auctioneer_id for `search_auctions`, or to resolve an auctioneer subdomain (its site id) to the company record. |
| `online-auctions/lot` | 5 | After `search_lots`, or when given a hibid.com/lot/{id} URL. |
| `online-auctions/lot_bids` | 5 | To see how a lot is being bid on. Bidder names are masked by HiBid; this function does not place bids. |
| `online-auctions/search_auctions` | 5 | To find auction ids for `auction` and `search_lots` (catalog listing), to list one auctioneer's auctions (auctioneer_id, e.g. 87212 for cit… |
| `online-auctions/search_lots` | 5 | Start here to find lot ids (for `lot` and `lot_bids`) and auction ids, or to list one auction's catalog (auction_id, sort LOT_NUMBER). For … |

<a id="p-ikea-com"></a>

### IKEA (`ikea-com`)

IKEA category discovery, product specifications and advertised prices in the market's own currency, variants, materials, care, safety documents and review excerpts for any IKEA market on www.ikea.com (91 country/language storefronts in 50 countries). No store stock or delivery availability.

| Capability | Credits | Use |
| --- | --- | --- |
| `products/discover` | 5 | Discover product cards on the first page of an IKEA category in any IKEA market on www.ikea.com (/{country}/{language}/ storefronts such as… |
| `products/materials_care` | 5 | Read component materials and care instructions of an IKEA product in any IKEA market on www.ikea.com (/{country}/{language}/ storefronts su… |
| `products/product` | 5 | Read an IKEA product article in any IKEA market on www.ikea.com (/{country}/{language}/ storefronts such as /us/en/, /gb/en/, /de/de/, /ae/… |
| `products/reviews` | 5 | Read review excerpts embedded on an IKEA product page in any IKEA market on www.ikea.com (/{country}/{language}/ storefronts such as /us/en… |
| `products/safety_documents` | 5 | Read IKEA product safety warnings and links to assembly or care PDFs in any IKEA market on www.ikea.com (/{country}/{language}/ storefronts… |
| `products/variants` | 5 | Read source-linked color/style alternatives of an IKEA product in any IKEA market on www.ikea.com (/{country}/{language}/ storefronts such … |

<a id="p-ironplanet-com"></a>

### IronPlanet (`ironplanet-com`)

IronPlanet (Ritchie Bros.) used heavy equipment and truck marketplace: category/make listings with filters, sort and pagination, keyword suggestions, the anonymous item preview (photos, features, serial, meter), upcoming online auctions per realm and one auction's lots.

| Capability | Credits | Use |
| --- | --- | --- |
| `equipment-auctions/get_equipment_preview` | 5 | Fetch what the site exposes anonymously for an item found with `list_equipment` or `list_auction_lots`. |
| `equipment-auctions/list_auction_lots` | 5 | List the lots of an auction found with `list_upcoming_auctions`. |
| `equipment-auctions/list_equipment` | 5 | Browse or filter equipment for sale by category or make; discover filter values via `include_facets`; paginate with `continuation`. |
| `equipment-auctions/list_upcoming_auctions` | 5 | Find the sale group ids of upcoming online auctions before listing their lots. |
| `equipment-auctions/suggest` | 5 | Turn a free-text equipment keyword into the category slug / make filter that `list_equipment` needs. |

<a id="p-jlcpcb-com"></a>

### JLCPCB parts library (`jlcpcb-com`)

Search the JLCPCB SMT assembly parts library (LCSC catalogue) by keyword, C-number, manufacturer part number or category; read one part's stock, assembly and purchase price breaks, package, basic/extended type, attributes and datasheet; list the two-level category taxonomy; and get search-box suggestions. Read-only, anonymous, USD prices as served to US visitors.

| Capability | Credits | Use |
| --- | --- | --- |
| `electronic-components/get_part` | 5 | After search_parts, or when the caller already has a C-number, MPN or a JLCPCB part URL. |
| `electronic-components/list_categories` | 5 | Discover category names and ids before a category search. |
| `electronic-components/search_parts` | 5 | Find candidate parts for a keyword, part number or category; page through a category; then call get_part with a returned component_code for… |
| `electronic-components/suggest_parts` | 5 | Expand a partial part number or keyword before a search. |

<a id="p-kbb-com"></a>

### Kelley Blue Book (`kbb-com`)

US car inventory, listing details, model-year trims and regional Kelley Blue Book valuations.

| Capability | Credits | Use |
| --- | --- | --- |
| `vehicles/book_value` | 5 | Kelley Blue Book value for one vehicle: make, model, year, trim (slug from `trims`, or KBB vehicle_id), mileage and condition. Returns the … |
| `vehicles/listing` | 5 | One kbb.com listing by its numeric listing id (from `listings`): full description, features, every photo URL, seller address and rating, wa… |
| `vehicles/listings` | 5 | Search kbb.com dealer and private-seller inventory for a make (optionally model and trim) within a radius of a US ZIP code, optionally filt… |
| `vehicles/trims` | 5 | Every trim kbb.com prices for a model year (make, model, year): KBB vehicle id, trim slug for `book_value`, Fair Purchase Price, typical-mi… |

<a id="p-landefeld-de"></a>

### Landefeld industrial parts catalogue (`landefeld-de`)

Landefeld Druckluft + Hydraulik (www.landefeld.de): anonymous read access to the German storefront. Full-text and part-number search, catalogue browsing, article-group listings with spec filters and pagination, and article details with net EUR prices, availability, GTIN, specs, documents and images.

| Capability | Credits | Use |
| --- | --- | --- |
| `products/browse_catalog` | 5 | Browsing the catalogue top-down when no search term is known; traversing to the article groups of a branch. |
| `products/get_article` | 5 | Full details for an article number returned by search_articles or list_group_articles, or for a pasted landefeld.de article URL. |
| `products/list_group_articles` | 5 | Listing or filtering the variants of a group id from search_groups, browse_catalog or get_article (e.g. `KH14BE`), e.g. all ball valves of … |
| `products/search_articles` | 5 | Finding a concrete article from a part number or number fragment, e.g. `KH 14 B E` or `KH 14`. Also works for designation words but the ful… |
| `products/search_groups` | 5 | Finding where a kind of part lives in the catalogue from a German description, e.g. `Kugelhahn`, `Steckverschraubung`. For part numbers use… |
| `products/suggest` | 5 | Autocomplete, or discovering the shop's vocabulary before a search_groups call. |

<a id="p-microcenter-com"></a>

### Micro Center US (`microcenter-com`)

Micro Center (microcenter.com) US retail catalog: store-scoped product search, exact SKU lookup with store price and inventory, product detail, the store list and Bazaarvoice reviews.

| Capability | Credits | Use |
| --- | --- | --- |
| `products/get_product` | 5 | One known product id (from search results, a SKU lookup or a microcenter.com/product/ URL). Pass store_id to get that store's price and inv… |
| `products/get_reviews` | 5 | After search_products or get_product, when the review text, ratings or recommendation counts for a product id are needed. |
| `products/list_stores` | 5 | To find the store_id for a city before calling search_products, lookup_by_sku or get_product. |
| `products/lookup_by_sku` | 5 | You know the 6-digit SKU and need the current price/stock at a specific store. Use get_product for specs and reviews, search_products for d… |
| `products/search_products` | 5 | Discovery: find products by keyword or browse a category (e.g. "Graphics Cards\|518") for a given store_id. Use lookup_by_sku for a known S… |

<a id="p-newegg-com"></a>

### Newegg US (`newegg-com`)

Search Newegg US electronics and open-box listings, retrieve live prices, condition and availability for an item, and page through every written customer review of an item.

| Capability | Credits | Use |
| --- | --- | --- |
| `products/open_box` | 5 | Open-box availability on Newegg US for a model number or product keywords: the retailer's Open Box facet, only listings flagged open-box, e… |
| `products/product` | 5 | Live price and stock for one Newegg US item number (N82E16814932771, 14-932-771, open-box variant 14-932-771R, or marketplace 9SIB0GJKJ6064… |
| `products/reviews` | 5 | Every written customer review for a Newegg US item, 100 per page: rating, title, text, pros, cons, public display name, ISO submission time… |
| `products/search` | 5 | Search Newegg US by model number, SKU-like keyword or product name. Returns one page of listings with displayed price, in-stock flag, condi… |

<a id="p-nike-com"></a>

### Nike US (`nike-com`)

Nike US products, prices, sizes, availability and public customer reviews from Nike's own web APIs.

| Capability | Credits | Use |
| --- | --- | --- |
| `products/availability` | 5 | Stock bands per size for one style/color or a product family; no exact inventory counts. |
| `products/product` | 5 | One known style/color or a nike.com/t/ product URL. Use search for discovery, availability for stock only. |
| `products/review_summary` | 5 | Rating histogram and fit/comfort summary for a style; cheaper than paging reviews. |
| `products/reviews` | 5 | One page of recent public reviews; use review_summary for the histogram, review_photos for images. |
| `products/search` | 5 | Search Nike US products with query or browse path. For the first page, provide query or path and optionally count (24, 50 or 100; default 2… |
| `products/suggestions` | 5 | Autocomplete or popular searches; call before search when the query is uncertain. |

<a id="p-play-google-com"></a>

### Google Play Books and Movies & TV (`play-google-com`)

Google Play Books and Movies & TV: search, ebook / audiobook / movie / TV show detail with rating histograms, offers and metadata, every season of a show with the episodes of any season by season id, book series and author pages, paginated user reviews, and the Google Books volume record by ISBN for joins. Logged-out store pages and the store's batchexecute RPC; apps are out of scope.

| Capability | Credits | Use |
| --- | --- | --- |
| `media/audiobook` | 5 | Ratings, metadata and related titles for a Play audiobook id (type `audiobook` in `search`, or `audiobook_id` from `book`). |
| `media/author` | 5 | Bio and works with ratings for a Play author id (`authors[].id` of `book`, or type `author` in `search`). |
| `media/book` | 5 | Ratings, metadata and related titles for a Play Books volume id (also the Google Books volume id). |
| `media/google_books_volume` | 5 | Resolve an ISBN to the Play / Google Books volume id and bibliographic data before calling `book` or `reviews`. |
| `media/movie` | 5 | Ratings and details for a Play movie id from `search`. |
| `media/reviews` | 5 | Read what audiences wrote about a book, film or show on Google Play, page by page. |
| `media/search` | 5 | To find the Play id of a book, film or show before calling `book`, `movie`, `show` or `reviews`. |
| `media/series` | 5 | All books of a series with position, rating and price, from a `book_series` id (`search`) or the `series.series_id` of `book`. |
| `media/show` | 5 | Details, season list and the episodes of one season (default or chosen by `season_id`) for a Play TV show id from `search`. |

<a id="p-prisjakt-nu"></a>

### Prisjakt Sweden (`prisjakt-nu`)

Prisjakt Sweden (prisjakt.nu) price comparison: product search and autocomplete, product detail with every retailer offer, lowest-price history, product and store reviews, and category listings. Prices in SEK from the site's own anonymous GraphQL API.

| Capability | Credits | Use |
| --- | --- | --- |
| `price-comparison/get_price_history` | 5 | Judging whether a current price is a good deal or when a product was cheapest. |
| `price-comparison/get_product` | 5 | Comparing retailer offers and prices for a product found with search_products or suggest. |
| `price-comparison/get_product_reviews` | 5 | Reading what Swedish buyers say about a product; combine with get_product for prices. |
| `price-comparison/get_store` | 5 | Checking a retailer seen in get_product offers before buying. |
| `price-comparison/list_category` | 5 | Browsing a category's products ranked by popularity or price instead of searching by keyword. |
| `price-comparison/search_products` | 5 | Finding Swedish products and their lowest prices by keyword; take `product_id` from `product` items into get_product, get_price_history and… |
| `price-comparison/suggest` | 5 | Resolving a vague or partial product name to concrete product ids or a better search phrase before searching. |

<a id="p-psacard-com"></a>

### PSA (`psacard-com`)

Browse public collectible price-guide categories, sets, grade values and featured dealer profiles. No cert or population lookup.

| Capability | Credits | Use |
| --- | --- | --- |
| `collectibles/categories` | 5 | Browse public PSA price-guide categories. |
| `collectibles/dealer` | 5 | Read one public PSA dealer profile: address, phone, specialties and services. |
| `collectibles/dealers` | 5 | List featured dealers from the public PSA dealer directory, not the complete dealer database. |
| `collectibles/sets` | 5 | List collectible sets within a PSA price-guide category. Offset/limit slice the fetched page. |
| `collectibles/values` | 5 | Read card names and published guide values by grade. Blank cells remain unknown; +/- change markers are retained. These are not offers or r… |

<a id="p-psauction-se"></a>

### PS Auction (`psauction-se`)

PS Auction (psauction.se), Sweden's online auction house for industrial equipment, vehicles, tools, bankruptcy estates and surplus goods: lot search with category, location, auction-type and shipping filters, lot detail, the current and ended auction calendar, one auction's lots or closed results, the filter taxonomy and the smart-search suggester. Read-only, anonymous, from the site's own bidder…

| Capability | Credits | Use |
| --- | --- | --- |
| `auction-lots/get_filters` | 5 | Before search_items, to turn a category name or a town into the item_type_ids or location slug the search takes, or to see how many lots ea… |
| `auction-lots/get_item` | 5 | After search_items or list_auction_items returned an item_number, or when given a https://psauction.se/item/view/{number}/{slug} URL. |
| `auction-lots/list_auction_items` | 5 | Walking a whole auction from list_auctions, or reading an auction's closed results. Use get_item for one lot's full detail. |
| `auction-lots/list_auctions` | 5 | Discovering which auctions (bankruptcy estates, divestments, surplus sales) are open or recently closed on psauction.se before drilling int… |
| `auction-lots/search_items` | 5 | Finding lots by keyword or category on psauction.se, e.g. welding machines, tractors, lots in Skåne, or everything in item type 88 (Verktyg… |
| `auction-lots/suggest` | 5 | Turning a vague or misspelled product word into better search_items queries and categories, or a quick 'what is on offer for X' glance. |

<a id="p-rtings-com"></a>

### RTINGS (`rtings-com`)

RTINGS public-tier lab reviews, buying guides, rankings and tested-product metadata; member-only measurements remain unavailable.

| Capability | Credits | Use |
| --- | --- | --- |
| `tests/guides` | 5 | List the published buying guides ("Best X" recommendation pages), popular reviews and tools for one RTINGS product category, e.g. tv, headp… |
| `tests/products` | 5 | Every product RTINGS has lab-tested in a category, across all methodology (test bench) versions: name, brand, review URL, variant SKUs, rel… |
| `tests/ranking` | 5 | One RTINGS buying guide: the ranked, lab-tested picks for a category (or a sub-guide such as by-size/65-inch), each with the product's publ… |
| `tests/review` | 5 | One RTINGS lab review: the product's public overall score, test bench version, featured test results with measured values and scores, per-u… |

<a id="p-russelcoinc-com"></a>

### Russelco Inc (`russelcoinc-com`)

Russelco Inc (russelcoinc.com): a New Jersey wholesale distributor's public storefront (OTC medicine, personal care, baby, household, snacks; ~940 products, USD) built on the iinvy Next.js platform. Search and browse the catalogue with category, sort, on-sale and wholesale-price options, read one product by UPC with its 'you may also like' items, and walk the category tree. Anonymous and read-onl…

| Capability | Credits | Use |
| --- | --- | --- |
| `products/get_product` | 5 | After search_products, to read one product record and discover related items; or directly for a pasted product URL. |
| `products/list_categories` | 5 | To discover category ids for search_products, or to walk the catalogue by department, product type and brand. |
| `products/search_products` | 5 | Start here to find products by name or brand, to list a category, or to enumerate the catalogue page by page; then call get_product with a … |

<a id="p-shopify"></a>

### Shopify (`shopify`)

Search products across Shopify merchants or within one store, resolve product identifiers and inspect variants through Shopify's UCP catalogs.

| Capability | Credits | Use |
| --- | --- | --- |
| `catalog/get_product` | 5 | Get details, variants and availability for a product_id returned by search or lookup. Optional selected options refine the variant. Does no… |
| `catalog/lookup_catalog` | 5 | Look up 1–50 products using product_ids returned by search, or product URLs. Inspect messages for unmatched identifiers. |
| `catalog/search_catalog` | 5 | Search products across Shopify merchants by query, such as trail running shoes under $150. Narrow results by country and use limit and curs… |
| `storefront/get_product` | 5 | Get details and availability for a product_id from the selected store's search or lookup. Keep the same store_domain. Optional selected opt… |
| `storefront/lookup_catalog` | 5 | Look up 1–10 product_ids within store_domain. Use IDs returned by that store's search, not Global Catalog IDs. Inspect messages for unmatch… |
| `storefront/search_catalog` | 5 | Search products in a Shopify store by store_domain and query, or leave query empty to browse. Use limit and cursor for pagination. The stor… |

<a id="p-sothebys-com"></a>

### Sotheby's (`sothebys-com`)

Sotheby's (sothebys.com) auctions, lots with estimates and realized prices, Buy Now (marketplace) items and the site-wide search over lots, auctions, artists and articles, from the public GraphQL API (clientapi.prod.sothelabs.com) and Algolia search index behind the website.

| Capability | Credits | Use |
| --- | --- | --- |
| `auctions/auction` | 5 | Use after search (an Auction hit's id, or a Lot hit's auction URL) or when the user pastes https://www.sothebys.com/en/buy/auction/{year}/{… |
| `auctions/auction_lots` | 5 | Use with an auction_id from auction or from a search Auction hit to list what is or was offered and what it fetched. Page with offset (next… |
| `auctions/buy_now_item` | 5 | Use when a search hit has type Buy Now (its url is https://www.sothebys.com/en/buy/_{slug}) or when the user pastes such a URL. Not for auc… |
| `auctions/lot` | 5 | Use with a lot_id from auction_lots or a search Lot hit's id, or when the user pastes https://www.sothebys.com/en/buy/auction/{year}/{aucti… |
| `auctions/search` | 5 | Start here for any free-text question (artist, title, sale number, auction name). Filter with type (Lot, Auction, Buy Now, Artist, Article,… |

<a id="p-steelcitycollectibles-com"></a>

### Steel City Collectibles (`steelcitycollectibles-com`)

Steel City Collectibles (www.steelcitycollectibles.com), a US sports-card and trading-card retailer: keyword search, category listings with filters and sort, the group-break room, product detail with USD prices, stock, release dates, images and attributes, and the related-products feed, read from the storefront's server-rendered pages and its JSON routes.

| Capability | Credits | Use |
| --- | --- | --- |
| `products/get_product` | 5 | After search_products, list_category or list_group_breaks with a result's `slug`, or when the user pastes a www.steelcitycollectibles.com/i… |
| `products/list_category` | 5 | Browse a department instead of searching: 'all 2025 baseball boxes and cases, cheapest first'. Take the category slug from a site URL or th… |
| `products/list_group_breaks` | 5 | For live or upcoming group breaks rather than sealed product. Each result is a product; get_product with its `slug` has the full descriptio… |
| `products/related_products` | 5 | After get_product or a listing, with the numeric product `id`, to find the case/box/pack siblings and similar products. |
| `products/search_products` | 5 | Start here for a product or set name ('2025 topps chrome baseball', 'pokemon prismatic evolutions'). Follow with get_product using a result… |

<a id="p-stockx-com"></a>

### StockX (`stockx-com`)

StockX marketplace data from its own GraphQL gateway: product search and category browse, per-size market state (lowest ask, highest bid, last sale, statistics), recent sales and the ask/bid order book. US and GB markets.

| Capability | Credits | Use |
| --- | --- | --- |
| `products/browse_options` | 5 | Look up valid sort ids and brand aliases before calling search_products or browse_products. |
| `products/browse_products` | 5 | Walk a catalogue slice by category, brand, size, price range or gender instead of free text. Filter ids and values come from the `filters` … |
| `products/get_price_levels` | 5 | Market depth for a product or one size variant. transaction_type ASK lists sell offers, BID lists buy offers. Paginate with page while next… |
| `products/get_product` | 5 | Price and market check for one known product. Use search_products or browse_products to find the url_key; use the variant ids here for size… |
| `products/get_sales` | 5 | Recent sale prices for a product or one size. The site exposes only the most recent `first` sales; there is no older-page cursor through th… |
| `products/search_products` | 5 | Find products and their url_key by keyword. Then call get_product for market data per size, get_sales for recent sales or get_price_levels … |

<a id="p-target-com"></a>

### Target (`target-com`)

Discover featured Target US products, inspect product specifications and child variant options, and read every public customer review of a product with a resumable cursor. No search, price or inventory coverage.

| Capability | Credits | Use |
| --- | --- | --- |
| `products/featured` | 5 | Discover the limited set of product links featured on the Target US homepage; not a searchable or exhaustive catalog. |
| `products/product` | 5 | Read a known Target product URL: brand, descriptive specifications, highlights, image and published return-policy text. Price and availabil… |
| `products/reviews` | 5 | Use for review text and ratings of a known Target product (url or tcin from featured or variants). To sync incrementally, call with sort=ne… |
| `products/variants` | 5 | List child product identifiers, option combinations and images from a Target parent product page. Follow child URLs for specifications. Cat… |

<a id="p-tiendanube-com"></a>

### Tiendanube / Nuvemshop stores (`tiendanube-com`)

Product catalogues, prices, stock, variants and categories from any Tiendanube (Nuvemshop in Brazil) store, read from its public storefront pages and sitemap while respecting the store's robots.txt. Input is the store's domain or any URL on it; pages are verified to be Tiendanube storefront pages.

| Capability | Credits | Use |
| --- | --- | --- |
| `products/get_product` | 5 | Details, variants (sizes/colours) and per-variant price or stock of one product in a Tiendanube / Nuvemshop store, e.g. from a pasted produ… |
| `products/list_categories` | 5 | Navigate a Tiendanube store's catalogue and find the category path to pass to list_products. |
| `products/list_products` | 5 | Catalogue, new products (sort created-descending), prices or stock of a store on Tiendanube / Nuvemshop (*.mitiendanube.com, *.lojavirtualn… |

<a id="p-traderjoes-com"></a>

### Trader Joe's (`traderjoes-com`)

Trader Joe’s public store finder, store-specific product search and product nutrition, ingredients and allergens.

| Capability | Credits | Use |
| --- | --- | --- |
| `products/product` | 5 | One Trader Joe's product by SKU as published for a store: price, size, availability, description, category path, images, full nutrition fac… |
| `products/search` | 5 | Search Trader Joe's products available at one store by keyword: SKU, title, shelf price (USD), pack size, availability flag, category path … |
| `products/stores` | 5 | Trader Joe's stores near a US ZIP code: store code (used by search and product), address, coordinates, distance, phone, weekly hours and al… |

<a id="p-uswitch-com"></a>

### Uswitch broadband (`uswitch-com`)

UK home broadband price comparison from Uswitch's own broadband API: addresses at a postcode, availability-checked deals with prices, speeds, contract terms and fees, deal detail, provider directory and Trustpilot scores. Read-only; no switching or sign-up.

| Capability | Credits | Use |
| --- | --- | --- |
| `products/get_deal` | 5 | You have a deal_id from search_deals and want the complete record. Fails with not_found for an unknown or expired deal_id. |
| `products/get_provider_reviews` | 5 | You have a provider id (from list_providers or a deal) and want its public rating and recent review text. Fixed latest-10 reviews; no pagin… |
| `products/list_providers` | 5 | Resolve a provider name to the id that search_deals.provider_ids and get_provider_reviews need. |
| `products/lookup_addresses` | 5 | You have a UK postcode and need the uprn of a specific address before searching deals. Fails with not_found for a postcode Royal Mail does … |
| `products/search_deals` | 5 | Compare home broadband deals for a UK address (postcode + uprn from lookup_addresses) or nationally. One page per call (limit, default 20, … |

<a id="p-walmart-com"></a>

### Walmart.com (`walmart-com`)

Walmart US storefront: product search, category browsing, product detail with variants, prices and fulfillment options, customer reviews, search suggestions and store pages, read from the server-rendered __NEXT_DATA__ of www.walmart.com and its public typeahead JSON.

| Capability | Credits | Use |
| --- | --- | --- |
| `products/browse` | 5 | Enumerate a category page by page, or follow a breadcrumb id returned by an earlier call. |
| `products/product` | 5 | Get the full record for an item found by `search`, `browse` or pasted as a walmart.com/ip/ URL. |
| `products/reviews` | 5 | Read what buyers say about an item found by `search` or `product`. |
| `products/search` | 5 | Find Walmart products by keyword and pick a `us_item_id` for `product` or `reviews`. |
| `products/store` | 5 | Look up a store seen in `product.location.store_id` or a walmart.com/store/ URL, or hop to nearby stores. |
| `products/suggest` | 5 | Expand a vague shopping term into the queries Walmart itself proposes, then call `search`. |

<a id="p-woocommerce-com"></a>

### WooCommerce stores (`woocommerce-com`)

Product catalogues, prices, stock, variations and categories from any WooCommerce store through the public WooCommerce Store API that storefronts use. Input is the store's domain or any URL on it; responses are verified to be Store API data.

| Capability | Credits | Use |
| --- | --- | --- |
| `products/get_product` | 5 | Details, variants (sizes/colours) and per-variant price or stock of one product in a WooCommerce store, e.g. from a pasted product URL. |
| `products/list_attributes` | 5 | Find attribute taxonomies and term slugs for search_products attribute filters, or list a store's brands/sizes/colours. |
| `products/list_categories` | 5 | Navigate a WooCommerce store's catalogue and find the category id or slug to pass to search_products. |
| `products/search_products` | 5 | Product catalogue, prices or stock from a store running WooCommerce (WordPress shops on their own domain). Start here; get ids or slugs for… |

Also in this category: [Alibaba wholesale products](#p-alibaba), [AuctionTime](#p-auctiontime-com), [Cars & Bids](#p-carsandbids-com), [NIH Dietary Supplement Label Database (dsld.od.nih.gov)](#p-dsld-od-nih-gov), [Floor & Decor](#p-flooranddecor-com), [Kickstarter](#p-kickstarter-com), [Nissan USA dealer locator and inventory](#p-nissanusa-com), [PeerSpot](#p-peerspot-com), [Reclame Aqui](#p-reclameaqui-com-br), [CPSC Recalls (SaferProducts.gov)](#p-saferproducts-gov), [U-Haul](#p-uhaul-com), [Wayfair Careers and Product Reviews](#p-wayfair-com), [Open Food Facts](#p-world-openfoodfacts-org)

## skills

Website instructions and source files for agents and browser interactions.

<a id="p-doi-org"></a>

### DOI.org (`doi-org`)

DOI resolution through the doi.org Handle proxy: landing URL and handle values for a DOI, registration-agency lookup for batches of DOIs, content-negotiated bibliographic metadata (CSL JSON, BibTeX, citations, RDF/XML, DataCite JSON), prefix administration, the registration-agency directory and DOI system statistics.

| Capability | Credits | Use |
| --- | --- | --- |
| `identifiers/metadata` | 5 | You need the title, authors, venue, year or a citation for a DOI, or the full CSL/DataCite record. |
| `identifiers/monthly_statistics` | 5 | Chart DOI system growth or resolution volume over time. |
| `identifiers/prefix` | 5 | Learn which agency and which metadata endpoint serve every DOI under a prefix. |
| `identifiers/registration_agencies` | 5 | List the agencies that issue DOIs and where to find them. |
| `identifiers/registration_agency` | 5 | Triage a list of DOIs before fetching metadata: which are real, and which agency's metadata service will answer. |
| `identifiers/resolution_statistics` | 5 | Size the DOI system or see where resolutions come from. |
| `identifiers/resolve` | 5 | You hold a DOI (or a doi.org link) and want its canonical landing URL, its registration agency and the raw handle record. |

<a id="p-qasa"></a>

### Qasa Swedish rentals (`qasa`)

Swedish area resolution, rental search and listing details with SEK rent, service fees, dates and amenities.

| Capability | Credits | Use |
| --- | --- | --- |
| `real-estate/areas` | 5 | Resolve a Swedish city into the source search area. Returns an empty list for unknown areas. |
| `real-estate/rental_listing` | 5 | Read a Swedish rental listing by ID, including rent and service fee, source UTC dates, description, amenities and photos. |
| `real-estate/rental_search` | 5 | Search Swedish rental listings by city, SEK monthly cost, rooms, furnishing, pets and contract type; paginated results. |

<a id="p-web-archive-org"></a>

### Wayback Machine (`web-archive-org`)

Find archived website snapshots and read text from archived HTML pages.

| Capability | Credits | Use |
| --- | --- | --- |
| `captures/content` | 5 | Retrieve readable static text and title from an exact archived HTML capture, or the verbatim text of a plain-text, XML/RSS or JSON capture,… |
| `captures/history` | 5 | Oldest indexed snapshots (default 5, maximum 20), or the snapshot closest to midnight UTC on date YYYYMMDD; earlier wins ties. One page, no… |
| `captures/oldest` | 5 | Find when a website first appeared in the Internet Archive, or get its oldest archived page. |

## social

Public social media accounts: profiles, follower counts, posts, hashtags, boards and pins.

<a id="p-bilibili-com"></a>

### Bilibili (`bilibili-com`)

Bilibili (bilibili.com) public video metadata: video detail and batch verification by BV/av id, keyword search for videos and uploaders, uploader profiles and archive listings, comments and time-limited DASH stream URLs, all anonymous through the site's web JSON API with WBI request signing.

| Capability | Credits | Use |
| --- | --- | --- |
| `videos/search_uploaders` | 5 | To find an artist's or uploader's mid from a name (e.g. `ピノキオピー`) before calling uploader_profile or uploader_videos. |
| `videos/search_videos` | 5 | To discover videos by keyword (e.g. `VOCALOID 初音ミク`), optionally restricted to a partition such as 30 (VOCALOID·UTAU) and sorted by plays, … |
| `videos/suggest` | 5 | To expand or correct a search term before search_videos. |
| `videos/uploader_profile` | 5 | When you have a mid (from video_detail owner or search_uploaders) and need the uploader's profile and follower count. |
| `videos/uploader_videos` | 5 | To list everything an uploader published (e.g. all MVs of mid 203655966) page by page. |
| `videos/video_batch` | 5 | When you hold a curated list of BV/av ids (e.g. 30 Vocaloid MVs) and need their titles, uploaders and URLs verified in one call. |
| `videos/video_comments` | 5 | To read viewer reactions to a video identified by its aid (from video_detail). |
| `videos/video_detail` | 5 | When you have a BV/av id or a video URL and need to verify the title, uploader and canonical URL, or need a cid for video_streams / an aid … |
| `videos/video_streams` | 5 | When you need a direct, time-limited media URL for a video; take cid from video_detail (omit it to use the first part). |

<a id="p-letterboxd-com"></a>

### Letterboxd (`letterboxd-com`)

Letterboxd film data from the public site: one film's identity, credits, crew, tagline, alternative titles, release dates, similar films and weighted average rating (by Letterboxd URL, boxd.it short link, slug, TMDB id or IMDb id); the full half-star rating histogram with watched/list/like counts; bulk average ratings for a list of film URLs or slugs; film search with cursor pagination; the all-t…

| Capability | Credits | Use |
| --- | --- | --- |
| `films/browse_films` | 5 | Discover films and collect many average ratings without a fixed URL list. `page` continues where the previous call stopped (`next_page`). O… |
| `films/film` | 5 | Pass a Letterboxd film URL or boxd.it link (`url`), a slug (`slug`), a boxd.it id (`lid`), a TMDB id (`tmdb_id`) or an IMDb id (`imdb_id`);… |
| `films/film_ratings` | 5 | Pass `film` as a slug (parasite-2019), a Letterboxd film URL or a boxd.it link. Lighter than `film` (two small fragments instead of the ful… |
| `films/list_entries` | 5 | Pass a list `url` (as returned by lists[].url, /detail/ and /page/n/ suffixes tolerated) or `owner` + `slug`. Page with `page`. |
| `films/lists` | 5 | Which curated lists a film appears in: pass `film` (slug, Letterboxd URL or boxd.it link), `tmdb_id` or `imdb_id`, pick a `sort` and page t… |
| `films/ratings_bulk` | 5 | Bulk extraction of Letterboxd average ratings from a list of film URLs, boxd.it links or slugs. Items are fetched concurrently on one proxy… |
| `films/review_comments` | 5 | Pass `review_id` (the viewing id returned by reviews) or the review page `url` (https://letterboxd.com/<member>/film/<slug>/). Page with `s… |
| `films/reviews` | 5 | What members think of a film, beyond the average: pass `film` (slug, Letterboxd URL or boxd.it link), `tmdb_id` or `imdb_id`, pick a `sort`… |
| `films/search_films` | 5 | Find the Letterboxd slug or URL for a title before calling film, film_ratings or ratings_bulk. Pass `cursor` from the previous page to cont… |

<a id="p-stackexchange-com"></a>

### Stack Exchange (`stackexchange-com`)

Stack Exchange public questions, answers and accepted answers with source attribution. Quora is not covered.

| Capability | Credits | Use |
| --- | --- | --- |
| `questions/accepted_answers` | 5 | Accepted answers by topic: the top questions on one site carrying every tag in `tagged` (optionally narrowed by `q`), each paired with its … |
| `questions/answer` | 5 | One answer by `answer_id`, or up to 100 answers by `answer_ids`, on one site. Returns the full answer records (bodies, score, is_accepted, … |
| `questions/answers` | 5 | Answers to one question (by `question_id` + `site` or URL), one page per call, sorted by votes, activity or creation. Each answer carries i… |
| `questions/question` | 5 | One question identified by `question_id` + `site` or by its URL, with its answers (default: by votes) and the accepted answer surfaced sepa… |
| `questions/search` | 5 | Questions on one Stack Exchange site matching free text (`q`: one term or up to 5 searched together), tags, or title/body text, optionally … |
| `questions/sites` | 5 | Sites in the Stack Exchange network with the `site` parameter every other function takes. Input: page and page size. Returns site name, URL… |

<a id="p-x-com"></a>

### X (`x-com`)

Inference-backed public X research with sourced structured outputs.

| Capability | Credits | Use |
| --- | --- | --- |
| `posts/lookup` | 30 | Analyze a known public post with X Search thread fetch; exact retrieval must be live verified. |
| `posts/search` | 30 | Research public X posts with a sourced summary and structured evidence; not exact recent-search pagination. |
| `users/lookup` | 30 | Research one public X profile using Grok user search; unknown metrics remain null. |
| `users/posts` | 30 | Analyze a sample of posts from one account, with a date range. Not a complete paginated timeline. |

<a id="p-youtube"></a>

### YouTube (`youtube`)

Read public YouTube video metadata, descriptions and available transcripts through Firecrawl Scrape.

| Capability | Credits | Use |
| --- | --- | --- |
| `read` | 1 | Read video metadata, description and any available transcript. Transcript availability is not guaranteed. Not channel listings, comments or… |

Also in this category: [Oriane](#p-oriane), [Blizzard US Forums](#p-us-forums-blizzard-com)

## software

Open-source packages: registry metadata, versions, licences, download counts and dependents on npm, PyPI, crates.io and Maven Central.

<a id="p-curated-design"></a>

### Curated (curated.design) (`curated-design`)

Curated's public web design inspiration gallery: list featured websites by industry category, browse the server-rendered industry, style and tag shelves, read one site's detail page, search the library, and list the public filter vocabulary. Each site carries its name, live URL, preview image and video.

| Capability | Credits | Use |
| --- | --- | --- |
| `web-design-inspiration/get_site` | 5 | After list_sites, list_shelf_sites or search_sites returned an id, or when the user pastes a curated.design/sites/s/ URL. An unknown id is … |
| `web-design-inspiration/list_filters` | 5 | To pick a `category` for list_sites or a `slug` for list_shelf_sites, or to show what the gallery can be filtered by. |
| `web-design-inspiration/list_shelf_sites` | 5 | The public route for the issue's 'filter by style' (dark, minimal, ...) or by tag (saas, ecommerce, ...). Slugs come from list_filters. A s… |
| `web-design-inspiration/list_sites` | 5 | The default listing. Use `category` with an industry slug from list_filters (`agency`, `portfolio`, `finance`, ...). For style or tag filte… |
| `web-design-inspiration/search_sites` | 5 | Finding a specific featured site by name or topic. Not for exhaustive listing: use list_sites or list_shelf_sites for that. Sections are Pr… |

<a id="p-hub-docker-com"></a>

### Docker Hub (`hub-docker-com`)

Docker Hub, the public container image registry: catalog search with badge, architecture, OS and category filters; repository metadata and README; tag listings and tag detail with per-architecture digests, sizes and push dates; a namespace's repositories and profile; catalog categories; Docker Scout vulnerability summaries by image digest.

| Capability | Credits | Use |
| --- | --- | --- |
| `container-images/get_image_vulnerability_summary` | 5 | Check how many known vulnerabilities a specific image digest carries before pulling it; pair with `get_tag` to go from a tag name to its pe… |
| `container-images/get_namespace` | 5 | Identify who publishes an image (organization vs. individual, company, website) from the namespace in a repository name. |
| `container-images/get_repository` | 5 | Read one image's metadata and README after finding it with `search_images`, or when the user gives a Docker Hub repository name or URL. |
| `container-images/get_tag` | 5 | Resolve a tag such as `latest` to its digests and supported architectures, or check when a specific tag was last pushed. |
| `container-images/list_categories` | 5 | Look up the category slug to filter a search by, or show the available categories. |
| `container-images/list_namespace_repositories` | 5 | Enumerate everything a publisher ships (e.g. all `grafana/*` images or all official images) before reading individual repositories. |
| `container-images/list_tags` | 5 | List or filter the tags of an image, see which architectures each tag supports and when it was last pushed, and pick a tag or digest for `g… |
| `container-images/search_images` | 5 | Find container images by name or words before reading a repository or its tags; filter to official images, a CPU architecture or a category. |

<a id="p-osv-dev"></a>

### OSV.dev open source vulnerabilities (`osv-dev`)

OSV.dev, Google's open source vulnerability database (api.osv.dev), keyless: known vulnerabilities for a package version, purl or Git commit across npm, PyPI, Go, Maven, crates.io, RubyGems, NuGet, Packagist, Linux distributions and more; batch checks of up to 100 dependencies; and full OSV records by OSV, GHSA or CVE id. Every record carries its source database (GitHub Advisory Database, PyPI, G…

| Capability | Credits | Use |
| --- | --- | --- |
| `vulnerabilities/query` | 5 | "Is lodash 4.17.15 vulnerable?", "what should I upgrade to": one package at a time. Use query_batch for a dependency list and vuln for the … |
| `vulnerabilities/query_batch` | 5 | Auditing a dependency list or lockfile: which of these packages at these versions have known vulnerabilities. |
| `vulnerabilities/vuln` | 5 | Details of one vulnerability id from query or query_batch, or a CVE/GHSA someone mentions. |

<a id="p-package-registry-metadata-download-stats"></a>

### Package registries (`package-registry-metadata-download-stats`)

npm, PyPI, crates.io and Maven Central package metadata: latest version, license, links, version history, weekly and monthly downloads and dependent counts.

| Capability | Credits | Use |
| --- | --- | --- |
| `packages/dependents` | 1 | How many packages depend on one version of a package (deps.dev total/direct/indirect; the default version unless one is named). For crates … |
| `packages/downloads` | 1 | Daily download counts for one npm, PyPI or crates.io package as a series with 1/7/30-day sums; last-week, last-month or last-year (capped b… |
| `packages/package` | 1 | One package's current record: latest version and publish time, description, license, homepage/repository/issues links, keywords, version co… |
| `packages/versions` | 1 | A package's version history from deps.dev, newest first, with publish time, default flag and deprecation; paged with offset and limit. All … |

Also in this category: [NIST National Vulnerability Database (NVD)](#p-nvd-nist-gov)

## sports

Sports federations and circuits: tournament calendars, match results and player rankings.

<a id="p-baseballsavant-mlb-com"></a>

### MLB Baseball Savant (`baseballsavant-mlb-com`)

MLB Baseball Savant (Statcast): player name search and trending players, player bio by MLBAM id, per-plate-appearance game logs, pitch-by-pitch Statcast search over a date window, per-pitch-type summaries, season leaderboards (expected stats, exit velocity, sprint speed, outs above average, pitch arsenals) and the daily MLB schedule with win probability.

| Capability | Credits | Use |
| --- | --- | --- |
| `baseball-statcast/get_leaderboard` | 5 | Season-level rankings across players; take `player_id` into the player functions. Boards not listed here are not supported. |
| `baseball-statcast/get_pitch_type_summary` | 5 | A compact pitch-mix / pitch-outcome profile for a known `player_id` without pulling every pitch. |
| `baseball-statcast/get_player` | 5 | After `search_players`, to confirm identity and get bio fields before pulling Statcast data for the id. |
| `baseball-statcast/get_player_gamelogs` | 5 | Per-plate-appearance detail for a known `player_id` and season; take `play_id` or `game_pk` into further lookups. |
| `baseball-statcast/get_schedule` | 5 | Find `game_pk` values and scores for a day; a date in the off-season legitimately has zero games. |
| `baseball-statcast/search_players` | 5 | Resolve a player's name to the MLBAM `player_id` needed by `get_player`, `get_player_gamelogs`, `get_pitch_type_summary` and `search_statca… |
| `baseball-statcast/search_statcast` | 5 | Statcast pitch-level data for a known `player_id` (or team abbreviation) in a date window; narrow the window or add `pitch_types` to keep r… |
| `baseball-statcast/trending_players` | 5 | Discover who is being looked up on Baseball Savant right now; feed `player_id` into the detail functions. |

<a id="p-basketball-fantasysports-yahoo-com"></a>

### Yahoo Fantasy Basketball (public) (`basketball-fantasysports-yahoo-com`)

Yahoo Fantasy Basketball public data without a login: player search, a public league's player list with projected, total, average and standard-deviation stat windows and 9-category stats (FG%, FT%, 3PTM, PTS, REB, AST, ST, BLK, TO), Yahoo rank windows, public team rosters and the public Yahoo Sports player news index.

| Capability | Credits | Use |
| --- | --- | --- |
| `fantasy-basketball-players/list_players` | 5 | Browse or rank players by 9-category stats in a public league. Pass stat_period explicitly (S_AS_2025 = 2025-26 per-game averages, S_S_2026… |
| `fantasy-basketball-players/player_news` | 5 | Recent news about a player resolved by search_players (news_url / player_id). Does not use the login-gated Fantasy player-note panel. |
| `fantasy-basketball-players/player_rankings` | 5 | Compare players by Yahoo's pre-season and actual rank windows in a public league. Sort with OR (pre-season), AR_S, AR_L30, AR_L14, AR_L7 (t… |
| `fantasy-basketball-players/public_team_roster` | 5 | Inspect a specific public team (league_id + team_id, e.g. from a /nba/{league}/{team} URL). NBA rosters are daily: pass date (YYYY-MM-DD) o… |
| `fantasy-basketball-players/search_players` | 5 | Resolve a player name to Yahoo player ids/keys before list_players, public_team_roster or player_news. Give league_id or league_url of any … |

<a id="p-cbssports-com"></a>

### CBS Sports fantasy football and basketball (`cbssports-com`)

CBS Sports (cbssports.com) NFL fantasy football and NBA fantasy basketball from its server-rendered pages. Football: weekly and rest-of-season projections and fantasy stats for every position in PPR and non-PPR scoring, and the weekly and draft rankings of its three fantasy experts. Basketball: season, rest-of-season and scoring-period projections, season, recent-day and scoring-period stats in C…

| Capability | Credits | Use |
| --- | --- | --- |
| `fantasy-sports-rankings/projections` | 5 | This week's or next week's projected points and stat lines for a football position, rest-of-season projections, or NBA fantasy basketball s… |
| `fantasy-sports-rankings/rankings` | 5 | Start/sit rankings for a football position this week, football draft rankings, or NBA fantasy basketball roto rankings by position. |
| `fantasy-sports-rankings/stats` | 5 | Actual fantasy production: last week's football scores, this season to date, a past season's totals, or recent NBA fantasy basketball form. |

<a id="p-draftsharks-com"></a>

### Draft Sharks NFL rankings (`draftsharks-com`)

Draft Sharks (draftsharks.com) NFL fantasy football rankings: weekly and rest-of-season boards for every position in standard, half PPR, PPR and TE-premium scoring, with or without superflex, each player carrying the site's median, floor, ceiling and consensus projections, tiers, matchup and strength of schedule. Read from the server-rendered table fragments the pages load; anonymous.

| Capability | Credits | Use |
| --- | --- | --- |
| `fantasy-sports-rankings/ros_rankings` | 5 | Rest-of-season trade and waiver value for a position. |
| `fantasy-sports-rankings/weekly_rankings` | 5 | Weekly start/sit rankings and point projections for a position, for example week 4 half-PPR quarterbacks. Omit week for the current week. |

<a id="p-espn-com"></a>

### ESPN (`espn-com`)

ESPN public sports data from the anonymous site and core JSON APIs: sport/league discovery, scoreboards by date or week (schedules, live and final scores with explicit status), event summaries, teams, team records and schedules, rosters, standings, player bios with career statistics, league injury reports, and site search. US and international coverage as ESPN exposes it (NFL, NBA, MLB, NHL, coll…

| Capability | Credits | Use |
| --- | --- | --- |
| `sports-data/event` | 5 | Read a specific game/match after finding its event_id in scoreboard or team_schedule. |
| `sports-data/injuries` | 5 | Check who is out or questionable before a game, for fantasy lineups or betting research; feed athlete_id to `player`. |
| `sports-data/leagues` | 5 | Start here to discover `sport` and `league` slugs before calling scoreboard, teams, standings or search. |
| `sports-data/player` | 5 | Read a player's bio and season-by-season statistics after finding the athlete_id in roster or search. |
| `sports-data/roster` | 5 | Get athlete_id values and roster details for a team; feed athlete_id to `player`. |
| `sports-data/scoreboard` | 5 | Find schedules, live and completed scores for a league and day, and the event_id for `event`. |
| `sports-data/search` | 5 | Resolve a team or player name to ESPN ids and the league slug to use with team, roster, player. |
| `sports-data/standings` | 5 | Read a league table or conference/division standings for a season. |
| `sports-data/team` | 5 | Read a team's record, standing and next fixture by team_id. |
| `sports-data/team_schedule` | 5 | List a team's fixtures and results with event_ids for `event`. |
| `sports-data/teams` | 5 | Get team_id values for team, team_schedule, roster. |

<a id="p-fantasydata-com"></a>

### FantasyData NFL rankings (`fantasydata-com`)

FantasyData (fantasydata.com) NFL weekly fantasy football rankings from the site's public ranking pages: rank, player, team, opponent, positional rank and projected points for every offensive position, kickers, team defenses and IDP, in standard, half-PPR and PPR scoring. Anonymous; the site shows the top 100 rows per page to visitors without Premium.

| Capability | Credits | Use |
| --- | --- | --- |
| `fantasy-sports-rankings/rankings` | 5 | This week's start/sit order or projected points for a position from FantasyData, for example half-PPR running backs or the kicker ranking. |

<a id="p-fantasyfootballcalculator-com"></a>

### Fantasy Football Calculator NFL rankings and ADP (`fantasyfootballcalculator-com`)

Fantasy Football Calculator (fantasyfootballcalculator.com) NFL data: the current week's rankings with projected fantasy points for standard, PPR, half-PPR and 2-QB leagues, dynasty and dynasty rookie rankings, and average draft position from the site's mock drafts by format, league size, season and position.

| Capability | Credits | Use |
| --- | --- | --- |
| `fantasy-sports-rankings/adp` | 5 | Where players go in drafts for a scoring format and league size, this season or any season back to 2007. |
| `fantasy-sports-rankings/rankings` | 5 | This week's start/sit order and projected points for a position in standard, PPR, half-PPR or 2-QB scoring, or long-term dynasty and rookie… |

<a id="p-fftoday-com"></a>

### FFToday NFL projections and rankings (`fftoday-com`)

FFToday (fftoday.com) NFL fantasy football projections and rankings from the site's public pages: weekly projections (QB, RB, WR, TE, K) and season projections (also team defense and IDP) with per-stat lines and points in ten scoring presets, and weekly staff rankings with tiers for every position. Anonymous.

| Capability | Credits | Use |
| --- | --- | --- |
| `fantasy-sports-rankings/season_projections` | 5 | Season-long projected totals for drafts or rest-of-season planning. |
| `fantasy-sports-rankings/weekly_projections` | 5 | Projected points and stat lines for a position in one NFL week, in a specific league's scoring. |
| `fantasy-sports-rankings/weekly_rankings` | 5 | Weekly start/sit order for a position. |

<a id="p-football-fantasysports-yahoo-com"></a>

### Yahoo Fantasy Football (public) (`football-fantasysports-yahoo-com`)

Yahoo Fantasy Football public data without a login: player search, a public league's player list with projected and actual stat periods and rank windows, public team rosters and the public Yahoo Sports player news index.

| Capability | Credits | Use |
| --- | --- | --- |
| `fantasy-football-players/list_players` | 5 | Browse or rank players by projected or actual fantasy points in a public league. Pass stat_period explicitly (S_PW_5 = Week 5 projections, … |
| `fantasy-football-players/player_news` | 5 | Recent news about a player resolved by search_players (news_url / player_id). Does not use the login-gated Fantasy player-note panel. |
| `fantasy-football-players/player_rankings` | 5 | Compare players by Yahoo's projected vs actual rank windows in a public league. Sort with PR_W, PR_N4W, PR_S (projected) or AR_LW, AR_L4W, … |
| `fantasy-football-players/public_team_roster` | 5 | Inspect a specific public team (league_id + team_id, e.g. from a /f1/{league}/{team} URL). Private leagues are refused with upstream_blocke… |
| `fantasy-football-players/search_players` | 5 | Resolve a player name to Yahoo player ids/keys before list_players, public_team_roster or player_news. Give league_id or league_url of any … |

<a id="p-nfl-com"></a>

### NFL.com (`nfl-com`)

Official NFL data from nfl.com's own API (api.nfl.com): weekly injury and practice participation reports, club rosters, standings, weekly schedules with scores, clubs, games, player profiles and news.

| Capability | Credits | Use |
| --- | --- | --- |
| `sports-league-data/game` | 5 | Follow up on a game id from `schedule`. |
| `sports-league-data/injury_report` | 5 | The user wants the official practice participation or injury designations for a week (e.g. '2026 Week 3 injury report', 'Falcons practice r… |
| `sports-league-data/news` | 5 | The user wants recent official articles about a club or the league (e.g. dated team injury articles). |
| `sports-league-data/player` | 5 | Follow up on a player id from injury_report or team_roster. |
| `sports-league-data/schedule` | 5 | The user asks what games are on in a week, when a club plays, or the scores of a past week. |
| `sports-league-data/standings` | 5 | The user asks who leads a division, a club's record, or playoff clinches for a given week. |
| `sports-league-data/team_roster` | 5 | The user asks for a team's roster, depth or who plays a position for a club. |
| `sports-league-data/teams` | 5 | Resolve a club name or abbreviation to its UUID before calling team_roster or injury_report, or list the league. |

<a id="p-startwho-com"></a>

### StartWho NFL fantasy projections (`startwho-com`)

StartWho (startwho.com) NFL fantasy football projections from the site's own JSON API: weekly projections built from sportsbook player props (each market with its consensus line, odds and per-sportsbook lines), season and rest-of-season projections with overall and positional rank, weekly projected-vs-actual results with the site's accuracy grading, and the injury list. Standard, half-PPR and PPR…

| Capability | Credits | Use |
| --- | --- | --- |
| `fantasy-sports-rankings/injury_report` | 5 | Who is hurt before setting a lineup. |
| `fantasy-sports-rankings/projections` | 5 | Start/sit decisions from betting lines: this week's projected points and the props behind them. |
| `fantasy-sports-rankings/ros_projections` | 5 | In-season rankings for trades and waivers. |
| `fantasy-sports-rankings/season_projections` | 5 | Season-long rankings for drafts or trades. |
| `fantasy-sports-rankings/weekly_results` | 5 | Checking how projections held up, or a week's actual fantasy scores. |

<a id="p-worldtabletennis-com"></a>

### World Table Tennis (`worldtabletennis-com`)

Public WTT table tennis events, official match results and cards, and senior/youth ITTF ranking lists.

| Capability | Credits | Use |
| --- | --- | --- |
| `table-tennis/event_results` | 5 | Official match results for one completed WTT/ITTF event, identified by its numeric event id (from `events`). Returns every official match w… |
| `table-tennis/events` | 5 | Search the WTT/ITTF tournament calendar (2022 to date, including scheduled events). Input optionally narrows by season year, free-text name… |
| `table-tennis/match` | 5 | One match card by event id and WTT document code (as listed by `event_results`): competitors with ITTF ids and associations, best-of, per-g… |
| `table-tennis/ranking_weeks` | 5 | Published ITTF senior ranking weeks (year, week number, publication date), newest first. Input is just an optional limit; useful to learn w… |
| `table-tennis/rankings` | 5 | Current ITTF world ranking list. Input selects senior (SEN, default) or youth (YOU) category, the list (MS/WS singles, MD/WD/XD doubles pai… |

Also in this category: [Polymarket](#p-polymarket), [TickPick](#p-tickpick-com)

## travel

Travel: hotels, their guest ratings, rankings in a destination and public reviews.

<a id="p-amtrak-com"></a>

### Amtrak (`amtrak-com`)

Amtrak (US national passenger rail) read-only: station directory and search with addresses, hours and amenities; named routes with ordered stops and train numbers; live train positions and stop-by-stop status decrypted from the public Track Your Train feed. Public feeds of www.amtrak.com and maps.amtrak.com, no login. Fares, schedules by date and booking are not covered (the /dotcom/ APIs sit beh…

| Capability | Credits | Use |
| --- | --- | --- |
| `train-status/get_route` | 5 | Route detail after `list_routes`; the train numbers feed `train_status`, the stop codes feed `get_station`. |
| `train-status/get_station` | 5 | Station detail once you have a code from `list_stations`, `search_stations`, a route's stops or a train's stops. |
| `train-status/list_routes` | 5 | Find a route code or name for `get_route`, or filter `live_trains` by `route_name`. |
| `train-status/list_stations` | 5 | Start here to find station codes for `get_station`, `search_stations` inputs or route stops; filter by `state` to keep the result small. |
| `train-status/live_trains` | 5 | A snapshot of where trains are right now; use `train_status` for one train with its stop-by-stop times. |
| `train-status/search_stations` | 5 | Find a station code when you know a place name or a partial name; `get_station` for full detail. |
| `train-status/train_status` | 5 | Train status by number, the Track Your Train equivalent. Train numbers come from `get_route` or `live_trains`. |

<a id="p-booking-com"></a>

### Booking.com stays (`booking-com`)

Booking.com accommodation: destination lookup, stay search by dates and guests with total prices, property details and policies, room availability with cancellation terms, guest reviews and surroundings, over Booking.com's public GraphQL endpoint.

| Capability | Credits | Use |
| --- | --- | --- |
| `hotels/availability` | 5 | Retrieve availability, total prices and policies for one property (hotel_id from `search`) and dates. |
| `hotels/hotel` | 5 | Detail step after `search` (country_code + page_name) or from a pasted booking.com/hotel/{cc}/{page}.html URL. Prices and rooms are in `ava… |
| `hotels/locations` | 5 | First step when the caller has a place name and needs a Booking.com destination id; also resolves a hotel name to its hotel_id. |
| `hotels/reviews` | 5 | Read guest feedback for a hotel_id from `search`; pass ufi and country_code from the same result to save a lookup. |
| `hotels/search` | 5 | Compare accommodation for given dates in a city, district, region, landmark or airport area (dest_id from `locations`), or by free-text `qu… |
| `hotels/surroundings` | 5 | Location context for a hotel_id from `search` (pass its ufi to save a lookup). |

<a id="p-expedia-co-uk"></a>

### Expedia UK hotels (`expedia-co-uk`)

Expedia UK destination lookup, dated hotel search and live room offers in GBP for one room. Anonymous site prices; no bookings or member discounts.

| Capability | Credits | Use |
| --- | --- | --- |
| `hotels/availability` | 5 | Read live Expedia UK room offers and numeric GBP total stay prices for one hotel and one room. Includes rate-plan IDs, payment model and so… |
| `hotels/locations` | 0 | Find destination region IDs on Expedia UK for use with search. Returns destination suggestions only, not hotel-name suggestions. |
| `hotels/search` | 5 | Search Expedia UK hotels for dates and guests in one room. Returns hotel IDs, source URLs and displayed GBP stay prices. Resume with next_o… |

<a id="p-flights-google-com"></a>

### Google Flights (`flights-google-com`)

Google Flights airport/city lookup and one-way or two-step round-trip fare search, with optional carry-on/checked bag repricing.

| Capability | Credits | Use |
| --- | --- | --- |
| `flights/search_flights` | 5 | Search Google Flights one-way fares or round-trip outbound options. For matching returns, call again with a chosen selection in selected_ou… |
| `flights/suggest_places` | 0 | Find Google Flights airport and city identifiers by name or IATA code. Includes nearby airports, deduplicated; omits rail stations and regi… |

<a id="p-golfnow-com"></a>

### GolfNow US (`golfnow-com`)

GolfNow US public course discovery: location and course search, courses with tee times near a point, per-facility tee times with displayed rates, per-day availability summaries, course profiles and GolfNow reviews. Anonymous, read-only.

| Capability | Credits | Use |
| --- | --- | --- |
| `tee-times/course_detail` | 5 | Details for one `facility_id`. Two page fetches; no availability (use `facility_tee_times`). |
| `tee-times/course_reviews` | 5 | Read what golfers wrote about a course. Only reviews left on GolfNow itself; the larger GolfPass review count on course records is a differ… |
| `tee-times/courses_near` | 5 | Discover courses near a place (coordinates from `suggest_locations`); then call `facility_tee_times` with a `facility_id`. |
| `tee-times/facility_day_summaries` | 5 | Pick a day before calling `facility_tee_times`; up to 31 days per call. |
| `tee-times/facility_tee_times` | 5 | Availability and displayed prices for a known `facility_id` on one day. Discovery only: nothing is held or booked. |
| `tee-times/search_courses` | 5 | Find a `facility_id` from a course name; every id-keyed function needs one. |
| `tee-times/suggest_locations` | 5 | Turn a place name into latitude/longitude for `courses_near`. |
| `tee-times/tee_time_rates` | 5 | Expand `has_more_rates` on a `facility_tee_times` row. Without `tee_time_id`, the first tee time of `date` for `players` is used. |

<a id="p-skyscanner-net"></a>

### Skyscanner (`skyscanner-net`)

Skyscanner flight search and fare comparison: place autosuggest (sky place ids and entity ids), live itinerary search by origin, destination, dates, passengers and cabin with airlines, durations, stops, fare policy flags and booking-source deep links, plus cached indicative fares per day and per month. Anonymous same-origin JSON APIs on www.skyscanner.com; live quotes and cached indicative prices…

| Capability | Credits | Use |
| --- | --- | --- |
| `flights/monthly_prices` | 5 | Find the cheapest month for a route; then price_calendar for days and search_flights for a live quote. When a direct_only calendar comes ba… |
| `flights/price_calendar` | 5 | Find cheap dates for a route before running a live search_flights for a specific day. |
| `flights/search_flights` | 5 | Compare fares and itineraries for concrete dates. Resolve places with suggest_places first; use price_calendar or monthly_prices for cheap-… |
| `flights/suggest_places` | 5 | Start here to resolve a city or airport name into the identifiers the other functions take. |

<a id="p-trip-com"></a>

### Trip.com (`trip-com`)

Public hotel destination directories and hotel profiles, room types, amenities and policies. No date-specific availability or offers.

| Capability | Credits | Use |
| --- | --- | --- |
| `hotels/amenities` | 5 | Read published popular hotel amenities with source charge labels. Partial amenity coverage; no unlisted amenity is inferred absent. |
| `hotels/destinations` | 5 | List linked hotel city directories from the public hotels landing page. Not a complete destination catalog. |
| `hotels/hotel` | 5 | Read hotel identity, street address, description and published property facts. Does not quote a stay. |
| `hotels/hotels` | 5 | List featured hotel profiles from a known city directory. Curated directory content, not dated availability search; marketing prices are om… |
| `hotels/policies` | 5 | Read published property policy sections including check-in/out, children, pets and fees when present. Policies may vary by room and do not … |
| `hotels/rooms` | 5 | Read published room types, bed descriptions and room features. Room types do not establish availability; price and availability are unknown. |

<a id="p-turo-com"></a>

### Turo (`turo-com`)

Search public US Turo rental vehicles, read vehicle details and request anonymous dated price estimates. Search is a bounded source window, not exhaustive inventory. No account, booking or checkout actions.

| Capability | Credits | Use |
| --- | --- | --- |
| `car-rentals/filters` | 0 | Read Turo's public US vehicle-type, sort and fuel labels. vehicle_types and sort_options supply values accepted by search. Fuel labels are … |
| `car-rentals/search` | 1 | Search US Turo rentals around coordinates with optional make, vehicle type and sort. Dates use pickup-local time; omitted dates default to … |
| `car-rentals/vehicle` | 1 | Read one public US Turo vehicle URL: identity, listing status, location, specifications, rating and indicative daily price. Optional paired… |

<a id="p-untourism-int"></a>

### UN Tourism (`untourism-int`)

Discover UN Tourism free statistical files and indicators, and read live country-year tourism observations with source units, flags and editions.

| Capability | Credits | Use |
| --- | --- | --- |
| `statistics/data` | 5 | Country-year observations for up to 10 indicator codes (from `indicators`), parsed live from the official Excel files: value as source text… |
| `statistics/files` | 5 | The official UN Tourism Key Tourism Statistics Excel files (13 files: inbound arrivals/expenditure/by region/by purpose/by transport/accomm… |
| `statistics/indicators` | 5 | Search the 148 free indicators (code, name, series group, unit, source file). `query` matches words in the code, name, previous Compendium … |

<a id="p-vrbo-com"></a>

### Vrbo vacation rentals (`vrbo-com`)

Vrbo (US storefront) destination lookup, dated vacation-rental search, listing details and anonymous USD stay quotes. Read-only; no bookings, inquiries or account data.

| Capability | Credits | Use |
| --- | --- | --- |
| `vacation-rentals/details` | 5 | Read a Vrbo listing's public details by Expedia property id: name, description, bedrooms/bathrooms/sleeps, popular amenities, house rules, … |
| `vacation-rentals/locations` | 5 | Find Vrbo destination region IDs (Expedia gaia ids) for use with search. Returns regions (cities, neighborhoods, POIs, airports) with coord… |
| `vacation-rentals/offers` | 5 | Quote one Vrbo listing for a stay: the single-unit rate plan with numeric USD total, displayed nightly price, base/tax components, payment … |
| `vacation-rentals/search` | 5 | Search Vrbo vacation rentals in a destination for dates and guests. Returns Expedia property ids, Vrbo listing ids, listing URLs, headline,… |

Also in this category: [Campspot](#p-campspot-com), [Hipcamp](#p-hipcamp-com), [NOAA National Hurricane Center (nhc.noaa.gov)](#p-nhc-noaa-gov), [Resident Advisor](#p-ra-co), [Recreation.gov](#p-recreation-gov), [SeatGeek](#p-seatgeek-com), [SpotHero parking](#p-spothero-com), [StubHub](#p-stubhub-com), [TickPick](#p-tickpick-com), [TodayTix](#p-todaytix-com), [U.S. State Department Travel Advisories (travel.state.gov)](#p-travel-state-gov)

