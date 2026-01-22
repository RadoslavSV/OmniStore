from __future__ import annotations

from typing import List, Tuple, Optional
from app.db.connection import get_connection


class HistoryRepository:
    def add_view(self, customer_user_id: int, item_id: int, viewed_at: str) -> None:
        """
        Inserts a history record. (CustomerUserID, ItemID, ViewedAt) is the PK.
        """
        conn = get_connection()
        try:
            conn.execute(
                """
                INSERT INTO History (CustomerUserID, ItemID, ViewedAt)
                VALUES (?, ?, ?)
                """,
                (customer_user_id, item_id, viewed_at),
            )
            conn.commit()
        finally:
            conn.close()

    def list_views(
        self,
        customer_user_id: int,
        limit: int = 50,
        newest_first: bool = True,
    ) -> List[Tuple[int, str]]:
        """
        Returns list of tuples: (item_id, viewed_at)
        """
        order = "DESC" if newest_first else "ASC"

        conn = get_connection()
        try:
            cur = conn.execute(
                f"""
                SELECT ItemID, ViewedAt
                FROM History
                WHERE CustomerUserID = ?
                ORDER BY ViewedAt {order}
                LIMIT ?
                """,
                (customer_user_id, limit),
            )
            rows = cur.fetchall()
            return [(int(r["ItemID"]), str(r["ViewedAt"])) for r in rows]
        finally:
            conn.close()

    def clear(self, customer_user_id: int) -> None:
        conn = get_connection()
        try:
            conn.execute(
                """DELETE FROM History WHERE CustomerUserID = ?""",
                (customer_user_id,),
            )
            conn.commit()
        finally:
            conn.close()
