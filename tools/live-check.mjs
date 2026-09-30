/* ============================================================
   BIS Sahayak — live backend browser check (SIH demo dress rehearsal)

   Serves as an end-to-end probe of the REAL experience: launches
   headless Chrome (same discovery as verify.mjs), opens the pages
   SERVED BY THE FASTAPI BACKEND, and asserts:

     1. chat page   — BIS_API_BASE injected in <head>, a question sent
                      through the real composer hits POST /chat exactly
                      once, returns cited, badge-classified answer text,
                      with zero console errors.
     2. lab-finder  — /labs endpoint reachable from the page, the
                      6-lab baseline still renders.
     3. recommender — /standards/search reachable from the page and
                      returns ranked results; cards still render.

   Usage:
     node tools/live-check.mjs [baseURL]      # default http://localhost:8000
   Exit 0 = all good. Needs Node 22+ and Chrome or Edge.
   ============================================================ */
import { spawn } from "node:child_process";
import { existsSync } from "node:fs";
import path from "node:path";
import { randomUUID } from "node:crypto";

const BASE = (process.argv[2] || process.env.BIS_BASE || "http://localhost:8000").replace(/\/+$/, "");
const TIMEOUT = Number(process.env.LIVECHECK_TIMEOUT || 20000);

const CHROME_CANDIDATES = [
  process.env.CHROME_PATH,
  "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
  "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
  "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
  "C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe",
  "/usr/bin/google-chrome",
  "/usr/bin/chromium-browser",
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
].filter(Boolean);

function findChrome() {
  for (const bin of CHROME_CANDIDATES) if (existsSync(bin)) return bin;
  throw new Error("No Chrome/Edge found — set CHROME_PATH.");
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

function launchChrome(bin, port) {
  const profile = path.join(process.env.TEMP || "/tmp", `bis-live-${randomUUID().slice(0, 8)}`);
  return spawn(bin, [
    "--headless=new", "--disable-gpu", "--hide-scrollbars",
    "--no-first-run", "--no-default-browser-check",
    `--remote-debugging-port=${port}`, `--user-data-dir=${profile}`,
    "--window-size=1440,1000", "about:blank",
  ], { stdio: "ignore" });
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
    ws.onopen = () => resolve({
      send(method, params = {}) {
        const msgId = ++id;
        return new Promise((res, rej) => {
          pending.set(msgId, { res, rej });
          ws.send(JSON.stringify({ id: msgId, method, params }));
        });
      },
      on(fn) { listeners.push(fn); },
      close() { ws.close(); },
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

/* ---- page driver ---- */
async function goto(cdp, url, waitExpr = "document.readyState === 'complete'") {
  const errors = [];
  cdp.on((msg) => {
    if (msg.method === "Runtime.consoleAPICalled" &&
        ["error", "warning"].includes(msg.params.type)) {
      errors.push(msg.params.args.map((a) => a.value ?? a.description ?? "").join(" "));
    }
    if (msg.method === "Log.entryAdded" && msg.params.entry.level === "error") {
      errors.push(msg.params.entry.text);
    }
  });
  await cdp.send("Runtime.enable");
  await cdp.send("Log.enable");
  await cdp.send("Page.enable");
  await cdp.send("Page.navigate", { url });
  const deadline = Date.now() + TIMEOUT;
  while (Date.now() < deadline) {
    const r = await cdp.send("Runtime.evaluate",
      { expression: waitExpr, returnByValue: true }).catch(() => null);
    if (r?.result?.value === true) break;
    await sleep(150);
  }
  return errors;
}

async function evalJS(cdp, expr, { awaitPromise = false } = {}) {
  const r = await cdp.send("Runtime.evaluate", {
    expression: expr, returnByValue: true, awaitPromise,
  });
  if (r.exceptionDetails) throw new Error(r.exceptionDetails.text + " " +
    (r.exceptionDetails.exception?.description || ""));
  return r.result?.value;
}

async function waitFor(cdp, expr, label) {
  const deadline = Date.now() + TIMEOUT;
  while (Date.now() < deadline) {
    if (await evalJS(cdp, expr)) return;
    await sleep(200);
  }
  throw new Error("timeout waiting for: " + label);
}

/* ---- checks ---- */
const results = [];
function record(name, ok, detail = "") {
  results.push({ name, ok, detail });
  console.log(`${ok ? "✓" : "✗"} ${name}${detail ? " — " + detail : ""}`);
}

const chrome = launchChrome(findChrome(), 9333);
try {
  const cdp = await connect(9333);

  /* 1 — chat page speaks to the live backend */
  {
    const errors = await goto(cdp, `${BASE}/website/chat.html`,
      "document.readyState === 'complete' && !!window.BIS && !!document.getElementById('composer')");
    const injected = await evalJS(cdp,
      "typeof window.BIS_API_BASE === 'string' && window.BIS_API_BASE.startsWith('http')");
    record("chat: BIS_API_BASE injected", injected,
      injected ? "head snippet present" : "window.BIS_API_BASE missing");
    // count /chat fetches the client actually makes
    await evalJS(cdp, `
      window.__chatCalls = 0;
      window.__chatUrls = [];
      const __of = window.fetch;
      window.fetch = function (...a) {
        const u = String(a[0]);
        // only the BIS API counts — Supabase chat_messages persistence also
        // contains '/chat' in its URL
        if (window.BIS_API_BASE && u.startsWith(window.BIS_API_BASE) && u.endsWith('/chat')) {
          window.__chatCalls++; window.__chatUrls.push(u + ' [' + (a[1] && a[1].method || 'GET') + ']');
        }
        return __of.apply(this, a);
      };`);
    await evalJS(cdp, `
      document.getElementById('msg').value = 'Is IS 302 mandatory for home appliances?';
      document.getElementById('composer')
        .dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));`);;
    await waitFor(cdp,
      "document.querySelectorAll('#scroll .citation').length > 0",
      "cited answer bubble");
    await sleep(400); // let late renders/console settle
    const state = await evalJS(cdp, `({
      calls: window.__chatCalls,
      urls: window.__chatUrls || [],
      cites: document.querySelectorAll('#scroll .citation').length,
      badge: !!document.querySelector('#scroll .confidence'),
      text: (document.querySelector('#scroll .bubble')?.textContent || '').slice(0, 90),
    })`);
    record("chat: composer hit POST /chat exactly once", state.calls === 1,
      `calls=${state.calls} :: ${state.urls.join(" | ") || "none"}`);
    record("chat: answer carries citations + confidence badge",
      state.cites > 0 && state.badge, `cites=${state.cites}`);
    record("chat: answer text grounded (IS 302 in reply)",
      /IS\s*302/.test(state.text), JSON.stringify(state.text));
    record("chat: zero console errors", errors.length === 0,
      errors.slice(0, 2).join(" | "));
  }

  /* 2 — lab-finder: /labs reachable from the page, baseline intact */
  {
    const errors = await goto(cdp, `${BASE}/website/lab-finder.html`,
      "document.readyState === 'complete' && document.querySelectorAll('.lab').length > 0");
    const probe = await evalJS(cdp, `
      fetch(window.BIS_API_BASE.replace(/\\/+$/, '') + '/labs')
        .then((r) => r.json())
        .then((d) => ({ ok: true, count: d.count }))
        .catch((e) => ({ ok: false, err: String(e) }));`,
      { awaitPromise: true });
    record("labs: GET /labs reachable from page",
      probe.ok && probe.count >= 5, `count=${probe.count ?? probe.err}`);
    const baseline = await evalJS(cdp,
      "document.querySelectorAll('.lab').length");
    record("labs: 6-lab baseline still rendered", baseline === 6, `n=${baseline}`);
    record("labs: zero console errors", errors.length === 0,
      errors.slice(0, 2).join(" | "));
  }

  /* 3 — recommender: live search reachable, cards render */
  {
    const errors = await goto(cdp, `${BASE}/website/recommender.html`,
      "document.readyState === 'complete' && !!document.getElementById('recoForm')");
    const probe = await evalJS(cdp, `
      fetch(window.BIS_API_BASE.replace(/\\/+$/, '') + '/standards/search?q=' +
            encodeURIComponent('LED bulb driver'))
        .then((r) => r.json())
        .then((d) => ({ ok: true, n: d.results.length,
                        top: d.results[0] && d.results[0].doc }))
        .catch((e) => ({ ok: false, err: String(e) }));`,
      { awaitPromise: true });
    record("reco: GET /standards/search reachable from page",
      probe.ok && probe.n > 0, `top=${probe.top ?? probe.err}`);
    await evalJS(cdp, `
      document.getElementById('prod').value = 'LED bulb driver';
      document.getElementById('recoForm')
        .dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));`);
    await waitFor(cdp,
      "!document.getElementById('results').hidden && document.querySelectorAll('.std-card').length > 0",
      "result cards");
    const nCards = await evalJS(cdp,
      "document.querySelectorAll('.std-card').length");
    record("reco: standard cards render after search", nCards > 0, `n=${nCards}`);
    record("reco: zero console errors", errors.length === 0,
      errors.slice(0, 2).join(" | "));
  }
} finally {
  chrome.kill();
}

const failed = results.filter((r) => !r.ok);
console.log(`\n${results.length - failed.length}/${results.length} live checks passed (${BASE})`);
process.exit(failed.length ? 1 : 0);
