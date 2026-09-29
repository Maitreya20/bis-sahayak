# -*- coding: utf-8 -*-
"""Build 'Intelligent Conversational AI for KSP Crime Database' review PPT
by rewriting REVIEW PPT TEMPLATE.pptx in place (formatting preserved)."""
import copy
import io
from pptx import Presentation
from pptx.util import Pt, Inches
from pptx.oxml.ns import qn
from pptx.enum.shapes import MSO_SHAPE_TYPE
from lxml import etree
from PIL import Image, ImageDraw, ImageFont

SRC = r"D:/Final yr project/REVIEW PPT TEMPLATE.pptx"
OUT = r"D:/Final yr project/Intelligent Conversational AI for KSP Crime Database - Review PPT.pptx"

prs = Presentation(SRC)
S = list(prs.slides)

# ---------------- low-level helpers ----------------
def find_pPr(tf, lvl, min_idx=0):
    """pPr of the first non-empty original paragraph at this level."""
    for p in list(tf.paragraphs)[min_idx:]:
        if not ''.join(r.text for r in p.runs).strip():
            continue
        if p.level == lvl:
            pPr = p._p.find(qn('a:pPr'))
            if pPr is not None:
                return copy.deepcopy(pPr)
    return None

def find_rPr(tf, bold, min_idx=0):
    """rPr of the first original run matching the requested bold state."""
    fb = None
    for p in list(tf.paragraphs)[min_idx:]:
        for r in p.runs:
            rPr = r._r.find(qn('a:rPr'))
            if rPr is None:
                continue
            if fb is None:
                fb = rPr
            if bold is None:
                if r.font.bold is None:
                    return copy.deepcopy(rPr)
            elif r.font.bold == bold:
                return copy.deepcopy(rPr)
    return copy.deepcopy(fb) if fb is not None else None

def set_frame(tf, paras, keep_prefix=0):
    """paras: list of (lvl, [(text, bold), ...]) or (lvl, runs, src_paragraph_index).
    Empty runs => blank line. src indexes the ORIGINAL paragraph list (incl. kept prefix)."""
    orig_ps = list(txBody.findall(qn('a:p'))) if (txBody := tf._txBody) else []

    pPrs, rPrs = {}, {}
    for spec in paras:
        lvl, runs = spec[0], spec[1]
        src = spec[2] if len(spec) > 2 else None
        if src is None and lvl not in pPrs:
            pPrs[lvl] = find_pPr(tf, lvl, min_idx=keep_prefix)
        for _, bold in runs:
            if bold not in rPrs:
                rPrs[bold] = find_rPr(tf, bold, min_idx=keep_prefix)

    for p in list(txBody.findall(qn('a:p')))[keep_prefix:]:
        txBody.remove(p)

    for spec in paras:
        lvl, runs = spec[0], spec[1]
        src = spec[2] if len(spec) > 2 else None
        p = etree.SubElement(txBody, qn('a:p'))
        pPr = None
        if src is not None:
            orig = orig_ps[src].find(qn('a:pPr'))
            if orig is not None:
                pPr = copy.deepcopy(orig)
        elif lvl in pPrs and pPrs[lvl] is not None:
            pPr = copy.deepcopy(pPrs[lvl])
        if pPr is None and lvl:
            pPr = etree.Element(qn('a:pPr'))
        if pPr is not None:
            pPr.set('lvl', str(lvl))
            p.insert(0, pPr)
        for text, bold in runs:
            r = etree.SubElement(p, qn('a:r'))
            rPr = rPrs.get(bold)
            rPr = copy.deepcopy(rPr) if rPr is not None else etree.Element(qn('a:rPr'))
            rPr.set('lang', 'en-US')
            if bold is not None:
                rPr.set('b', '1' if bold else '0')   # bold is an ATTRIBUTE of a:rPr
            r.append(rPr)
            t = etree.SubElement(r, qn('a:t'))
            t.text = text

def set_cell(cell, text):
    tf = cell.text_frame
    pPr = None
    rPr = None
    for p in tf.paragraphs:
        if pPr is None:
            pPr = p._p.find(qn('a:pPr'))
        for r in p.runs:
            if rPr is None:
                rPr = r._r.find(qn('a:rPr'))
        if pPr is not None and rPr is not None:
            break
    txBody = tf._txBody
    for p in txBody.findall(qn('a:p')):
        txBody.remove(p)
    p = etree.SubElement(txBody, qn('a:p'))
    if pPr is not None:
        p.append(copy.deepcopy(pPr))
    if text:
        r = etree.SubElement(p, qn('a:r'))
        if rPr is not None:
            r.append(copy.deepcopy(rPr))
        etree.SubElement(r, qn('a:t')).text = text

def replace_text(slide, old, new):
    for sh in slide.shapes:
        if not sh.has_text_frame:
            continue
        for p in sh.text_frame.paragraphs:
            for r in p.runs:
                if old in r.text:
                    r.text = r.text.replace(old, new)
                    return True
    return False

def body_shape(slide, idx=0):
    return [sh for sh in slide.shapes if sh.has_text_frame and sh.text_frame.text.strip()][idx]

def fill_table(slide, rows, start_row=1):
    tbl = next(sh for sh in slide.shapes if sh.has_table).table
    for ri, row in enumerate(rows, start=start_row):
        for ci, val in enumerate(row):
            set_cell(tbl.cell(ri, ci), val)

# ---------------- slide 1: title ----------------
replace_text(S[0], 'Project Title', 'Intelligent Conversational AI for KSP Crime Database')

# ---------------- slide 3: INTRODUCTION ----------------
set_frame(body_shape(S[2], 1).text_frame, [
    (0, [("The Karnataka State Crime Records Bureau (SCRB) manages a large and continuously growing repository of crime data streamed from 1,100+ police stations across the state.", None)]),
    (0, []),
    (0, [("Investigators today depend on static dashboards, rigid menus and manual queries. This limits deep analysis and delays real-time, data-driven decisions.", None)]),
    (0, []),
    (0, [("Conversational AI changes how officers interact with crime data: they simply ask questions in plain English or Kannada — by text or voice — and receive precise, evidence-backed answers.", None)]),
    (0, []),
    (0, [("The platform combines Natural Language Processing, Retrieval-Augmented Generation (RAG) and NL-to-SQL translation to convert questions into secure database queries and analytical insights.", None)]),
    (0, []),
    (0, [("Beyond question answering, it uncovers crime patterns, criminal networks, hotspots and predictive early warnings — turning a passive database into an active investigative partner.", None)]),
])

# ---------------- slide 4: intro contd. (title + sections + lvl-1 bullets) ----------------
set_frame(body_shape(S[3]).text_frame, [
    (0, [("Importance of Conversational Access to Crime Data", True)], 0),
    (0, [("Real-Time Investigative Support:", True)], 1),
    (1, [("Fast Answers: ", True), ("Officers ask ad-hoc questions and get results in seconds, instead of filing manual query requests.", False)], 2),
    (1, [("Voice-First Access: ", True), ("Kannada + English voice interaction serves field officers and non-technical users.", False)], 2),
    (0, [("Deeper Analysis:", True)], 5),
    (1, [("Hidden Patterns: ", True), ("Crime pattern discovery, criminal network analysis and behavioural profiling run automatically on live data.", False)], 2),
    (1, [("Socio-Demographic Insights: ", True), ("Data linked across 1,100+ stations reveals trends invisible to static dashboards.", False)], 2),
    (0, [("Proactive Policing:", True)], 5),
    (1, [("Early Warnings: ", True), ("Trend and hotspot detection shifts policing from reactive response to prevention.", False)], 2),
    (1, [("Network Disruption: ", True), ("Graph analysis surfaces key actors and relationships for targeted action.", False)], 2),
])

# ---------------- slides 5-7: LITERATURE REVIEW tables ----------------
fill_table(S[4], [
    ["Lewis et al. (2020)", "Retrieval-Augmented Generation (RAG)", "Ground LLM answers in retrieved knowledge", "RAG grounds answers in evidence and reduces hallucination", "Improved factuality of open-domain answers", "Retrieval quality bounds answer quality"],
    ["Yu et al. (2018)", "Text-to-SQL semantic parsing (Spider)", "Translate natural language into SQL queries", "Cross-domain text-to-SQL is learnable via schema linking", "Accurate parsing of complex queries", "Degrades on unseen database schemas"],
    ["Kakwani et al. (2020)", "IndicBERT / IndicNLG (multilingual NLP)", "Pretrain models for 12 Indian languages incl. Kannada", "Multilingual pretraining transfers to Indic tasks", "Strong results on Indic NLP benchmarks", "Limited domain-specific police vocabulary"],
    ["Kipf & Welling (2017)", "Graph Convolutional Networks", "Learn representations from graph-structured data", "Semi-supervised graph learning works with few labels", "Accurate node classification and link prediction", "Needs sampling on very large graphs"],
])
fill_table(S[5], [
    ["Radford et al. (2023)", "Whisper speech recognition", "Robust multilingual speech-to-text", "680k-hour training gives strong low-resource accuracy", "Usable Kannada/English voice input in the field", "Accuracy drops in heavy ambient noise"],
    ["Mohler et al. (2015)", "Predictive policing (randomized field trials)", "Test epidemic-type crime forecasting", "Model-guided patrols outperform hotspot baselines", "Significant drop in forecasted crime events", "Depends on quality historical incident data"],
    ["Chainey et al. (2008)", "Crime hotspot mapping", "Compare hotspot mapping techniques", "Kernel density estimation finds persistent hotspots", "Practical guidance for patrol allocation", "Static maps miss emerging hotspots"],
    ["Ribeiro et al. (2016)", "LIME — Explainable AI", "Explain individual model predictions", "Faithful local explanations build user trust", "Interpretable rationale for every prediction", "Explanations can be unstable across runs"],
    ["Lundberg & Lee (2017)", "SHAP feature attribution", "Unified model interpretation framework", "Consistent, locally accurate attributions", "Global + local interpretability of models", "Computationally heavy on large models"],
])
fill_table(S[6], [
    ["Morselli (2009)", "Social network analysis of crime", "Map structures inside criminal networks", "Networks trade efficiency for security", "Reveals key actors and hidden roles", "Built on incomplete investigation data"],
    ["Duijn et al. (2014)", "Criminal network disruption modelling", "Simulate the impact of arrests on networks", "Removing mid-level actors is most disruptive", "Evidence base for targeted disruption", "Needs reliable relationship/link data"],
    ["Nath (2006)", "Data mining for crime patterns", "Cluster and classify offence records", "Similar MO crimes can be auto-grouped", "Cross-jurisdiction pattern detection", "Handcrafted features limit scalability"],
    ["Gao et al. (2023)", "RAG survey for LLMs", "Systematize retrieval-augmented LLM pipelines", "Retrieval + generation beats fine-tuning alone", "Blueprint for grounded chatbots", "Index maintenance and latency overhead"],
    ["Sandhu et al. (1996)", "Role-Based Access Control (RBAC)", "Formalize permissions through roles", "RBAC simplifies security administration", "Basis for role-based secure access", "Coarse-grained without attribute rules"],
])

# ---------------- slide 8: PROBLEM STATEMENT (keep header p0) ----------------
set_frame(body_shape(S[7]).text_frame, [
    (0, [("The State Crime Records Bureau (SCRB) manages a large and continuously expanding repository of crime-related data contributed by 1,100+ police stations across Karnataka.", None)]),
    (0, []),
    (0, [("Current systems rely on static dashboards and manual queries. Officers cannot freely explore the data, cross-link cases, or obtain insights in real time.", None)]),
    (0, []),
    (0, [("Deep analysis — crime pattern discovery, criminal network analysis, socio-demographic insights, behavioural profiling and proactive prevention intelligence — requires data-science skills that most police units do not have.", None)]),
    (0, []),
    (0, [("Required: an intelligent conversational AI platform that lets investigators query crime data in natural language (English + Kannada, text + voice) and securely delivers patterns, relationships and predictive insights — with explainable AI and full audit trails.", None)]),
], keep_prefix=1)

# ---------------- slide 9: OBJECTIVES ----------------
set_frame(body_shape(S[8], 1).text_frame, [
    (0, [("To develop a multilingual conversational interface (English + Kannada, text + voice) for querying the KSP crime database in natural language.", None)]),
    (0, [("To design a secure NL-to-SQL + RAG pipeline that converts officer questions into governed database queries with grounded, cited answers.", None)]),
    (0, [("To implement analytics modules for crime pattern discovery, criminal network analysis, hotspot & trend detection and predictive early warnings.", None)]),
    (0, [("To ensure explainable AI with audit trails and role-based secure access for every query, insight and export.", None)]),
])

# ---------------- slide 10: PROPOSED METHODOLOGY ----------------
set_frame(body_shape(S[9], 1).text_frame, [
    (0, [("Approach:", True)], 0),
    (1, [("Conversational Layer: ", True), ("Multilingual chatbot (English + Kannada) with voice-enabled, context-aware multi-turn conversations.", False)], 1),
    (1, [("NL-to-SQL Engine: ", True), ("Questions are parsed into safe, role-scoped SQL over the crime database — no hand-written queries needed.", False)], 1),
    (1, [("RAG Pipeline: ", True), ("SOPs, rules and case knowledge are retrieved and grounded into every answer to prevent hallucination.", False)], 1),
    (1, [("Analytics Core: ", True), ("Graph analytics for criminal networks; ML models for trends, hotspots and predictive warnings.", False)], 1),
    (1, [("Trust & Governance: ", True), ("Explainable AI with audit trails; role-based access control on every query and export.", False)], 1),
])

# ---------------- slide 11: benefits ----------------
set_frame(body_shape(S[10]).text_frame, [
    (0, [("Benefits of Conversational AI for Crime Analysis", True)], 0),
    (0, [("Faster Investigations:", True)], 1),
    (1, [("Instant Answers: ", True), ("Investigators ask in plain language and get results in seconds, instead of manual query requests.", False)], 2),
    (0, [("Democratised Analytics:", True)], 1),
    (1, [("No SQL Skills Needed: ", True), ("Every officer can explore the data regardless of technical background; voice input removes entry barriers.", False)], 2),
    (0, [("Trustworthy Insights:", True)], 1),
    (1, [("Explainable by Design: ", True), ("Every answer carries its sources, generated SQL and an audit trail.", False)], 2),
    (0, [("Proactive Policing:", True)], 1),
    (1, [("Early Warnings: ", True), ("Hotspot forecasts and anomaly alerts let teams act before crimes occur.", False)], 2),
])

# ---------------- slide 12: benefits contd. (18pt, flat lvl-0) ----------------
set_frame(body_shape(S[11]).text_frame, [
    (0, [("Scalability:", True)], 0),
    (0, [("Distributed Architecture: ", True), ("Handles data streams from 1,100+ stations and continuously growing volumes.", False)], 1),
    (0, [("Multilingual by Design: ", True), ("Kannada + English today; extensible to other Indian languages.", False)], 1),
    (0, [("Reliability and Accountability:", True)], 3),
    (0, [("Audit Trails: ", True), ("Every answer logs its data sources, generated SQL and reasoning steps.", False)], 4),
    (0, [("Role-Based Security: ", True), ("Officers see only the data their role permits — end to end.", False)], 4),
    (0, [("Institutional Fit:", True)], 6),
    (0, [("PDF Export: ", True), ("Conversation histories export as case-ready reports.", False)], 7),
    (0, [("Complements Existing Systems: ", True), ("Works alongside current SCRB dashboards without replacing them.", False)], 7),
])

# ---------------- slide 13: SYSTEM ARCHITECTURE text ----------------
set_frame(body_shape(S[12], 1).text_frame, [
    (0, [("Data Collection and Preprocessing", True)], 0),
    (0, [("Data Sources:", True)], 1),
    (1, [("Source: ", True), ("Crime records from the SCRB / CCTNS repository contributed by 1,100+ police stations across Karnataka — FIRs, arrests, recoveries and socio-demographic attributes.", False)], 2),
    (1, [("Enrichment: ", True), ("Location geocoding, entity resolution of names/aliases and time normalisation for trend analysis.", False)], 2),
    (0, [("Preprocessing:", True)], 1),
    (1, [("Cleaning & Anonymisation: ", True), ("Deduplication, masking of protected attributes and role-based visibility rules before any analysis.", False)], 2),
])

# fix template typos
replace_text(S[1], 'SYTEM', 'SYSTEM')
replace_text(S[12], 'SYTEM', 'SYSTEM')

# ---------------- slide 14: flowchart ----------------
replace_text(S[13], 'Fig. Model Flowchart', 'Fig. System Architecture / Flowchart')

NAVY = (11, 45, 91); SAFFRON = (255, 153, 51); GREEN = (18, 136, 7)
SLATE = (90, 107, 133); WHITE = (255, 255, 255); OFFW = (244, 246, 249)

def F(sz, bold=True):
    try:
        return ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf' if bold else 'C:/Windows/Fonts/arial.ttf', sz)
    except Exception:
        return ImageFont.load_default()

BOXES = [
    ("INVESTIGATOR", "text · voice · EN/KN"),
    ("INPUT LAYER", "STT (Whisper) · text"),
    ("AI CORE", "LLM + RAG · multi-turn"),
    ("NL → SQL", "schema linking"),
    ("SECURITY GATE", "RBAC · audit log"),
    ("KSP CRIME DB", "SCRB · 1,100+ stations"),
    ("ANALYTICS", "patterns · hotspots · ML"),
    ("EXPLAINABLE OUTPUT", "answer + sources"),
    ("DELIVERY", "text · TTS · PDF export"),
]

W, H = 1500, 1000
img = Image.new("RGB", (W, H), OFFW)
d = ImageDraw.Draw(img)
m, g = 46, 22
bw_ = (W - 2 * m - 4 * g) / 5
bh = 170
y1, y2 = 40, H - 40 - bh
pos1 = [(m + i * (bw_ + g), y1) for i in range(5)]
pos2 = [(W - m - bw_ - i * (bw_ + g), y2) for i in range(4)]

def draw_box(x, y, title, sub, fill, tcol, border, bwd):
    d.rounded_rectangle([x, y, x + bw_, y + bh], radius=14, fill=fill, outline=border, width=bwd)
    fs = 30
    while d.textlength(title, font=F(fs)) > bw_ - 20 and fs > 16:
        fs -= 1
    d.text((x + bw_ / 2, y + (bh - 16) / 2 - 8), title, font=F(fs), fill=tcol, anchor="mm")
    d.text((x + bw_ / 2, y + bh - 26), sub, font=F(20, False), fill=SLATE, anchor="mm")

def arrow_h(x1, x2, y):
    s = 1 if x2 > x1 else -1
    d.line([x1, y, x2 - s * 12, y], fill=SLATE, width=5)
    d.polygon([(x2 - s * 14, y - 10), (x2 - s * 14, y + 10), (x2, y)], fill=SLATE)

for i, ((x, y), (t, s)) in enumerate(zip(pos1 + pos2, BOXES)):
    if i == 5:
        draw_box(x, y, t, s, NAVY, WHITE, NAVY, 6)
    else:
        bcol = GREEN if i in (2, 6) else NAVY
        draw_box(x, y, t, s, WHITE, NAVY, bcol, 6 if i == 4 else 4)

for i in range(4):
    arrow_h(pos1[i][0] + bw_, pos1[i + 1][0], y1 + bh / 2)
for i in range(3):
    arrow_h(pos2[i][0], pos2[i + 1][0] + bw_, y2 + bh / 2)

xb = pos1[4][0] + bw_ / 2
d.line([xb, y1 + bh, xb, y2 - 12], fill=SLATE, width=5)
d.polygon([(xb - 10, y2 - 14), (xb + 10, y2 - 14), (xb, y2)], fill=SLATE)
lab1 = y1 + bh + 14; lab2 = y2 - 36
d.text((pos1[0][0], lab1), "ask in natural language", font=F(24, False), fill=SLATE)
d.text((pos1[2][0], lab1), "intent + entities", font=F(24, False), fill=SLATE)
d.text((pos2[3][0], lab2), "safe SQL", font=F(24, False), fill=SLATE)
d.text((pos2[2][0], lab2), "results → insights", font=F(24, False), fill=SLATE)
d.text((pos2[1][0], lab2), "grounded answer", font=F(24, False), fill=SLATE)

buf = io.BytesIO()
img.save(buf, format="PNG")

# swap the picture on slide 14: delete old, drop rel, add new
pic = next(sh for sh in S[13].shapes if sh.shape_type == MSO_SHAPE_TYPE.PICTURE)
rId = pic._element.blip_rId
pic._element.getparent().remove(pic._element)
try:
    S[13].part.drop_rel(rId)
except Exception:
    pass

cap = next(sh for sh in S[13].shapes if sh.has_text_frame and 'Fig' in sh.text_frame.text)
cap_top = cap.top if cap.top is not None else Inches(6.6)
cap_h = cap.height if cap.height is not None else Inches(0.5)
if cap_top > prs.slide_height / 2:
    top, bottom = Inches(0.45), cap_top - Inches(0.12)
else:
    top, bottom = cap_top + cap_h + Inches(0.12), prs.slide_height - Inches(0.3)
avail_h, avail_w = bottom - top, Inches(12.2)
asp = W / H
h = min(avail_h, int(avail_w / asp))
w = int(h * asp)
left = int((prs.slide_width - w) / 2)
S[13].shapes.add_picture(io.BytesIO(buf.getvalue()), left, top, width=w, height=h)

# ---------------- slide 15: EXPECTED RESULT ----------------
body15 = next(sh for sh in S[14].shapes
              if sh.has_text_frame and 'EXPECTED' not in sh.text_frame.text.upper())
tf15 = body15.text_frame
items = [
    ("Working platform — ", "investigators query 1,100+ stations' crime data in plain English or Kannada, by text or voice."),
    ("Accurate NL-to-SQL — ", "grounded, cited answers; target ≥90% query-intent accuracy on held-out questions."),
    ("Actionable analytics — ", "detected crime patterns, criminal-network graphs, hotspot maps and predictive early warnings."),
    ("Explainable & secure — ", "every answer shows its sources, generated SQL and audit log; role-based access enforced throughout."),
    ("Case-ready output — ", "PDF export of conversation histories for case files and briefings."),
]
first = True
for lead, rest in items:
    p = tf15.paragraphs[0] if first else tf15.add_paragraph()
    first = False
    r1 = p.add_run(); r1.text = lead; r1.font.size = Pt(20); r1.font.bold = True
    r2 = p.add_run(); r2.text = rest; r2.font.size = Pt(20)

# ---------------- slide 16: CONCLUSION ----------------
set_frame(body_shape(S[15], 1).text_frame, [
    (0, [("This project replaces static dashboards with an intelligent conversational layer over the KSP crime database: investigators simply ask, and receive grounded, explainable answers.", None)]),
    (0, []),
    (0, [("The proposed architecture unifies multilingual NLP, NL-to-SQL translation, retrieval-augmented generation, graph analytics and predictive modelling in one secure platform.", None)]),
    (0, []),
    (0, [("By making deep analysis accessible to every officer — in English or Kannada, by text or voice — the system shifts policing from reactive reporting to proactive, intelligence-led prevention.", None)]),
])

# ---------------- slide 17: REFERENCES ----------------
refs = [
    "Lewis, P., et al. 2020. \u201cRetrieval-Augmented Generation for Knowledge-Intensive NLP Tasks.\u201d NeurIPS 33.",
    "Yu, T., et al. 2018. \u201cSpider: A Large-Scale Human-Labeled Dataset for Complex and Cross-Domain Semantic Parsing and Text-to-SQL Task.\u201d EMNLP.",
    "Kakwani, D., et al. 2020. \u201cIndicNLG Suite: Multilingual Datasets for Generative NLG in Indic Languages.\u201d EMNLP.",
    "Radford, A., et al. 2023. \u201cRobust Speech Recognition via Large-Scale Weak Supervision (Whisper).\u201d ICML.",
    "Mohler, G., et al. 2015. \u201cRandomized Controlled Field Trials of Predictive Policing.\u201d Journal of the American Statistical Association 110(512).",
    "Kipf, T. N., and M. Welling. 2017. \u201cSemi-Supervised Classification with Graph Convolutional Networks.\u201d ICLR.",
    "Duijn, P., V. Kashirin, and P. M. A. Sloot. 2014. \u201cThe Relative Ineffectiveness of Criminal Network Disruption.\u201d Scientific Reports 4.",
    "Ribeiro, M. T., et al. 2016. \u201c\u2018Why Should I Trust You?\u2019: Explaining the Predictions of Any Classifier (LIME).\u201d KDD.",
    "Sandhu, R. S., E. J. Coyne, H. L. Feinstein, and C. E. Youman. 1996. \u201cRole-Based Access Control Models.\u201d IEEE Computer 29(2).",
]
paras17 = []
for i, ref in enumerate(refs):
    paras17.append((0, [(ref, None)]))
    if i < len(refs) - 1:
        paras17.append((0, []))
set_frame(body_shape(S[16], 1).text_frame, paras17)

prs.save(OUT)
print("saved:", OUT)

# ---------------- verification ----------------
chk = Presentation(OUT)
bad = ['Autonomous', 'Federat', 'Kaggle', 'vehicles', 'SYTEM', 'Project Title',
       'Chellapandi', 'Nguyen', 'Othman', 'Perla']
issues = []
for i, s in enumerate(chk.slides, 1):
    alltxt = ' '.join(sh.text_frame.text for sh in s.shapes if sh.has_text_frame)
    for tblsh in [sh for sh in s.shapes if sh.has_table]:
        for row in tblsh.table.rows:
            for c in row.cells:
                alltxt += ' ' + c.text_frame.text
    for b in bad:
        if b.lower() in alltxt.lower():
            issues.append(f"slide {i}: leftover {b!r}")
    txts = [' '.join(sh.text_frame.text.split())[:55] for sh in s.shapes
            if sh.has_text_frame and sh.text_frame.text.strip()]
    print(f"{i:2d} || {' || '.join(txts)[:130]}")
pics14 = [sh for sh in list(chk.slides)[13].shapes if sh.shape_type == MSO_SHAPE_TYPE.PICTURE]
print("slide14 pictures:", [(p.image.size, len(p.image.blob)) for p in pics14])
print("ISSUES:", issues if issues else "none — clean")
