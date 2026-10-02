---
name: html-explainer
description: >
  Generate a beautiful, interactive, self-contained HTML explainer page for any topic. Use when the user says "explain this in HTML", "make an interactive explainer", "3b1b style", "build a visual for this", or any time a concept benefits from visual, interactive treatment. Produces a single .html file — no external dependencies.
---

# HTML Explainer Skill

Generate bespoke, interactive HTML explainer pages for complex topics. The standard is 3b1b (3Blue1Brown) quality — build intuition visually and interactively, not just textually.

---

## Design Principles

### Goal
Make the concept as easy to understand as possible. Every design choice serves comprehension, not decoration.

### Layout
- Full-width, single scrolling document or tabbed multi-section layout
- Generous whitespace: 40-60px section padding
- Max content width: 900px, centered
- Dark header section + light body creates strong visual hierarchy

### Typography
- System font stack: `-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif`
- Headlines: 700-800 weight, 32-48px
- Body: 400-500 weight, 15-16px, line-height 1.6
- Code: `'Courier New', monospace`, 13px, on `#F5F5F5` background

### Color Palette (neutral default — swap for context)
```
--bg:          #0F1117   /* dark header/hero */
--accent:      #4A9EFF   /* primary highlight */
--accent-soft: #1A3A5C   /* muted accent bg */
--surface:     #FFFFFF   /* card/content background */
--surface-alt: #F7F9FC   /* alternating sections */
--text:        #1A1A2E   /* primary text */
--text-muted:  #6B7280   /* secondary text */
--border:      #E5E7EB   /* dividers */
```
When in Salesforce context, use the sf-html-report palette instead.

---

## Interactive Components

### Tabs
```html
<div class="tabs">
  <button class="tab active" onclick="showTab('tab1')">Section 1</button>
  <button class="tab" onclick="showTab('tab2')">Section 2</button>
</div>
<div id="tab1" class="tab-content active">...</div>
<div id="tab2" class="tab-content" style="display:none">...</div>
<script>
function showTab(id) {
  document.querySelectorAll('.tab-content').forEach(t => t.style.display = 'none');
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.getElementById(id).style.display = 'block';
  event.target.classList.add('active');
}
</script>
```

### Collapsible Sections
```html
<details>
  <summary style="cursor:pointer;font-weight:600;padding:12px 0;">Section title</summary>
  <div style="padding:12px 0 12px 16px;">Content here</div>
</details>
```

### Inline SVG Diagrams
- Draw all charts and diagrams as inline SVG — never use Chart.js, D3, or other CDN libraries
- Use `viewBox` for responsive scaling
- Label everything directly on the diagram

### Animated Callouts
```html
<div class="callout" style="
  background: var(--accent-soft);
  border-left: 4px solid var(--accent);
  padding: 16px 20px;
  border-radius: 0 8px 8px 0;
  margin: 24px 0;
  animation: slideIn 0.3s ease;
">
  <strong>Key insight:</strong> ...
</div>
```

### Step-by-Step Walkthrough
Use numbered steps with visual connectors for sequential processes.

---

## Technical Rules

1. **Single file**: all CSS in `<style>`, all JS in `<script>` at bottom
2. **No external dependencies**: no CDN, no Google Fonts, no external images
3. **SVG only** for all charts/diagrams
4. **Responsive**: CSS grid with `auto-fit` for cards, media queries at 768px
5. **Accessible**: use semantic HTML, `alt` attributes, sufficient color contrast

---

## Content Structure Template

```
[Hero section: title + one-sentence premise]
[Why this matters: 2-3 sentences, the hook]
[Core concept: visual diagram or animated walkthrough]
[Deep dive: tabbed sections for detail]
[Key takeaways: 3-5 bullet callouts]
[Further reading or next steps: optional]
```

---

## File Naming
- Concept explainer: `<topic>_explainer.html`
- Analysis: `<topic>_analysis.html`  
- Guide: `<topic>_guide.html`

After writing the file, always open it: `open <filename>.html`

---

## Quality Bar
Before finishing, ask:
- Does the visual make the concept clearer than prose alone would?
- Can a reader understand the core idea in 30 seconds from the top of the page?
- Are interactive elements adding comprehension value, not just decoration?
