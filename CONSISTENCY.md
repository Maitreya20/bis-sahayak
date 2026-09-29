# Cross-Surface Consistency Checklist — self-review (§7)

Reviewed against the generated `UI/` output.

- [x] **Same colour tokens on web and app** — all pages import `assets/css/bis.css`;
      tokens defined once in `:root` (§2.2 hex values verbatim). WhatsApp uses
      emoji-equivalent hierarchy instead of colour (§6.1).
- [x] **Citation format identical everywhere** — `📄 [Standard], Clause [clause]`
      produced by `BIS.citationChips()` (web + app fixtures) and hardcoded to the
      same string in `widget/bis-widget.js` and `whatsapp/templates.md`
      (`📄 Source: IS 302 Part 1, Clause 4.2`).
- [x] **Confidence badge logic identical everywhere** — one implementation,
      `BIS.confidenceBadge()` / widget `badge()`: high→✅ green, medium→⚠️ amber,
      low→❌ red (§2.4(4)). WhatsApp prefixes the same three states as emoji (§6.1).
- [x] **Same language set on all 3 surfaces** — English · हिंदी · मराठी switchers on
      portal pages, app screens, widget header, and the WhatsApp welcome list;
      `i18n` in `assets/js/bis.js` covers all three for placeholder/badge strings.
- [x] **Quick-action labels worded identically** — "Find my standard / Certification
      steps / Check hallmark / Find a lab" appear in the portal chat composer, the
      app home grid, and the WhatsApp menu (translated 1:1 in `whatsapp/templates.md` §2).

## Additional notes

- Widget is Shadow-DOM isolated and `position: fixed` (§4.1A) — proven by
  `website/widget-demo.html`, which loads deliberately hostile host CSS.
- Dark mode follows `prefers-color-scheme` on every colour surface (§2.2);
  WhatsApp uses the stock dark chat theme (no custom theming allowed).
- Responsive breakpoints 375 / 768 / 1280 (§4.2): chat collapses
  history|chat|sources → chat|sources → single column with bottom-sheet source drawer.
- All chat/recommender/hallmark fixtures match the `POST /chat` response shape in §3 —
  thin clients, backend can be swapped in without UI changes.
