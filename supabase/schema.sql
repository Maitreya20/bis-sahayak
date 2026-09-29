/* ============================================================
   BIS Sahayak — Supabase schema, RLS policies and seed data

   Paste the whole file into Supabase -> SQL Editor -> New query -> Run.
   Nothing else is required: assets/js/supabase.js picks up the project
   URL and anon key from its own config block at the top of that file.

   Three tables:
     chat_messages  every turn of every conversation, keyed by session
     labs           the Lab Finder directory
     standards      the Standard Recommender catalogue

   NOTE on seed counts: website/lab-finder.html renders from `labs` and
   website/recommender.html from `standards`. tools/verify.mjs asserts the
   seeded baseline (6 labs; the LED rule resolves to 3 standards). If you
   add rows, update those two expectations alongside them.
   ============================================================ */


/* ---------- 1. chat history ---------- */

create table if not exists public.chat_messages (
  id          uuid primary key default gen_random_uuid(),
  session_id  text not null,
  role        text not null check (role in ('user', 'assistant')),
  content     text not null,
  language    text not null default 'en' check (language in ('en', 'hi', 'mr')),
  confidence  text check (confidence in ('high', 'medium', 'low')),
  citations   jsonb,
  created_at  timestamptz not null default now()
);

create index if not exists chat_messages_session_idx
  on public.chat_messages (session_id, created_at);


/* ---------- 2. recognised testing labs ---------- */

create table if not exists public.labs (
  id          bigint generated always as identity primary key,
  name        text not null unique,
  city        text not null,                       -- display string, e.g. 'Pune, Maharashtra'
  state       text not null,
  categories  text[] not null default '{}',
  scope       text[] not null default '{}',
  distance    text not null default ''
);


/* ---------- 3. Indian Standard catalogue ---------- */

create table if not exists public.standards (
  id          bigint generated always as identity primary key,
  no          text not null unique,                -- e.g. 'IS 302 (Part 1)'
  title       text not null,
  why         text not null,
  confidence  text not null default 'medium' check (confidence in ('high', 'medium', 'low')),
  citations   jsonb not null default '[]'::jsonb
);


/* ---------- 4. Row Level Security ---------- */

alter table public.chat_messages enable row level security;
alter table public.labs           enable row level security;
alter table public.standards      enable row level security;

-- Reads are public: the anon key ships in the browser by design and these
-- tables hold no personal data beyond the questions a visitor types.
drop policy if exists "labs readable by anyone" on public.labs;
create policy "labs readable by anyone"
  on public.labs for select to anon, authenticated using (true);

drop policy if exists "standards readable by anyone" on public.standards;
create policy "standards readable by anyone"
  on public.standards for select to anon, authenticated using (true);

drop policy if exists "chat readable by anyone" on public.chat_messages;
create policy "chat readable by anyone"
  on public.chat_messages for select to anon, authenticated using (true);

drop policy if exists "chat writable by anyone" on public.chat_messages;
create policy "chat writable by anyone"
  on public.chat_messages for insert to anon, authenticated with check (true);

-- Demo-grade policies above: the UI has no sign-in yet, so anything holding
-- the anon key can read every session. Before real traffic, turn on
-- Supabase Auth and replace the two chat_messages policies with ownership
-- checks, e.g.:
--
--   create policy "read own sessions" on public.chat_messages
--     for select using (auth.uid()::text = session_id);
--
--   create policy "write own sessions" on public.chat_messages
--     for insert with check (auth.uid()::text = session_id);


/* ---------- 5. seed: the six recognised labs ---------- */

insert into public.labs (name, city, state, categories, scope, distance) values
  ('ETL Test Labs (BIS recognised)',        'Pune, Maharashtra',    'Maharashtra',   array['Electronics & IT'],                      array['IS 302', 'IS 16107', 'EMC'],              '4.2 km from Chakan MIDC'),
  ('Intertek India Pvt Ltd',                'Bengaluru, Karnataka', 'Karnataka',     array['Electronics & IT', 'Chemicals & Plastics'], array['CRS electronics', 'RoHS'],             '11 km from Whitefield'),
  ('BIS Regional Testing Centre',           'Delhi NCR',            'Delhi',         array['Metals & Steel', 'Electronics & IT'],    array['IS 15489', 'IS 302', 'FMCS'],             'Okhla Phase II'),
  ('SGS India - Food Lab',                  'Ahmedabad, Gujarat',   'Gujarat',       array['Food & Agriculture'],                    array['IS 16547', 'Microbiology', 'Nutrition panel'], 'Sanand'),
  ('TVS & Sons Quality Control',            'Chennai, Tamil Nadu',  'Tamil Nadu',    array['Metals & Steel', 'Textiles'],            array['IS 15489', 'Textile azo dyes'],            'Guindy'),
  ('CIPET - Centre for Polymer Testing',    'Hyderabad, Telangana', 'Telangana',     array['Chemicals & Plastics'],                  array['Food contact', 'IS 15735'],                'Balnagar')
on conflict (name) do nothing;


/* ---------- 6. seed: the six standards ---------- */

insert into public.standards (no, title, why, confidence, citations) values
  ('IS 1417',                    'Gold jewellery & gold artefacts - fineness',
   'Applies to 22K/18K gold articles; defines purity grades and marking.',
   'high',   '[{"doc":"IS 1417","clause":"5","url":"#is1417"}]'::jsonb),

  ('IS 302 (Part 1)',            'Safety of household electrical appliances',
   'Base safety standard for mains-powered appliances and their drivers.',
   'high',   '[{"doc":"IS 302 Part 1","clause":"4.2","url":"#is302"}]'::jsonb),

  ('IS 16107 (Part 2/Sec 11)',   'LED modules - performance & safety',
   'Matches LED bulb/driver performance requirements under CRS.',
   'high',   '[{"doc":"IS 16107","clause":"7","url":"#is16107"}]'::jsonb),

  ('IS 10322 (Part 5/Sec 1)',    'Luminaires - general lighting requirements',
   'Applies if you ship finished luminaires, not bare drivers.',
   'medium', '[{"doc":"IS 10322","clause":"5","url":"#is10322"}]'::jsonb),

  ('IS 15489',                   'Steel bars & rods for concrete reinforcement',
   'TMT rebar grades and mechanical property limits.',
   'high',   '[{"doc":"IS 15489","clause":"6","url":"#is15489"}]'::jsonb),

  ('IS 16547',                   'Packaged food labelling requirements',
   'Declaration, nutrition panel and batch marking for retail packs.',
   'medium', '[{"doc":"IS 16547","clause":"4","url":"#is16547"}]'::jsonb)
on conflict (no) do nothing;
