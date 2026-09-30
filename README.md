# BIS Sahayak

**Evidence-gated AI assistant for Indian Standards and BIS services**

> *Cites the clause or escalates to a human. Never guessed.*

| | |
|---|---|
| Problem statement | **SIH26107** — AI-powered conversational assistant for Indian Standards and BIS services |
| Organisation | Bureau of Indian Standards (BIS) |
| Theme · Category | Smart Automation · Software |
| Team | **Hack Forge** — ID 125600 |

The pitch deck — **`BIS_Sahayak_SIH2026_Final_v2.pptx`** (6 slides: idea →
technical approach → feasibility → impact → research) — is the source of truth
for this submission. The three things it sets out, and where each one lives in
this repo, are below.

---

## 1 · The problem *(deck, slide 2)*

Finding the right Indian Standard, certification scheme or recognised laboratory
means searching thousands of separate documents — the catalogue alone holds
**14,000+ standards**, alongside schemes, QCO notices and a laboratory
directory. And a wrong answer carries real compliance risk.

- **Fragmented discovery.** Standards, schemes, labs and hallmark rules each
  live in their own place; a manufacturer needs all four to ship a product.
- **Easy to cite the wrong thing.** Amendments and QCO notices make an outdated
  standard easy to miss, and nothing in a PDF search tells you *which clause*
  applies to your product.
- **Language gap.** MSMEs and consumers ask in Hindi and Marathi; most
  reference material does not answer in those languages, and certainly not by
  voice.
- **Helpdesk load.** Repetitive information queries reach a human officer who
  could be spending that time on real cases.

## 2 · The solution *(deck, slides 2–3)*

**One assistant, four surfaces, three languages** — web portal, mobile app,
WhatsApp and an embeddable widget, in English, Hindi and Marathi — covering
standards lookup and recommendation, schemes, certification steps, consumer
queries, hallmarking and lab suggestions from a single knowledge base. Every
surface returns the same answer with the same clause citation.

A single evidence-gated pipeline:

```
   ASK          →  UNDERSTAND   →  RETRIEVE         →  ANSWER              →  ACT
 text or voice     product,         hybrid search       reply + clause         scheme, lab,
 web / app /       intent, user     over the BIS        citation +             hallmark check
 WhatsApp          language         knowledge base      confidence badge       or human handoff
```

**What makes it different**

- **Cite the clause or refuse.** An answer is released only if a retrieved
  clause supports it — never a guessed standard.
- **Confidence triage.** Every reply carries a `high / medium / low` badge;
  low confidence hands off to a human officer with a ticket (target: one
  working day).
- **Made-in-India voice.** Sarvam Saaras v3 (speech-to-text) and Bulbul v3
  (text-to-speech), used in the prototype; BHASHINI and AI4Bharat extend from
  3 towards 22 languages.
- **Version-aware.** Amendments and QCO notices are re-indexed on schedule so
  answers follow the current standard.

## 3 · How the prototype works *(deck, slides 3–4)*

What exists today is the **UI and the contract**, built with zero dependencies —
static HTML/CSS/JS, no build step.

| Stage | How the prototype handles it |
|---|---|
| **Ask** | Chat bars on the portal, app and WhatsApp, plus quick-chip prompts. Language switcher follows the reader across surfaces (`en` / `hi` / `mr`). |
| **Understand** | Intent is matched against a client-side knowledge base; language is carried on every request. |
| **Retrieve → Answer** | `BIS.chat()` returns `{ answer, citations[], confidence, suggested_actions[], audio_url }` — the fixed **`POST /chat`** contract (§3 of the spec). |
| **Act** | Standard recommender, Lab Finder, HUID hallmark check, and suggested next-step actions. |
| **Escalate** | `low` confidence renders a refusal plus escalation affordances instead of a fabricated answer. |

Two properties make the swap to a real backend painless:

- **Fixtures first.** Every response is a canned client-side fixture shaped
  exactly like the live contract, so the UI is complete with no server. On
  network failure it falls back to fixtures rather than failing.
- **One attribute flips it live:** `data-api="https://your-api"` on the
  `bis.js` script tag (or `window.BIS_API_BASE`). Without it, the only network
  call is Google Fonts.

**Evidence today** — `node tools/verify.mjs` drives headless Chrome across all
surfaces and asserts the contract: **11 automated checks pass, zero console
errors.** Answer accuracy on the curated BIS question set is the next gate
(validation plan on slide 6 of the deck).

---

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
| — | Supabase data layer (optional — chat persistence, labs, standards) | `assets/js/supabase.js` |
| — | Supabase schema, RLS policies and seed data | `supabase/migrations/*.sql` |

## Running it

Open `index.html` as the entry point, or jump straight to a surface — there is
no build and no install.

```bash
node tools/verify.mjs   # needs Node 22+ and Chrome or Edge; exit 0 = all good
```

- **Dark mode** follows `prefers-color-scheme` via CSS variables (§2.2).
- **Typography** is Inter + Noto Sans Devanagari, so Marathi/Hindi never
  renders as tofu (§2.3).
- **Responsive** at 375 / 768 / 1280 breakpoints (§4.2).

## Live backend (prototype API)

The same UI can run against the real FastAPI backend in `backend/` — with zero
changes to any HTML/JS file. The server injects `window.BIS_API_BASE` into
every page it serves, and `assets/js/bis.js` automatically switches from
fixtures to live `POST /chat`:

```bash
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload --port 8000
# UI:      http://localhost:8000/            (this landing page)
# portal:  http://localhost:8000/website/    (chat, recommender, labs, hallmark)
# app:     http://localhost:8000/app/        mobile surface
# API:     http://localhost:8000/health      corpus stats + llm/tts status
```

What `POST /chat` does (§3 contract, kept exactly):

1. **Language** — `hi`/`mr` Devanagari auto-detect, `en` default (header/body wins).
2. **Intent** — schema question vs procedure vs lab vs product→standard vs smalltalk.
3. **Hybrid retrieval** — BM25 + vector (TF-IDF style) fused with reciprocal-rank
   fusion and a coverage reranker over 19 standards / 44 clause-level units in
   3 domains (Electronics & IT, Metals & Jewellery, Metals & Steel).
4. **Structured tools** — lab finder (category/state filters matching the Labs
   page), scheme process lookup (CRS/ISI/Hallmarking/FMCS), product→IS mapping.
5. **Grounded generation** — answers are composed *only* from retrieved clause
   excerpts, with `citations[]` (`doc` + `clause` + `url`) always attached.
6. **Confidence + fallback** — `high`/`medium` with citations, `low` + BIS Branch
   Office referral when nothing in the corpus matches.

Works **keyless out of the box** (deterministic composer). Optional env hooks:

| Variable | Effect |
| --- | --- |
| `BIS_LLM_KEY` + `BIS_LLM_MODEL` (+ `BIS_LLM_BASE` for non-OpenAI) | Grounded LLM phrasing over retrieved clauses |
| `SARVAM_API_KEY` | Fills `audio_url` via Sarvam TTS |
| `BIS_PUBLIC_BASE` | API base injected into pages (default `http://localhost:8000`) |

Open a page served by the backend, ask
"Is IS 302 mandatory for home appliances?" and the answer will come from the
live corpus — same shape, same confidence badges, same citation chips.

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

## Research & references

- Retrieval grounds answers in evidence, but retrieval alone does not eliminate
  hallucinations — Magesh et al., *Journal of Empirical Legal Studies*, 2025.
- Standards-applicability research retrieves candidate standards from a
  free-text description and infers applicability — Han, Ceross & Bergmann,
  arXiv:2506.18511, 2025.
- Design implication: evidence checks **plus refusal** are essential for
  high-stakes standards guidance.
- Data sources: BIS Indian Standards catalogue (14,000+ standards), schemes,
  QCOs, laboratory directory; BHASHINI (MeitY), AI4Bharat, Sarvam AI.

*Guidance only — not legal advice.*
