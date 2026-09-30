# AUDIT — BIS Sahayak UI deliverables

Static audit of `D:\BIS Designs\UI` (9 pages, 2 JS modules, 1 CSS system).
Two parts: **§1 Network / endpoint inventory**, **§2 Issues** (fixed vs open).
Everything "fixed" was verified behaviourally by `tools/verify.mjs` (11 checks, exit 0)
plus CDP assertions — this folder is not a git repo, so behaviour is the diff.

---

## §1 Endpoint & network inventory

The prototype is intentionally offline-first: **the only request a page makes on its own is Google Fonts.**
One API endpoint exists and is opt-in.

| # | Endpoint / URL | Direction | Where | Status |
|---|---|---|---|---|
| 1 | **`POST {base}/chat`** → `{ message, language }` → `{ answer, citations[], confidence, suggested_actions[], audio_url, session_id }` | outbound, opt-in | `assets/js/bis.js:169` (`BIS.chat`); widget parity at `website/widget/bis-widget.js:133` (commented) | **Off by default** — fires only when the page opts in via `<script … data-api="https://…">` or `window.BIS_API_BASE`; otherwise resolves from local fixtures after a simulated 450–850 ms delay. On network failure it logs `[BIS] /chat unreachable …` and **falls back to fixtures** rather than failing the UI. |
| 2 | **`bissahayak://chat?q=…`** | app deep link (documented, never fired by this UI) | `index.html:333`, `app/index.html:187`, `app/index.html:398` | Documentation only — matches spec §5.3; no `location.href = bissahayak:` anywhere. |
| 3 | **`https://cdn.bissahayak.gov.in/widget/bis-widget.js`** | embed snippet shown in docs | `website/widget-demo.html:56` | Documentation only — the demo page loads the local `website/widget/bis-widget.js`. |
| 4 | **`https://fonts.googleapis.com/css2?family=Inter…&family=Noto+Sans+Devanagari…`** (+ `fonts.gstatic.com` preconnect) | outbound, automatic | every `*.html` head (7 pages) | **The only unconditional network request.** System-font fallbacks declared, so offline rendering is still correct. |
| 5 | Citation links | in-page navigation | `assets/js/bis.js:227`, static chips in `index.html:392`, `app/index.html:301/308/359` | Fragment/deep-page targets: `#source-is302-4-2`, `#recommender`, `#labs`, plus real cross-page links `website/chat.html?q=…` (read by `chat.html:197`) and `website/recommender.html#cert` (exists at `recommender.html:79`). No dead citation target found. |
| 6 | Fixture-only data sources | local | `assets/js/bis.js` KB; `website/hallmark.html`, `website/lab-finder.html`, `website/recommender.html` | HUID verification, lab directory and standard recommendation are **client-side canned fixtures** — no endpoint exists for them yet. |

**No other egress:** no websockets, no `sendBeacon`, no analytics, no image/font CDN beyond #4,
no `XMLHttpRequest` besides the single opt-in `fetch` in #1.

---

## §2 Issues

### 2.1 Fixed — functional / correctness

| Sev | Issue | File | Fix |
|---|---|---|---|
| High | Horizontal overflow: doc panel pushed the 3-column chat grid wider than the viewport | `whatsapp/index.html` | `minmax(0,1fr)` + `.doc-panel { min-width: 0 }` |
| High | 15 dead fragment links — frames had no ids (`#permissions`, `#home`, `#chat`, `#standards`, `#notes`) so tab bar / skip link did nothing; Labs linked to a fragment instead of the real page | `app/index.html` | Frame ids added, Labs → `../website/lab-finder.html`; `tools/verify.mjs` asserts `deadFragments.length === 0` |
| High | `data-auto` widget mounted a *second* instance instead of using the documented `#widget-root` | `website/widget/bis-widget.js` | Mounts into existing `#widget-root` (`dataset.bisMounted === "1"`) |
| High | Invalid HTML: `<li>` used as a bare flex child outside any list | `whatsapp/index.html` | Wrapped in `<ul>`; check asserts `bareLi === 0` on both surfaces |
| Med | Duplicate label **"Clause Clause 4.2"** — fixtures stored `"Clause 4.2"` *and* the chip rendered its own `Clause ` prefix | `assets/js/bis.js`, `recommender.html`, `hallmark.html` | Data normalized to bare clause numbers; `citationChips()` strips any stray prefix |
| Med | Language choice reset on every page load → reader had to re-pick Marathi per surface; and even after restoring, pages listening for `bis:lang` never heard about it (placeholder stayed English) | `assets/js/bis.js` | `localStorage["bis-lang"]` persisted + `restoreLanguage()` now **dispatches `bis:lang`**; verified end-to-end by an iframe round-trip check |
| Med | WhatsApp thread timestamps could go backwards after several replies | `whatsapp/index.html` | Monotonic thread clock |
| Med | Main menu didn't match the documented template (missing `Change language / भाषा बदला` row); feedback row used an ad-hoc control instead of the documented `🔊 Listen / 👍 Helpful / 👎 Not quite` trio | `whatsapp/index.html`, `templates.md` | List message = 6 rows incl. language row; documented feedback trio for static *and* dynamic messages; `templates.md` Marathi/Hindi cells re-synced to shipped strings |
| Med | Widget fixtures violated the §3 contract (`suggested_actions`, `session_id` missing) | `website/widget/bis-widget.js` | Parity with `BIS.chat()` |
| Med | Voice-composer was a non-focusable fake `<div>`; status bar announced to screen readers; 7 phone frames shared one tab-bar label; unselected toggles exposed no state | `app/index.html` | Real focusable control, `aria-hidden` status bar, unique `aria-label`s, `aria-pressed="false"` everywhere |
| Med | Chat history entries and citation chips in the app were inert | `website/chat.html`, `app/index.html` | `data-q` handlers replay the thread; citation hrefs → real portal/deep-page links |
| Low | Every page 404'd on `/favicon.ico` (console noise on all 10 pages) | root | Root `favicon.ico` added → console clean (`logs: []` on all checks) |
| Low | Entry page claimed "8 pages" — there are 9 | `index.html` | Corrected |
| Low | Empty chat state sat at the top instead of centred in the column | `website/chat.html` | `.chat-scroll` flex + `.chat-empty { margin: auto }` |
| Low | Only 1 of 9 pages had an `<h1>` | `whatsapp/index.html` | Header added |

### 2.2 Fixed — visual / design-system

| Issue | Where | Fix |
|---|---|---|
| Prototype looked flat — no visual layer beyond the token sheet | `assets/css/bis.css` §2.5 | Tricolour certification stripe under the nav, blueprint grid paper, rotating dashed-ring rubber-stamp seal, mono `--font-mono` for IS/clause/hex data, orchestrated `.reveal` scroll entrance, typing dots |
| Grid overlay too faint to read as paper (2% alpha) | `bis.css` | 14% alpha + wider mask fade |
| Seal overlapped demo answer text | `index.html` | `.demo .a { padding-right: 70px }` |
| Entry page was a bare index, not a showcase | `index.html` | Rewritten: hero + live "ask → type → cite → stamp" demo, 9-surface cards, `/chat` contract doc, click-to-copy token swatches, component gallery |
| Ask bar was static | `website/index.html` | Typed ghost placeholder (pauses on focus, reduced-motion safe) + 3-step strip |
| Spec §2.2 tokens weren't referenceable from the page | `index.html` | Swatches copy hex/`var()` to clipboard |

### 2.3 Open — known, deliberate, or needs a decision

| Sev | Issue | Notes |
|---|---|---|
| Med | **Widget's live endpoint is commented out** (`bis-widget.js:133`) and would resolve relative `/chat` against the *host page's* origin when embedded cross-origin | Before shipping the widget: give it a `data-api` attribute (same opt-in as `BIS.chat`) or an absolute base URL. Fixtures keep the demo working meanwhile. |
| Med | **Fixture citation URLs are fragments** (`#source-is302-4-2`, `#source`, …). Inside the widget's Shadow DOM / an embedding host page these resolve against the *host* document, not a BIS document | Wire absolute `https://…` document URLs when the backend lands; `BIS.chat()` already passes `c.url` through untouched, so no UI change needed. |
| Low | `audio_url: "#audio-demo"` points at a non-existent audio file | Placeholder by design (no audio assets in scope); the Listen control is a prototype affordance. |
| Low | Google Fonts is a third-party dependency on an otherwise self-contained deliverable | Already mitigated with system fallbacks; if the deliverable must be fully offline, self-host the two WOFF2 files. |
| Low | Hallmark / lab finder / recommender data is fixture-only (no endpoint in spec §3 covers them) | If they go live they need either a `/verify-huid`, `/labs` endpoint or client-side datasets — currently out of the documented contract. |
| Low | No CSP / security headers (static folder, opened from disk or a plain server) | Add `Content-Security-Policy` (`default-src 'self'`; `style-src` Google Fonts) at deploy time. |
| Info | Static + no build step is a hard constraint | No dependencies added; `tools/verify.mjs` is dependency-free Node (in-process server + CDP) and does not affect the deliverable. |

---

## §2.4 Prototype backend status (backend/, post-integration)

The FastAPI backend in `backend/` now serves every page with
`window.BIS_API_BASE` injected into `<head>` (no UI file edits), so `BIS.chat()`
switches from fixtures to live `POST /chat` automatically. Status of the
previously-open items:

| Previously open | Status now |
|---|---|
| Widget's live endpoint commented out | **Unchanged for the embeddable widget** (its Shadow-DOM fixtures still demo); host pages served by the backend get live `/chat` via `BIS.chat()`. Give the widget a `data-api` when embedding externally. |
| Fixture citation URLs are fragments | **Resolved in live mode** — `/chat` returns absolute/`/website/…` URLs; fixtures untouched for offline demo. |
| Lab finder / recommender fixture-only | **Resolved** — `GET /labs` and `GET /standards/search` exist and both pages now fetch them when served by the backend (mapped onto the fixture shape); fixtures remain the offline fallback. |
| `audio_url` placeholder | Still `null`/demo keyless; fills via `SARVAM_API_KEY` env hook. |
| No CSP headers | Unchanged (dev prototype); add at deploy time. |

Keyless by default: answers are composed from the clause-level corpus
(19 standards / 44 clauses, en/hi/mr) with citations + confidence + low-confidence
fallback to BIS Branch Office referral. Verified: 51 pytest contract tests,
11/11 demo questions pass the §3 contract over HTTP
(`answer/citations/confidence/suggested_actions/audio_url/session_id`), and
11/11 CDP browser checks pass against the live server (`tools/live-check.mjs`).

---

## §3 How to re-verify

```powershell
node tools\verify.mjs      # exit 0 = all 11 checks pass (needs Chrome/Edge, Node 22+)
```

Checks: entry showcase · portal landing · chat send + citations + source drawer ·
chat history replay · recommender (3 cards, badges, no "Clause Clause") · hallmark
valid/invalid HUID · lab finder filter · widget `#widget-root` mount · app (dead
fragments, lists, `aria-pressed`, unique tab labels) · whatsapp (6-row menu, quick
replies, source line, monotonic clock, h1, no bare `<li>`) · language persistence
across surfaces · **zero console errors on every page**.
