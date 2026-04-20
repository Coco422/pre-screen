import psycopg


def test_bootstrap_schemas_exist():
    with psycopg.connect("postgresql://postgres:postgres@localhost:5432/prescreen") as conn:
        with conn.cursor() as cur:
            expected_versions = {
                "auth": "flyway_history_auth",
                "resume": "flyway_history_resume",
                "exam": "flyway_history_exam",
                "judge": "flyway_history_judge",
                "scoring": "flyway_history_scoring",
                "risk": "flyway_history_risk",
            }

            for schema_name, history_table in expected_versions.items():
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
                  ('resume', 'candidates'),
                  ('resume', 'resume_files')
                )
                order by table_name
                """
            )
            rows = cur.fetchall()

    assert rows == [("resume", "candidates"), ("resume", "resume_files")]
