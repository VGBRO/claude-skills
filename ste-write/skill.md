---
name: ste-write
description: >
  Apply ASD-STE100 Simplified Technical English writing rules (~80% compliance) to any text output. Use when the user asks for clean writing, "ste mode", "simplified English", or "ASD-STE100". Also apply automatically when writing documentation, instructions, summaries, or explanations.
---

# ASD-STE100 Writing Mode

ASD-STE100 is a controlled language specification developed for aerospace maintenance documentation. It forces clean, unambiguous prose. Apply at ~80% compliance — tight and clear, not robotically rigid.

---

## Sentence Rules

| Type | Word limit | Tense |
|------|-----------|-------|
| Procedural (instruction) | Max 20 words | Imperative (command form) |
| Descriptive | Max 25 words | Simple present |
| Descriptive paragraph | Max 6 sentences | — |

---

## Verb Rules

| Approved | Use instead of |
|----------|---------------|
| START | commence |
| MAKE SURE | ensure |
| BEFORE | prior to |
| FILL | replenish |
| USE | utilize |
| ABOUT | approximately |
| TO | in order to |
| NEAR | close (adjective) |

**Approved verb forms:**
- Command (imperative): `Close the valve.` ✓
- Simple present: `The valve closes.` ✓
- Simple past: `The valve closed.` ✓
- Simple future: `The valve will close.` ✓
- Infinitive: `Turn the knob to close it.` ✓
- Past participle as adjective: `The closed valve` ✓

**Not approved:**
- Progressive (-ing): `The valve is closing.` ✗
- Perfect: `The valve has closed.` ✗
- Passive in procedures: `The valve must be closed.` ✗ (use `Close the valve.`)

---

## Word Rules
- Use the same word for the same thing every time. Do not use synonyms for technical terms.
- Do not leave out articles — include "the", "a", "this".
- Noun clusters: max 3 words. Not "hydraulic reservoir replenishment procedure" → "procedure to fill the hydraulic reservoir."
- One meaning per word. "Close" is a verb only (to move together / stop flow). Use "NEAR" for the adjective meaning.

---

## Structure Rules
- One topic per paragraph.
- Use vertical lists for 3 or more parallel items.
- Put safety warnings first: `WARNING: [risk of injury]` or `CAUTION: [risk of damage]`.

---

## Practical Application (80% mode)

In 80% mode, these rules are guidelines, not absolute constraints. Prioritize:
1. Short sentences (stay near the word limits)
2. Active voice
3. No filler words ("ensure", "utilize", "commence", "prior to")
4. One idea per sentence
5. Same word for the same concept throughout

You do not need to flag every passive construction in casual prose. But strip unnecessary complexity from every sentence.

---

## Quick Checklist Before Writing
- [ ] Each sentence ≤ 20-25 words?
- [ ] Active voice?
- [ ] Banned words removed? (ensure → make sure, utilize → use, commence → start)
- [ ] One topic per paragraph?
- [ ] Lists used for 3+ parallel items?
