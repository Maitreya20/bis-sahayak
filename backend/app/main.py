"""
BIS Sahayak — FastAPI backend for the SIH prototype.

Serves the existing static UI (unchanged) plus the POST /chat contract that
assets/js/bis.js already speaks:

    POST /chat   { message, language }  ->  { answer, citations[], confidence,
                                              suggested_actions[], audio_url,
                                              session_id }

Keyless by default: deterministic grounded composer over the local corpus.
Optional env hooks (never required):
    BIS_LLM_KEY / BIS_LLM_MODEL / BIS_LLM_BASE   OpenAI-compatible generation
    SARVAM_API_KEY                               TTS (audio_url)

Run:  uvicorn backend.app.main:app --reload --port 8000
"""
from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from pydantic import BaseModel, Field

from . import services

def _find_ui_dir() -> Path:
    """Locate the UI folder whether the repo root is the parent (backend/ inside
    the UI repo) or the folder that contains backend/ itself."""
    here = Path(__file__).resolve().parent      # backend/app/
    for root in (here.parents[1], here.parents[1].parent):
        cand = root / "UI"
        if cand.is_dir():
            return cand
    return here.parents[1].parent / "UI"


UI_DIR = _find_ui_dir()
PORT = int(os.environ.get("BIS_PORT", "8000"))

app = FastAPI(title="BIS Sahayak API", version="0.1.0")

# ---------------------------------------------------------------------------
# /chat contract (what bis.js already speaks)
# ---------------------------------------------------------------------------


class ChatIn(BaseModel):
    message: str = Field(..., min_length=0, max_length=2000)
    language: str | None = None  # sanitised in the handler (unknown -> auto-detect)


@app.post("/chat")
def chat(body: ChatIn, accept_language: str | None = Header(default=None)):
    lang = (accept_language or body.language or "").strip().lower()[:2]
    if lang not in ("en", "hi", "mr"):
        lang = None
    result = services.answer_question(body.message.strip(), header_lang=lang)
    return JSONResponse(result)


# ---------------------------------------------------------------------------
# Meta endpoints (useful for the SIH demo) — registered BEFORE the UI catch-all
# ---------------------------------------------------------------------------


@app.get("/health")
def health():
    return {
        "ok": True,
        "standards": len(services._STANDARDS),
        "clauses": sum(len(s["clauses"]) for s in services._STANDARDS),
        "schemes": len(services._SCHEMES),
        "labs": len(services._LABS),
        "mappings": len(services._MAPPINGS),
        "llm": bool(services._LLM_KEY and services._LLM_MODEL),
        "tts": bool(os.environ.get("SARVAM_API_KEY")),
    }


@app.get("/labs")
def labs(category: str = "", state: str = "", q: str = ""):
    rows = services.tool_find_labs(category, state)
    if q:
        ql = q.lower()
        rows = [r for r in rows if ql in (r["name"] + " " + r["city"] + " " + r["state"]).lower()]
    return {"labs": rows, "count": len(rows)}


@app.get("/standards")
def standards():
    return JSONResponse({"standards": services._STANDARDS})


@app.get("/standards/search")
def standards_search(q: str):
    hits = services.retrieve(q, top_k=8)
    out = []
    for u, score in hits:
        row = {"score": round(score, 3), "kind": u.kind}
        if u.kind == "clause":
            std, c = u.std
            row.update({"doc": std["no"], "clause": c["clause"],
                        "topic": c.get("topic_en", ""), "excerpt": c.get("excerpt_en", "")})
        elif u.kind == "scheme":
            row.update({"doc": u.scheme["name_en"], "clause": "Process"})
        elif u.kind == "mapping":
            row.update({"doc": u.mapping["is_no"], "clause": "Scope", "product": u.mapping["product"]})
        elif u.kind == "lab":
            row.update({"doc": u.lab["name"], "clause": u.lab["city"]})
        out.append(row)
    return {"results": out}


# ---------------------------------------------------------------------------
# UI serving — zero edits to the existing UI folder.
# ---------------------------------------------------------------------------

CONFIG_SNIPPET = (
    "\n<script>window.BIS_API_BASE = window.BIS_API_BASE || '%s';</script>\n"
)

# pages get the injection; assets/ is served verbatim
_HTML_SUFFIXES = {".html"}


def _ui_file(path: str) -> Path | None:
    """Resolve a safe path inside UI/ (blocks traversal)."""
    if not path or "\x00" in path:
        return None
    try:
        target = (UI_DIR / path.lstrip("/")).resolve()
        target.relative_to(UI_DIR.resolve())
    except ValueError:
        return None
    if target.is_dir():
        target = target / "index.html"
    if not target.is_file():
        return None
    return target


@app.get("/", include_in_schema=False)
def ui_index():
    return _serve_html(UI_DIR / "index.html")


@app.get("/{path:path}", include_in_schema=False)
def ui_static(path: str):
    target = _ui_file(path)
    if target is None:
        raise HTTPException(status_code=404, detail="Not found")
    if target.suffix.lower() in _HTML_SUFFIXES:
        return _serve_html(target)
    return FileResponse(target)


def _serve_html(target: str | Path) -> HTMLResponse:
    """Serve a UI page with the API-base config injected into <head>, so it runs
    BEFORE assets/js/bis.js (which reads window.BIS_API_BASE at load time)."""
    p = Path(target)
    html = p.read_text(encoding="utf-8", errors="replace")
    base = os.environ.get("BIS_PUBLIC_BASE", f"http://localhost:{PORT}")
    snippet = CONFIG_SNIPPET % base
    if "</head>" in html:
        html = html.replace("</head>", snippet + "</head>", 1)
    elif "</body>" in html:
        html = html.replace("</body>", snippet + "</body>", 1)
    else:
        html += snippet
    return HTMLResponse(html)
