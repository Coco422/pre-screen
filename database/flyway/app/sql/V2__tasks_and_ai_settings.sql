create table if not exists app.screening_tasks (
  id text primary key,
  title text not null,
  department text not null default '',
  city text not null default '',
  jd_text text not null default '',
  tags jsonb not null default '[]'::jsonb,
  template_config jsonb not null default '{}'::jsonb,
  duration_minutes integer not null default 90,
  status text not null default 'open',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists screening_tasks_status_idx on app.screening_tasks (status);
create index if not exists screening_tasks_created_at_idx on app.screening_tasks (created_at desc);

create table if not exists app.ai_settings (
  id integer primary key default 1 check (id = 1),
  base_url text not null default '',
  model text not null default '',
  api_key text not null default '',
  updated_at timestamptz not null default now()
);

insert into app.ai_settings (id, base_url, model, api_key)
values (1, '', '', '')
on conflict (id) do nothing;

create table if not exists app.id_counters (
  kind text primary key,
  value integer not null default 0
);
