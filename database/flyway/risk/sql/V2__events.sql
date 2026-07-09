create table if not exists risk.events (
  id bigserial primary key,
  session_id text not null,
  event_type text not null,
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists risk_events_session_id_idx on risk.events (session_id);
create index if not exists risk_events_created_at_idx on risk.events (created_at desc);
create index if not exists risk_events_type_idx on risk.events (event_type);
