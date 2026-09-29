# WhatsApp Message Template Library — BIS Sahayak (§6.3)

Six templates, three languages. Formatting follows §6.1: `*bold*`, emoji hierarchy,
citation line in the exact `📄 Source: …` format, confidence as emoji prefix.

Variables: `{{name}}`, `{{standard}}`, `{{clause}}`, `{{huid}}`, `{{ticket}}`, `{{contact}}`

---

## 1 · Welcome

**EN**
```
🙏 Namaste! I'm *BIS Sahayak* — your helper for Indian Standards & BIS services.

Choose your language:
```
Buttons (List message, up to 10):
```
English
हिंदी
मराठी
```

**HI**
```
🙏 नमस्ते! मैं *BIS Sahayak* हूँ — भारतीय मानकों और BIS सेवाओं का सहायक।

अपनी भाषा चुनें:
```

**MR**
```
🙏 नमस्कार! मी *BIS Sahayak* — भारतीय मानक आणि BIS सेवांचा सहाय्यक.

तुमची भाषा निवडा:
```

---

## 2 · Language-select (acknowledgement → main menu)

**EN**
```
Great! How can I help you today?
```
**HI**
```
बढ़िया! मैं आज आपकी किस तरह मदद कर सकता हूँ?
```
**MR**
```
उत्तम! मी तुम्हाला कशी मदत करू शकतो?
```

Quick replies (max 3) — **labels identical in meaning across all 3 surfaces** (§7):

| EN | HI | MR |
|---|---|---|
| Find my standard | मेरा मानक खोजें | माझा मानक शोधा |
| Certification steps | प्रमाणन चरण | प्रमाणपत्र प्रक्रिया |
| Check hallmark | हॉलमार्क जाँच | हॉलमार्क तपासा |

*(4th option "Type / voice" opens free-text mode — goes in a List message with the other three.)*

---

## 3 · Main menu (List message)

Header: `BIS Sahayak — Main menu`
Body: `Pick an option, or just type your question.`

```
1. Find my standard
2. Certification steps
3. Check hallmark
4. Find a lab
5. Talk to a BIS officer
6. Change language / भाषा बदला
```

---

## 4 · Answer with citation (the core template)

Structure — never reorder the four parts:

```
{✅ | ⚠️} {answer in plain language, *key terms bolded*}

📄 Source: {{standard}}, Clause {{clause}}

{🔊 Listen} {👍 Helpful} {👎 Not quite}
```

**EN example**
```
✅ Yes — household appliances fall under *IS 302 (Part 1)* and need BIS CRS registration before sale in India. Clause 4.2 covers protection against electric shock.

📄 Source: IS 302 Part 1, Clause 4.2
```
Buttons: `🔊 Listen` (triggers Bulbul v3 voice note) · `👍 Helpful` · `👎 Not quite`

**HI example**
```
✅ जी हाँ — घरेलू उपकरण *IS 302 (भाग 1)* के अंतर्गत आते हैं और भारत में बिक्री से पहले BIS CRS पंजीकरण आवश्यक है। खंड 4.2 विद्युत झटके से सुरक्षा से संबंधित है।

📄 Source: IS 302 Part 1, Clause 4.2
```

**MR example**
```
✅ हो — घरगुती उपकरणे *IS 302 (भाग 1)* अंतर्गत येतात आणि भारतात विक्रीपूर्वी BIS CRS नोंदणी आवश्यक आहे. कलम 4.2 विद्युत आघातापासून संरक्षणाशी संबंधित आहे.

📄 Source: IS 302 Part 1, Clause 4.2
```

⚠️ **Medium confidence variant** — prefix `⚠️`, add line:
`Partial match — confirm with the nearest BIS office.`

---

## 5 · Low-confidence fallback

```
❌ *Not found in BIS records* for "{{question}}".

Here's who to contact:
• Nearest BIS Branch Office: {{contact}}
• Raise it in the *BIS Care* app
• Or tap below and I'll pass it to a BIS officer

[Talk to BIS officer] [Send to my email]
```

**MR**
```
❌ "{{question}}" BIS रेकॉर्डमध्ये सापडले नाही.

संपर्क साधा:
• जवळचे BIS शाखा कार्यालय: {{contact}}
• *BIS Care* अ‍ॅपवर तक्रार नोंदवा
• किंवा खाली टैप करा — मी हे BIS अधिकाऱ्यांकडे पाठवतो

[BIS अधिकाऱ्याशी विचारा]
```

---

## 6 · Human handoff

```
Got it — I've summarised your question for a BIS officer.

🎟️ Ticket: {{ticket}}
⏱️ Reply within 1 working day

You'll get the answer right here in this chat.
```

Then the agent-side note (internal, not sent):
`Summary: {last user question} · Language: {lang} · Citations shown: {n} · Confidence: {high|medium|low}`

---

## Voice-note round trip (§6.3)

| Step | Event |
|---|---|
| 1 | User sends a voice note |
| 2 | Sarvam **Saaras v3** transcribes → `language: auto` |
| 3 | Same `POST /chat` call as every other surface |
| 4 | Reply = **4** (text + citation) with `🔊 Listen` button |
| 5 | User taps 🔊 → **Bulbul v3** sends `audio_url` as a voice note |

Transcription failure: `⚠️ I couldn't catch that — try again, or type your question.`
