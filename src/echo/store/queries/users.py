from textwrap import dedent

CREATE_USERS_TABLE_SQL = dedent("""
CREATE TABLE IF NOT EXISTS {table_name} (
    user_id           UUID PRIMARY KEY,
    contact_id        TEXT,
    opportunity_id    TEXT,
    name              TEXT,
    last_name         TEXT,
    phone_number      TEXT,
    mail              TEXT,
    market            TEXT,
    faculty           TEXT,
    plancode          TEXT,
    track             TEXT,
    is_active         BOOLEAN NOT NULL DEFAULT true,
    added_timestamp   TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_timestamp TIMESTAMPTZ NOT NULL DEFAULT now()
);
""")

CREATE_USER_ID_INDEX_SQL = dedent("""
CREATE INDEX IF NOT EXISTS idx_users_user_id
ON {table_name} (user_id);
""")

CREATE_OPPORTUNITY_ID_INDEX_SQL = dedent("""
CREATE INDEX IF NOT EXISTS idx_users_opportunity_id
ON {table_name} (opportunity_id);
""")

UPSERT_USER_SQL = dedent("""
INSERT INTO {table_name} (
    user_id,
    contact_id,
    opportunity_id,
    name,
    last_name,
    phone_number,
    mail,
    market,
    faculty,
    plancode,
    track,
    is_active,
    added_timestamp,
    updated_timestamp
)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, true, now(), now())
ON CONFLICT (user_id)
DO UPDATE SET
    contact_id        = COALESCE({table_name}.contact_id, EXCLUDED.contact_id),
    opportunity_id    = COALESCE({table_name}.opportunity_id, EXCLUDED.opportunity_id),
    name              = COALESCE({table_name}.name, EXCLUDED.name),
    last_name         = COALESCE({table_name}.last_name, EXCLUDED.last_name),
    phone_number      = COALESCE({table_name}.phone_number, EXCLUDED.phone_number),
    mail              = COALESCE({table_name}.mail, EXCLUDED.mail),
    market            = COALESCE({table_name}.market, EXCLUDED.market),
    faculty           = COALESCE({table_name}.faculty, EXCLUDED.faculty),
    plancode          = COALESCE({table_name}.plancode, EXCLUDED.plancode),
    track             = COALESCE({table_name}.track, EXCLUDED.track),
    updated_timestamp = now();
""")


LIST_USERS_SQL = dedent("""
SELECT
    user_id,
    contact_id,
    opportunity_id,
    name,
    last_name,
    phone_number,
    mail,
    market,
    faculty,
    plancode,
    track,
    is_active,
    added_timestamp,
    updated_timestamp
FROM {table_name}
ORDER BY added_timestamp DESC;
""")


GET_USER_BY_IDENTIFIER_SQL = dedent("""
SELECT
    user_id,
    contact_id,
    opportunity_id,
    name,
    last_name,
    phone_number,
    mail,
    market,
    faculty,
    plancode,
    track,
    is_active,
    added_timestamp,
    updated_timestamp
FROM {table_name}
WHERE user_id = ?
   OR contact_id = ?
   OR opportunity_id = ?
LIMIT 1;
""")

SOFT_DELETE_USER_SQL = dedent("""
UPDATE {table_name}
SET
    is_active = false,
    updated_timestamp = now()
WHERE user_id = ?
  AND is_active = true;
""")

