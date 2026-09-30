"""Contract tests for the /chat pipeline (service layer, no HTTP)."""
import backend.app.services as svc


class TestLanguageDetection:
    def test_explicit_header_wins(self):
        # Devanagari text but header says en -> header wins
        assert svc.detect_language("क्या यह अनिवार्य है?", header_lang="en") == "en"

    def test_header_hi(self):
        assert svc.detect_language("anything", header_lang="hi") == "hi"

    def test_devanagari_hindi(self):
        assert svc.detect_language("क्या IS 302 अनिवार्य है?") == "hi"

    def test_devanagari_marathi(self):
        assert svc.detect_language("सोन्याचे हॉलमार्क HUID कसे तपासायचे?") == "mr"

    def test_romanised_defaults_en(self):
        assert svc.detect_language("Is IS 302 mandatory?") == "en"

    def test_empty_defaults_en(self):
        assert svc.detect_language("") == "en"


class TestIntent:
    def test_lab(self):
        assert svc.detect_intent("Which BIS lab tests home appliances?") == "lab"

    def test_procedure_steps(self):
        assert svc.detect_intent("What are the BIS certification steps?") == "procedure"

    def test_procedure_timeline(self):
        assert svc.detect_intent("What is the CRS licence timeline?") == "procedure"

    def test_mapping(self):
        assert svc.detect_intent("Which IS codes apply to steel rebar?") == "mapping"

    def test_mapping_led(self):
        assert svc.detect_intent("Find my applicable standard for LED drivers") == "mapping"

    def test_smalltalk(self):
        assert svc.detect_intent("hi") == "smalltalk"

    def test_schema_default(self):
        assert svc.detect_intent("Is IS 302 mandatory for home appliances?") == "schema"


class TestRetrieval:
    def test_flagship_query_hits_is302(self):
        hits = svc.retrieve("Is IS 302 mandatory for home appliances?")
        assert hits, "no retrieval hits"
        u, score = hits[0]
        assert u.kind == "clause"
        assert u.std[0]["no"].startswith("IS 302")
        assert score >= 0.45  # high-confidence band

    def test_plural_stemming(self):
        # "drivers" must still find the LED module/driver mapping rows
        hits = svc.retrieve("LED drivers")
        assert any(u.kind == "mapping" and "16107" in u.mapping["is_no"] for u, _ in hits)

    def test_gibberish_scores_low(self):
        hits = svc.retrieve("xyzzy qwerty flux")
        assert not hits or hits[0][1] < 0.22

    def test_synonym_expansion(self):
        hits = svc.retrieve("Is the fridge standard mandatory?")
        assert hits and "302" in hits[0][0].std[0]["no"]


class TestTools:
    def test_labs_filter_category_state(self):
        rows = svc.tool_find_labs("Electronics & IT", "Maharashtra")
        assert rows and all("Electronics & IT" in r["categories"] for r in rows)
        assert rows[0]["city"] == "Pune"

    def test_labs_no_filter_returns_all(self):
        assert len(svc.tool_find_labs()) == 6

    def test_scheme_lookup_crs(self):
        sc = svc.tool_find_scheme("What are the CRS registration steps?")
        assert sc and sc["id"] == "crs"

    def test_scheme_lookup_hallmark(self):
        sc = svc.tool_find_scheme("How does gold hallmarking work?")
        assert sc and sc["id"] == "hallmark"

    def test_product_to_is(self):
        hits = svc.tool_product_to_is("Which standard applies to steel rebar?")
        assert hits and hits[0]["is_no"] == "IS 1786"

    def test_product_to_is_ignores_acronyms(self):
        # "CRS licence" alone must NOT map to a product standard
        assert svc.tool_product_to_is("What is the CRS licence timeline?") == []

    def test_get_clause(self):
        got = svc.tool_get_clause("IS 1417", "7")
        assert got and got["clause"]["clause"] == "7"

    def test_get_clause_unknown(self):
        assert svc.tool_get_clause("IS 999999") is None


class TestAnswerContract:
    KEYS = {"answer", "citations", "confidence", "suggested_actions", "audio_url", "session_id"}

    def _ask(self, q, lang="en"):
        return svc.answer_question(q, header_lang=lang)

    def test_all_keys_present(self):
        for q in [
            "Is IS 302 mandatory for home appliances?",
            "How do I verify a gold hallmark HUID?",
            "Which BIS lab tests home appliances?",
            "What are the BIS certification steps?",
            "Find my applicable standard for LED drivers",
            "What is the CRS licence timeline?",
            "hi",
        ]:
            r = self._ask(q)
            assert self.KEYS <= set(r), q

    def test_high_confidence_carries_citations(self):
        r = self._ask("Is IS 302 mandatory for home appliances?")
        assert r["confidence"] == "high"
        assert r["citations"]
        for c in r["citations"]:
            assert {"doc", "clause", "url"} <= set(c)

    def test_low_confidence_no_citations(self):
        r = self._ask("xyzzy qwerty flux")
        assert r["confidence"] == "low"
        assert r["citations"] == []
        assert "BIS" in r["answer"]  # fallback referral

    def test_hindi_answer_is_hindi(self):
        r = self._ask("Is IS 302 mandatory for home appliances?", lang="hi")
        assert any("\u0900" <= ch <= "\u097F" for ch in r["answer"])

    def test_marathi_detected_without_header(self):
        r = svc.answer_question("सोन्याचे हॉलमार्क HUID कसे तपासायचे?")
        assert any("\u0900" <= ch <= "\u097F" for ch in r["answer"])

    def test_citation_urls_are_navigable(self):
        r = self._ask("What are the BIS certification steps?")
        for c in r["citations"]:
            assert c["url"].startswith(("http", "/"))

    def test_empty_message_still_responds(self):
        r = self._ask("")
        assert r["answer"]

    def test_scheme_answer_lists_steps(self):
        r = self._ask("What are the BIS certification steps?")
        assert "(1)" in r["answer"] and "(2)" in r["answer"]

    def test_lab_answer_names_a_lab(self):
        r = self._ask("Which BIS lab tests home appliances?")
        assert "Lab" in r["answer"] and r["confidence"] == "high"
