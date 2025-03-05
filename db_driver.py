import sqlite3
from typing import Optional
from dataclasses import dataclass
from contextlib import contextmanager


@dataclass
class Reservation:
    reservation_id: str
    guest_name: str
    room_type: str
    check_in: str
    check_out: str


class DatabaseDriver:
    def __init__(self, db_path: str = "hotel_db.sqlite"):
        self.db_path = db_path
        self._init_db()

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Create reservations table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS reservations (
                    reservation_id TEXT PRIMARY KEY,
                    guest_name TEXT NOT NULL,
                    room_type TEXT NOT NULL,
                    check_in TEXT NOT NULL,
                    check_out TEXT NOT NULL
                )
            """
            )
            conn.commit()

    def create_reservation(
        self,
        reservation_id: str,
        guest_name: str,
        room_type: str,
        check_in: str,
        check_out: str,
    ) -> Reservation:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO reservations (reservation_id, guest_name, room_type, check_in, check_out) VALUES (?, ?, ?, ?, ?)",
                (reservation_id, guest_name, room_type, check_in, check_out),
            )
            conn.commit()
            return Reservation(
                reservation_id=reservation_id,
                guest_name=guest_name,
                room_type=room_type,
                check_in=check_in,
                check_out=check_out,
            )

    def get_reservation_by_id(self, reservation_id: str) -> Optional[Reservation]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM reservations WHERE reservation_id = ?", (reservation_id,)
            )
            row = cursor.fetchone()
            if not row:
                return None

            return Reservation(
                reservation_id=row[0],
                guest_name=row[1],
                room_type=row[2],
                check_in=row[3],
                check_out=row[4],
            )
