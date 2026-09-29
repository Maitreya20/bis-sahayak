# WhatsApp Conversation Flow — BIS Sahayak (§6.2 / §6.3)

Machine-readable map of every menu branch. The rendered flowchart lives in
[`index.html`](index.html) (diagram section).

```yaml
entry:
  trigger: "first message | /start | hello/hi/नमस्ते/नमस्कार"
  template: welcome            # 1
  message_type: list           # up to 10 options
  options: [English, हिंदी, मराठी, + more]

language_selected:
  template: language_select    # 2
  then: main_menu

main_menu:
  template: main_menu          # 3
  message_type: list
  branches:
    find_my_standard:
      label: { en: "Find my standard", hi: "मेरा मानक खोजें", mr: "माझ्यासाठी मानक शोधा" }
      prompt: "Describe your product in a line"
      input: free_text | voice_note
      api: POST /chat
      reply: answer_with_citation   # 4
    certification_steps:
      label: { en: "Certification steps", hi: "प्रमाणन चरण", mr: "प्रमाणपत्र प्रक्रिया" }
      question: "CRS (made in India) or FMCS (made abroad)?"
      reply: numbered_step_list      # bold headers, one message per step
      then: feedback_row
    check_hallmark:
      label: { en: "Check hallmark", hi: "हॉलमार्क जाँचें", mr: "हॉलमार्क तपासा" }
      prompt: "Send the HUID (6 characters)"
      input: text
      branches:
        huid_verified:
          prefix: "✅"
          reply: "Hallmark verified — {{standard}}, purity {{grade}}, assay centre {{centre}}"
          citations: [{ doc: IS 1417, clause: "Clause 5" }]
        huid_not_found:
          template: low_confidence_fallback   # 5
          prefix: "❌"
      then: feedback_row
    find_a_lab:
      label: { en: "Find a lab", hi: "प्रयोगशाला खोजें", mr: "चाचणी प्रयोगशाला शोधा" }
      ask: ["product category", "state/city"]
      reply: list_message   # up to 10 labs, tap → address + hours
    talk_to_bis_officer:
      template: human_handoff   # 6
      ticket_format: "BIS-####"
      sla: "1 working day"
    free_text:
      input: text | voice_note
      voice_pipeline: "Saaras v3 → POST /chat → text + optional Bulbul v3 audio"
      api: POST /chat
      reply: answer_with_citation  # 4

confidence_routing:            # identical logic on all 3 surfaces (§7)
  high:   { prefix: "✅", suffix: null }
  medium: { prefix: "⚠️", suffix: "Partial match — confirm with BIS office." }
  low:    { prefix: "❌", template: low_confidence_fallback }   # 5

answer_with_citation:          # 4 — structure never changes
  order:
    - confidence_prefix        # ✅ | ⚠️
    - answer                   # plain language, *bold* key terms
    - "📄 Source: {{standard}}, Clause {{clause}}"   # exact format
    - quick_replies: ["🔊 Listen", "👍 Helpful", "👎 Not quite"]  # max 3

feedback_row:
  helpful:     "🙏 Thanks — noted!"
  not_helpful: "What should I check differently?" → back to free_text
  ask_officer: template: human_handoff   # 6

escape_hatches:
  /language: back to language list
  /menu:     back to main_menu
  wrong_language_detected: "Reply in detected language + offer switch"
```

## Consistency guarantees (§7 checklist)

- Citation format `📄 Source: [Standard], [Clause]` — same string on web, app, WhatsApp.
- Confidence logic (high/medium/low → ✅/⚠️/❌) is one implementation in `/chat`;
  surfaces only choose their rendering (colour badge vs emoji).
- Quick-action labels use the same translation keys as the portal and app.
- Language set identical across all three surfaces.
