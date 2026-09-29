# BIS Sahayak — UI Deliverables

Generated from `../bis-sahayak-design-spec.md` (SIH26107 · Team Hack Horizon).
One design system, three surfaces — *"Same RAG backend, same citations, three doors in."*

Open **`index.html`** as the entry point, or jump straight to a surface.

## What's inside

| Spec § | Deliverable | File(s) |
|---|---|---|
| §2 | Shared design system (tokens, bubbles, citation chip, confidence badge, seal, language switcher, mic, quick chips, source drawer) | `assets/css/bis.css` |
| — | Supabase data layer (optional — chat persistence, labs, standards) | `assets/js/supabase.js` |
| — | Supabase schema, RLS policies and seed data | `supabase/migrations/*.sql` |
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

## Supabase

The site runs entirely on local fixtures until it is pointed at a project — zero
network calls. `assets/js/supabase.js` ships already configured for the linked
project, so cloning the repo gives you a working connection immediately.

**Point it at your own project** (Supabase CLI, via `npx` so nothing global is
installed):

```bash
npx supabase login                       # browser flow, or --token <access token>
npx supabase init                        # creates supabase/config.toml
npx supabase link --project-ref <ref>
npx supabase db push                     # applies supabase/migrations/*.sql
```

The migration creates `chat_messages`, `labs` and `standards`, turns on Row
Level Security, and seeds the labs and standards the UI already ships with.
No CLI? Paste the same file into Supabase → SQL Editor instead.

Then put your values in the config block at the top of `assets/js/supabase.js`
(the only place they live):

```js
window.BIS_SUPABASE_URL      = "https://YOUR-PROJECT.supabase.co";
window.BIS_SUPABASE_ANON_KEY = "eyJ...";
```

The anon key is public by design — it ships in the browser and is guarded by the
RLS policies in the migration, so committing it is expected. **Never commit the
`service_role` key.** Leave both values empty and nothing changes.

Once configured:

| Surface | What Supabase does |
|---|---|
| Chat (portal, app, WhatsApp, entry demo) | Every turn is written to `chat_messages` with the session id (`BIS.sessionId()`), language, confidence and citations. Read it back with `BISSupa.loadMessages(sessionId)`. |
| Lab Finder | Reads `labs` and swaps them in over the six fixtures once they arrive. |
| Recommender | Reads `standards`; re-renders results if you had already searched. |

Three properties hold everywhere, so nothing can regress: the fixtures render
first and stay visible until data lands, a failed or empty read silently falls
back to fixtures, and `BISSupa` never rejects or logs a console *error*.

> Seeding note: `tools/verify.mjs` asserts the seeded baseline (6 labs; the LED
> rule resolving to 3 standards). If you add rows to `labs` or `standards`,
> update those two expectations alongside them.
