from uuid import UUID
from datetime import datetime
import duckdb

import echo.events.v1 as events
from echo.utils import queries as q


class Database:
    def __init__(self) -> None:
        self.conn = duckdb.connect(config = {'threads': 1})
        self._setup()

    def _setup(self) -> None:
        self.conn.sql(q.CREATE_SECRET_SQL)
        self.conn.sql(q.ATTACH_SQL)
        self.conn.sql(q.CREATE_TABLE_SQL)

    def set_room_start(
        self,
        room_id: str,
        opportunity_id: str,
        start_time: datetime,
    ) -> None:
        self.conn.execute(
            q.UPSERT_ROOM_SQL,
            (
                room_id,
                opportunity_id,
                start_time,
                None,
                None,
            )
        )

    def set_room_end(
        self,
        room_id: str,
        end_time: datetime,
    ) -> None:
        self.conn.execute(
            q.UPSERT_ROOM_SQL,
            (
                room_id,
                None,
                None,
                end_time,
                None,
            )
        )

    def set_room_report(self, room_id: str, report_url: str) -> None:
        self.conn.execute(
            q.UPSERT_ROOM_SQL,
            (
                room_id,
                None,
                None,
                None,
                report_url,
            )
        )

    def get_rooms(self) -> None:
        pass

db = Database()
start_event = events.SessionStarted(
    room_id="3ea05c2d-ab15-443b-85c7-916401096733",
    opportunity_id="5d18063c-5a2d-4036-88ba-c52345e298cf",
)
import time
time.sleep(3)

end_event = events.SessionEnded(
    room_id="3ea05c2d-ab15-443b-85c7-916401096733",
    opportunity_id="5d18063c-5a2d-4036-88ba-c52345e298cf",
    report_url="some_report_url",
    report=b'',
)


db.set_room_start(
    room_id=start_event.room_id,
    opportunity_id=start_event.opportunity_id,
    start_time=start_event.timestamp,
)

db.set_room_end(
    room_id=end_event.room_id,
    end_time=end_event.timestamp,
)
db.set_room_report(
    room_id=end_event.room_id,
    report_url=end_event.report_url,
)
