create table if not exists scoring.results (
  id text primary key,
  session_id text not null,
  candidate_id text not null,
  paper_id text not null,
  task_id text,
  status text not null default 'submitted',
  review_status text not null default 'pending',
  screening_decision text,
  summary jsonb not null default '{}'::jsonb,
  question_reviews jsonb not null default '[]'::jsonb,
  risk_events jsonb not null default '[]'::jsonb,
  review_notes jsonb not null default '[]'::jsonb,
  risk_override text,
  submitted_at timestamptz not null default now(),
  reviewed_at timestamptz,
  completed_at timestamptz,
  created_at timestamptz not null default now()
);

create index if not exists scoring_results_candidate_id_idx on scoring.results (candidate_id);
create index if not exists scoring_results_task_id_idx on scoring.results (task_id);
create index if not exists scoring_results_status_idx on scoring.results (status);
create index if not exists scoring_results_submitted_at_idx on scoring.results (submitted_at desc);
