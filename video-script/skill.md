---
name: video-script
description: >
  Generate a structured explainer video script from a topic. Produces a JSON script file
  with scene-by-scene narration, visual direction, and timing. Feed the output to /video-render
  to produce the final MP4. Triggers: "video on X", "explainer video", "script for video", "teach me X as a video".
---

# Video Script Skill

Generate a structured, 3b1b-quality explainer video script. The script drives `/video-render` — every field matters for animation quality.

---

## Step 1 — Understand the topic

Before writing:
- Identify the single core insight the video must land (the "aha" moment)
- Identify 2-4 supporting concepts that build to it
- Decide the narrative arc: problem → intuition → mechanism → payoff

3b1b style means: build intuition first, formalism second. Never define before you show.

---

## Step 2 — Write the script

Generate a JSON file at `<topic_slug>_script.json` with this exact structure:

```json
{
  "title": "Short punchy title",
  "topic_slug": "snake_case_identifier",
  "voice": "en-US-AndrewNeural",
  "fps": 30,
  "width": 1920,
  "height": 1080,
  "scenes": [
    {
      "id": "scene_01",
      "title": "Hook / opening question",
      "duration_seconds": 8,
      "narration": "Exact words the narrator speaks. Keep sentences short. Active voice only.",
      "visual_type": "title_card",
      "visual_direction": "Large centered title text fades in. Subtitle slides up from below. Background: deep navy #0F1117.",
      "key_elements": ["title text", "subtitle text"],
      "animation_notes": "Spring fade on title (0-30 frames). Slide up on subtitle (20-50 frames)."
    }
  ]
}
```

### Fields reference

| Field | Description |
|-------|-------------|
| `id` | `scene_01`, `scene_02`, ... — sequential, no gaps |
| `duration_seconds` | How long this scene plays. 5–15s per scene is ideal. |
| `narration` | Exact spoken text. This becomes the audio. Write for ears, not eyes. |
| `visual_type` | One of the types below |
| `visual_direction` | Plain English description of what appears on screen |
| `key_elements` | Array of text strings or labels that appear on screen |
| `animation_notes` | Frame-level hints for the renderer (optional but helpful) |

### Visual types

| Type | Use for |
|------|---------|
| `title_card` | Opening, section breaks, conclusion |
| `concept_reveal` | Introducing a new idea — elements fade in one by one |
| `diagram` | Relationships, flows, architecture — SVG-based |
| `comparison` | Side-by-side contrast of two things |
| `step_list` | Sequential numbered steps |
| `code_walkthrough` | Showing and explaining code |
| `stat_callout` | One big number or fact, centered |
| `transition` | Short scene that links two ideas (2-4s) |

---

## Step 3 — Pacing rules

- **Total video length**: 90–180 seconds is optimal. Longer is allowed but justify each scene.
- **Scenes**: 6–12 scenes for a 2-minute video.
- **Narration density**: ~130 words per minute of speech. Count words, set duration accordingly.
- **Opening hook**: Scene 1 must pose a question or reveal a surprising fact. Never start with a definition.
- **Closing**: Last scene restates the core insight and gives a "now you see it" payoff.

---

## Step 4 — Narration writing rules (ASD-STE100 ~80%)

- Max 20 words per sentence.
- Active voice. No passive constructions.
- No "ensure", "utilize", "commence", "prior to" — use simple words.
- Same word for the same concept throughout.
- Write as if speaking — contractions are fine, jargon is not (unless you define it first).

---

## Step 5 — Output

Save the file: `<topic_slug>_script.json`

After saving, print a summary table:

| Scene | Type | Duration | First 8 words of narration |
|-------|------|----------|---------------------------|
| scene_01 | title_card | 8s | ... |
| ... | | | |

Total duration: X seconds

Then tell the user: "Run `/video-render` to generate the video."
