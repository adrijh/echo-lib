from textwrap import dedent

# Not for now
CREATE_CONTEXT_TYPE_ENUM_SQL = dedent("""
CREATE TYPE IF NOT EXISTS context_type AS ENUM ('chat', 'summary');
""")


# Not for now
CREATE_CHANNEL_TYPE_ENUM_SQL = dedent("""
CREATE TYPE IF NOT EXISTS context_channel AS ENUM (
    'voice',
    'whatsapp',
    'web'
);
""")

ADD_EXTENSION_SQL = """CREATE EXTENSION IF NOT EXISTS "uuid-ossp";"""


CREATE_CONTEXT_TABLE_SQL = dedent("""
CREATE TABLE IF NOT EXISTS {table_name} (
    context_id        TEXT PRIMARY KEY,
    thread_id         UUID NOT NULL,
    opportunity_id    TEXT NOT NULL,
    user_id           UUID NOT NULL,
    content           JSON NOT NULL,
    type              TEXT NOT NULL,
    channel           TEXT NOT NULL,
    added_timestamp   TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_timestamp TIMESTAMPTZ NOT NULL DEFAULT now()
);
""")


CREATE_CONTEXT_INDEXES_SQL = dedent("""
CREATE INDEX IF NOT EXISTS idx_context_thread_id
ON {table_name}(thread_id);

CREATE INDEX IF NOT EXISTS idx_context_user_id
ON {table_name}(user_id);

CREATE INDEX IF NOT EXISTS idx_context_channel
ON {table_name}(channel);

CREATE UNIQUE INDEX IF NOT EXISTS uq_thread_chat_context
ON {table_name}(thread_id)
WHERE type = 'chat';
""")


INSERT_CONTEXT_SQL = dedent("""
INSERT INTO {table_name} (
    context_id,
    thread_id,
    opportunity_id,
    user_id,
    channel,
    content,
    type
)
VALUES (?, ?, ?, ?, ?, ?, ?);
""")


UPDATE_CONTEXT_CONTENT_SQL = dedent("""
UPDATE {table_name}
SET
    content = ?,
    updated_timestamp = now()
WHERE context_id = ?;
""")


LIST_CONTEXTS_SQL = dedent("""
SELECT
    context_id,
    thread_id,
    opportunity_id,
    user_id,
    channel,
    content,
    type,
    added_timestamp,
    updated_timestamp
FROM {table_name}
ORDER BY added_timestamp DESC;
""")


GET_CONTEXT_BY_ID_SQL = dedent("""
SELECT
    context_id,
    thread_id,
    opportunity_id,
    user_id,
    channel,
    content,
    type,
    added_timestamp,
    updated_timestamp
FROM {table_name}
WHERE context_id = ?;
""")

FETCH_CONTEXT_HISTORY_BASE_SQL = """
SELECT
    context_id,
    thread_id,
    opportunity_id,
    user_id,
    channel,
    content,
    type,
    added_timestamp,
    updated_timestamp
FROM {table_name}
WHERE {where_clause}
ORDER BY added_timestamp DESC;
"""
