import os

import psycopg
import pytest

DSN = os.environ.get(
    "POSTGRES_DSN_TEST",
    "postgresql://postgres:postgres@localhost:5432/prescreen",
)


def _can_connect() -> bool:
    try:
        with psycopg.connect(DSN, connect_timeout=2) as conn:
            with conn.cursor() as cur:
                cur.execute("select 1")
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not _can_connect(), reason="Postgres not available on localhost:5432")


def test_bootstrap_schemas_exist():
    with psycopg.connect(DSN) as conn:
        with conn.cursor() as cur:
            expected_histories = {
                "app": "flyway_history_app",
                "auth": "flyway_history_auth",
                "resume": "flyway_history_resume",
                "exam": "flyway_history_exam",
                "judge": "flyway_history_judge",
                "scoring": "flyway_history_scoring",
                "risk": "flyway_history_risk",
            }

            for schema_name, history_table in expected_histories.items():
                cur.execute(
                    f"""
                    select version
                    from {schema_name}.{history_table}
                    where success = true
                      and version = '1'
                    order by installed_rank
                    """
                )
                versions = [row[0] for row in cur.fetchall()]
                assert versions == ["1"], schema_name

            cur.execute(
                """
                select table_schema, table_name
                from information_schema.tables
                where (table_schema, table_name) in (
                  ('app', 'screening_tasks'),
                  ('app', 'ai_settings'),
                  ('auth', 'users'),
                  ('auth', 'sessions'),
                  ('resume', 'candidates'),
                  ('resume', 'resume_files'),
                  ('resume', 'upload_jobs'),
                  ('exam', 'papers'),
                  ('exam', 'sessions'),
                  ('exam', 'invitations'),
                  ('scoring', 'results'),
                  ('risk', 'events'),
                  ('judge', 'submissions')
                )
                order by table_schema, table_name
                """
            )
            rows = cur.fetchall()

    expected_tables = {
        ("app", "ai_settings"),
        ("app", "screening_tasks"),
        ("auth", "sessions"),
        ("auth", "users"),
        ("exam", "invitations"),
        ("exam", "papers"),
        ("exam", "sessions"),
        ("judge", "submissions"),
        ("resume", "candidates"),
        ("resume", "resume_files"),
        ("resume", "upload_jobs"),
        ("risk", "events"),
        ("scoring", "results"),
    }
    assert set(rows) == expected_tables
