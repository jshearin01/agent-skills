# Text & Copywriting Slop Reference

## Table of Contents
1. [The Master Slop Word List](#1-the-master-slop-word-list)
2. [Slop Phrase Patterns](#2-slop-phrase-patterns)
3. [Structural Tells](#3-structural-tells)
4. [Linguistic Analysis Heuristics](#4-linguistic-analysis-heuristics)
5. [Domain-Specific Slop](#5-domain-specific-slop)
6. [Remediation Principles](#6-remediation-principles)
7. [Before / After Examples](#7-before--after-examples)

---

## 1. The Master Slop Word List

These words are statistically overrepresented in LLM output vs. human writing (sourced from slop-forensics research across 10 LLMs). Presence of 3+ in a single paragraph is a strong signal. Presence of 8+ in a document is near-certain AI slop.

### Tier 1 — Highest Confidence AI Tells (avoid entirely)
```
delve / delving         tapestry               testament to
meticulous/meticulously pivotal                underscore/underscores
intricate/intricacies   vibrant                garner/garnered
bolster/bolstered       robust                 leverage (as a verb)
revolutionize           transformative         game-changing
cutting-edge            bleeding-edge          groundbreaking
comprehensive           multifaceted           nuanced
synergy/synergize       paradigm shift         unlock (potential of)
harness (the power of)  pave the way           embark on a journey
navigate the complexities  foster a culture of  spearhead
```

### Tier 2 — High Confidence (overused transitions and filler)
```
furthermore     moreover        additionally    in conclusion
in summary      it's worth noting               it's important to
notably         consequently    thus / thereby  indeed
that being said at the forefront of             in today's fast-paced world
in the ever-evolving landscape of
```

### Tier 3 — Context-Dependent (flag only when clustered)
```
crucial     essential   significant  enhance     optimize
innovative  impactful   actionable   scalable    seamless
streamline  empower
```

### Era-Specific Tells (useful for dating AI involvement)
- **2023–mid 2024** (GPT-4 era): delve, tapestry, testament, meticulous, pivotal, landscape, garner
- **Mid 2024–mid 2025** (GPT-4o era): align with, fostering, highlighting, showcasing, emphasizing
- **2025–present**: "not just X, but Y" constructions, "at the intersection of", "thoughtful approach"

---

## 2. Slop Phrase Patterns

### The "Not Just X, But Y" Construction
Overrepresented 3–4x in AI text vs. human writing. Flags immediately.

Examples to catch:
- "Not just a tool, but a partner"
- "Not just about speed, but about quality"
- "Not just features, but experiences"
- "More than just X — it's Y"

**Fix**: Pick one. Either X or Y. The construction usually signals the writer couldn't commit.

### Grandiose Opener Phrases (delete the entire sentence)
- "In today's fast-paced world..."
- "In an era of unprecedented change..."
- "As the digital landscape continues to evolve..."
- "In the rapidly evolving world of..."
- "At the intersection of innovation and..."

**Fix**: Delete the opener entirely. Start with the actual point.

### Hollow Superlatives (replace with specifics)
- "Unparalleled excellence" → name what specifically is excellent
- "Best-in-class solution" → name the benchmark you're comparing against
- "World-class results" → name the result with a number
- "Industry-leading approach" → name the approach and who uses it

### AI Hedge Stacks (pick one hedge or none)
Multiple hedges in one sentence:
- "It's important to note that, in some cases, this may potentially lead to..."
- "While it's possible that this could, under certain circumstances, perhaps..."

**Fix**: Make a claim. Own it. Add a single caveat only if it's genuinely necessary.

### The Disclaimer Sandwich
Pattern: [Positive claim] → [Extensive qualification] → [Vague positive restatement]

Example: "This approach is highly effective. However, results may vary depending on a number of factors including context, implementation, and individual circumstances. That said, many users find it valuable."

**Fix**: State what's actually true. If you don't know, say so directly.

---

## 3. Structural Tells

### The 3-Section Symmetry Trap
AI defaults to perfectly symmetrical lists: 3 features, 3 benefits, 3 steps — all identical word count. Real humans write uneven lists because some points matter more than others.

**Signal**: Every bullet is 15–20 words. Every section is 2 paragraphs. Every paragraph has 3 sentences.

**Fix**: Let important points breathe. Collapse minor ones. Break the symmetry intentionally.

### The "Challenges" Section Boilerplate
A section titled "Challenges" or "Limitations" that:
- Begins with "Despite its [positive attribute], [subject] faces challenges..."
- Ends with optimism about "ongoing initiatives" or "future developments"
- Contains zero specific, named challenges

**Fix**: Name exactly one real challenge in specific terms, or cut the section entirely.

### The Conclusion That Restates the Introduction
AI introductions and conclusions are nearly identical. The conclusion uses "In summary" or "In conclusion" and repeats every point from the intro verbatim.

**Fix**: Conclusions should move forward — what to do next, what it means, or a call to action. Not a recap.

### "Active Social Media Presence" Filler
The phrase "maintains an active social media presence" (or variants) is almost exclusively AI-generated. Same for "particularly on Instagram/LinkedIn/X, where they regularly share..."

**Fix**: Either name a specific account with notable content, or cut entirely.

---

## 4. Linguistic Analysis Heuristics

### Sentence-Level Tells

**Low burstiness**: Human writing alternates short punchy sentences with longer complex ones. AI writing has uniformly medium-length sentences (15–25 words each).

Measure: Scan for any sentences under 8 words. If there are none in a 500-word piece, it's AI.

**Passive voice overuse**:
- "It has been observed that..." → "We found..."
- "It is considered best practice to..." → "Do X because..."
- "Results were achieved through..." → "We achieved results by..."

**Nominalization** (converting verbs into nouns):
- "The implementation of..." → "Implementing..."
- "The utilization of..." → "Using..."
- "The facilitation of learning..." → "Learning..."

**Missing contractions** — formal AI writing avoids them:
- "It is" → "It's" (in casual/marketing contexts)
- "Do not" → "Don't"
- "We are" → "We're"

### Coherence Red Flags

**Confident generalities with no specifics**: "Many users report significant improvements" — which users? What improvements? By how much?

**Unsourced round-number statistics**: "Studies show 73% of..." — which studies?

**Temporal vagueness**: "Recently, there has been a growing trend..." — when? How is "recently" defined?

---

## 5. Domain-Specific Slop

### Marketing / Landing Page Copy

**Slop signals**:
- Every section has an icon + headline + 2-sentence description
- Value props sound like: "Save time. Save money. Grow faster."
- CTA is "Get Started" or "Learn More" (never says what happens next)
- Hero headline contains "effortless", "powerful", "seamless", or "intelligent"
- Features described as solving "modern challenges" or "today's demands"

**Fix checklist**:
- Replace abstract claims with metrics: "Cut your onboarding time in half" not "Streamlined onboarding"
- Name the exact user: "For teams shipping more than twice a week" not "For developers"
- Make the CTA describe the action: "Start your free 14-day trial" not "Get Started"
- Use negative space: what won't this product do?

### B2B / Enterprise Copy

**Slop signals**:
- "Robust solutions for your enterprise needs"
- "End-to-end platform that scales with your business"
- "Trusted by leading organizations worldwide"
- "Digital transformation journey"
- "Drive ROI across your organization"

**Fix**: Replace every abstract claim with a proof point. "Trusted by 200+ teams who ship daily" beats "trusted by leading organizations."

### Technical Documentation

**Slop signals**:
- "Simply run the following command to..."
- "Easily configure the settings by..."
- "Just add the following snippet..."
- Numbered steps all identical in complexity
- "Note: This is important" before a note that is not actually important
- No explanation of *why*, only *what*

**Fix**: Explain consequences. Say what goes wrong if they skip a step. Acknowledge hard parts as hard.

---

## 6. Remediation Principles

### The Specificity Test
Every abstract claim must survive: "Prove it." If you can't replace "improves productivity" with a specific number or named mechanism, cut it.

### The Voice Test
Read aloud. Would a human actually say this in conversation? "Leverage our comprehensive suite of solutions to unlock synergies across your organization" — nobody says this.

### The Opener Test
Delete the first sentence of every paragraph. Does the paragraph still make sense? AI openers usually just restate the paragraph's topic. Cut them.

### The Symmetry Break Test
Deliberately make one list item longer or shorter than the others. If it feels wrong, AI wrote it.

### The Stakes Test
Does the copy communicate what's at stake if the reader doesn't act? AI copy explains features; human copy explains consequences.

---

## 7. Before / After Examples

### Example 1: Landing Page Hero

**BEFORE (AI Slop):**
> In today's fast-paced digital landscape, businesses need a robust solution that empowers teams to leverage their full potential. Our comprehensive platform provides seamless collaboration, enabling organizations to navigate the complexities of modern work and drive meaningful results.

**AFTER (Human):**
> Your team is shipping features. Your customers can't find them. Beacon connects product updates to the people who need them — automatically, at the right moment, without another meeting.

**Principles applied**: Delete the opener. Name a specific problem. Name the mechanism. Drop all Tier 1 slop words.

---

### Example 2: Feature Description

**BEFORE (AI Slop):**
> **Advanced Analytics**
> Our cutting-edge analytics engine provides comprehensive insights into your data, empowering decision-makers to make informed choices and drive impactful outcomes across the organization.

**AFTER (Human):**
> See which features your power users actually use — and which ones they've never touched. Export a heat map in two clicks.

**Principles applied**: Replace adjectives with descriptions. Name a specific user action. Add a concrete detail.

---

### Example 3: Email Subject Line

**BEFORE (AI Slop):**
> Unlock the Power of Our Revolutionary New Feature: Transform Your Workflow Today!

**AFTER (Human):**
> You can now schedule posts 3 months out

**Principles applied**: Feature, not hype. Specific, not vague. No exclamation point.

---

### Example 4: Product Description

**BEFORE (AI Slop):**
> Our solution is meticulously crafted to address the multifaceted challenges that modern teams face. It is important to note that while results may vary, many users have reported significant improvements in their day-to-day workflows, fostering a culture of productivity and collaboration.

**AFTER (Human):**
> We cut Acme Corp's sprint planning from 90 minutes to 20. Here's how.

**Principles applied**: Remove all Tier 1 words. Replace vague social proof with a named example. Show, don't tell.
