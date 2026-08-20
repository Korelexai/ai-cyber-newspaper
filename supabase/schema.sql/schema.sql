-- Run this once in Supabase: your project → SQL Editor → New query → paste → Run
--
-- Creates the subscribers table used by:
--   - api/subscribe.py       (adds a new row when someone subscribes)
--   - send_newsletter.py     (reads all rows to know who to email)

create table if not exists subscribers (
  id uuid primary key default gen_random_uuid(),
  name text,
  email text not null unique,
  subscribed_at timestamptz not null default now(),
  unsubscribed boolean not null default false
);

-- Speeds up "give me everyone who hasn't unsubscribed" queries.
create index if not exists idx_subscribers_unsubscribed
  on subscribers (unsubscribed);
