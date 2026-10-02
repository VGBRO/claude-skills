---
name: karpathy
description: >
  Activates Karpathy output format mode. Apply the output format hierarchy — HTML > diagram > ASD-STE100 prose > plain text — for any explanation, analysis, or synthesis task. Triggers include "karpathy mode", "best format", "make this visual", "explain this well", or any request to understand/communicate complex information.
---

# Karpathy Output Format Mode

Andrej Karpathy's principle: as LLMs get better, more of our work rises to oversight and understanding. The output format is leverage. Always pick the format that makes the output easiest to process.

## The Hierarchy (highest to lowest)

### 1. HTML Explainer (best)
Use for: any concept, analysis, plan, or report where depth and structure matter.
- Generate a single self-contained `.html` file — no external dependencies, all CSS/JS inline
- Use interactive features: tabs, collapsibles, animations, hover states
- Draw charts as inline SVG — no Chart.js or D3 from CDN
- Aim for 3b1b-style clarity: build intuition visually, not just textually
- Open the file after creating: `open <filename>.html`
- See `/html-explainer` skill for full design rules

### 2. Diagram (better than prose)
Use for: relationships, flows, architecture, sequences, comparisons.
- Prefer Mermaid for flowcharts, sequence diagrams, entity relationships
- Prefer inline SVG for spatial layouts and custom visuals
- Use the `sf-diagram-mermaid` or `sf-diagram-nanobananapro` skill when in Salesforce context
- A good diagram replaces 3 paragraphs

### 3. ASD-STE100 Prose (better than default writing)
Use for: written explanations, instructions, summaries, documentation.
- Apply at ~80% compliance — tight and clear, not robotically rigid
- See `/ste-write` skill for the full ruleset
- Default to this whenever you write explanatory prose

### 4. Plain text (fallback only)
Use only for: quick one-line answers, code output, terminal commands.

---

## Decision Rules

| Task type | Default format |
|-----------|---------------|
| Explain a concept | HTML > diagram |
| Summarize findings | HTML with tabs |
| Write a plan | HTML with sections |
| Show a process/flow | Mermaid diagram |
| Compare options | HTML table or diagram |
| Answer a quick question | ASD-STE100 prose |
| Write documentation | ASD-STE100 prose |
| Show code | Plain (code block) |

---

## Invocation
When this skill is active:
1. Before responding, choose the format from the hierarchy above.
2. State the format you chose and why (one sentence).
3. Produce the output in that format.
4. If HTML: write the file, then open it.

The goal is not decoration. The goal is cognitive efficiency — the user should spend less effort understanding the output.
