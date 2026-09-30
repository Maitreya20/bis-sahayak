"""HTTP-level tests: the exact §3 contract bis.js speaks, plus UI serving."""
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app, _find_ui_dir


@pytest.fixture(scope="module")
def client():
    # CI-safe: skip UI-serving tests if the UI folder is missing
    if not _find_ui_dir().is_dir():
        pytest.skip("UI folder not present")
    return TestClient(app)


class TestChatEndpoint:
    def post(self, client, message, language=None, accept_language=None):
        headers = {"Content-Type": "application/json"}
        if accept_language:
            headers["Accept-Language"] = accept_language
        body = {"message": message}
        if language:
            body["language"] = language
        return client.post("/chat", json=body, headers=headers)

    def test_contract_keys(self, client):
        r = self.post(client, "Is IS 302 mandatory for home appliances?")
        assert r.status_code == 200
        data = r.json()
        assert {"answer", "citations", "confidence", "suggested_actions",
                "audio_url", "session_id"} <= set(data)
        assert data["confidence"] in ("high", "medium", "low")
        assert data["session_id"].startswith("sess-")

    def test_body_language_beats_detect(self, client):
        data = self.post(client, "Is IS 302 mandatory?", language="hi").json()
        assert any("\u0900" <= ch <= "\u097F" for ch in data["answer"])

    def test_accept_language_header(self, client):
        data = self.post(client, "Is IS 302 mandatory?",
                         accept_language="mr").json()
        assert any("\u0900" <= ch <= "\u097F" for ch in data["answer"])

    def test_gibberish_falls_back_low(self, client):
        data = self.post(client, "xyzzy qwerty flux").json()
        assert data["confidence"] == "low"
        assert data["citations"] == []

    def test_language_payload_ignored_when_invalid(self, client):
        # must not 500 on a junk language value
        r = self.post(client, "Which BIS lab tests toys?", language="xx")
        assert r.status_code == 200

    def test_oversized_message_rejected(self, client):
        r = self.post(client, "x" * 3000)
        assert r.status_code == 422

    def test_missing_message_rejected(self, client):
        r = client.post("/chat", json={})
        assert r.status_code == 422


class TestMetaEndpoints:
    def test_health(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        d = r.json()
        assert d["ok"] is True
        assert d["standards"] >= 15
        assert d["clauses"] >= 40
        assert d["schemes"] >= 3
        assert d["labs"] >= 5

    def test_labs_filters(self, client):
        d = client.get("/labs", params={"category": "Electronics & IT",
                                        "state": "Maharashtra"}).json()
        assert d["count"] >= 1
        assert all("Electronics & IT" in r["categories"] for r in d["labs"])

    def test_labs_search(self, client):
        d = client.get("/labs", params={"q": "pune"}).json()
        assert d["count"] == 1 and "Pune" in d["labs"][0]["name"]

    def test_standards_search(self, client):
        d = client.get("/standards/search", params={"q": "hallmark HUID"}).json()
        assert d["results"] and d["results"][0]["score"] > 0

    def test_standards_payload(self, client):
        d = client.get("/standards").json()
        assert len(d["standards"]) >= 15
        first = d["standards"][0]
        assert {"id", "no", "clauses"} <= set(first)


class TestUIServing:
    def test_index_served_with_injection(self, client):
        r = client.get("/")
        assert r.status_code == 200
        # injection must appear BEFORE the first script include
        html = r.text
        assert "BIS_API_BASE" in html
        assert html.index("BIS_API_BASE") < html.index("assets/js/bis.js")

    def test_directory_urls_resolve_index(self, client):
        for path in ("/", "/website/", "/app/", "/whatsapp/"):
            assert client.get(path).status_code == 200, path

    def test_assets_not_injected(self, client):
        r = client.get("/assets/js/bis.js")
        assert r.status_code == 200
        # the injected snippet is a <script> tag; bis.js only *mentions* the
        # variable name in its doc-comment
        assert "<script>window.BIS_API_BASE" not in r.text

    def test_traversal_blocked(self, client):
        assert client.get("/..%2fbackend%2fapp%2fmain.py").status_code in (404, 400)

    def test_unknown_page_404(self, client):
        assert client.get("/website/nope.html").status_code == 404
