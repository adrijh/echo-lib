import os
from textwrap import dedent

CREATE_SECRET_SQL = dedent(f"""
    CREATE SECRET (
        TYPE postgres,
        HOST '{os.environ["POSTGRES_HOST"]}',
        PORT {os.environ["POSTGRES_PORT"]},
        DATABASE {os.environ["POSTGRES_DB"]},
        USER '{os.environ["POSTGRES_USER"]}',
        PASSWORD '{os.environ["POSTGRES_PASSWORD"]}'
    );
""")

ATTACH_SQL = "ATTACH '' AS postgres (TYPE postgres);"

CREATE_TABLE_SQL = dedent("""
    CREATE TABLE IF NOT EXISTS postgres.rooms (
        room_id          UUID PRIMARY KEY,
        opportunity_id   UUID NOT NULL,
        start_timestamp  TIMESTAMPTZ,
        end_timestamp    TIMESTAMPTZ,
        report_url       TEXT
    );
""")


UPDATE_START_SQL = dedent("""
INSERT INTO postgres.rooms (
    room_id,
    opportunity_id,
    start_timestamp
)
VALUES (?, ?, ?)
ON CONFLICT (room_id)
DO UPDATE
SET start_timestamp = COALESCE(postgres.rooms.start_timestamp, EXCLUDED.start_timestamp);
""")

UPDATE_END_SQL = dedent("""
INSERT INTO postgres.rooms (
    room_id,
    opportunity_id,
    end_timestamp,
    report_url
)
VALUES (?, ?, ?, ?)
ON CONFLICT (room_id)
DO UPDATE
SET
    end_timestamp = EXCLUDED.end_timestamp,
    report_url    = COALESCE(EXCLUDED.report_url, postgres.rooms.report_url);
""")

UPSERT_ROOM_SQL = dedent("""
INSERT INTO postgres.rooms (
    room_id,
    opportunity_id,
    start_timestamp,
    end_timestamp,
    report_url
)
VALUES (?, ?, ?, ?, ?)
ON CONFLICT (room_id)
DO UPDATE SET
    start_timestamp = COALESCE(postgres.rooms.start_timestamp, EXCLUDED.start_timestamp),
    end_timestamp   = COALESCE(postgres.rooms.end_timestamp,   EXCLUDED.end_timestamp),
    report_url      = COALESCE(EXCLUDED.report_url,            postgres.rooms.report_url);
""")

LIST_ROOMS_SQL = dedent("""
SELECT
    room_id,
    opportunity_id,
    start_timestamp,
    end_timestamp,
    report_url
FROM postgres.rooms
ORDER BY start_timestamp ASC NULLS LAST;
""")
