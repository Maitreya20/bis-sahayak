# BIS Sahayak — UI Deliverables

Generated from `../bis-sahayak-design-spec.md` (SIH26107 · Team Hack Horizon).
One design system, three surfaces — *"Same RAG backend, same citations, three doors in."*

Open **`index.html`** as the entry point, or jump straight to a surface.

## What's inside

| Spec § | Deliverable | File(s) |
|---|---|---|
| §2 | Shared design system (tokens, bubbles, citation chip, confidence badge, seal, language switcher, mic, quick chips, source drawer) | `assets/css/bis.css` |
| §4.1B | Portal — landing page (ask bar + 4 feature cards) | `website/index.html` |
| §4.1B | Portal — chat page, 3-column (history \| chat \| live source drawer) | `website/chat.html` |
| §4.1B | Standard Recommender (form → cards with confidence + citation) | `website/recommender.html` |
| §4.1B | Lab Finder (filters + map/list of recognized labs) | `website/lab-finder.html` |
| §4.1B | Hallmark Verification (HUID → verified / not verified) | `website/hallmark.html` |
| §4.1A | Embeddable widget (collapsed + expanded 380×560, Shadow DOM, fixed positioning) | `website/widget-demo.html`, `website/widget/bis-widget.js` |
| §5 | Mobile app — onboarding, home, chat, standard detail, voice mode, 5-tab bar | `app/index.html` |
| §6 | WhatsApp — conversation flow, message template library, flowchart | `whatsapp/index.html`, `whatsapp/templates.md`, `whatsapp/flow.md` |
| §7 | Cross-surface consistency checklist (self-review results) | `CONSISTENCY.md` |
| — | Audit: endpoint inventory + fixed/open issue list | `AUDIT.md` |
| — | Regression checks (dependency-free, exits non-zero on failure) | `tools/verify.mjs` |

## Notes

- **Mock data:** all chat/recommender/hallmark responses are canned client-side fixtures shaped exactly like the `POST /chat` contract in §3 (`answer`, `citations[]`, `confidence`, `suggested_actions[]`, `audio_url`) — swap in the real API without touching the UI.
- **Point it at the real backend:** add `data-api="https://your-api"` to the `bis.js` script tag (or set `window.BIS_API_BASE` before it) and `BIS.chat()` starts doing a real `POST {base}/chat` with `{ message, language }`, falling back to fixtures if the request fails. Without it, zero network calls are made besides Google Fonts.
- **Dark mode:** follows `prefers-color-scheme` via CSS variables (§2.2).
- **Typography:** Inter + Noto Sans Devanagari fallback so Marathi/Hindi never renders as tofu (§2.3).
- **Responsive:** 375 / 768 / 1280 breakpoints (§4.2).
- Everything is static HTML/CSS/JS — no build step, no dependencies (fonts load from Google Fonts with system fallbacks).
