from textwrap import dedent

CREATE_ROOMS_TABLE_SQL = dedent("""
    CREATE TABLE IF NOT EXISTS {table_name} (
        room_id          TEXT PRIMARY KEY,
        thread_id        UUID NOT NULL,
        opportunity_id   TEXT NOT NULL,
        start_timestamp  TIMESTAMPTZ,
        end_timestamp    TIMESTAMPTZ,
        report_url       TEXT,
        metadata         JSONB
    );
""")

UPSERT_ROOM_SQL = dedent("""
INSERT INTO {table_name} (
    room_id,
    thread_id,
    opportunity_id,
    start_timestamp,
    end_timestamp,
    report_url,
    metadata
)
VALUES (?, ?, ?, ?, ?, ?, ?::jsonb)
ON CONFLICT (room_id)
DO UPDATE SET
    start_timestamp = COALESCE({table_name}.start_timestamp, EXCLUDED.start_timestamp),
    end_timestamp   = COALESCE({table_name}.end_timestamp,   EXCLUDED.end_timestamp),
    report_url      = COALESCE(EXCLUDED.report_url,            {table_name}.report_url),
    metadata        = COALESCE(
        {table_name}.metadata::jsonb || EXCLUDED.metadata::jsonb,
        {table_name}.metadata::jsonb,
        EXCLUDED.metadata::jsonb
    );
""")

LIST_ROOMS_SQL = dedent("""
SELECT
    room_id,
    thread_id,
    opportunity_id,
    start_timestamp,
    end_timestamp,
    report_url,
    metadata
FROM {table_name}
ORDER BY start_timestamp DESC NULLS LAST;
""")
