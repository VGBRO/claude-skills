---
name: sf-html-report
description: >
  Generate a polished HTML report, story, or presentation using Salesforce visual language.
  Invoke when the user says "use Salesforce template", "Salesforce taste", "Salesforce style",
  "make an HTML", "build a report", or "create a story" and wants a shareable HTML artifact.
  Produces a single self-contained .html file — no external dependencies.
---

# Salesforce HTML Report Skill

When invoked, produce a single self-contained HTML file using the Salesforce visual design system extracted from official Salesforce decks. No frameworks, no CDN dependencies — everything inline.

---

## Design System

### Color Palette
```
--sf-navy:        #032D60   /* primary dark background, headers */
--sf-blue:        #0B5CAB   /* primary accent, buttons, links */
--sf-blue-bright: #022AC0   /* CTAs, active states */
--sf-blue-light:  #CFE9FE   /* card backgrounds, highlights */
--sf-blue-pale:   #EFF7FE   /* page background, alternating rows */
--sf-indigo:      #5867E8   /* secondary accent, charts */
--sf-indigo-light:#BEC7F6   /* indigo tints */
--sf-red:         #D33900   /* danger, high risk, alerts */
--sf-gray-text:   #59575C   /* body text */
--sf-gray-light:  #F3F3F3   /* dividers, subtle backgrounds */
--white:          #FFFFFF
```

### Typography
```
Headlines/Numbers : 'Salesforce Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif
                    font-weight: 700-800
                    Use for: slide titles (36-48px), stat numbers (48-72px), section heads (24-32px)

Body/Labels       : 'Salesforce Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif
                    font-weight: 400-500
                    Use for: body text (14-16px), labels (11-13px), captions (11px)

Avoid             : Google Fonts CDN, external font loading — use system stack fallbacks only
```

### Layout Principles
- **16:9 slide-like pages** or full-width scrolling documents
- **Full-bleed navy header** (`#032D60`) with white headline + light blue (`#CFE9FE`) subtitle
- **Stat cards**: white background, `#CFE9FE` or `#EFF7FE` tint, large bold number in `#032D60` or `#0B5CAB`, small gray label
- **Section headers**: `#032D60` text, 24-28px, bold, with a `#0B5CAB` left border accent (4px)
- **Tables**: light gray header row (`#F3F3F3`), white rows, `#CFE9FE` hover, `#59575C` text
- **Generous whitespace**: 40-48px section padding, 16-20px card padding
- **Border radius**: 8-10px cards, 4px badges
- **Dividers**: `#CFE9FE` or `#F3F3F3`, never harsh black

### Component Patterns

**Stat Card**
```html
<div style="background:#EFF7FE; border-radius:10px; padding:20px 24px; border:1px solid #CFE9FE;">
  <div style="font-size:11px;font-weight:600;color:#59575C;text-transform:uppercase;letter-spacing:0.8px;">Label</div>
  <div style="font-size:42px;font-weight:800;color:#032D60;line-height:1;">Value</div>
  <div style="font-size:12px;color:#59575C;">Sub-label</div>
</div>
```

**Section Header**
```html
<div style="border-left:4px solid #0B5CAB; padding-left:12px; margin-bottom:8px;">
  <div style="font-size:22px;font-weight:700;color:#032D60;">Section Title</div>
  <div style="font-size:13px;color:#59575C;">Subtitle or context</div>
</div>
```

**Badge / Risk Tag**
```html
<!-- High risk -->
<span style="background:#FDECEA;color:#D33900;font-size:11px;font-weight:600;padding:2px 8px;border-radius:12px;">High Risk</span>
<!-- Positive -->
<span style="background:#E8F5E9;color:#2E7D32;font-size:11px;font-weight:600;padding:2px 8px;border-radius:12px;">Proceed</span>
<!-- Neutral -->
<span style="background:#EFF7FE;color:#0B5CAB;font-size:11px;font-weight:600;padding:2px 8px;border-radius:12px;">Premier</span>
```

**Horizontal Bar Chart**
```html
<div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
  <div style="min-width:200px;font-size:12px;color:#59575C;text-align:right;">Label</div>
  <div style="flex:1;height:22px;background:#F3F3F3;border-radius:4px;overflow:hidden;">
    <div style="width:65%;height:100%;background:#0B5CAB;border-radius:4px;display:flex;align-items:center;padding-left:8px;">
      <span style="font-size:11px;font-weight:600;color:white;">Value</span>
    </div>
  </div>
  <div style="font-size:12px;color:#59575C;min-width:40px;">65%</div>
</div>
```

**Nav Tabs**
```html
<nav style="background:white;border-bottom:2px solid #CFE9FE;padding:0 48px;display:flex;">
  <div style="padding:14px 20px;color:#0B5CAB;border-bottom:2px solid #0B5CAB;font-weight:600;font-size:13px;margin-bottom:-2px;cursor:pointer;">Active Tab</div>
  <div style="padding:14px 20px;color:#59575C;font-size:13px;cursor:pointer;">Other Tab</div>
</nav>
```

**Insight Callout**
```html
<div style="background:#EFF7FE;border-left:4px solid #0B5CAB;padding:14px 16px;border-radius:0 8px 8px 0;font-size:13px;color:#032D60;margin-bottom:16px;">
  <strong style="display:block;font-size:14px;margin-bottom:4px;">Insight Title</strong>
  Insight body text here.
</div>
```

---

## File Structure Rules

1. **Single self-contained `.html` file** — all CSS inline in `<style>`, all JS in `<script>` at bottom
2. **No external dependencies** — no CDN, no Google Fonts, no images from URLs
3. **SVG for charts/diagrams** — draw inline, never use Chart.js or D3 from CDN
4. **Tab navigation** with JS `showTab()` for multi-section documents
5. **Mobile responsive** — use CSS grid with `auto-fit` and media queries for <900px breakpoints
6. **Open in browser** after creating: `open <filename>.html`

---

## Output Naming Convention
- Executive story / report: `<topic>_exec_story.html`
- Analysis report: `<topic>_analysis.html`
- Plan / spec: `<topic>_plan.html`

---

## Trigger Phrases
- "use Salesforce template"
- "Salesforce taste" / "Salesforce style"
- "make an HTML" / "build an HTML"
- "create a story" / "executive story"
- "build a report" (when context is Salesforce work)
