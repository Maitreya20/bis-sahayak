/* ============================================================
   BIS Sahayak — Embeddable widget (§4.1A)
   Mounted into a host page via:
     <div id="widget-root"></div>
     <script src="widget/bis-widget.js"><\/script>
     BISWidget.mount(document.getElementById("widget-root"));
   Renders inside a Shadow DOM so host-page CSS cannot leak in
   and our styles cannot leak out. Fixed position, bottom-right.
   ============================================================ */

const BISWidget = (() => {
  const PANEL_W = 380;
  const PANEL_H = 560;

  const css = `
    :host { all: initial; }
    * { box-sizing: border-box; }

    .launcher {
      position: fixed; right: 22px; bottom: 22px; z-index: 2147483000;
      width: 60px; height: 60px; border-radius: 50%; border: 0; cursor: pointer;
      background: #FF9933; color: #0B2D5B;
      font: 700 22px/1 "Inter", system-ui, sans-serif;
      box-shadow: 0 10px 26px rgba(11,45,91,.35);
      display: flex; align-items: center; justify-content: center;
      transition: transform .15s ease;
    }
    .launcher:hover { transform: scale(1.06); }
    .launcher .mark {
      width: 34px; height: 34px; border-radius: 9px; background: #0B2D5B; color: #FF9933;
      display: flex; align-items: center; justify-content: center;
      font: 800 15px/1 "Inter", system-ui, sans-serif; letter-spacing: -.02em;
    }

    .panel {
      position: fixed; right: 22px; bottom: 94px; z-index: 2147483001;
      width: ${PANEL_W}px; height: ${PANEL_H}px;
      background: #FFFFFF; color: #101A2C;
      border: 1px solid #DCE3EC; border-radius: 16px;
      box-shadow: 0 24px 60px rgba(11,45,91,.28);
      display: none; flex-direction: column; overflow: hidden;
      font: 400 15px/1.5 "Inter", "Noto Sans Devanagari", system-ui, sans-serif;
    }
    .panel.open { display: flex; animation: pop .18s ease; }
    @keyframes pop { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: none; } }

    header {
      background: #0B2D5B; color: #fff; padding: 14px 16px;
      display: flex; align-items: center; gap: 10px;
    }
    header .title { font-weight: 700; font-size: 15px; flex: 1; }
    header .title span { display: block; font-weight: 400; font-size: 11px; color: #B9CBE6; }
    header button {
      background: transparent; border: 1px solid rgba(255,255,255,.35); color: #fff;
      border-radius: 999px; font: 600 12px/1 "Inter", system-ui, sans-serif;
      padding: 5px 10px; cursor: pointer; margin-right: 6px;
    }
    header button[aria-pressed="true"] { background: #FF9933; border-color: #FF9933; color: #3A2200; }
    header .close { border: 0; font-size: 16px; padding: 2px 6px; margin: 0; }

    .body { flex: 1; overflow-y: auto; padding: 14px; background: #FBFCFE; }
    .msg { display: flex; margin-bottom: 12px; }
    .msg.user { justify-content: flex-end; }
    .bubble { max-width: 82%; padding: 10px 13px; border-radius: 14px; font-size: 14px; }
    .msg.user .bubble { background: #0B2D5B; color: #fff; border-bottom-right-radius: 4px; }
    .msg.ai .bubble { background: #F4F6F9; border: 1px solid #E5EAF1; border-bottom-left-radius: 4px; }

    .cite {
      display: inline-flex; align-items: center; gap: 5px;
      font: 600 11px/1 "Inter", system-ui, sans-serif; color: #0B2D5B;
      background: #fff; border: 1px solid #DCE3EC; border-radius: 999px;
      padding: 5px 9px; margin: 7px 5px 0 0; text-decoration: none;
    }
    .badge {
      display: inline-flex; align-items: center; gap: 5px;
      font: 700 11px/1 "Inter", system-ui, sans-serif;
      border-radius: 999px; padding: 5px 10px; margin-top: 8px;
    }
    .badge.high { color: #0B5C04; background: #E4F5E2; border: 1px solid #A9DDA5; }
    .badge.medium { color: #B26A00; background: #FFF3E0; border: 1px solid #FFD699; }
    .badge.low { color: #D32F2F; background: #FDECEC; border: 1px solid #F3B8B8; }
    .meta { display: block; font-size: 11px; color: #5A6B85; margin-top: 7px; }

    .chips { display: flex; gap: 6px; flex-wrap: wrap; padding: 0 14px 10px; background: #FBFCFE; }
    .chips button {
      font: 600 12px/1 "Inter", system-ui, sans-serif; background: #fff; color: #101A2C;
      border: 1px solid #DCE3EC; border-radius: 999px; padding: 7px 11px; cursor: pointer;
    }
    .chips button:hover { border-color: #FF9933; }

    .composer { display: flex; gap: 8px; align-items: center; padding: 12px; border-top: 1px solid #E5EAF1; background: #fff; }
    .composer input {
      flex: 1; min-width: 0; font: 400 14px/1.4 "Inter", system-ui, sans-serif;
      border: 1.5px solid #DCE3EC; border-radius: 10px; padding: 10px 12px; color: #101A2C;
    }
    .composer input:focus { outline: none; border-color: #0B2D5B; }
    .composer .mic {
      width: 38px; height: 38px; flex: none; border-radius: 50%; border: 0; cursor: pointer;
      background: #0B2D5B; color: #fff; font-size: 15px;
    }
    .composer .mic.rec { background: #D32F2F; animation: pulse 1.2s ease-out infinite; }
    @keyframes pulse { 0% { box-shadow: 0 0 0 0 rgba(211,47,47,.55); } 100% { box-shadow: 0 0 0 16px rgba(211,47,47,0); } }
    .composer .send {
      background: #FF9933; border: 0; border-radius: 10px; cursor: pointer;
      font: 700 13px/1 "Inter", system-ui, sans-serif; color: #3A2200; padding: 11px 14px;
    }

    @media (max-width: 480px) {
      .panel { right: 10px; left: 10px; width: auto; bottom: 84px; height: 70vh; }
      .launcher { right: 14px; bottom: 14px; }
    }
  `;

  const esc = (s) =>
    String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  /* Local copy of the confidence/citation formatting so the widget
     has zero dependency on the host page (mirrors §2.4 exactly). */
  const badge = (c) =>
    c === "high"
      ? '<span class="badge high">✅ Verified from BIS source</span>'
      : c === "medium"
      ? '<span class="badge medium">⚠️ Partial match — confirm with BIS office</span>'
      : '<span class="badge low">❌ Not found in BIS sources</span>';

  const cites = (list) =>
    (list || [])
      .map((c) => `<a class="cite" href="${esc(c.url)}">📄 ${esc(c.doc)}${c.clause ? ", Clause " + esc(c.clause) : ""}</a>`)
      .join("");

  async function ask(message) {
    /* Contract parity with assets/js/bis.js (§3). Point at the real endpoint:
       return fetch("/chat", { method: "POST", headers: { "Content-Type": "application/json" },
         body: JSON.stringify({ message, language }) }).then(r => r.json()); */
    const q = message.trim();
    const lower = q.toLowerCase();
    let res;
    if (/302|appliance|hallmark|HUID|certif/.test(lower)) {
      res = {
        answer:
          /hallmark|huid/i.test(lower)
            ? "A hallmark has four signs: the BIS logo, purity grade (916 = 22K), assay centre mark and HUID. Verify the HUID on the BIS Care app before buying."
            : /certif/i.test(lower)
            ? "CRS certification: apply on the BIS MANAK portal, test at a recognised lab, then receive the licence — typically 4–6 weeks."
            : "IS 302 (Part 1) covers safety of household appliances. Clause 4.2 requires accessible parts not to become live in normal operation. CRS registration is mandatory before sale in India.",
        citations: [{ doc: "IS 302 Part 1", clause: "4.2", url: "#source" }],
        confidence: "high",
        suggested_actions: ["find_lab", "view_scheme", "talk_to_bis"],
        audio_url: "#audio",
      };
    } else {
      res = {
        answer: `Closest match for “${q}” found in the MANAK catalogue — medium confidence. Open the cited clause to confirm scope.`,
        citations: [{ doc: "BIS MANAK catalogue", clause: "Relevant Part", url: "#recommender" }],
        confidence: "medium",
        suggested_actions: ["view_scheme"],
      };
    }
    res.session_id = "sess-demo-widget";
    await new Promise((r) => setTimeout(r, 500));
    return res;
  }

  function mount(target) {
    if (!target || target.dataset.bisMounted) return;
    target.dataset.bisMounted = "1";

    const host = document.createElement("div");
    const root = host.attachShadow({ mode: "open" });
    root.innerHTML = `<style>${css}</style>
      <button class="launcher" aria-label="Open BIS Sahayak assistant" aria-expanded="false">
        <span class="mark">IS</span>
      </button>
      <section class="panel" role="dialog" aria-label="BIS Sahayak chat">
        <header>
          <div class="title">BIS Sahayak <span>Indian Standards assistant</span></div>
          <button data-lang="en" aria-pressed="true">EN</button>
          <button data-lang="hi" aria-pressed="false">हिं</button>
          <button data-lang="mr" aria-pressed="false">मरा</button>
          <button class="close" aria-label="Close chat">✕</button>
        </header>
        <div class="body">
          <div class="msg ai"><div class="bubble">
            🙏 Namaste! Ask me anything about Indian Standards — I'll cite the exact clause.
            <span class="meta">Answers are stamped with their BIS source.</span>
          </div></div>
        </div>
        <div class="chips">
          <button>Find my standard</button>
          <button>Certification steps</button>
          <button>Check hallmark</button>
          <button>Find a lab</button>
        </div>
        <form class="composer">
          <button type="button" class="mic" aria-label="Voice input">🎙️</button>
          <input type="text" placeholder="Ask about any Indian Standard…" aria-label="Your question">
          <button type="submit" class="send">Send</button>
        </form>
      </section>`;
    target.appendChild(host);

    const launcher = root.querySelector(".launcher");
    const panel = root.querySelector(".panel");
    const body = root.querySelector(".body");
    const form = root.querySelector(".composer");
    const input = root.querySelector(".composer input");
    const mic = root.querySelector(".mic");

    const toggle = (open) => {
      panel.classList.toggle("open", open);
      launcher.setAttribute("aria-expanded", String(open));
      if (open) input.focus();
    };
    launcher.addEventListener("click", () => toggle(!panel.classList.contains("open")));
    root.querySelector(".close").addEventListener("click", () => toggle(false));

    root.querySelectorAll("header button[data-lang]").forEach((b) =>
      b.addEventListener("click", () => {
        root.querySelectorAll("header button[data-lang]").forEach((x) => x.setAttribute("aria-pressed", "false"));
        b.setAttribute("aria-pressed", "true");
        input.placeholder =
          b.dataset.lang === "hi" ? "किसी भी भारतीय मानक के बारे में पूछें…"
          : b.dataset.lang === "mr" ? "कोणत्याही भारतीय मानकाबद्दल विचारा…"
          : "Ask about any Indian Standard…";
      })
    );

    mic.addEventListener("click", () => {
      const on = mic.classList.toggle("rec");
      mic.setAttribute("aria-label", on ? "Recording — tap to stop" : "Voice input");
      if (!on) { input.value = "Is IS 302 mandatory for home appliances?"; input.focus(); }
    });

    const scroll = () => (body.scrollTop = body.scrollHeight);

    async function send(text) {
      const q = (text || input.value).trim();
      if (!q) return;
      input.value = "";
      body.insertAdjacentHTML("beforeend", `<div class="msg user"><div class="bubble">${esc(q)}</div></div>`);
      body.insertAdjacentHTML("beforeend", `<div class="msg ai" data-typing><div class="bubble">…</div></div>`);
      scroll();
      const res = await ask(q);
      const typing = body.querySelector("[data-typing]");
      typing.removeAttribute("data-typing");
      typing.innerHTML = `<div class="bubble">${esc(res.answer)}
        <div>${cites(res.citations)}</div>${badge(res.confidence)}
        <span class="meta">🔊 Listen · just now</span></div>`;
      scroll();
    }

    form.addEventListener("submit", (e) => { e.preventDefault(); send(); });
    root.querySelectorAll(".chips button").forEach((b) =>
      b.addEventListener("click", () => send(b.textContent.trim()))
    );
  }

  return { mount };
})();

/* Auto-mount when the script is included with data-auto attribute:
   <div id="widget-root"></div>
   <script src="bis-widget.js" data-auto></script>
   Uses an existing #widget-root when the host page provides one (§4.1A),
   otherwise appends its own #bis-widget-root to <body>. */
if (document.currentScript && document.currentScript.hasAttribute("data-auto")) {
  const autoMount = () => {
    let el = document.getElementById("widget-root");
    if (!el) {
      el = document.getElementById("bis-widget-root");
      if (!el) {
        el = document.createElement("div");
        el.id = "bis-widget-root";
        document.body.appendChild(el);
      }
    }
    BISWidget.mount(el);
  };
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", autoMount);
  } else {
    autoMount();
  }
}
