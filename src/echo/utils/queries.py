import os
from textwrap import dedent

CREATE_POSTGRES_SECRET_SQL = dedent(f"""
    CREATE SECRET (
        TYPE postgres,
        HOST '{os.environ["POSTGRES_HOST"]}',
        PORT {os.environ["POSTGRES_PORT"]},
        DATABASE {os.environ["POSTGRES_DB"]},
        USER '{os.environ["POSTGRES_USER"]}',
        PASSWORD '{os.environ["POSTGRES_PASSWORD"]}'
    );
""")

ATTACH_POSTGRES_SQL = "ATTACH '' AS postgres (TYPE postgres);"

CREATE_ROOMS_TABLE_SQL = dedent("""
    CREATE TABLE IF NOT EXISTS {table_name} (
        room_id          UUID PRIMARY KEY,
        opportunity_id   UUID NOT NULL,
        start_timestamp  TIMESTAMPTZ,
        end_timestamp    TIMESTAMPTZ,
        report_url       TEXT
    );
""")

UPSERT_ROOM_SQL = dedent("""
INSERT INTO {table_name} (
    room_id,
    opportunity_id,
    start_timestamp,
    end_timestamp,
    report_url
)
VALUES (?, ?, ?, ?, ?)
ON CONFLICT (room_id)
DO UPDATE SET
    start_timestamp = COALESCE({table_name}.start_timestamp, EXCLUDED.start_timestamp),
    end_timestamp   = COALESCE({table_name}.end_timestamp,   EXCLUDED.end_timestamp),
    report_url      = COALESCE(EXCLUDED.report_url,            {table_name}.report_url);
""")

LIST_ROOMS_SQL = dedent("""
SELECT
    room_id,
    opportunity_id,
    start_timestamp,
    end_timestamp,
    report_url
FROM {table_name}
ORDER BY start_timestamp ASC NULLS LAST;
""")
