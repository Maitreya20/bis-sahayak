/* ============================================================
   BIS Sahayak — shared client helpers
   All fixtures are shaped exactly like POST /chat (§3):
   { answer, citations[], confidence, suggested_actions[], audio_url }
   Point it at a real backend without touching any UI:

     <script src="assets/js/bis.js" data-api="https://api.example.gov.in"></script>
     <!-- or: window.BIS_API_BASE = "https://api.example.gov.in"; -->

   With no API configured (the default), every answer comes from the
   local fixtures below — same shape, same confidence logic.
   ============================================================ */

const BIS = (() => {
  const LANGS = ["en", "hi", "mr"];

  /* ---- endpoint (§3): POST {apiBase}/chat ---- */
  const API_BASE =
    (document.currentScript && document.currentScript.getAttribute("data-api")) ||
    window.BIS_API_BASE ||
    "";

  const i18n = {
    en: {
      askPlaceholder: "Ask about any Indian Standard… e.g. “IS 302 for home appliances”",
      send: "Send",
      verified: "Verified from BIS source",
      partial: "Partial match — confirm with BIS office",
      notFound: "Not found in BIS sources",
      quick: ["Find my standard", "Certification steps", "Check hallmark", "Find a lab"],
      listening: "Listening… tap to stop",
      tapMic: "Tap the mic and ask in your language",
      citeLabel: "Source",
    },
    hi: {
      askPlaceholder: "किसी भी भारतीय मानक के बारे में पूछें… जैसे “घरेलू उपकरणों के लिए IS 302”",
      send: "भेजें",
      verified: "BIS स्रोत से सत्यापित",
      partial: "आंशिक मिलान — BIS कार्यालय से पुष्टि करें",
      notFound: "BIS स्रोतों में नहीं मिला",
      quick: ["मेरा मानक खोजें", "प्रमाणन चरण", "हॉलमार्क जाँच", "प्रयोगशाला खोजें"],
      listening: "सुन रहा है… रोकने के लिए टैप करें",
      tapMic: "माइक पर टैप करें और अपनी भाषा में पूछें",
      citeLabel: "स्रोत",
    },
    mr: {
      askPlaceholder: "कोणत्याही भारतीय मानकाबद्दल विचारा… उदा. “घरगुती उपकरणांसाठी IS 302”",
      send: "पाठवा",
      verified: "BIS स्रोतातून पडताळलेले",
      partial: "अंशतः जुळणी — BIS कार्यालयाशी पुष्टी करा",
      notFound: "BIS स्रोतांमध्ये सापडले नाही",
      quick: ["माझा मानक शोधा", "प्रमाणपत्र प्रक्रिया", "हॉलमार्क तपासा", "चाचणी प्रयोगशाला शोधा"],
      listening: "ऐकत आहे… थांबवण्यासाठी टैप करा",
      tapMic: "माइकवर टैप करा आणि तुमच्या भाषेत विचारा",
      citeLabel: "स्रोत",
    },
  };

  let lang = "en";
  const STORE_KEY = "bis-lang";

  /* marked as early as possible so .reveal elements never flash unstyled */
  document.documentElement.classList.add("js");

  const t = () => i18n[lang] || i18n.en;

  /* ---- canned knowledge base (stands in for RAG over BIS docs) ---- */
  const KB = [
    {
      match: /\blabs?\b|प्रयोगशाला|प्रयोगशाळा|testing lab|चाचणी प्रयोग/i,
      confidence: "medium",
      answer: {
        en: "BIS recognises 3rd-party test labs under CRS and FMCS. For electronics, shortlist labs in your state using the Lab Finder — carry the sample and the standard's test schedule. I found labs near you; call ahead to confirm the specific clause testing is in scope.",
        hi: "BIS CRS और FMCS के तहत तृतीय-पक्ष प्रयोगशालाओं को मान्यता देता है। इलेक्ट्रॉनिक्स के लिए अपने राज्य में प्रयोगशालाओं की सूची देखें — नमूना और मानक का परीक्षण कार्यक्रम साथ ले जाएँ।",
        mr: "BIS CRS आणि FMCS अंतर्गत तृतीय-पक्ष चाचणी प्रयोगशालांना मान्यता देते. इलेक्ट्रॉनिक्ससाठी तुमच्या राज्यातील प्रयोगशाला शोधा — नमुना आणि मानकाचे चाचणी वेळापत्रक घेऊन जा.",
      },
      citations: [{ doc: "BIS Lab Finder directory", clause: "Recognised Labs (CRS)", url: "#labs" }],
      excerpt: {
        doc: "Recognised Laboratories — CRS list",
        text: "Laboratories recognised by BIS for testing of electronics and IT goods under the Compulsory Registration Scheme, searchable by state and product scope…",
      },
    },
    {
      match: /IS\s*302|appliance|उपकरण|उपकरणे|home appliance|safety of electrical/i,
      confidence: "high",
      answer: {
        en: "IS 302 (Part 1) is the Indian Standard for safety of household and similar electrical appliances. Clause 4.2 covers general protection against electric shock — accessible parts must not become live under normal operation. Every appliance sold in India needs BIS CRS registration under this standard.",
        hi: "IS 302 (भाग 1) घरेलू और समान विद्युत उपकरणों की सुरक्षा के लिए भारतीय मानक है। खंड 4.2 सामान्य विद्युत झटके से सुरक्षा से संबंधित है — सामान्य संचालन में सुलभ हिस्से विद्युत-चालित नहीं होने चाहिए।",
        mr: "IS 302 (भाग 1) हा घरगुती आणि समान विद्युत उपकरणांच्या सुरक्षिततेसाठीला भारतीय मानक आहे. कलम 4.2 सामान्य विद्युत आघातापासून संरक्षणाशी संबंधित आहे.",
      },
      citations: [
        { doc: "IS 302 Part 1", clause: "4.2", url: "#source-is302-4-2" },
        { doc: "IS 302 (Part 2/Sec 23)", clause: "21", url: "#source-is302-2-23" },
      ],
      excerpt: {
        doc: "IS 302 (Part 1) — Clause 4.2",
        text: "Protection against electric shock: accessible parts shall not become live under single fault conditions, except for parts intended to be live…",
      },
    },
    {
      match: /hallmark|हॉलमार्क|हॉलमार्क|HUID|gold|सोने|सोना/i,
      confidence: "high",
      answer: {
        en: "A BIS hallmark on gold jewellery has four signs: the BIS logo, the purity grade (e.g. 916 for 22K), the assay centre mark, and the HUID (Hallmark Unique ID). Verify any HUID on the BIS Care app — if it doesn't return a match, don't buy the piece.",
        hi: "सोने के गहने पर BIS हॉलमार्क चार चिह्न होते: BIS लोगो, शुद्धता ग्रेड (जैसे 22K के लिए 916), निरीक्षण केंद्र चिह्न, और HUID। किसी भी HUID को BIS Care ऐप पर जाँचें।",
        mr: "सोन्याच्या दागिन्यांवरील BIS हॉलमार्क चार चिन्हे असतात: BIS लोगो, शुद्धता ग्रेड (उदा. 22K साठी 916), तपासणी केंद्र चिन्ह आणि HUID. कोणत्याही HUID ची BIS Care अ‍ॅपवर पडताळणी करा.",
      },
      citations: [{ doc: "IS 1417", clause: "5 (Marking)", url: "#source-is1417" }],
      excerpt: {
        doc: "IS 1417 — Clause 5, Marking",
        text: "Every article of gold jewellery shall bear the BIS mark, fineness grade in parts per thousand, and the Hallmark Unique Identification (HUID) assigned by the assay centre…",
      },
    },
    {
      match: /certif|प्रमाणन|प्रमाणपत्र|license|CRS|FMCS|इसरार/i,
      confidence: "high",
      answer: {
        en: "BIS certification runs two ways: CRS (Compulsory Registration Scheme) for electronics — apply online via the BIS MANAK portal, test at a BIS-recognised lab, then get the licence. FMCS (Foreign Manufacture) needs an Indian authorised representative. Typical CRS timeline: 4–6 weeks from application to licence.",
        hi: "BIS प्रमाणन दो तरीकों से चलता है: इलेक्ट्रॉनिक्स के लिए CRS — BIS MANAK पोर्टल पर ऑनलाइन आवेदन करें, BIS मान्यता प्राप्त प्रयोगशाला में परीक्षण करें, फिर लाइसेंस प्राप्त करें। FMCS के लिए भारतीय अधिकृत प्रतिनिधि चाहिए।",
        mr: "BIS प्रमाणपत्र प्रक्रिया दोन पद्धतींनी चालते: इलेक्ट्रॉनिक्ससाठी CRS — BIS MANAK पोर्टलवर ऑनलाइन अर्ज करा, BIS ओळखीच्या प्रयोगशालेत चाचणी करा, नंतर परवाना मिळवा. FMCS साठी भारतीय अधिकृत प्रतिनिधी आवश्यक.",
      },
      citations: [
        { doc: "BIS CRS Regulations 2018", clause: "Reg. 5 (Application)", url: "#source-crs" },
      ],
      excerpt: {
        doc: "BIS CRS Regulations 2018 — Regulation 5",
        text: "The applicant shall submit an application in Form-I along with test reports from a BIS recognised laboratory…",
      },
    },
    {
      match: /lead|steel|cement|textile|food|IS\s*\d{2,5}/i,
      confidence: "medium",
      answer: null, // falls through to generic medium answer below
    },
  ];

  const generic = (q) => ({
    confidence: "medium",
    answer: {
      en: `Good question. For “${q}” the closest applicable Indian Standard is covered in the MANAK catalogue — I've matched it with medium confidence. Open the cited clause to confirm scope, or ask a BIS officer if your product falls under a separate part.`,
      hi: `अच्छा प्रश्न। “${q}” के लिए निकटतम लागू भारतीय मानक MANAK सूची में है — मैंने इसे मध्यम विश्वास से मिलाया है। परिधि की पुष्टि के लिए उद्धृत खंड खोलें।`,
      mr: `छान प्रश्न. “${q}” साठी जवळचा लागू भारतीय मानक MANAK यादीत आहे — मी हे मध्यम विश्वासाने जुळवले आहे. व्याप्ती पडताळण्यासाठी संदर्भित कलम उघडा.`,
    },
    citations: [{ doc: "BIS MANAK catalogue", clause: "Relevant Part", url: "#recommender" }],
    excerpt: {
      doc: "BIS MANAK — matched section",
      text: "Standards relating to your query are grouped under this section of the national catalogue. Confirm the exact Part/Section for your product category…",
    },
  });

  const lowAnswer = (q) => ({
    confidence: "low",
    answer: {
      en: `I couldn't find “${q}” in the BIS knowledge base. Here's who to contact: the nearest BIS Branch Office, or the BIS Care app's grievance section. I can also draft the question for you to send to a BIS officer.`,
      hi: `मैं BIS नॉलेज बेस में “${q}” नहीं खोज सका। संपर्क करें: निकटतम BIS शाखा कार्यालय, या BIS Care ऐप की शिकायत अनुभाग।`,
      mr: `मी BIS ज्ञानकोशात “${q}” शोधू शकलो नाही. संपर्क साधा: जवळचे BIS शाखा कार्यालय किंवा BIS Care अ‍ॅपचा तक्रार विभाग.`,
    },
    citations: [],
    excerpt: null,
  });

  /** Real POST /chat when an API base is configured, fixtures otherwise.
      Returns a Promise either way, so the UI never has to know. */
  async function chat(message) {
    const q = (message || "").trim();

    if (API_BASE) {
      try {
        const res = await fetch(API_BASE.replace(/\/+$/, "") + "/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json", "Accept-Language": lang },
          body: JSON.stringify({ message: q, language: lang }),
        });
        if (!res.ok) throw new Error("HTTP " + res.status);
        const data = await res.json();
        return { suggested_actions: [], audio_url: null, ...data, session_id: data.session_id || "sess-live" };
      } catch (err) {
        console.warn("[BIS] /chat unreachable (" + err.message + ") — serving offline fixtures", err);
      }
    }

    const hit = KB.find((k) => k.match.test(q));
    let res;
    if (hit && hit.answer) {
      res = {
        answer: hit.answer[lang] || hit.answer.en,
        citations: hit.citations,
        confidence: hit.confidence,
        suggested_actions: ["find_lab", "view_scheme", "talk_to_bis"],
        audio_url: "#audio-demo",
      };
      res.excerpt = hit.excerpt;
    } else if (hit) {
      res = generic(q);
      res.answer = res.answer[lang] || res.answer.en;
    } else if (q.length < 3) {
      res = lowAnswer(q);
      res.answer = res.answer[lang] || res.answer.en;
    } else {
      res = generic(q);
      res.answer = res.answer[lang] || res.answer.en;
    }
    res.session_id = "sess-demo";
    return new Promise((resolve) => setTimeout(() => resolve(res), 450 + Math.random() * 400));
  }

  /* ---- UI factories (§2.4) ---- */
  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  }

  function confidenceBadge(confidence) {
    const map = {
      high: ["high", `✅ ${t().verified}`],
      medium: ["medium", `⚠️ ${t().partial}`],
      low: ["low", `❌ ${t().notFound}`],
    };
    const [cls, label] = map[confidence] || map.medium;
    return `<span class="confidence ${cls}">${label}</span>`;
  }

  function citationChips(citations) {
    if (!citations || !citations.length) return "";
    return citations
      .map(
        (c) =>
          `<a class="citation" href="${escapeHtml(c.url)}" title="Open source document">📄 ${escapeHtml(c.doc)}${
            c.clause
              ? `, Clause ${escapeHtml(String(c.clause).replace(/^\s*clause\s+/i, ""))}`
              : ""
          }</a>`
      )
      .join("");
  }

  function aiBubble(res, opts = {}) {
    const el = document.createElement("div");
    el.className = "msg ai";
    el.innerHTML = `
      <div class="bubble">
        ${escapeHtml(res.answer)}
        <div>${citationChips(res.citations)}</div>
        ${confidenceBadge(res.confidence)}
        <span class="meta">🔊 Listen${res.audio_url ? " · " : ""}${
          opts.time || "just now"
        }</span>
      </div>`;
    return el;
  }

  function userBubble(text) {
    const el = document.createElement("div");
    el.className = "msg user";
    el.innerHTML = `<div class="bubble">${escapeHtml(text)}</div>`;
    return el;
  }

  /** "…" placeholder shown while /chat is in flight — three bouncing dots. */
  function typingBubble() {
    const el = document.createElement("div");
    el.className = "msg ai";
    el.setAttribute("aria-hidden", "true");
    el.innerHTML = `<div class="bubble"><span class="typing-dots"><i></i><i></i><i></i></span></div>`;
    return el;
  }

  function sourcePanel(res) {
    if (!res.excerpt) {
      return `<p class="muted small">No source excerpt for this answer — confidence is ${
        res.confidence
      }.</p>`;
    }
    return `
      <div class="source-excerpt">
        <span class="doc">📄 ${escapeHtml(res.excerpt.doc)}</span>
        ${escapeHtml(res.excerpt.text)}
      </div>
      ${citationChips(res.citations)}`;
  }

  function setLanguage(next) {
    if (!LANGS.includes(next)) return;
    lang = next;
    try { localStorage.setItem(STORE_KEY, next); } catch (e) { /* private mode */ }
    document.documentElement.lang = next;
    document.querySelectorAll(".lang-switch button").forEach((b) => {
      b.setAttribute("aria-pressed", String(b.dataset.lang === next));
    });
    document.dispatchEvent(new CustomEvent("bis:lang", { detail: { lang } }));
  }

  function getLanguage() {
    return lang;
  }

  /* language follows the reader across every surface, not just one page */
  function restoreLanguage() {
    let saved = null;
    try { saved = localStorage.getItem(STORE_KEY); } catch (e) { /* private mode */ }
    if (LANGS.includes(saved)) lang = saved;
    document.documentElement.lang = lang;
    document.querySelectorAll(".lang-switch button").forEach((b) => {
      b.setAttribute("aria-pressed", String(b.dataset.lang === lang));
    });
    /* tell the page, so per-page strings (placeholders, badges) catch up */
    document.dispatchEvent(new CustomEvent("bis:lang", { detail: { lang } }));
  }

  function bindLanguageSwitchers() {
    document.querySelectorAll(".lang-switch").forEach((group) => {
      group.querySelectorAll("button").forEach((b) => {
        b.setAttribute("aria-pressed", String(b.dataset.lang === lang));
        b.addEventListener("click", () => setLanguage(b.dataset.lang));
      });
    });
  }

  /** Staggers .reveal elements into view once — call again after injecting markup. */
  function reveal(scope) {
    const root = scope || document;
    const els = Array.prototype.slice.call(root.querySelectorAll(".reveal:not(.in)"));
    if (!els.length) return;
    if (!("IntersectionObserver" in window)) {
      els.forEach((el) => el.classList.add("in"));
      return;
    }
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          const el = entry.target;
          el.style.transitionDelay = (Number(el.dataset.revealDelay) || 0) + "ms";
          el.classList.add("in");
          io.unobserve(el);
        });
      },
      { rootMargin: "0px 0px -6% 0px", threshold: 0.08 }
    );
    els.forEach((el) => io.observe(el));
  }

  document.addEventListener("DOMContentLoaded", () => {
    restoreLanguage();
    bindLanguageSwitchers();
    reveal();
  });

  return {
    chat,
    t,
    LANGS,
    apiBase: API_BASE,
    escapeHtml,
    confidenceBadge,
    citationChips,
    aiBubble,
    userBubble,
    typingBubble,
    sourcePanel,
    setLanguage,
    getLanguage,
    reveal,
  };
})();
