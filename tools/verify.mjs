/* ============================================================
   BIS Sahayak — UI regression checks
   No dependencies, no build step: serves this folder over an
   in-process HTTP server, drives headless Chrome over CDP, and
   asserts the things that keep the three surfaces honest.

   Usage:  node tools/verify.mjs
   Needs:  Node 22+ and Chrome or Edge installed.
   Exit code 0 = all checks pass, 1 = something broke.
   ============================================================ */

import { createServer } from "node:http";
import { readFile, stat } from "node:fs/promises";
import { spawn, execFile } from "node:child_process";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { randomUUID } from "node:crypto";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const TYPES = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".md": "text/plain; charset=utf-8",
  ".ico": "image/x-icon",
  ".png": "image/png",
  ".svg": "image/svg+xml",
};
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

/* ---------- 1. static server over the project folder ---------- */
async function serve() {
  const server = createServer(async (req, res) => {
    try {
      const url = decodeURIComponent(req.url.split("?")[0]);
      let file = path.join(ROOT, url === "/" ? "/index.html" : url);
      if (!file.startsWith(ROOT)) throw new Error("outside root");
      const info = await stat(file);
      if (info.isDirectory()) file = path.join(file, "index.html");
      const body = await readFile(file);
      res.writeHead(200, { "Content-Type": TYPES[path.extname(file)] || "application/octet-stream" });
      res.end(body);
    } catch {
      res.writeHead(404, { "Content-Type": "text/plain" });
      res.end("not found");
    }
  });
  await new Promise((r) => server.listen(0, "127.0.0.1", r));
  return { origin: `http://127.0.0.1:${server.address().port}`, close: () => server.close() };
}

/* ---------- 2. headless Chrome ---------- */
const CHROME_CANDIDATES = [
  process.env.CHROME_PATH,
  "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
  "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
  "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
  "C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe",
  "/usr/bin/google-chrome",
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
].filter(Boolean);

async function findChrome() {
  for (const c of CHROME_CANDIDATES) {
    try {
      await stat(c);
      return c;
    } catch {}
  }
  if (process.platform !== "win32") {
    for (const name of ["google-chrome", "chromium", "chromium-browser"]) {
      const found = await new Promise((r) =>
        execFile("which", [name], (e, out) => r(e ? null : out.trim()))
      );
      if (found) return found;
    }
  }
  throw new Error("No Chrome/Edge found — set CHROME_PATH.");
}

function launchChrome(bin, port) {
  const profile = path.join(process.env.TEMP || "/tmp", `bis-verify-${randomUUID().slice(0, 8)}`);
  const proc = spawn(
    bin,
    [
      "--headless=new",
      "--disable-gpu",
      "--hide-scrollbars",
      "--no-first-run",
      "--no-default-browser-check",
      `--remote-debugging-port=${port}`,
      `--user-data-dir=${profile}`,
      "--window-size=1440,1000",
      "about:blank",
    ],
    { stdio: "ignore" }
  );
  return proc;
}

async function connect(port) {
  for (let i = 0; i < 80; i++) {
    try {
      const list = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
      const page = list.find((t) => t.type === "page");
      if (page) return await openSocket(page.webSocketDebuggerUrl);
    } catch {}
    await sleep(250);
  }
  throw new Error("Chrome did not start");
}

function openSocket(url) {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(url);
    const pending = new Map();
    const listeners = [];
    let id = 0;
    ws.onerror = () => reject(new Error("CDP socket failed"));
    ws.onopen = () =>
      resolve({
        send(method, params = {}) {
          const msgId = ++id;
          return new Promise((res, rej) => {
            pending.set(msgId, { res, rej });
            ws.send(JSON.stringify({ id: msgId, method, params }));
          });
        },
        on(fn) {
          listeners.push(fn);
        },
        close() {
          ws.close();
        },
      });
    ws.onmessage = (ev) => {
      const msg = JSON.parse(ev.data);
      if (msg.id && pending.has(msg.id)) {
        const { res, rej } = pending.get(msg.id);
        pending.delete(msg.id);
        msg.error ? rej(new Error(JSON.stringify(msg.error))) : res(msg.result);
      } else if (msg.method) listeners.forEach((fn) => fn(msg));
    };
  });
}

/* ---------- 3. the checks ---------- */
/* Each check: open a page, evaluate an async expression, then apply
   assert rules to the value it returns. `logs` must stay clean. */
const COMMON = `({ overflowX: document.documentElement.scrollWidth - window.innerWidth })`;

const CHECKS = [
  {
    name: "entry page (index.html)",
    url: "/index.html",
    expr: `({
      ...${COMMON},
      title: document.title,
      demoAnswer: document.getElementById('demoA').textContent.slice(0, 40),
      cites: document.querySelectorAll('#demoCites .citation').length,
      doubledClause: /Clause Clause/.test(document.getElementById('demoCites').textContent),
      swatches: document.querySelectorAll('.swatch').length,
      revealsIn: document.querySelectorAll('.reveal.in').length,
      stripe: getComputedStyle(document.querySelector('.topnav'), '::after').backgroundImage.includes('rgb(255, 153, 51)')
    })`,
    assert: (v) => [
      ["no horizontal overflow", v.overflowX === 0],
      ["live demo produced an answer", v.demoAnswer.length > 10],
      ["two citation chips rendered", v.cites === 2],
      ['no "Clause Clause" duplication', !v.doubledClause],
      ["7 token swatches", v.swatches === 7],
      ["certification stripe on the nav", v.stripe === true],
      ["scroll reveal fired", v.revealsIn > 0],
    ],
  },
  {
    name: "portal landing (website/index.html)",
    url: "/website/index.html",
    expr: `({
      ...${COMMON},
      widget: !!document.querySelector('#widget-root [data-bis-mounted]') || !!document.getElementById('widget-root'),
      features: document.querySelectorAll('.feature').length,
      steps: document.querySelectorAll('.step').length,
      ask: !!document.getElementById('ask'),
      ghost: !!document.getElementById('ghost')
    })`,
    assert: (v) => [
      ["no horizontal overflow", v.overflowX === 0],
      ["4 feature cards", v.features === 4],
      ["3-step strip", v.steps === 3],
      ["ask bar + typed example present", v.ask && v.ghost],
    ],
  },
  {
    name: "chat (website/chat.html)",
    url: "/website/chat.html",
    wait: 3000,
    expr: `(async () => {
      await send('Is IS 302 mandatory for home appliances?');
      await new Promise(r => setTimeout(r, 300));
      const typingGone = document.querySelectorAll('.typing-dots').length;
      await new Promise(r => setTimeout(r, 1400));
      return {
        ...${COMMON},
        msgs: document.querySelectorAll('.msg').length,
        citations: document.querySelectorAll('.msg.ai .citation').length,
        source: /IS 302/.test(document.getElementById('sourceBody').textContent),
        typingLeft: typingGone,
        emptyGone: !document.getElementById('empty')
      };
    })()`,
    assert: (v) => [
      ["no horizontal overflow", v.overflowX === 0],
      ["answer + question rendered", v.msgs === 2],
      ["citations attached", v.citations === 2],
      ["source drawer updated", v.source],
      ["typing indicator removed after reply", v.typingLeft === 0],
      ["empty state dismissed on first message", v.emptyGone === true],
    ],
  },
  {
    name: "chat history (website/chat.html)",
    url: "/website/chat.html",
    wait: 3000,
    expr: `(async () => {
      document.querySelector('.history-item[data-q]').click();
      await new Promise(r => setTimeout(r, 300));
      const typing = document.querySelectorAll('.typing-dots').length;
      await new Promise(r => setTimeout(r, 1500));
      return { typing, msgs: document.querySelectorAll('.msg').length, ...${COMMON} };
    })()`,
    assert: (v) => [
      ["no horizontal overflow", v.overflowX === 0],
      ["history item showed a typing indicator", v.typing === 1],
      ["history item produced a reply", v.msgs === 2],
    ],
  },
  {
    name: "standard recommender (website/recommender.html)",
    url: "/website/recommender.html",
    wait: 3000,
    expr: `(async () => {
      document.getElementById('prod').value = '12W LED bulb drivers sold in India';
      document.getElementById('recoForm').dispatchEvent(new Event('submit', { cancelable: true }));
      await new Promise(r => setTimeout(r, 250));
      return {
        ...${COMMON},
        cards: document.querySelectorAll('#results .std-card').length,
        badges: document.querySelectorAll('#results .confidence').length,
        doubled: /Clause Clause/.test(document.getElementById('results').textContent)
      };
    })()`,
    assert: (v) => [
      ["no horizontal overflow", v.overflowX === 0],
      ["3 standard cards", v.cards === 3],
      ["confidence badge on every card", v.badges === 3],
      ['no "Clause Clause" duplication', !v.doubled],
    ],
  },
  {
    name: "hallmark check (website/hallmark.html)",
    url: "/website/hallmark.html",
    wait: 3000,
    expr: `(async () => {
      document.querySelector('[data-demo="AB1C23"]').click();
      await new Promise(r => setTimeout(r, 250));
      const ok = document.getElementById('result').className;
      document.querySelector('[data-demo="XX9999"]').click();
      await new Promise(r => setTimeout(r, 250));
      return { ok, bad: document.getElementById('result').className, ...${COMMON} };
    })()`,
    assert: (v) => [
      ["no horizontal overflow", v.overflowX === 0],
      ["valid HUID verifies", /verified/.test(v.ok)],
      ["invalid HUID fails", /failed/.test(v.bad)],
    ],
  },
  {
    name: "lab finder (website/lab-finder.html)",
    url: "/website/lab-finder.html",
    wait: 3000,
    expr: `(async () => {
      const before = document.querySelectorAll('.lab').length;
      const st = document.getElementById('state');
      st.value = 'Karnataka';
      st.dispatchEvent(new Event('change'));
      await new Promise(r => setTimeout(r, 200));
      const after = document.querySelectorAll('.lab').length;
      const label = document.getElementById('count').textContent;
      st.value = ''; st.dispatchEvent(new Event('change'));
      return { before, after, label, ...${COMMON} };
    })()`,
    assert: (v) => [
      ["no horizontal overflow", v.overflowX === 0],
      ["6 labs listed", v.before === 6],
      ["state filter narrows the list", v.after === 1 && /1 of 6/.test(v.label)],
    ],
  },
  {
    name: "widget embed demo (website/widget-demo.html)",
    url: "/website/widget-demo.html",
    expr: `({
      ...${COMMON},
      mounted: document.getElementById('widget-root')?.dataset.bisMounted === '1',
      host: document.querySelectorAll('#widget-root div').length
    })`,
    assert: (v) => [
      ["no horizontal overflow", v.overflowX === 0],
      ["widget mounted into the documented #widget-root", v.mounted === true],
      ["shadow host present", v.host === 1],
    ],
  },
  {
    name: "mobile app (app/index.html)",
    url: "/app/index.html",
    expr: `({
      ...${COMMON},
      deadFragments: [...document.querySelectorAll('a[href^="#"]')]
        .map(a => a.getAttribute('href'))
        .filter(h => h.length > 1 && !document.getElementById(h.slice(1))),
      bareLi: [...document.querySelectorAll('li')].filter(li => !li.closest('ul,ol')).length,
      optsWithoutState: [...document.querySelectorAll('.opt')].filter(o => !o.hasAttribute('aria-pressed')).length,
      phones: document.querySelectorAll('.phone').length,
      tabLabels: [...new Set([...document.querySelectorAll('.tabbar')].map(n => n.getAttribute('aria-label')))].length,
      tabbars: document.querySelectorAll('.tabbar').length
    })`,
    assert: (v) => [
      ["no horizontal overflow", v.overflowX === 0],
      ["every fragment link resolves", v.deadFragments.length === 0],
      ["no <li> outside a list", v.bareLi === 0],
      ["every toggle declares aria-pressed", v.optsWithoutState === 0],
      ["7 phone frames", v.phones === 7],
      ["each tab bar has a unique label", v.tabLabels === v.tabbars],
    ],
  },
  {
    name: "whatsapp conversation (whatsapp/index.html)",
    url: "/whatsapp/index.html",
    wait: 3500,
    expr: `(async () => {
      const field = document.getElementById('waField');
      field.value = 'Is IS 302 mandatory for home appliances?';
      document.getElementById('waComposer').dispatchEvent(new Event('submit', { cancelable: true }));
      await new Promise(r => setTimeout(r, 1400));
      const times = [...document.querySelectorAll('#dynamic .time')].map(t => parseInt(t.textContent));
      return {
        ...${COMMON},
        bareLi: [...document.querySelectorAll('li')].filter(li => !li.closest('ul,ol')).length,
        h1: !!document.querySelector('h1'),
        menuRows: document.querySelectorAll('.wa-list button').length,
        hasLanguageRow: /भाषा बदला/.test(document.querySelector('.wa-list').textContent),
        quickReplies: [...document.querySelectorAll('#dynamic .wa-btn')].length,
        replyCites: /📄 Source: IS 302/.test(document.getElementById('dynamic').textContent),
        clockAdvances: times.length >= 1 && times.every((t, i) => i === 0 || t >= times[i - 1]),
        langPressed: document.querySelectorAll('#langBtns [aria-pressed="true"]').length
      };
    })()`,
    assert: (v) => [
      ["no horizontal overflow", v.overflowX === 0],
      ["no <li> outside a list", v.bareLi === 0],
      ["page has an <h1>", v.h1 === true],
      ["main menu is the documented 6-row list", v.menuRows === 6],
      ["list includes Change language", v.hasLanguageRow === true],
      ["answer ends with max-3 quick replies", v.quickReplies === 3],
      ["reply carries the 📄 Source line", v.replyCites === true],
      ["thread timestamps never go backwards", v.clockAdvances === true],
      ["language buttons expose pressed state", v.langPressed === 1],
    ],
  },
  {
    name: "language persists across surfaces",
    url: "/index.html",
    wait: 2500,
    expr: `(async () => {
      const previous = localStorage.getItem('bis-lang');
      localStorage.setItem('bis-lang', 'mr');
      const f = document.createElement('iframe');
      f.style.cssText = 'position:fixed;left:-9999px;width:1200px;height:800px';
      f.src = '/website/chat.html';
      document.body.appendChild(f);
      await new Promise(r => { f.onload = () => setTimeout(r, 1600); });
      // BIS is a lexical global: read it from inside the frame
      const frame = f.contentWindow.eval(
        "({ lang: BIS.getLanguage(), htmlLang: document.documentElement.lang, placeholder: (document.getElementById('msg')||{}).placeholder || '' })"
      );
      const { lang, htmlLang, placeholder } = frame;
      f.remove();
      previous === null ? localStorage.removeItem('bis-lang') : localStorage.setItem('bis-lang', previous);
      return { lang, htmlLang, translated: placeholder.includes('मानक') };
    })()`,
    assert: (v) => [
      ["saved language restored on another surface", v.lang === "mr"],
      ["document language follows it", v.htmlLang === "mr"],
      ["UI strings localised (Marathi placeholder)", v.translated === true],
    ],
  },
];

/* ---------- 4. runner ---------- */
async function main() {
  const origin = (await serve()).origin;
  const bin = await findChrome();
  const port = 9500 + Math.floor(Math.random() * 400);
  const chrome = launchChrome(bin, port);
  const cdp = await connect(port);

  const failures = [];
  let passed = 0;
  let consoleErrors = [];

  cdp.on((m) => {
    if (m.method === "Runtime.consoleAPICalled" && m.params.type === "error")
      consoleErrors.push(m.params.args.map((a) => a.value ?? a.description ?? "").join(" "));
    if (m.method === "Runtime.exceptionThrown")
      consoleErrors.push("EXCEPTION " + (m.params.exceptionDetails.exception?.description || m.params.exceptionDetails.text));
    if (m.method === "Log.entryAdded" && m.params.entry.level === "error")
      consoleErrors.push(m.params.entry.text + " " + (m.params.entry.url || ""));
  });

  await cdp.send("Runtime.enable");
  await cdp.send("Log.enable");
  await cdp.send("Page.enable");

  for (const check of CHECKS) {
    if (check.skipAssert) continue;
    consoleErrors = [];
    await cdp.send("Page.navigate", { url: origin + check.url });
    await sleep(check.wait || 2200);

    let value;
    try {
      const res = await cdp.send("Runtime.evaluate", {
        expression: check.expr,
        returnByValue: true,
        awaitPromise: true,
      });
      if (res.exceptionDetails) throw new Error(res.exceptionDetails.text);
      value = res.result.value;
    } catch (e) {
      failures.push(`${check.name} — evaluation failed: ${e.message}`);
      console.log(`\u2717 ${check.name} (evaluation failed)`);
      console.log(`     \u2192 ${e.message}`);
      continue;
    }

    const results = check.assert(value);
    const bad = results.filter(([, ok]) => !ok);
    results.forEach(([label, ok]) => (ok ? passed++ : failures.push(`${check.name} — ${label}`)));
    console.log(`${bad.length ? "\u2717" : "\u2713"} ${check.name}${bad.length ? ` (${bad.length} failed)` : ""}`);
    bad.forEach(([label]) => console.log(`     \u2192 ${label}`));

    if (consoleErrors.length) {
      consoleErrors.forEach((e) => failures.push(`${check.name} — console: ${e}`));
      console.log(`     \u2192 console: ${consoleErrors[0]}`);
    }
  }

  cdp.close();
  chrome.kill();
  process.exit(failures.length ? 1 : 0);
}

main().catch((e) => {
  console.error("verify failed to run:", e.message);
  process.exit(1);
});
