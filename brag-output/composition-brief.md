# HyperFrames Composition Brief: BodyLingo

## Objective
Create a short, polished launch-style brag video for BodyLingo.

## Output
- Composition directory: `brag-output/composition/`
- Rendered video: `brag-output/brag.mp4`
- Format: landscape — 1920x1080
- Duration: 22 seconds

## Source Material
- Project root: `/Users/annmaria/Desktop/BodyLingo`
- Primary files read: `frontend/index.html`, `frontend/src/App.tsx`, `frontend/src/styles.css`, `backend/data/lessons.json`, `backend/alembic/versions/20261017_03_scenarios.py`
- Product name: BodyLingo
- Tagline / strongest claim: “communication, with care”; “There’s more than one way to connect.”
- Key UI or visual moment to recreate: lesson view + quiz response, then scenario practice screen
- Copy that must appear verbatim:
  - “A furrowed brow or a brief smile”
  - “Facial Expressions Without Assumptions”
  - “You notice someone frowning during a conversation. What is a useful next step?”
  - “Consider the context and ask gently if something is on their mind”
  - “That’s right.”
  - “Try a moment from everyday life.”
  - “There’s more than one way to connect.”
  - “communication, with care”

## Creative Direction
- Tone preset: polished
- Creative direction: quiet, human-centered product film
- Interpretation: confident, caring pacing, generous readable holds, and restrained motion.
- Angle: One cue can invite more than one interpretation. Follow a learner from a real lesson, through its quiz, into branching practice.
- Hook: “A furrowed brow. What might it mean?”
- Outro / punchline: “There’s more than one way to connect.” Resolve into the BodyLingo mark and “communication, with care.”
- Avoid:
  - Generic SaaS language
  - Abstract filler visuals
  - Unrelated visual redesign
  - Unsupported product claims or real personal data

## Visual Identity
- Background: `#f5f7f4`
- Text: `#24322f`
- Accent: `#356b56`, with mint `#e6f0e9`, cream `#f8f7f0`, coral `#dd8d78`
- Display font: Georgia
- Body font: Inter with system sans-serif fallback
- Visual references from the project: rounded sage lesson cards, BodyLingo green brand mark, friendly penguin mascot, context-first quiz feedback

## Storyboard
Use the storyboard in `brag-output/brag-plan.md` as the creative contract.

Scene summary:
1. One visible cue — 3s — real lesson cue card and two context prompts
2. The lesson — 4s — app learning UI and lesson card opening
3. A thoughtful answer — 5s — actual quiz prompt, answer selection, correct feedback
4. Practice with possibility — 6s — scenario library and branching practice paths
5. Brand close — 4s — exact brand line, mark, and tagline

## Audio
- Audio role: quiet polished support
- Audio arc: warm understated opening, restrained selection moment, gentle fade under logo
- Music: `happy-beats-business-moves-vol-12-by-ende-dot-app.mp3`
- Music treatment: around 0.22 volume; preserve clear readable holds; fade out at the close
- Music cue guidance: Hyperframes grid is about 110 BPM. Use 1.635s for the cue cards, 15.285s for a non-text branch accent, and 19.655s for the end-card rule; the grid is saved at `composition/beats/assets/music/happy-beats-business-moves-vol-12-by-ende-dot-app.mp3.json`.
- Audio-reactive treatment: subtly breathe an existing green halo/card presence from per-frame data extracted with HyperFrames’ `hyperframes-creative` helper
- Audio-coupled moments: cue card reveal; quiz choice selection; final brand settle
- SFX selection guidance: no SFX files are bundled; use the music bed only
- SFX analysis guidance: `/Users/annmaria/.codex/skills/brag/assets/sfx/sfx-analysis.md`
- Exact SFX choice: none; no sound assets are included in the skill bundle
- Audio files: place the bundled music under `composition/assets/music/`

## HyperFrames Instructions
Use the HyperFrames composition contract and current CLI conventions. Build a standalone 20-second 1920x1080 HTML composition with the actual BodyLingo copy and UI-shaped scenes, deterministic seek-safe animations, and the bundled music bed. Run `npx hyperframes check`, inspect snapshots, then render locally. Keep all output local; do not publish or upload.
