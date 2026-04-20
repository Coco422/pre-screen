import psycopg


def test_bootstrap_schemas_exist():
    with psycopg.connect("postgresql://postgres:postgres@localhost:5432/prescreen") as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                select schema_name
                from information_schema.schemata
                where schema_name in ('auth', 'resume', 'exam', 'judge', 'scoring', 'risk')
                order by schema_name
                """
            )
            rows = [row[0] for row in cur.fetchall()]

    assert rows == ["auth", "exam", "judge", "resume", "risk", "scoring"]
