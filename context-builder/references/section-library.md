# Section Library

Catalog of sections for context-builder prompts. Each section includes: purpose, default questions, and output file spec. Select and customize based on consulting focus.

## Core Sections

### Revenue & Service Map
**ID**: `revenue-service-map`
**Purpose**: Understand the business model and what generates money.
**Best for**: All assessments, especially existential strategy.
**Questions**:
- What are the main revenue streams? (list with rough proportions)
- For each service line: client type, pricing model, margin
- Which services are growing vs plateauing vs declining?
- Client lifecycle: acquisition -> onboarding -> delivery -> expansion/churn
- Pricing model: % of spend, retainer, project-based, success-based?
**Output**: `context-output/01-revenue-service-map.md`
**Output spec**: Revenue streams with proportions, service lines table, growth trajectory

### Process Inventory
**ID**: `process-inventory`
**Purpose**: Map current workflows end to end.
**Best for**: Automation focus.
**Questions**:
- What are the main workflows? (list all core processes)
- For each: what triggers it, what data feeds it, steps, who executes each step?
- Which processes are formalized/documented vs tribal knowledge?
- Where do handoffs happen between people, systems, or both?
**Output**: `context-output/01-process-map.md`
**Output spec**: Structured workflow descriptions, triggers/inputs/steps/outputs, documented vs undocumented flags

### Pain Points & Waste
**ID**: `pain-points`
**Purpose**: Identify where time/money/quality is lost.
**Best for**: All assessments.
**Questions**:
- What takes longer than it should?
- Where do errors happen most?
- What decisions are bottlenecks?
- What manual work feels obviously automatable?
- What information is hard to find when needed?
- What prevents scaling with the same headcount?
**Output**: `context-output/02-pain-points.md`
**Output spec**: Pain Point Matrix: issue | severity (1-5) | frequency | current workaround. Sorted by impact.

### Current Tech Stack
**ID**: `tech-stack`
**Purpose**: Map the full technology and data landscape.
**Best for**: All assessments.
**Questions**:
- What software systems are used daily?
- What internal/custom tools exist?
- How do systems connect? (APIs, manual export, spreadsheets)
- What data exists but isn't being used?
- What integrations are fragile or manual?
**Output**: `context-output/03-tech-stack.md`
**Output spec**: All systems with purpose, integrations, data formats. Connection map. Gaps highlighted.

### The Existential Question
**ID**: `existential`
**Purpose**: Honest strategic assessment of what survives AI transformation.
**Best for**: Existential strategy focus.
**Questions**:
- Which parts of the business could AI fully automate in 1-2 years? 3-5 years?
- What does a human here genuinely do that AI cannot today? (be concrete, not abstract)
- If platforms built perfect self-serve AI tools, what would clients still need you for?
- Is the current service model viable as a standalone business in 5 years?
- What would a team at 20% of current size generating the same revenue look like?
- Where is the "but" -- the thing you tried to automate but couldn't?
**Output**: `context-output/04-existential-assessment.md`
**Output spec**: Automation timeline, defensibility analysis, risk assessment, strategic options with trade-offs

### AI Opportunity Mapping
**ID**: `ai-opportunities`
**Purpose**: Identify where AI/agents could help existing operations.
**Best for**: Automation focus.
**Questions** (customize by industry):
- Process monitoring and anomaly detection
- Dynamic scheduling and replanning
- Automated quality checks
- Knowledge capture from experienced staff
- Document/compliance checking
- Reporting and narrative generation
- Client communication assistance
**Output**: `context-output/05-ai-opportunities.md`
**Output spec**: Prioritized list: opportunity | impact | effort | dependencies | timeframe. Grouped: quick wins, medium-term, strategic.

### New Business Models
**ID**: `new-business-models`
**Purpose**: Explore what the company could become.
**Best for**: Existential strategy, pivots.
**Questions**:
- What adjacent markets could be served with existing expertise + AI?
- Could parts of the service become self-serve tools?
- Could proprietary data/models become products?
- What business model experiments would you run with 3 months and a small team?
- What would the company look like if rebuilt from scratch today?
**Output**: `context-output/06-new-business-models.md`
**Output spec**: Business model canvas sketches for top 2-3 options, experiment designs, resource requirements

### People & Organizational Dynamics
**ID**: `people-org`
**Purpose**: Understand the human dimension of transformation.
**Best for**: All assessments.
**Questions**:
- Who are the AI champions? Who is skeptical, and why?
- What's the current skill distribution? (advanced AI users vs basic vs none)
- What would change in team structure if AI handles 50% of manual work?
- Which roles grow more important with AI?
- How does the team feel emotionally about AI transformation?
- Appetite for learning vs "just tell me what to do"?
**Output**: `context-output/07-people-org.md`
**Output spec**: Team AI readiness map, skill gap analysis, recommended structure evolution

### Client Value Chain Analysis
**ID**: `client-value-chain`
**Purpose**: Understand how value flows to clients and what's at risk.
**Best for**: Service businesses, existential strategy.
**Questions**:
- What do clients actually value most? (cost, expertise, convenience, speed, results, relationship?)
- Which client segments are most at risk of going direct/self-serve?
- Which segments would pay more for AI-augmented services?
- What do clients complain about or wish was different?
- What would make a client say "I'd never leave"?
- Adjacent services clients need that aren't currently offered?
**Output**: `context-output/08-client-value-chain.md`
**Output spec**: Client segmentation by AI-risk, value proposition mapping (current vs future), deepening opportunities

### Data & Knowledge Assets
**ID**: `data-assets`
**Purpose**: Audit what proprietary assets exist and their defensibility.
**Best for**: Product development, existential strategy.
**Questions**:
- What historical data exists? (volume, timespan, quality)
- What expert knowledge lives only in people's heads?
- If you wanted to fine-tune a model on your expertise, what would training data look like?
- What competitive intelligence do you have that others don't?
- What would be needed to turn data into a defensible AI product?
**Output**: `context-output/09-data-knowledge-assets.md`
**Output spec**: Data inventory: type | volume | quality | defensibility. Knowledge capture priorities. Productization path.

### Make vs Buy Assessment
**ID**: `make-buy`
**Purpose**: For specific technology/platform decisions.
**Best for**: When there's a concrete build-or-buy decision pending.
**Questions**:
- What capabilities are non-negotiable?
- What's unique to the company's process that off-the-shelf can't handle?
- What's commodity functionality?
- Cost of building wrong vs buying wrong?
- Timeline pressure?
**Output**: `context-output/04-make-buy-scorecard.md`
**Output spec**: Capability breakdown: capability | must-have? | unique? | vendor coverage | build effort

### Constraints & Compliance
**ID**: `constraints`
**Purpose**: Map hard regulatory and operational boundaries.
**Best for**: Regulated industries (manufacturing, healthcare, finance).
**Questions**:
- Industry regulations affecting automation
- Safety requirements
- Quality certifications/standards
- Data privacy/security (GDPR, etc.)
- Insurance/liability considerations
**Output**: `context-output/07-constraints-compliance.md`
**Output spec**: Regulatory requirements table, safety implications, certifications to maintain

### Budget, Timeline & Active Projects
**ID**: `budget-timeline`
**Purpose**: Ground the conversation in reality.
**Best for**: When concrete implementation is expected.
**Questions**:
- Budget envelope for AI/automation investment
- Active projects or client commitments constraining experimentation
- Hiring plans or resource constraints
- Key decision deadlines
**Output**: `context-output/08-budget-timeline.md`
**Output spec**: Budget constraints, active commitments, decision deadlines, resource availability

### Data Reality Check
**ID**: `data-reality`
**Purpose**: Assess actual data quality vs assumed.
**Best for**: Automation focus, when AI deployment is planned.
**Questions**:
- What data is reliably captured today vs assumed to exist?
- Where are gaps: missing, inconsistent, unreliable?
- How much is in spreadsheets, emails, or people's heads?
- What instrumentation is needed for desired automations?
**Output**: `context-output/09-data-reality.md`
**Output spec**: Data inventory: type | source | quality | format. Gaps needing instrumentation. Quick data wins.

### Quick Wins & Pilots
**ID**: `quick-wins`
**Purpose**: Define immediate next steps (4-8 weeks).
**Best for**: All assessments (always include as final section).
**Questions**:
- What manual tasks could be automated this month with existing tools?
- What 1-2 small experiments could test a new hypothesis?
- How to move more of the team from basic ChatGPT to compound AI workflows?
- Is there a client engagement where AI-augmented delivery could be tested?
- How would you measure success?
**Output**: `context-output/10-pilots-quickwins.md`
**Output spec**: 2-3 immediate automations with owner/timeline/impact. 1-2 strategic experiments with hypothesis/method/criteria. Team activation plan.

## Section Numbering

Output file numbers are assigned based on the order sections appear in the selected set. When fewer than 10 sections are selected, number them sequentially (01, 02, 03...) in the order they appear in the prompt. The final CLAUDE.md is always the last file generated.

## Express Mode Grouping

When building Express mode, group selected sections into exactly 4 mega-sections. Suggested groupings:

1. **What you do** -- Revenue/process/tech stack/team sections
2. **What hurts** -- Pain points/constraints/data reality sections
3. **What's defensible** -- Existential/client value/data assets/new models sections
4. **What to build** -- AI opportunities/quick wins/pilots sections

Adjust labels and contents based on the specific sections selected.
