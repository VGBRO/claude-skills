---
name: voice-setup
description: Install and configure voice/STT input for Claude Code on macOS. Installs the claude-stt plugin (local Moonshine model, no cloud), applies known patches for config serialization and long-recording failures, and starts the daemon. Use when a user asks to set up voice input or speech-to-text.
---

# Voice Input Setup for Claude Code

This skill installs and configures the `claude-stt` plugin, which gives you push-to-talk / toggle voice input directly into Claude Code using a local Moonshine STT model (~200MB, no audio sent to any server).

**Hotkey after setup:** `Ctrl+Shift+Space` to start/stop recording.

## Context

The native `/voice` command in Claude Code is behind a server-side feature gate (`tengu_voice_init_gate`) that is not enabled in the Salesforce proxy environment. This plugin is the working alternative — it processes audio fully on-device.

Two bugs exist in `claude-stt@0.1.0` that must be patched after installation:
1. **Config save crash** — `audio_device: None` is not TOML-serializable; setup fails on first run.
2. **Long recording failure** — Moonshine has a ~30s context limit; longer recordings return empty string without chunking.

This skill applies both patches automatically.

---

## Instructions

### Step 1: Check if already installed

```bash
claude plugin list 2>/dev/null | grep claude-stt || echo "NOT_INSTALLED"
```

If output contains `claude-stt`, skip to **Step 4** (apply patches and restart).

### Step 2: Install the plugin

Tell the user to run these two slash commands directly in Claude Code:

```
/plugin marketplace add jarrodwatts/claude-stt
/plugin install claude-stt@jarrodwatts-claude-stt
```

Wait for confirmation that both commands completed before continuing.

### Step 3: Find plugin install path

```bash
find ~/.claude/plugins/cache/jarrodwatts-claude-stt -name "config.py" 2>/dev/null | head -1
```

Store the directory containing `config.py` — call it `PLUGIN_SRC`. It will be something like:
`~/.claude/plugins/cache/jarrodwatts-claude-stt/claude-stt/0.1.0/src/claude_stt/`

### Step 4: Apply Patch 1 — Config serialization fix

Read `config.py` from `PLUGIN_SRC`, then find the `save()` method's `data = {...}` block and replace it so `audio_device` is omitted when `None`.

Find this block in `config.py`:

```python
        data = {
            "claude-stt": {
                "hotkey": self.hotkey,
                "mode": self.mode,
                "engine": self.engine,
                "moonshine_model": self.moonshine_model,
                "whisper_model": self.whisper_model,
                "sample_rate": self.sample_rate,
                "max_recording_seconds": self.max_recording_seconds,
                "audio_device": self.audio_device,
                "output_mode": self.output_mode,
                "sound_effects": self.sound_effects,
            }
        }
```

Replace with:

```python
        stt_section: dict = {
            "hotkey": self.hotkey,
            "mode": self.mode,
            "engine": self.engine,
            "moonshine_model": self.moonshine_model,
            "whisper_model": self.whisper_model,
            "sample_rate": self.sample_rate,
            "max_recording_seconds": self.max_recording_seconds,
            "output_mode": self.output_mode,
            "sound_effects": self.sound_effects,
        }
        if self.audio_device is not None:
            stt_section["audio_device"] = self.audio_device
        data = {"claude-stt": stt_section}
```

### Step 5: Apply Patch 2 — Long recording chunking

Read `engines/moonshine.py` from `PLUGIN_SRC`, then find the `transcribe()` method and replace it with a version that chunks audio into 30-second segments.

Find this entire method:

```python
    def transcribe(self, audio: np.ndarray, sample_rate: int = 16000) -> str:
        """Transcribe audio to text.

        Args:
            audio: Audio data as numpy array (float32, mono, 16kHz recommended).
            sample_rate: Sample rate of the audio.

        Returns:
            Transcribed text, or empty string if transcription fails.
        """
        if not self.load_model():
            return ""

        try:
            # Moonshine expects float32 audio normalized to [-1, 1]
            if audio.dtype != np.float32:
                audio = audio.astype(np.float32)

            # Normalize if needed
            max_val = np.abs(audio).max()
            if max_val > 1.0:
                audio = audio / max_val

            # Use the transcribe function from moonshine_onnx
            result = _transcribe_fn(audio, model=self._model)

            # Result is a list of strings (batch results)
            if isinstance(result, list) and len(result) > 0:
                return result[0].strip()
            elif isinstance(result, str):
                return result.strip()

            return ""

        except Exception:
            self._logger.exception("Transcription failed")
            return ""
```

Replace with:

```python
    # Moonshine's decoder context fits ~30s of audio at 16kHz
    _CHUNK_SAMPLES = 30 * 16000
    _OVERLAP_SAMPLES = 1 * 16000  # 1-second overlap to avoid cutting mid-word

    def _transcribe_chunk(self, audio: np.ndarray) -> str:
        result = _transcribe_fn(audio, model=self._model)
        if isinstance(result, list) and len(result) > 0:
            return result[0].strip()
        if isinstance(result, str):
            return result.strip()
        return ""

    def transcribe(self, audio: np.ndarray, sample_rate: int = 16000) -> str:
        """Transcribe audio to text.

        Args:
            audio: Audio data as numpy array (float32, mono, 16kHz recommended).
            sample_rate: Sample rate of the audio.

        Returns:
            Transcribed text, or empty string if transcription fails.
        """
        if not self.load_model():
            return ""

        try:
            # Moonshine expects float32 audio normalized to [-1, 1]
            if audio.dtype != np.float32:
                audio = audio.astype(np.float32)

            # Normalize if needed
            max_val = np.abs(audio).max()
            if max_val > 1.0:
                audio = audio / max_val

            # Chunk long recordings — Moonshine degrades / fails above ~30s
            if len(audio) <= self._CHUNK_SAMPLES:
                return self._transcribe_chunk(audio)

            parts = []
            start = 0
            while start < len(audio):
                end = min(start + self._CHUNK_SAMPLES, len(audio))
                chunk = audio[start:end]
                text = self._transcribe_chunk(chunk)
                if text:
                    parts.append(text)
                # Advance by chunk size minus overlap so we don't repeat words
                start += self._CHUNK_SAMPLES - self._OVERLAP_SAMPLES

            return " ".join(parts)

        except Exception:
            self._logger.exception("Transcription failed")
            return ""
```

### Step 6: Check Python version

```bash
python3 --version 2>/dev/null || python --version 2>/dev/null || echo "NOT_FOUND"
```

- Python 3.10+ → use that command in Step 7.
- Python 3.9 or lower → install 3.12 first:
  ```bash
  brew install python@3.12
  ```
  Then use `python3.12` in Step 7.
- NOT_FOUND → install Python via Homebrew as above.

### Step 7: Run setup script

```bash
python3.12 ~/.claude/plugins/cache/jarrodwatts-claude-stt/claude-stt/0.1.0/scripts/setup.py
```

(Replace `python3.12` with whatever was detected in Step 6.)

Expected success output ends with:
```
Setup complete.
Press ctrl+shift+space to start, press again to stop.
```

### Step 8: Grant Accessibility permission (macOS only)

The daemon needs Accessibility permission to detect the hotkey. Tell the user:

> Open **System Settings → Privacy & Security → Accessibility** and enable your terminal app (Terminal, iTerm2, or Ghostty). Then come back here.

Once they confirm it's done, restart the daemon so it picks up the permission:

```bash
PLUGIN_PATH=~/.claude/plugins/cache/jarrodwatts-claude-stt/claude-stt/0.1.0/scripts/exec.py
python3 $PLUGIN_PATH -m claude_stt.daemon stop 2>/dev/null; sleep 1
python3 $PLUGIN_PATH -m claude_stt.daemon start &
sleep 3
python3 $PLUGIN_PATH -m claude_stt.daemon status
```

### Step 9: Verify

Confirm the daemon is running and the hotkey is active. Tell the user:

> **Press Ctrl+Shift+Space** to start recording. Speak, then press again to stop. Your text will be injected into the active input field.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| Hotkey does nothing | Accessibility not granted, or granted before daemon started — re-grant and restart daemon (Step 8) |
| Long recordings return nothing | Patch 2 not applied — reapply Step 5 and restart daemon |
| `TypeError: NoneType not TOML serializable` on setup | Patch 1 not applied — reapply Step 4 and re-run setup |
| `No audio input device` | Check System Settings → Privacy & Security → Microphone |
| Daemon won't start | Run `python3 ~/.claude/plugins/cache/jarrodwatts-claude-stt/claude-stt/0.1.0/scripts/exec.py -m claude_stt.daemon status` and share the output |
