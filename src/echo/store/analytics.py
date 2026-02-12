from typing import Any, Protocol
from uuid import UUID

import duckdb

from echo.store.queries import analytics as q


class CallInsightProtocol(Protocol):
    answer: bool
    voicemail_answer: bool
    availability: str | None
    recording_consent: bool | None
    motivation: str | None
    work_status: str
    financial_interest: bool
    financial_topics: list[str]
    financial_details: str | None
    objection: str | None
    score: str
    summary: str
    callback_requested: bool
    callback_reference_day: str | None
    callback_day: str | None
    callback_time: str | None


class AnalyticsTable:
    def __init__(self, conn: duckdb.DuckDBPyConnection, is_postgres: bool) -> None:
        self.conn = conn
        self.table_name = "postgres.public.call_history_details" if is_postgres else "call_history_details"

    def setup_table(self) -> None:
        self.conn.execute(q.CREATE_ANALYTICS_TABLE_SQL.format(table_name=self.table_name))

    def insert_call_metric(
        self,
        room_id: str,
        opportunity_id: str,
        thread_id: UUID | None,
        user_name: str | None,
        user_phone: str | None,
        user_email: str | None,
        duration: int,
        insight: Any,
        recording_url: str,
    ) -> None:
        self.conn.execute(
            q.INSERT_ANALYTICS_SQL.format(table_name=self.table_name),
            (
                room_id,
                opportunity_id,
                thread_id,
                user_name,
                user_phone,
                user_email,
                insight.answer,
                insight.voicemail_answer,
                insight.availability,
                insight.recording_consent,
                insight.motivation,
                insight.work_status,
                insight.financial_interest,
                insight.financial_topics,
                insight.financial_details,
                insight.objection,
                insight.score,
                insight.summary,
                insight.callback_requested,
                insight.callback_reference_day,
                insight.callback_day,
                insight.callback_time,
                duration,
                recording_url,
            ),
        )
