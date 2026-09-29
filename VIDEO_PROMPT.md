# BIS Sahayak — 5-Minute SIH 2026 Video · Generation Prompt + Script

Everything needed to produce the pitch video for **SIH26107 · Team Hack Horizon** on
**Google Flow (Veo 3)** or any other video platform. Facts, screens and flows are
pulled from `README.md`, `AUDIT.md`, `CONSISTENCY.md`, `whatsapp/flow.md`,
`whatsapp/templates.md`, `index.html` and `assets/js/bis.js`.

---

## 0 · Pick your production path

| Path | Best for | What you do |
|---|---|---|
| **A · Hybrid (recommended)** | Winning pitch videos | ~10 AI b-roll clips from Flow/Veo + **screen recordings of the real prototype** + the narration script as voiceover. Judges trust the real UI. |
| **B · Script-to-video tool** | Fastest | Paste §5's script into Pictory / InVideo AI / Canva Magic Video — it auto-matches stock footage. Drop in screen recordings at §6 marks. |
| **C · Full AI** | Showcase only | Extend each Flow scene to 8 s and chain ~38 clips. Slowest and text renders unreliably — not advised for UI demos. |

> **Rule for all paths:** never ask the AI to render the UI or official BIS marks.
> Generate **metaphor b-roll only**; composite real screenshots/recordings and the
> seal/logo in the edit (CapCut / DaVinci Resolve / Premiere).

---

## 1 · Master prompt (paste into Flow / Veo 3 as the project brief)

```
Create a 5-minute cinematic pitch video for "BIS Sahayak", an AI chatbot for Indian
Standards (Bureau of Indian Standards) built for the Smart India Hackathon 2026,
problem statement SIH26107, by Team Hack Horizon.

STYLE: modern Indian documentary-tech aesthetic. Palette locked to BIS Navy #0B2D5B,
Saffron #FF9933, Green #128807 on off-white; occasional blueprint-grid paper texture
and a rotating dashed-ring rubber "source stamped" seal motif. Clean sans-serif
on-screen text (Inter), Devanagari accents for हिंदी/मराठी. Lighting: warm practical
light in workshops/markets, cool soft light on devices. Camera: slow dolly-ins,
macro inserts, subtle parallax; smooth gimbal moves; 16:9, 1080p, 24fps look.

STORY (5 acts): (1) The problem — India's 14,000+ product standards are locked in
dense English PDFs; a small manufacturer risks failed certification, a gold buyer
risks a fake hallmark. (2) The solution — one RAG chatbot brain ("same citations,
three doors in"): web portal, mobile app, WhatsApp. (3) The workflow — every surface
sends POST /chat {message, language}; the pipeline returns answer + clause-level
citations + confidence (✅ high / ⚠️ medium / ❌ low) + suggested actions + audio_url;
voice mode = Sarvam Saaras v3 speech-to-text → same endpoint → Bulbul v3 text-to-speech.
(4) The UI tour — portal chat with live source drawer, Standard Recommender, Lab
Finder, HUID hallmark verifier, embeddable 380×560 Shadow-DOM widget, mobile app with
voice mode and offline cache, WhatsApp flow with quick replies and human handoff
(ticket BIS-####, 1-working-day SLA); language switching English → हिंदी → मराठी.
(5) Use case & close — an appliance maker goes from question to cited standard,
certification steps, and nearby test labs in minutes; end card with team name.

AUDIO: confident female Indian-English narrator (calm, warm, ~140 wpm), soft
percussive tech score, subtle market/workshop ambience, satisfying "stamp" thunk
when a source is cited. On-screen text kept minimal (short labels only — no long
sentences rendered by AI).

AVOID: garbled or long AI-rendered text, watermarks, official government emblems,
logos, readable UI screenshots, distorted hands, morphing faces.
```

**Negative prompt (where supported):** `garbled text, long paragraphs on screen,
watermark, logo, government emblem, extra fingers, warped faces, UI screenshot,
low contrast, flicker`

---

## 2 · Visual style card (attach/repeat with every clip)

- **Palette:** BIS Navy `#0B2D5B` · Saffron `#FF9933` · Green `#128807` · Off-white `#F4F6F9`
- **Type:** Inter for on-screen labels; Noto Sans Devanagari for हिंदी/मराठी words; monospace for "IS 302 · Clause 4.2"
- **Recurring motifs:** tricolour stripe, blueprint grid paper, dashed-ring seal stamp, citation chip `📄 Source: IS 302 Part 1, Clause 4.2`
- **Music arc:** sparse → build at Act 3 → warm resolve at Act 5

---

## 3 · Scene-by-scene Flow/Veo prompts (10 AI clips · 8 s each)

Paste one prompt per clip. Keep dialogue lines for Veo 3's native audio, or mute
clips and lay the §5 voiceover instead (cleaner).

**CLIP 1 — Hook (timeline 0:00–0:08)**
```
Macro slow dolly across shelves of packaged Indian products — pressure cookers,
electric kettles, gold bangles — each bearing a small certification mark. Warm
shop light, shallow depth of field, documentary style, BIS navy and saffron colour
grading. Audio: soft ticking, low drone, one deep "thunk". No text, no readable
labels.
```

**CLIP 2 — The problem (0:08–0:16)**
```
A young Indian manufacturer at a workshop desk at night, buried under stacked paper
standards documents, rubbing her temples, desk lamp glow, blueprint texture faint on
the wall behind. Slow push-in, cinematic documentary, moody navy tones. Audio: paper
rustle, distant clock. No readable text on the pages.
```

**CLIP 3 — The problem, consumer side (0:16–0:24)**
```
Close-up of hands holding a gold bangle under a jeweller's lamp in a busy Indian
market; the buyer's eyes search for a mark that isn't there. Rack focus from bangle
to uncertain face, warm saffron ambience. Audio: market murmur. No text.
```

**CLIP 4 — Transition: three doors (0:24–0:32)**
```
Abstract motion graphic: a glowing navy sphere (a "brain") pulses as streams of
document pages are drawn into it, then three clean doors of light open in saffron,
white and green — one shaped like a browser window, one like a phone, one like a
chat bubble. Minimal flat 3D, blueprint grid backdrop. Audio: rising synth swell.
```

**CLIP 5 — RAG pipeline (1:05–1:13)**
```
Abstract data-flow animation on deep navy: labelled nodes "Knowledge Base", "RAG
Retrieval", "Answer", "Citations", "Confidence" connected by light streams; a clause
card flies out and gets stamped by a rotating dashed-ring seal. Flat tech infographic
style, saffron/green accents, monospace labels. Audio: soft data whooshes, one stamp
thunk.
```

**CLIP 6 — Confidence triage (1:21–1:29)**
```
Three lanes of light in green, amber and red; glowing orbs travel down them — green
ones pass through a checkmark gate, amber slow at a warning gate, red ones divert
into a human-hand slot. Clean minimal 3D motion graphic, navy background. Audio:
three subtle tones high/mid/low.
```

**CLIP 7 — Voice loop (1:38–1:46)**
```
A hand raises a phone; a warm soundwave leaves the mouth, enters the phone, splits
into text particles, recombines and returns as a spoken waveform back out of the
speaker. Dark navy backdrop, saffron waveform, green text particles, macro lens feel.
Audio: soft chime loop mirroring the wave.
```

**CLIP 8 — Three doors in daily life (2:05–2:13)**
```
Triptych montage: a laptop in a government-style office where a small chat widget
pops into the corner of a webpage; a thumb taps a mic on a phone on a moving train;
a hand types a WhatsApp message in a sunlit market stall. Matching navy-saffron
grade across all three. No readable UI text.
```

**CLIP 9 — Use-case b-roll (3:35–3:43)**
```
Sunrise over a small Indian appliance workshop; a confident woman entrepreneur
powers on a mixer assembly line, then checks her phone and smiles. Golden-hour
warmth, slow gimbal arc, hopeful tone. Audio: machines humming up, birds.
```

**CLIP 10 — Outro (4:44–4:52)**
```
On deep navy, a dashed-ring seal rotates and stamps the words "SOURCE STAMPED" in
clean sans-serif; tricolour stripe sweeps beneath as particles settle into calm.
Elegant minimal motion graphic, 2 seconds of hold at the end for an end card.
Audio: final stamp thunk into warm resolve chord.
```

*(Remaining runtime = your screen recordings per §6 + end card made in the editor.)*

---

## 4 · Screen-recording shot list (the real prototype — record at 1920×1080, 60 fps)

Browser zoom 100 %, clean profile, DevTools closed. Dark mode: toggle OS appearance
for one quick "theme flick" shot. Record English first; repeat the two marked 🌐
shots in हिंदी and मराठी for the language montage.

| # | Page | Action | Chat time |
|---|---|---|---|
| S1 | `index.html` | Watch hero demo auto-loop; click chip "Is IS 302 mandatory…"; capture typing dots → answer → citation chips → badge → **seal stamp** | 12 s |
| S2 | `index.html` | Scroll: tokens swatches → component gallery → `/chat` contract code block | 8 s |
| S3 | `website/index.html` | Typed ghost placeholder in ask bar; hover 4 feature cards | 8 s |
| S4 | `website/chat.html` | Send "Is IS 302 mandatory for home appliances?"; open **live source drawer**; replay a history entry | 15 s |
| S5 | `website/recommender.html` | Fill form → 3 result cards with confidence badge + citation | 10 s |
| S6 | `website/lab-finder.html` | Apply state/product filters → map + list update | 10 s |
| S7 | `website/hallmark.html` | Enter valid HUID → ✅ verified; then invalid → ❌ | 12 s |
| S8 | `website/widget-demo.html` | Open widget on the hostile-CSS host page; ask a question inside it | 12 s |
| S9 | `app/index.html` | Onboarding language → permissions → home grid → **voice mode mic** → standard detail → 5-tab nav | 20 s |
| S10 | `whatsapp/index.html` | Send "hi" → welcome list → pick हिंदी 🌐 → main menu (6 rows) → "Check hallmark" → HUID → feedback trio | 20 s |
| S11 | `whatsapp/index.html` | "Find my standard" → cited answer → 🔊 Listen → 👍 Helpful → handoff ticket | 12 s |
| S12 | Any two pages 🌐 | Switch language on page A, reload page B — placeholder/badges follow (persistence) | 10 s |
| S13 | Terminal | `node tools/verify.mjs` → 11 checks pass, exit 0 | 6 s |

---

## 5 · Full narration script (5:00 · ~710 words · ~140 wpm)

Read as voiceover (ElevenLabs / Veo dialogue / human). Numbers on the left = cut point.

**[0:00 — ACT 1 · The problem]**
> Every product sold in India answers to one agency — the Bureau of Indian Standards.
> Over fourteen thousand standards. Hundreds of clauses. A language barrier that spans
> English, Hindi and Marathi. For a small manufacturer, one wrong clause means a failed
> certification. For a consumer buying gold, a fake hallmark means lost savings. The
> information exists — it's just locked inside dense PDFs, scattered portals, and
> offices that close at five.

**[0:35 — ACT 2 · The solution]**
> This is BIS Sahayak — built by Team Hack Horizon for problem statement SIH26107.
> An AI assistant that turns BIS documents into plain-language answers, every one
> stamped with its exact source. One retrieval-augmented brain. Three doors in: a web
> portal, a mobile app, and WhatsApp — because in India, the answer should reach you
> wherever you already are.

**[1:05 — ACT 3 · Workflow of the resources]**
> Here's how a question becomes a verified answer. Every surface speaks one contract:
> POST slash chat. A message and a language go in; the RAG pipeline retrieves the
> relevant clause from the BIS knowledge base, and returns five things: the answer,
> citations down to the clause, a confidence score, suggested next actions, and an
> audio URL. That confidence score drives everything. High confidence gets a green
> verified badge. Medium gets an amber warning to confirm with a BIS office. Low
> confidence never guesses — it escalates to a human officer with a ticket and a
> one-working-day SLA. And if typing isn't your thing, just speak: Sarvam Saaras
> transcribes your voice note, the same endpoint answers it, and Bulbul reads the
> reply back — in your language. The same citation, the same confidence logic, on
> every single surface. That's not three chatbots. That's one brain, three doors.

**[2:05 — ACT 4 · The UI and its modes]**
> Let's open the doors. The portal: ask a question, and the answer arrives with
> clickable citation chips and a live source drawer showing the exact clause it came
> from. Need the right standard? The recommender matches your product to its IS
> number. Shipping electronics for testing? The Lab Finder filters BIS-recognised
> labs by state. Buying jewellery? Paste a HUID — instantly verified or flagged.
> Next, the widget: one script tag, and any government or business site gets the
> full assistant in a 380-by-560 window, style-isolated in a Shadow DOM, so the host
> page can't break it. The mobile app: onboarding in your language, a
> thumb-reachable mic for voice mode, and the last twenty answers cached — because
> standards questions don't wait for good networks. And WhatsApp: no app install at
> all. A menu, quick replies, voice notes — the same four-part answer: verdict,
> plain language, citation, listen. Switch to Hindi or Marathi anywhere, and the
> choice follows you across every surface.

**[3:35 — ACT 5 · Use case and close]**
> Follow one real journey. Priya runs a small appliance workshop. She types one
> question: is IS 302 mandatory for home appliances? Green badge — verified. Clause
> 4.2, electric-shock protection, cited. She taps the certification path — CRS,
> online application, recognised lab, licence. The Lab Finder shortlists labs in her
> state. Total time: four minutes. The same answer, on her phone, in Marathi, on
> WhatsApp, for her supplier across the world. Under the hood, this whole prototype
> is one design system — navy, saffron, green — with no build step, dark mode, and
> an automated test suite that runs eleven regression checks with zero console
> errors. Swap in one attribute, and the fixtures become the live backend.
> BIS Sahayak: answers you can cite, in the language you think in, on the app you
> already use. Team Hack Horizon — SIH 2026. Because every Indian deserves standards
> that speak their language.

---

## 6 · Assembly timeline (Path A — edit map)

| Time | Visuals | Script | On-screen text |
|---|---|---|---|
| 0:00–0:24 | Clips 1–3 | Act 1 | "14,000+ standards · 3 languages · 1 problem" |
| 0:24–0:35 | Clip 4 | Act 2 start | Title card: **BIS Sahayak — One brain, three doors in** |
| 0:35–1:05 | S1 hero demo + Clip 4 reprise | Act 2 end | "Same RAG backend · same citations" |
| 1:05–1:38 | Clip 5 + `/chat` contract code block (S2) | Act 3 first half | Animate the JSON: answer → citations → confidence |
| 1:38–2:05 | Clip 7 + S10/S11 voice-note round trip | Act 3 second half | "Saaras v3 → /chat → Bulbul v3" |
| 2:05–2:50 | S3 → S4 → S5 → S6 → S7 | Act 4 first half | Chips: "Recommender · Lab Finder · HUID check" |
| 2:50–3:35 | S8 widget → S9 app → S10/S11 WhatsApp → S12 🌐 | Act 4 second half | "380×560 · Shadow DOM · offline cache · 3 languages" |
| 3:35–4:20 | Clip 9 + replay S1 → S5 → S6 fast | Act 5 story | Step ticker: Ask → Cite → Certify → Lab |
| 4:20–4:44 | S13 verify.mjs + dark-mode flick + S2 tokens | Act 5 engineering | "11 regression checks · 0 console errors · 0 build steps" |
| 4:44–5:00 | Clip 10 + end card | Closing line | **BIS Sahayak · Team Hack Horizon · SIH 2026** |

**Edit notes:** captions burned in (many judges watch muted); music ducked −12 dB
under VO; stamp SFX on every citation chip appearance; keep each screen shot ≥ 2.5 s;
export 1080p H.264, < 200 MB for the SIH portal.

---

## 7 · Platform quick-settings

- **Google Flow (Veo 3):** Text-to-Video per clip (§3), 16:9, 1080p; use *Ingredients* with a navy/saffron style frame for consistency; use *Frames-to-Video* with a prototype screenshot as the **end frame** to cut cleanly into your screen recordings. Veo outputs 8 s — chain/extend only for b-roll, never for UI.
- **Voiceover:** ElevenLabs (Indian-English voice) or Veo 3 native dialogue; export the §5 script per act for file-per-section control.
- **Alternatives:** Sora / Runway Gen-4 / Luma (b-roll), Pictory / InVideo AI (paste §5 script → auto video), CapCut or DaVinci Resolve (free assembly + captions).
- **Don't:** let any AI render the BIS logo, government emblems, or the UI — composite those from real screenshots in the editor.

## 8 · Pre-submission checklist

- [ ] VO matches cuts (script §5 ↔ timeline §6)
- [ ] Real prototype shown ≥ 60 % of runtime (S1–S13)
- [ ] All three surfaces + widget appear; all three languages appear
- [ ] Citation format `📄 Source: IS 302 Part 1, Clause 4.2` legible at 1080p
- [ ] Confidence triage (✅⚠️❌) and human-handoff SLA mentioned
- [ ] Problem statement **SIH26107** + team name on title and end cards
- [ ] 5:00 ± 5 s, 1080p, captions on, file size within SIH limits
