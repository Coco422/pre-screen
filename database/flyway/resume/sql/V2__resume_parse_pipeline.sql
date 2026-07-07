create table if not exists resume.resume_parse_runs (
  id bigserial primary key,
  resume_file_id bigint references resume.resume_files(id),
  external_file_id text not null,
  status text not null default 'pending',
  model_base_url text,
  model_name text,
  model_used boolean not null default false,
  raw_model_json jsonb not null default '{}'::jsonb,
  profile_json jsonb not null default '{}'::jsonb,
  markdown text not null default '',
  warnings jsonb not null default '[]'::jsonb,
  started_at timestamptz not null default now(),
  completed_at timestamptz
);

create table if not exists resume.resume_parse_pages (
  id bigserial primary key,
  parse_run_id bigint not null references resume.resume_parse_runs(id) on delete cascade,
  page_number integer not null,
  text_chars integer not null default 0,
  image_count integer not null default 0,
  needs_multimodal boolean not null default false,
  rendered_object_key text,
  model_summary text,
  unique (parse_run_id, page_number)
);

create table if not exists resume.resume_assets (
  id bigserial primary key,
  parse_run_id bigint not null references resume.resume_parse_runs(id) on delete cascade,
  asset_type text not null,
  status text not null default 'found',
  page_number integer,
  xref integer,
  bbox jsonb,
  minio_object_key text,
  local_path text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists resume.resume_batches (
  id bigserial primary key,
  batch_id text not null unique,
  output_dir text,
  analysis_markdown text not null default '',
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists resume.resume_batch_items (
  batch_id bigint not null references resume.resume_batches(id) on delete cascade,
  parse_run_id bigint references resume.resume_parse_runs(id) on delete set null,
  external_file_id text not null,
  original_filename text not null,
  primary key (batch_id, external_file_id)
);
