CREATE_ANALYTICS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS {table_name} (
    room_id TEXT PRIMARY KEY,
    opportunity_id TEXT,
    thread_id UUID,
    user_name TEXT,
    user_phone TEXT,
    user_email TEXT,
    answer BOOLEAN,
    voicemail_answer BOOLEAN,
    availability TEXT,
    recording_consent BOOLEAN,
    motivation TEXT,
    work_status TEXT,
    financial_interest BOOLEAN,
    financial_topics TEXT[],
    financial_details TEXT,
    objection TEXT,
    score TEXT,
    summary TEXT,
    callback_requested BOOLEAN,
    callback_reference_day TEXT,
    callback_day TEXT,
    callback_time TEXT,
    duration_seconds INTEGER,
    recording_url TEXT,
    processed_at TIMESTAMPTZ DEFAULT NOW()
);
"""

INSERT_ANALYTICS_SQL = """
INSERT INTO {table_name} (
    room_id, opportunity_id, thread_id,
    user_name, user_phone, user_email,
    answer, voicemail_answer, availability, recording_consent,
    motivation, work_status,
    financial_interest, financial_topics, financial_details, objection,
    score, summary,
    callback_requested, callback_reference_day, callback_day, callback_time,
    duration_seconds, recording_url
) VALUES (
    ?, ?, ?,
    ?, ?, ?,
    ?, ?, ?, ?,
    ?, ?,
    ?, ?, ?, ?,
    ?, ?,
    ?, ?, ?, ?,
    ?, ?
)
ON CONFLICT (room_id) DO NOTHING;
"""
