---
name: video-render
description: >
  Render a video from a video script JSON file (produced by /video-script). Scaffolds a Remotion
  project, generates React scene components, creates audio with edge-tts, runs a self-healing
  compile loop, and outputs a final MP4. Triggers: "render the video", "build the video",
  "/video-render", or run automatically after /video-script completes.
---

# Video Render Skill

Take a `<topic_slug>_script.json` file (from `/video-script`) and produce a rendered MP4.

---

## Prerequisites check

Before starting, verify:
```bash
node --version          # must be 18+
python3 -m edge_tts --version 2>/dev/null || echo "install: pip3 install edge-tts"
ffmpeg -version | head -1
ffprobe -version | head -1
```

If edge-tts is missing: `pip3 install edge-tts`

---

## Step 1 — Read the script

Read `<topic_slug>_script.json`. Extract:
- `topic_slug` → project directory name: `<topic_slug>_video`
- `voice` → TTS voice (default: `en-US-AndrewNeural`)
- `fps`, `width`, `height`
- `scenes[]` → each scene's id, duration_seconds, narration, visual_type, visual_direction, key_elements, animation_notes

---

## Step 2 — Scaffold Remotion project

```bash
npx create-video@latest --yes --blank <topic_slug>_video
cd <topic_slug>_video
npm install
mkdir -p src/scenes public/audio
```

The scaffold creates: `package.json`, `tsconfig.json`, `remotion.config.ts`, `src/index.ts`, `src/Root.tsx`.

---

## Step 3 — Generate audio for each scene

For each scene, run:
```bash
python3 -m edge_tts \
  --voice <voice> \
  --text "<narration text>" \
  --write-media public/audio/<scene_id>.mp3 \
  --write-subtitles public/audio/<scene_id>.vtt
```

Then get exact audio duration (use this to set `durationInFrames`):
```bash
ffprobe -v quiet -show_entries format=duration -of csv=p=0 public/audio/<scene_id>.mp3
```

Store each duration. `durationInFrames = Math.ceil(duration_seconds * fps)` — use the AUDIO duration, not the script's `duration_seconds` estimate. Audio is truth.

---

## Step 4 — Generate scene components

For each scene, create `src/scenes/<scene_id>.tsx`.

### Component template

```tsx
import React from 'react';
import {
  AbsoluteFill,
  Audio,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

export const <SceneId>: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();

  // --- animations ---
  // Example: fade in title
  const titleOpacity = spring({frame, fps, from: 0, to: 1, durationInFrames: 30});
  const titleY = interpolate(frame, [0, 30], [40, 0], {extrapolateRight: 'clamp'});

  return (
    <AbsoluteFill style={{backgroundColor: '#0F1117', justifyContent: 'center', alignItems: 'center'}}>
      <Audio src={staticFile('audio/<scene_id>.mp3')} />
      {/* scene content here */}
      <h1 style={{color: 'white', opacity: titleOpacity, transform: `translateY(${titleY}px)`, fontSize: 72, fontWeight: 800, fontFamily: 'system-ui'}}>
        Title Text
      </h1>
    </AbsoluteFill>
  );
};
```

### Visual type patterns

**`title_card`**
```tsx
// Large centered title + subtitle. Spring fade on title (0-30f). Slide up on subtitle (20-50f).
<AbsoluteFill style={{background: 'linear-gradient(135deg, #0F1117 0%, #1A1A2E 100%)', justifyContent: 'center', alignItems: 'center', flexDirection: 'column', gap: 24}}>
  <Audio src={staticFile('audio/<scene_id>.mp3')} />
  <h1 style={{color: 'white', opacity: titleOpacity, fontSize: 72, fontWeight: 800, textAlign: 'center', maxWidth: 1400, margin: 0}}>
    {title}
  </h1>
  <p style={{color: '#4A9EFF', opacity: subtitleOpacity, fontSize: 28, transform: `translateY(${subtitleY}px)`}}>
    {subtitle}
  </p>
</AbsoluteFill>
```

**`concept_reveal`**
Reveal elements one by one with staggered springs:
```tsx
const ELEMENTS = ['Element 1', 'Element 2', 'Element 3'];
const STAGGER = 20; // frames between each element

return (
  <AbsoluteFill style={{background: '#0F1117', padding: 80}}>
    <Audio src={staticFile('audio/<scene_id>.mp3')} />
    {ELEMENTS.map((text, i) => {
      const start = i * STAGGER;
      const opacity = spring({frame: frame - start, fps, from: 0, to: 1, durationInFrames: 25});
      const x = interpolate(frame - start, [0, 25], [-30, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
      return (
        <div key={i} style={{color: 'white', fontSize: 32, marginBottom: 24, opacity, transform: `translateX(${x}px)`}}>
          {text}
        </div>
      );
    })}
  </AbsoluteFill>
);
```

**`diagram`**
Use inline SVG with animated `strokeDashoffset` for path drawing:
```tsx
const pathProgress = interpolate(frame, [0, 60], [1, 0], {extrapolateRight: 'clamp'});
// In SVG: strokeDashoffset={pathLength * pathProgress}
```

**`step_list`**
Numbered steps appearing one at a time, staggered by 25 frames each.

**`comparison`**
Two-column layout, left side fades in first (0-30f), right side second (30-60f).

**`stat_callout`**
Large centered number with count-up animation:
```tsx
const value = Math.round(interpolate(frame, [0, 60], [0, targetNumber], {extrapolateRight: 'clamp'}));
```

**`code_walkthrough`**
Dark code block with monospace font. Lines highlight sequentially using background color animation.

---

## Step 5 — Generate Root.tsx

Replace `src/Root.tsx` entirely:

```tsx
import React from 'react';
import {Composition, Series} from 'remotion';
import {Scene01} from './scenes/scene_01';
import {Scene02} from './scenes/scene_02';
// ... all imports

const ExplainerVideo: React.FC = () => {
  return (
    <Series>
      <Series.Sequence durationInFrames={<scene_01_durationInFrames>}>
        <Scene01 />
      </Series.Sequence>
      <Series.Sequence durationInFrames={<scene_02_durationInFrames>}>
        <Scene02 />
      </Series.Sequence>
      {/* all scenes */}
    </Series>
  );
};

export const RemotionRoot: React.FC = () => {
  const totalFrames = <sum of all durationInFrames>;
  return (
    <Composition
      id="Explainer"
      component={ExplainerVideo}
      durationInFrames={totalFrames}
      fps={<fps>}
      width={<width>}
      height={<height>}
    />
  );
};
```

Also update `src/index.ts`:
```ts
import {registerRoot} from 'remotion';
import {RemotionRoot} from './Root';
registerRoot(RemotionRoot);
```

---

## Step 6 — Self-healing compile loop

Max **15 iterations**. In each iteration:

```bash
npx tsc --noEmit 2>&1
```

If errors:
1. Read the full error output.
2. Identify the root cause (type error, missing import, wrong prop, etc.).
3. Fix the specific file(s) causing the error.
4. Do not guess — read the exact error message and fix exactly that.
5. Re-run tsc.

Common errors and fixes:
| Error | Fix |
|-------|-----|
| `Cannot find module 'remotion'` | Run `npm install` in project dir |
| `Property X does not exist on type` | Check Remotion API — use correct prop names |
| `Type 'number' is not assignable to type 'string'` | Wrap value in template literal or `.toString()` |
| `Module has no exported member` | Check import — use named exports from scene files |
| `staticFile is not a function` | Import from 'remotion', not 'remotion/no-react' |

Stop loop when: `npx tsc --noEmit` exits with code 0.

---

## Step 7 — Render

```bash
npx remotion render . Explainer ../out/<topic_slug>.mp4 --log=verbose 2>&1
```

If render fails:
- Read the error carefully — most are missing audio files or invalid frame counts
- Fix and retry (up to 5 render retries)
- A frame count of 0 means `durationInFrames` was not set correctly — check audio duration calculation

On success:
```bash
open ../out/<topic_slug>.mp4
```

---

## Output summary

When done, print:

```
Video: out/<topic_slug>.mp4
Duration: Xs (N scenes)
Resolution: WxH @ FPS fps
Audio: edge-tts <voice>
```

---

## Directory layout (final)

```
<topic_slug>_video/
├── package.json
├── tsconfig.json
├── remotion.config.ts
├── public/
│   └── audio/
│       ├── scene_01.mp3
│       └── ...
└── src/
    ├── index.ts
    ├── Root.tsx
    └── scenes/
        ├── scene_01.tsx
        └── ...
out/
└── <topic_slug>.mp4
```
