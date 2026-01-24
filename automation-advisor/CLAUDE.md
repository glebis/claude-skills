# Automation Advisor - Project Context

## Design Context

### Users
**Who**: Knowledge workers, developers, and business owners evaluating whether to automate repetitive tasks.

**Context**: Professional decision-making sessions, often during strategic planning or workflow optimization. Users need to make rational, data-backed choices about time investment vs. automation benefits.

**Job to be Done**: Transform vague intuition ("this feels tedious") into quantified ROI analysis with clear recommendations. Help users confidently decide: automate now, maybe later, or stay manual.

### Brand Personality
**Three Words**: Curious, Refined, Confident

**Voice & Tone**:
- Intellectually curious, not prescriptive
- Sophisticated efficiency (Superhuman aesthetic)
- Data-driven but human-centered
- Guides without patronizing

**Emotional Goals**:
- **Primary**: Spark curiosity about automation opportunities
- **Secondary**: Build confidence through structured analysis
- **Tertiary**: Provide calm clarity in decision-making

### Aesthetic Direction
**Visual Tone**: Refined efficiency with purposeful minimalism. Dark theme optimized for focus, not theatrics.

**References**:
- Superhuman: Premium attention to detail, keyboard-first efficiency, sophisticated dark UI
- Design System: Blue (#3B82F6) → Purple (#8B5CF6) gradient palette (established)

**Anti-References**:
- ❌ Generic SaaS: Avoid gratuitous gradients and 2020s AI startup clichés
- ❌ Gamified: No playful badges/points—this is serious analytical work
- ❌ Trendy maximalism: No glassmorphism or excessive visual flair

**Color Strategy**:
- Semantic color coding for decisions (green = automate, amber = maybe, red = stay manual)
- Warm-tinted neutrals instead of pure grays (OKLCH for sophistication)
- Purposeful color, not decoration

**Theme**: Dark mode only (optimized for professional focus sessions)

### Design Principles

1. **Curiosity-Driven Clarity**
   Invite exploration through clear information hierarchy. Every question should feel like discovery, not interrogation. Progressive disclosure reveals complexity only when users want deeper understanding.

2. **Data Integrity, Human Warmth**
   Present objective analysis with professional warmth. Use semantic color to reinforce meaning (green for "go", amber for "consider", red for "stop"). Avoid sterile enterprise aesthetics while maintaining analytical rigor.

3. **Refined Efficiency**
   Every pixel serves a purpose. Sophisticated minimalism means removing obstacles between users and insights. Superhuman-level attention to interaction details (keyboard shortcuts, instant feedback, smooth transitions).

4. **Confident Guidance, Not Prescription**
   The tool advises, users decide. Design should feel like a trusted analyst presenting findings, not an automated gatekeeper. Use language like "Consider automating" rather than "You must automate."

5. **Accessibility Without Compromise**
   WCAG AA compliance is non-negotiable. Semantic color must be reinforced with text/icons. Focus states, keyboard navigation, and reduced motion support are essential—but invisible to users who don't need them.

---

## Implementation Notes

- Tech stack: Python Flask backend, vanilla HTML/CSS/JS frontend, Groq for voice
- Current state: Design system established, recently refined for "quieter" aesthetic
- Voice-enabled interface for accessibility and efficiency
- Multi-user session support for concurrent analysis sessions
