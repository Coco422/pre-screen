alter table resume.candidates
  add column if not exists external_id text,
  add column if not exists task_id text,
  add column if not exists role text,
  add column if not exists city text,
  add column if not exists phone text,
  add column if not exists screening_status text not null default '已上传简历',
  add column if not exists quality text not null default '',
  add column if not exists skills jsonb not null default '[]'::jsonb,
  add column if not exists hobbies jsonb not null default '[]'::jsonb,
  add column if not exists profile_json jsonb not null default '{}'::jsonb,
  add column if not exists analysis_json jsonb not null default '{}'::jsonb,
  add column if not exists projects_json jsonb not null default '[]'::jsonb,
  add column if not exists review_notes jsonb not null default '[]'::jsonb,
  add column if not exists paper_id text,
  add column if not exists result_id text,
  add column if not exists invitation_token text;

create unique index if not exists resume_candidates_external_id_uidx
  on resume.candidates (external_id)
  where external_id is not null;

create index if not exists resume_candidates_task_id_idx on resume.candidates (task_id);
create index if not exists resume_candidates_screening_status_idx on resume.candidates (screening_status);

create table if not exists resume.upload_jobs (
  id text primary key,
  task_id text not null,
  candidate_id text,
  file_name text not null,
  minio_bucket text,
  minio_object_key text,
  local_path text,
  status text not null default 'queued',
  progress integer not null default 0,
  error text,
  processing jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists resume_upload_jobs_task_id_idx on resume.upload_jobs (task_id);
create index if not exists resume_upload_jobs_status_idx on resume.upload_jobs (status);
