from textwrap import dedent


CREATE_SCHEDULE_CALLS_TABLE_SQL = dedent("""
CREATE TABLE IF NOT EXISTS {table_name} (
    opportunity_id    TEXT PRIMARY KEY,
    scheduled_at      TIMESTAMPTZ NOT NULL,
    metadata          JSON,
    status            TEXT NOT NULL,
    added_timestamp   TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_timestamp TIMESTAMPTZ NOT NULL DEFAULT now()
);
""")


CREATE_SCHEDULE_CALLS_STATUS_INDEX_SQL = dedent("""
CREATE INDEX IF NOT EXISTS idx_schedule_calls_status
ON {table_name} (status);
""")


CREATE_SCHEDULE_CALLS_SCHEDULED_AT_INDEX_SQL = dedent("""
CREATE INDEX IF NOT EXISTS idx_schedule_calls_scheduled_at
ON {table_name} (scheduled_at);
""")


UPSERT_SCHEDULE_CALL_SQL = dedent("""
INSERT INTO {table_name} (
    opportunity_id,
    scheduled_at,
    metadata,
    status,
    added_timestamp,
    updated_timestamp
)
VALUES (?, ?, ?, ?, now(), now())
ON CONFLICT (opportunity_id)
DO UPDATE SET
    scheduled_at      = EXCLUDED.scheduled_at,
    metadata          = EXCLUDED.metadata,
    status            = EXCLUDED.status,
    updated_timestamp = now();
""")


GET_READY_SCHEDULE_CALLS_SQL = dedent("""
SELECT
    opportunity_id,
    scheduled_at,
    metadata,
    status,
    added_timestamp,
    updated_timestamp
FROM {table_name}
WHERE status = 'pending'
  AND scheduled_at <= now()
ORDER BY scheduled_at ASC;
""")


UPDATE_SCHEDULE_CALL_STATUS_SQL = dedent("""
UPDATE {table_name}
SET
    status = ?,
    updated_timestamp = now()
WHERE opportunity_id = ?
  AND status = 'pending';
""")
