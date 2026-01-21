from __future__ import annotations

from typing import Optional
from app.db.connection import get_connection


class AdminRepository:
    def make_admin(self, user_id: int, role: str = "ADMIN") -> None:
        """
        Inserts (or replaces) a row in Admin table for the given user.
        """
        conn = get_connection()
        try:
            conn.execute(
                """
                INSERT INTO Admin (UserID, Role)
                VALUES (?, ?)
                ON CONFLICT(UserID) DO UPDATE SET Role = excluded.Role
                """,
                (user_id, role),
            )
            conn.commit()
        finally:
            conn.close()

    def is_admin(self, user_id: int) -> bool:
        conn = get_connection()
        try:
            cur = conn.execute(
                "SELECT 1 FROM Admin WHERE UserID = ? LIMIT 1",
                (user_id,),
            )
            return cur.fetchone() is not None
        finally:
            conn.close()

    def get_role(self, user_id: int) -> Optional[str]:
        conn = get_connection()
        try:
            cur = conn.execute(
                "SELECT Role FROM Admin WHERE UserID = ?",
                (user_id,),
            )
            row = cur.fetchone()
            return row["Role"] if row else None
        finally:
            conn.close()
