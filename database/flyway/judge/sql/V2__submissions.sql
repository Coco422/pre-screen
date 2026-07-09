create table if not exists judge.submissions (
  id bigserial primary key,
  session_id text not null,
  question_id text not null,
  mode text not null,
  language text not null default '',
  source_code text not null default '',
  result_json jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists judge_submissions_session_id_idx on judge.submissions (session_id);
create index if not exists judge_submissions_question_id_idx on judge.submissions (question_id);
