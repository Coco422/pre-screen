create table if not exists exam.job_templates (
  id text primary key,
  name text not null,
  role_type text not null default '',
  level text not null default '',
  template_config jsonb not null default '{}'::jsonb,
  tags jsonb not null default '[]'::jsonb,
  copied_from_template_id text,
  created_at timestamptz not null default now()
);

create table if not exists exam.papers (
  id text primary key,
  candidate_id text not null,
  task_id text,
  title text not null,
  duration_minutes integer not null default 90,
  status text not null default 'draft',
  introduction text not null default '',
  questions jsonb not null default '[]'::jsonb,
  mix jsonb not null default '{}'::jsonb,
  generation_summary jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists exam_papers_candidate_id_idx on exam.papers (candidate_id);
create index if not exists exam_papers_task_id_idx on exam.papers (task_id);

create table if not exists exam.invitations (
  id text primary key,
  paper_id text not null references exam.papers (id) on delete cascade,
  access_token text not null unique,
  one_time_code_hash text not null,
  verify_code_plain text,
  duration_minutes integer not null default 90,
  status text not null default 'ready',
  created_at timestamptz not null default now()
);

create index if not exists exam_invitations_paper_id_idx on exam.invitations (paper_id);

create table if not exists exam.sessions (
  id text primary key,
  invitation_id text,
  paper_id text not null,
  candidate_id text not null,
  access_token text not null,
  status text not null default 'in_progress',
  started_at timestamptz not null default now(),
  expires_at timestamptz not null,
  submitted_at timestamptz,
  last_heartbeat_at timestamptz,
  answers jsonb not null default '{}'::jsonb,
  risk_events jsonb not null default '[]'::jsonb,
  coding_submissions jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists exam_sessions_access_token_idx on exam.sessions (access_token);
create index if not exists exam_sessions_status_idx on exam.sessions (status);
create index if not exists exam_sessions_candidate_id_idx on exam.sessions (candidate_id);

create table if not exists exam.answer_drafts (
  session_id text not null references exam.sessions (id) on delete cascade,
  question_id text not null,
  draft_answer jsonb not null default '{}'::jsonb,
  updated_at timestamptz not null default now(),
  primary key (session_id, question_id)
);
