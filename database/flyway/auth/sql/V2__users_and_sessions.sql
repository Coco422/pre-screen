create table if not exists auth.users (
  id bigserial primary key,
  username text not null unique,
  password_hash text not null,
  display_name text not null,
  role text not null default 'hr',
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists auth.sessions (
  id bigserial primary key,
  user_id bigint not null references auth.users (id) on delete cascade,
  token_hash text not null unique,
  expires_at timestamptz not null,
  created_at timestamptz not null default now(),
  last_seen_at timestamptz not null default now()
);

create index if not exists auth_sessions_user_id_idx on auth.sessions (user_id);
create index if not exists auth_sessions_expires_at_idx on auth.sessions (expires_at);
