"""
BIS Sahayak — service layer (prototype).

Pipeline per question:
  1. language detect (hi/mr script, else en/romanised)
  2. intent classify (schema/procedure/lab/mapping/smalltalk)
  3. hybrid retrieval (BM25 + vector + RRF rerank) over clause-level corpus
  4. structured tool calls (labs, schemes, product->IS) when intent says so
  5. grounded answer generation:
       - optional LLM (OpenAI-compatible, BIS_LLM_* env) constrained to retrieved context
       - keyless deterministic composer otherwise
  6. confidence (high/medium/low) + always-cite + fallback
"""
from __future__ import annotations

import json
import math
import os
import re
import unicodedata
import urllib.request
import uuid
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


# --------------------------------------------------------------------------
# Corpus loading
# --------------------------------------------------------------------------

def _load(name: str):
    with open(DATA_DIR / name, encoding="utf-8") as fh:
        return json.load(fh)


_STANDARDS = _load("standards.json")["standards"]
_SCHEMES = _load("schemes.json")["schemes"]
_LABS = _load("labs.json")["labs"]
_MAPPINGS = _load("mappings.json")["mappings"]


# --------------------------------------------------------------------------
# Tokenisation / embedding helpers
# --------------------------------------------------------------------------

_TOKEN_RE = re.compile(r"[\w]+", re.UNICODE)
_STOP = {
    "the", "a", "an", "is", "are", "of", "for", "to", "in", "on", "and", "or",
    "what", "which", "how", "do", "does", "i", "my", "me", "need", "want",
    "के", "का", "की", "है", "में", "से", "क्या", "कौन", "कैसे", "कोई", "मुझे",
    "आहे", "मध्ये", "आणि", "काय", "कसे", "मला", "का", "तो", "ती",
}


def _norm(s: str) -> str:
    return unicodedata.normalize("NFC", (s or "").lower())


def _tokens(s: str) -> list[str]:
    out = []
    for t in _TOKEN_RE.findall(_norm(s)):
        if t in _STOP or len(t) <= 1:
            continue
        if t.endswith("s") and not t.endswith("ss") and len(t) > 3:
            t = t[:-1]  # light plural stem: drivers->driver, toys->toy
        out.append(t)
    return out


class Unit:
    """One retrievable unit: a standard's clause, a scheme, a mapping row, a lab."""

    __slots__ = ("kind", "std", "scheme", "mapping", "lab", "text", "toks", "vec")

    def __init__(self, kind, text, std=None, scheme=None, mapping=None, lab=None):
        self.kind = kind  # clause | scheme | mapping | lab
        self.std = std            # (standard_dict, clause_dict) for clauses
        self.scheme = scheme
        self.mapping = mapping
        self.lab = lab
        self.text = text
        self.toks = _tokens(text)
        self.vec: dict | None = None


def _embed(u: Unit, idf: dict) -> None:
    tf = Counter(u.toks)
    if not tf:
        u.vec = {}
        return
    w = {t: (1 + math.log(c)) * idf.get(t, 2.0) for t, c in tf.items()}
    nrm = math.sqrt(sum(v * v for v in w.values())) or 1.0
    u.vec = {t: v / nrm for t, v in w.items()}


# --------------------------------------------------------------------------
# Build index at import
# --------------------------------------------------------------------------

_UNITS: list[Unit] = []
for s in _STANDARDS:
    for c in s["clauses"]:
        text = " ".join(
            x for x in (
                s["no"], s["title_en"], s.get("title_hi", ""), s.get("title_mr", ""),
                " ".join(s["keywords"]),
                c.get("topic_en", ""), c.get("topic_hi", ""), c.get("topic_mr", ""),
                c.get("excerpt_en", ""), c.get("excerpt_hi", ""), c.get("excerpt_mr", ""),
                s["scheme"], "mandatory compulsory" if s.get("mandatory") else "voluntary",
            ) if x
        )
        _UNITS.append(Unit("clause", text, std=(s, c)))
for sc in _SCHEMES:
    text = " ".join(filter(None, (
        sc["name_en"], sc.get("name_hi", ""), sc.get("name_mr", ""), sc.get("authority", ""),
        sc.get("products_en", ""), sc.get("products_hi", ""), sc.get("products_mr", ""),
        " ".join(sc["keywords"]),
    )))
    _UNITS.append(Unit("scheme", text, scheme=sc))
for m in _MAPPINGS:
    text = " ".join(filter(None, (
        m["product"], m["is_no"], m["scheme"], m["domain"],
        m.get("note_en", ""), " ".join(m.get("read_with", [])),
    )))
    _UNITS.append(Unit("mapping", text, mapping=m))
for lab in _LABS:
    text = " ".join(filter(None, (
        lab["name"], lab["city"], lab["state"],
        " ".join(lab["categories"]), " ".join(lab["tests"]),
    )))
    _UNITS.append(Unit("lab", text, lab=lab))

_DF: Counter = Counter()
for u in _UNITS:
    _DF.update(set(u.toks))
_N = max(1, len(_UNITS))
_IDF = {t: math.log(1 + (_N - df + 0.5) / (df + 0.5)) for t, df in _DF.items()}
_AVGDL = sum(len(u.toks) for u in _UNITS) / _N
for u in _UNITS:
    _embed(u, _IDF)
_K1, _B = 1.5, 0.75


# --------------------------------------------------------------------------
# Retrieval: BM25 + vector cosine, fused with reciprocal-rank fusion
# --------------------------------------------------------------------------

def _bm25_scores(q_toks: list[str]) -> dict[int, float]:
    scores: dict[int, float] = {}
    for i, u in enumerate(_UNITS):
        tf = Counter(u.toks)
        dl = len(u.toks)
        s = 0.0
        for t in q_toks:
            f = tf.get(t, 0)
            if f:
                s += _IDF.get(t, 2.0) * (f * (_K1 + 1)) / (f + _K1 * (1 - _B + _B * dl / _AVGDL))
        if s:
            scores[i] = s
    return scores


def _vec_scores(q_toks: list[str]) -> dict[int, float]:
    qtf = Counter(q_toks)
    qw = {t: (1 + math.log(c)) * _IDF.get(t, 2.0) for t, c in qtf.items()}
    nrm = math.sqrt(sum(v * v for v in qw.values())) or 1.0
    qv = {t: v / nrm for t, v in qw.items()}
    out: dict[int, float] = {}
    for i, u in enumerate(_UNITS):
        if not u.vec:
            continue
        num = sum(w * u.vec.get(t, 0.0) for t, w in qv.items())
        if num > 0:
            out[i] = num  # unit vectors are L2-normalised, so num == cosine
    return out


def _rrf(rank_lists: list[list[int]], k: int = 60) -> dict[int, float]:
    fused: dict[int, float] = {}
    for ranking in rank_lists:
        for r, i in enumerate(ranking):
            fused[i] = fused.get(i, 0.0) + 1.0 / (k + r + 1)
    return fused


_SYN = {
    "mandatory": {"compulsory", "required", "crs", "isi"},
    "compulsory": {"mandatory", "required"},
    "home": {"household", "domestic"},
    "household": {"home"},
    "fridge": {"refrigerator", "refrigerating"},
    "refrigerator": {"fridge"},
    "bulb": {"lamp", "led"},
    "lamp": {"bulb"},
    "wire": {"cable", "pvc"},
    "cable": {"wire"},
    "sariya": {"rebar", "steel", "tmt"},
    "sariya": {"rebar", "steel", "tmt"},
    "gold": {"hallmark", "jewellery", "fineness"},
    "silver": {"hallmark", "jewellery"},
    "toy": {"toys"},
    "toys": {"toy"},
    "huid": {"hallmark", "marking"},
    "cement": {"opc", "portland"},
}


def _expand(q_toks: list[str]) -> list[str]:
    out = list(q_toks)
    for t in q_toks:
        out.extend(_SYN.get(t, ()))
    return out


def _rerank(q_toks: list[str], cand: list[int]) -> list[int]:
    """Light cross-encoder-style reranker: phrase + keyword-coverage boosts."""
    ql = " ".join(q_toks)
    scored = []
    for i in cand:
        u = _UNITS[i]
        cover_ratio = sum(1 for t in set(q_toks) if t in u.toks) / max(1, len(set(q_toks)))
        phrase = 2.0 if ql and ql in u.text.lower() else 0.0
        bonus = 0.15 if u.kind == "clause" else 0.0
        scored.append((phrase + 1.5 * cover_ratio + bonus, i))
    scored.sort(key=lambda x: (-x[0], x[1]))
    return [i for _, i in scored]


def retrieve(q: str, top_k: int = 6) -> list[tuple[Unit, float]]:
    q_toks = _expand(_tokens(q))
    bm = _bm25_scores(q_toks)
    vs = _vec_scores(q_toks)
    bm_rank = [i for i, _ in sorted(bm.items(), key=lambda kv: -kv[1])][:25]
    vs_rank = [i for i, _ in sorted(vs.items(), key=lambda kv: -kv[1])][:25]
    fused = _rrf([bm_rank, vs_rank])
    if len(fused) < 3:
        # fuzzy rescue pass for typos / number-free queries
        q_low = _norm(q)[:60]
        for i, u in enumerate(_UNITS):
            sim = SequenceMatcher(None, q_low, u.text[:60]).ratio()
            if sim > 0.55:
                fused[i] = fused.get(i, 0.0) + 0.5 * sim
    if not fused:
        return []
    cand = _rerank(q_toks, sorted(fused, key=fused.get, reverse=True)[:20])
    top = cand[:top_k]
    if not top:
        return []
    strength = max(fused.get(i, 0.0) for i in top)
    rel = strength / (strength + 0.02)  # normalise small RRF sums to [0,1)
    u0 = _UNITS[top[0]]
    cover = sum(1 for t in set(_tokens(q)) if t in u0.toks) / max(1, len(set(_tokens(q))))
    score = max(rel, 0.75 * cover)
    return [(_UNITS[i], min(1.0, score)) for i in top]


# --------------------------------------------------------------------------
# Language + intent
# --------------------------------------------------------------------------

_DEVANAGARI = re.compile(r"[\u0900-\u097F]")
_MARATHI_HINTS = ("आहे", "आहेत", "काय", "कसे", "कुठे", "मला", "माझ", "कशे")
_HINDI_HINTS = ("है", "हैं", "क्या", "कैसे", "कहाँ", "मुझे", "मेरी", "मेरा", "चाहिए", "करना")


def detect_language(text: str, header_lang: str | None = None) -> str:
    if header_lang in ("en", "hi", "mr"):
        return header_lang
    t = text or ""
    if _DEVANAGARI.search(t):
        mr = sum(t.count(x) for x in _MARATHI_HINTS)
        hi = sum(t.count(x) for x in _HINDI_HINTS)
        return "mr" if mr > hi else "hi"
    return "en"


def detect_intent(q: str) -> str:
    ql = _norm(q)
    if not ql.strip():
        return "smalltalk"
    if re.search(r"\b(lab|laboratory|testing|test at|where.*test|लैब|लॅब|चाचणी|जाँच)\b", ql):
        return "lab"
    if re.search(r"\b(timeline|duration|how long|weeks?|months?|days?|take)\b", ql):
        return "procedure"
    if re.search(r"\b(which|what)\b.*\b(is|standard|code|applies)\b|applicable|recommend|find my standard|कौन सा|कोणता", ql):
        return "mapping"
    if re.search(r"\b(steps?|procedure|process|how (do|to|can)|apply|licen[cs]e|register|प्रक्रिया|पंजीकरण|आवेदन|अर्ज)\b", ql):
        return "procedure"
    if re.search(r"\b(hi|hello|hey|namaste)\b", ql) and len(ql.split()) <= 3:
        return "smalltalk"
    return "schema"


def _default_actions(intent: str) -> list[str]:
    return {
        "lab": ["find_lab", "talk_to_bis"],
        "procedure": ["find_lab", "view_scheme", "talk_to_bis"],
        "mapping": ["find_lab", "view_scheme"],
        "schema": ["find_lab", "view_scheme", "talk_to_bis"],
        "smalltalk": ["ask_question"],
    }.get(intent, ["find_lab", "view_scheme", "talk_to_bis"])


# --------------------------------------------------------------------------
# Structured tools
# --------------------------------------------------------------------------

def tool_find_labs(category: str = "", state: str = "") -> list[dict]:
    out = []
    for lab in _LABS:
        if category and category not in lab["categories"]:
            continue
        if state and state not in lab["state"] and state not in lab["city"]:
            continue
        out.append(lab)
    return out


def tool_find_scheme(q: str) -> dict | None:
    best, best_s = None, 0
    q_toks = _tokens(q)
    for sc in _SCHEMES:
        text = _norm(" ".join([sc["name_en"], sc.get("products_en", ""), " ".join(sc["keywords"])]))
        tks = set(_tokens(text))
        score = sum(1 for t in q_toks if t in tks)
        if score > best_s:
            best, best_s = sc, score
    return best if best_s > 0 else None


_MAPPING_STOP = {"crs", "isi", "scheme", "licence", "license", "timeline", "bis", "india", "standard", "code", "certification"}

def tool_product_to_is(q: str) -> list[dict]:
    q_toks = set(_tokens(q)) - _MAPPING_STOP
    scored = []
    for m in _MAPPINGS:
        toks = set(_tokens(m["product"] + " " + m.get("note_en", "") + " " + m["is_no"]))
        inter = q_toks & toks
        if inter:
            scored.append((len(inter), m))
    scored.sort(key=lambda x: -x[0])
    return [m for _, m in scored[:3]]


def tool_get_clause(doc: str, clause: str | None = None) -> dict | None:
    for s in _STANDARDS:
        if _norm(s["no"]) == _norm(doc) or s["id"] == doc:
            if clause:
                for c in s["clauses"]:
                    if c["clause"] == clause:
                        return {"standard": s, "clause": c}
            return {"standard": s, "clause": s["clauses"][0]}
    return None


# --------------------------------------------------------------------------
# Optional LLM (OpenAI-compatible) + optional Sarvam TTS hooks
# --------------------------------------------------------------------------

_LLM_MODEL = os.environ.get("BIS_LLM_MODEL", "")
_LLM_BASE = os.environ.get("BIS_LLM_BASE", "https://api.openai.com/v1")
_LLM_KEY = os.environ.get("BIS_LLM_KEY", "")


def _llm_answer(question: str, contexts: list[str], lang: str) -> str | None:
    if not (_LLM_KEY and _LLM_MODEL and contexts):
        return None
    try:
        sys_prompt = (
            "You are BIS Sahayak, a factual assistant for Indian Standards (BIS). "
            "Answer ONLY from the CONTEXT excerpts. If they do not contain the answer, "
            "say you don't know and suggest the BIS branch office. "
            "Reply in language code: " + lang + " (en/hi/mr). Keep under 90 words."
        )
        ctx = "\n\n".join(f"[{i + 1}] {c}" for i, c in enumerate(contexts))
        req = urllib.request.Request(
            _LLM_BASE.rstrip("/") + "/chat/completions",
            data=json.dumps({
                "model": _LLM_MODEL,
                "messages": [
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": f"CONTEXT:\n{ctx}\n\nQUESTION: {question}"},
                ],
                "temperature": 0.2,
                "max_tokens": 220,
            }).encode(),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {_LLM_KEY}"},
        )
        with urllib.request.urlopen(req, timeout=12) as resp:
            payload = json.loads(resp.read().decode())
        return (payload["choices"][0]["message"]["content"] or "").strip() or None
    except Exception:
        return None


def _tts_audio(text: str, lang: str) -> str | None:
    """Optional Sarvam TTS hook; returns an audio URL or None (keyless = silent)."""
    key = os.environ.get("SARVAM_API_KEY", "")
    if not key:
        return None
    try:
        req = urllib.request.Request(
            "https://api.sarvam.ai/text-to-speech",
            data=json.dumps({"inputs": [text[:500]], "target_language_code": lang}).encode(),
            headers={"api-subscription-key": key, "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=12) as resp:
            payload = json.loads(resp.read().decode())
        b64 = ((payload.get("audios") or [None])[0]) if isinstance(payload, dict) else None
        if b64:
            import base64
            out = DATA_DIR.parent / "static" / "audio"
            out.mkdir(parents=True, exist_ok=True)
            p = out / f"{uuid.uuid4().hex}.mp3"
            p.write_bytes(base64.b64decode(b64))
            return "/static/audio/" + p.name
    except Exception:
        pass
    return None


# --------------------------------------------------------------------------
# Grounded generation (keyless default composer)
# --------------------------------------------------------------------------

_I18N = {
    "en": {
        "not_found": "I couldn't find this in the indexed BIS corpus.",
        "fallback": "Please verify with your nearest BIS Branch Office or on bis.gov.in.",
        "steps_label": "Process:",
        "labs_label": "BIS-recognised labs:",
        "read_with": "Read with",
        "call_ahead": "Call ahead to confirm the clause testing you need is in scope.",
    },
    "hi": {
        "not_found": "यह जानकारी अनुक्रमित BIS कॉर्पस में नहीं मिली।",
        "fallback": "कृपया नज़दीकी BIS शाखा कार्यालय या bis.gov.in पर पुष्टि करें।",
        "steps_label": "प्रक्रिया:",
        "labs_label": "BIS-मान्यता प्राप्त लैब:",
        "read_with": "इसके साथ पढ़ें",
        "call_ahead": "ज़रूरी जाँच की उपलब्धता पहले फ़ोन कर पुष्टि करें।",
    },
    "mr": {
        "not_found": "ही माहिती अनुक्रमित BIS कॉर्पसमध्ये सापडली नाही.",
        "fallback": "कृपया जवळच्या BIS शाखा कार्यालयात किंवा bis.gov.in वर खात्री करा.",
        "steps_label": "प्रक्रिया:",
        "labs_label": "BIS-मान्यताप्राप्त लॅब:",
        "read_with": "यासह वाचा",
        "call_ahead": "आवश्यक चाचणी उपलब्ध आहे का ते आधी फोन करून जमा करा.",
    },
}


def _t(lang: str, key: str) -> str:
    return _I18N.get(lang, _I18N["en"]).get(key, _I18N["en"][key])


def _compose_standard_answer(s: dict, c: dict, lang: str) -> str:
    topic = c.get(f"topic_{lang}") or c["topic_en"]
    excerpt = c.get(f"excerpt_{lang}") or c["excerpt_en"]
    return f"{s['no']} — {topic}. {excerpt}"


def _compose_scheme_answer(sc: dict, lang: str) -> str:
    steps = sc.get(f"steps_{lang}") or sc["steps_en"]
    intro = sc.get(f"name_{lang}") or sc["name_en"]
    return intro + " " + _t(lang, "steps_label") + " " + " ".join(
        f"({i + 1}) {st}" for i, st in enumerate(steps)
    )


def _compose_lab_answer(labs: list[dict], lang: str) -> str:
    if not labs:
        return _t(lang, "not_found") + " " + _t(lang, "fallback")
    items = [f"{l['name']} ({l['city']}) — {'; '.join(l['tests'][:3])}" for l in labs[:3]]
    return _t(lang, "labs_label") + " " + " | ".join(items) + ". " + _t(lang, "call_ahead")


def _compose_mapping_answer(m: dict, lang: str) -> str:
    rw = ""
    if m.get("read_with"):
        rw = f" ({_t(lang, 'read_with')}: {', '.join(m['read_with'])})"
    return f"{m['product']}: {m['is_no']}{rw}. {m.get('note_en', '')}"


def _session_id() -> str:
    return "sess-" + uuid.uuid4().hex[:12]


def _cites_from_hits(hits: list[tuple[Unit, float]]) -> list[dict]:
    cites = []
    for u, _s in hits[:3]:
        if u.kind == "clause":
            std, c = u.std
            cites.append({"doc": std["no"], "clause": c["clause"], "url": "https://www.bis.gov.in"})
        elif u.kind == "scheme":
            sc = u.scheme
            url = "/website/hallmark.html" if sc["id"] == "hallmark" else "/website/recommender.html#cert"
            cites.append({"doc": sc["name_en"], "clause": "Process", "url": url})
        elif u.kind == "mapping":
            m = u.mapping
            cites.append({"doc": m["is_no"], "clause": "Scope", "url": "/website/recommender.html"})
        elif u.kind == "lab":
            lab = u.lab
            cites.append({"doc": lab["name"], "clause": lab["city"], "url": "/website/lab-finder.html"})
    return cites


def answer_question(message: str, header_lang: str | None = None) -> dict:
    """Main entry: full pipeline. Returns the /chat response contract object."""
    lang = detect_language(message, header_lang)
    intent = detect_intent(message)
    suggested = _default_actions(intent)
    sess = _session_id()

    # smalltalk ------------------------------------------------------------
    if intent == "smalltalk":
        g = {
            "en": "Namaste! Ask me about any Indian Standard (IS), BIS certification steps, labs, or hallmarking.",
            "hi": "नमस्ते! किसी भी भारतीय मानक (IS), BIS प्रमाणन, लैब या हॉलमार्किंग के बारे में पूछें।",
            "mr": "नमस्कार! कोणत्याही भारतीय मानक (IS), BIS प्रमाणन, लॅब किंवा हॉलमार्किंगबद्दल विचारा.",
        }
        return {"answer": g.get(lang, g["en"]), "citations": [], "confidence": "medium",
                "suggested_actions": suggested, "audio_url": None, "session_id": sess}

    # structured tool: labs -------------------------------------------------
    if intent == "lab":
        m = re.search(
            r"(Electronics & IT|Food & Agriculture|Metals & Steel|Chemicals & Plastics|Metals & Jewellery|Textiles)",
            message, re.I)
        cat = m.group(0) if m else ""
        st = next((x for x in ("Maharashtra", "Karnataka", "Delhi NCR", "Gujarat", "Tamil Nadu")
                   if x.lower() in _norm(message)), "")
        labs = tool_find_labs(cat, st)
        if not labs and (cat or st):
            labs = tool_find_labs()
        cites = [{"doc": l["name"], "clause": l["city"], "url": "/website/lab-finder.html"} for l in labs[:3]]
        answer = _compose_lab_answer(labs, lang)
        return {"answer": answer, "citations": cites,
                "confidence": "high" if labs else "low",
                "suggested_actions": suggested, "audio_url": _tts_audio(answer, lang), "session_id": sess}

    # structured tool: scheme procedure --------------------------------------
    if intent == "procedure":
        sc = tool_find_scheme(message)
        if sc:
            answer = _compose_scheme_answer(sc, lang)
            url = "/website/hallmark.html" if sc["id"] == "hallmark" else "/website/recommender.html#cert"
            return {"answer": answer,
                    "citations": [{"doc": sc["name_en"], "clause": "Process", "url": url}],
                    "confidence": "high", "suggested_actions": suggested,
                    "audio_url": _tts_audio(answer, lang), "session_id": sess}

    # structured tool: product -> IS -----------------------------------------
    if intent == "mapping":
        hits_m = tool_product_to_is(message)
        if hits_m:
            m = hits_m[0]
            answer = _compose_mapping_answer(m, lang)
            return {"answer": answer,
                    "citations": [{"doc": m["is_no"], "clause": "Scope", "url": "/website/recommender.html"}],
                    "confidence": "high", "suggested_actions": suggested,
                    "audio_url": _tts_audio(answer, lang), "session_id": sess}
        sc = tool_find_scheme(message)
        if sc:
            answer = _compose_scheme_answer(sc, lang)
            url = "/website/hallmark.html" if sc["id"] == "hallmark" else "/website/recommender.html#cert"
            return {"answer": answer,
                    "citations": [{"doc": sc["name_en"], "clause": "Process", "url": url}],
                    "confidence": "high", "suggested_actions": suggested,
                    "audio_url": _tts_audio(answer, lang), "session_id": sess}

    # --- RAG path (schema intent & tool misses) ------------------------------
    hits = retrieve(message, top_k=6)
    if not hits or hits[0][1] < 0.22:
        return {"answer": _t(lang, "not_found") + " " + _t(lang, "fallback"),
                "citations": [], "confidence": "low",
                "suggested_actions": suggested, "audio_url": None, "session_id": sess}

    contexts = []
    for u, _s in hits:
        if u.kind == "clause":
            std, c = u.std
            contexts.append(f"{std['no']} Clause {c['clause']}: {c.get(f'excerpt_{lang}') or c['excerpt_en']}")

    llm = _llm_answer(message, contexts, lang)
    if llm:
        answer_text = llm
    else:
        u, _s = hits[0]
        if u.kind == "clause":
            std, c = u.std
            answer_text = _compose_standard_answer(std, c, lang)
        elif u.kind == "scheme":
            answer_text = _compose_scheme_answer(u.scheme, lang)
        elif u.kind == "mapping":
            answer_text = _compose_mapping_answer(u.mapping, lang)
        else:
            answer_text = _compose_lab_answer([u.lab], lang)
    conf = "high" if hits[0][1] >= 0.45 else "medium"
    return {"answer": answer_text, "citations": _cites_from_hits(hits), "confidence": conf,
            "suggested_actions": suggested, "audio_url": _tts_audio(answer_text, lang),
            "session_id": sess}
