from __future__ import annotations

import sqlite3
from typing import List

from app.db.connection import get_connection


class FavoritesRepository:
    def add(self, customer_user_id: int, item_id: int) -> None:
        conn = get_connection()
        try:
            conn.execute(
                """
                INSERT OR IGNORE INTO Favorites (CustomerUserID, ItemID)
                VALUES (?, ?)
                """,
                (customer_user_id, item_id),
            )
            conn.commit()
        finally:
            conn.close()

    def remove(self, customer_user_id: int, item_id: int) -> None:
        conn = get_connection()
        try:
            conn.execute(
                """
                DELETE FROM Favorites
                WHERE CustomerUserID = ? AND ItemID = ?
                """,
                (customer_user_id, item_id),
            )
            conn.commit()
        finally:
            conn.close()

    def is_favorite(self, customer_user_id: int, item_id: int) -> bool:
        conn = get_connection()
        try:
            cur = conn.execute(
                """
                SELECT 1 FROM Favorites
                WHERE CustomerUserID = ? AND ItemID = ?
                LIMIT 1
                """,
                (customer_user_id, item_id),
            )
            return cur.fetchone() is not None
        finally:
            conn.close()

    def list_item_ids(self, customer_user_id: int) -> List[int]:
        conn = get_connection()
        try:
            cur = conn.execute(
                """
                SELECT ItemID
                FROM Favorites
                WHERE CustomerUserID = ?
                ORDER BY ItemID ASC
                """,
                (customer_user_id,),
            )
            return [int(r["ItemID"]) for r in cur.fetchall()]
        finally:
            conn.close()
