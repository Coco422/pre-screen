create schema if not exists resume;

create table if not exists resume.candidates (
  id bigserial primary key,
  org_id bigint not null default 1,
  name text,
  phone text,
  email text,
  status text not null default 'draft',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists resume.resume_files (
  id bigserial primary key,
  candidate_id bigint not null references resume.candidates(id),
  minio_bucket text not null,
  minio_object_key text not null,
  file_name text not null,
  file_size bigint not null,
  page_count integer not null default 0,
  parse_status text not null default 'pending',
  parse_error text,
  created_at timestamptz not null default now()
);
