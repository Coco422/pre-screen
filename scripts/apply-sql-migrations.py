#!/usr/bin/env python3
"""Apply Flyway SQL files via host psycopg when docker Flyway cannot mount volumes."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import psycopg

ROOT = Path(__file__).resolve().parents[1]
FLYWAY = ROOT / "database" / "flyway"

ORDER: list[tuple[str, list[str]]] = [
    ("app", ["V1__bootstrap.sql", "V2__tasks_and_ai_settings.sql"]),
    ("auth", ["V1__bootstrap.sql", "V2__users_and_sessions.sql"]),
    ("resume", ["V1__bootstrap.sql", "V2__resume_parse_pipeline.sql", "V3__screening_links.sql"]),
    ("exam", ["V1__bootstrap.sql", "V2__core_tables.sql"]),
    ("judge", ["V1__bootstrap.sql", "V2__submissions.sql"]),
    ("scoring", ["V1__bootstrap.sql", "V2__results.sql"]),
    ("risk", ["V1__bootstrap.sql", "V2__events.sql"]),
]


def main() -> int:
    dsn = os.environ.get(
        "POSTGRES_DSN_SQL",
        "postgresql://postgres:postgres@localhost:5432/prescreen",
    )
    # Allow SQLAlchemy-style DSN.
    dsn = dsn.replace("postgresql+psycopg://", "postgresql://")

    with psycopg.connect(dsn) as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            for schema, files in ORDER:
                for name in files:
                    path = FLYWAY / schema / "sql" / name
                    if not path.exists():
                        print(f"skip missing {path}", file=sys.stderr)
                        continue
                    print(f"apply {schema}/{name}")
                    cur.execute(path.read_text(encoding="utf-8"))
    print("migrations applied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
