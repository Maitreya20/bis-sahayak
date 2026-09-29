/* ============================================================
   BIS Sahayak — Supabase data layer (optional)

   Static site, no build step: the client is pulled from the CDN
   with a dynamic import() the first time it is actually needed.

   Configure EITHER by setting these before this tag:

       window.BIS_SUPABASE_URL      = "https://xyz.supabase.co";
       window.BIS_SUPABASE_ANON_KEY = "eyJ...";

   ...or by passing them as attributes on the script tag:

       <script src="../assets/js/supabase.js"
               data-url="https://xyz.supabase.co"
               data-anon-key="eyJ..."></script>

   Contract with the rest of the UI:
     - unconfigured  -> every function resolves null, zero network
     - configured but unreachable / RLS denies / table empty
                        -> warns on console.warn and resolves null
     - callers treat null as "use the local fixtures"
     This module never rejects, so nothing can break the UI or the
     regression checks in tools/verify.mjs.
   ============================================================ */

/* ---- project credentials — the ONE place they live ------------
   Project URL + anon public key (Supabase → Project Settings → API, or
   `supabase projects api-keys --project-ref <ref>`).

   The anon key is public by design: it ships in the browser and is
   guarded by the Row Level Security policies in
   supabase/migrations/*.sql. Never put the service_role key here —
   that one is a server-side secret.

   Leave both empty and the site runs entirely on local fixtures with
   zero network calls. A page can override them by setting
   window.BIS_SUPABASE_URL / window.BIS_SUPABASE_ANON_KEY before this
   tag, or via data-url / data-anon-key attributes on the element. */
window.BIS_SUPABASE_URL =
  window.BIS_SUPABASE_URL || "https://llnwamcvygyzernemmop.supabase.co";
window.BIS_SUPABASE_ANON_KEY =
  window.BIS_SUPABASE_ANON_KEY ||
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxsbndhbWN2eWd5emVybmVtbW9wIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTA2OTkzOTcsImV4cCI6MjEwNjI3NTM5N30.HQSVlsoV4kMV0rG9HWL2JfJsAMaq_Aa6I80f-H7VVDg";

const BISSupa = (() => {
  const script = document.currentScript;
  const SUPABASE_URL =
    window.BIS_SUPABASE_URL || (script && script.getAttribute("data-url")) || "";
  const SUPABASE_ANON_KEY =
    window.BIS_SUPABASE_ANON_KEY || (script && script.getAttribute("data-anon-key")) || "";

  const configured = Boolean(SUPABASE_URL && SUPABASE_ANON_KEY);
  const CDN = "https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/+esm";

  let pendingClient = null;

  /** Lazily create the shared client; resolves null when unavailable. */
  function client() {
    if (!configured) return Promise.resolve(null);
    if (!pendingClient) {
      pendingClient = import(CDN)
        .then((mod) =>
          mod.createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
            auth: { persistSession: false, autoRefreshToken: false },
            global: { headers: { "x-client-info": "bis-sahayak-ui" } },
          })
        )
        .catch((err) => {
          console.warn("[BIS] Supabase client unavailable — staying on fixtures:", err && err.message);
          pendingClient = null;
          return null;
        });
    }
    return pendingClient;
  }

  /** SELECT helper: rows on success, null on any problem. */
  async function select(table, builder) {
    const sb = await client();
    if (!sb) return null;
    try {
      let query = sb.from(table).select("*");
      if (builder) query = builder(query);
      const { data, error } = await query;
      if (error) {
        console.warn(`[BIS] ${table} read failed (${error.code || "error"}) — using fixtures:`, error.message);
        return null;
      }
      return data || [];
    } catch (err) {
      console.warn(`[BIS] ${table} read failed — using fixtures:`, err && err.message);
      return null;
    }
  }

  /** Persist one turn of the conversation. Fire-and-forget by design. */
  async function saveMessage(msg) {
    const sb = await client();
    if (!sb || !msg || !msg.content) return null;
    try {
      const { error } = await sb.from("chat_messages").insert({
        session_id: msg.session_id || "sess-unknown",
        role: msg.role === "assistant" ? "assistant" : "user",
        content: String(msg.content),
        language: msg.language || "en",
        confidence: msg.confidence || null,
        citations: msg.citations || null,
      });
      if (error) {
        console.warn(`[BIS] chat_messages insert failed (${error.code || "error"}):`, error.message);
        return null;
      }
      return true;
    } catch (err) {
      console.warn("[BIS] chat_messages insert failed:", err && err.message);
      return null;
    }
  }

  /** Read a saved conversation back, oldest first. */
  async function loadMessages(sessionId, limit) {
    if (!sessionId) return null;
    return select("chat_messages", (q) =>
      q
        .eq("session_id", sessionId)
        .order("created_at", { ascending: true })
        .limit(limit || 100)
    );
  }

  /** Rows shaped exactly like the LABS fixture in website/lab-finder.html. */
  async function fetchLabs() {
    const rows = await select("labs");
    if (!rows || !rows.length) return null;
    return rows.map((r) => ({
      name: r.name,
      city: r.city,
      state: r.state || "",
      cat: r.categories || [],
      scope: r.scope || [],
      dist: r.distance || "",
    }));
  }

  /** Rows shaped exactly like the DB fixture in website/recommender.html. */
  async function fetchStandards() {
    const rows = await select("standards");
    if (!rows || !rows.length) return null;
    return rows.map((r) => ({
      no: r.no,
      title: r.title,
      why: r.why,
      conf: r.confidence || "medium",
      cites: r.citations || [],
    }));
  }

  return {
    configured,
    url: SUPABASE_URL,
    client,
    saveMessage,
    loadMessages,
    fetchLabs,
    fetchStandards,
  };
})();
