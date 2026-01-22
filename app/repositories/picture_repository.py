from __future__ import annotations

import sqlite3
from typing import List, Optional

from app.db.connection import get_connection
from app.models.picture import Picture


class PictureRepository:
    @staticmethod
    def _row_to_picture(row: sqlite3.Row) -> Picture:
        return Picture(
            id=row["ID"],
            item_id=row["ItemID"],
            file_path=row["FilePath"],
            is_main=bool(row["IsMain"]),
        )

    def add_picture(self, item_id: int, file_path: str, is_main: bool = False) -> int:
        """
        Adds a picture to an item. If is_main=True, it will also set it as the only main picture.
        Returns new picture ID.
        """
        file_path = (file_path or "").strip()
        if not file_path:
            raise ValueError("file_path cannot be empty")

        conn = get_connection()
        try:
            cur = conn.execute(
                """
                INSERT INTO Picture (ItemID, FilePath, IsMain)
                VALUES (?, ?, ?)
                """,
                (item_id, file_path, 1 if is_main else 0),
            )
            new_id = int(cur.lastrowid)

            # If set as main, unset all other pictures for this item
            if is_main:
                conn.execute(
                    """
                    UPDATE Picture
                    SET IsMain = 0
                    WHERE ItemID = ? AND ID != ?
                    """,
                    (item_id, new_id),
                )

            conn.commit()
            return new_id
        finally:
            conn.close()

    def get_by_id(self, picture_id: int) -> Optional[Picture]:
        conn = get_connection()
        try:
            cur = conn.execute(
                """SELECT ID, ItemID, FilePath, IsMain FROM Picture WHERE ID = ?""",
                (picture_id,),
            )
            row = cur.fetchone()
            return self._row_to_picture(row) if row else None
        finally:
            conn.close()

    def list_for_item(self, item_id: int) -> List[Picture]:
        conn = get_connection()
        try:
            cur = conn.execute(
                """
                SELECT ID, ItemID, FilePath, IsMain
                FROM Picture
                WHERE ItemID = ?
                ORDER BY IsMain DESC, ID ASC
                """,
                (item_id,),
            )
            return [self._row_to_picture(r) for r in cur.fetchall()]
        finally:
            conn.close()

    def get_main_for_item(self, item_id: int) -> Optional[Picture]:
        conn = get_connection()
        try:
            cur = conn.execute(
                """
                SELECT ID, ItemID, FilePath, IsMain
                FROM Picture
                WHERE ItemID = ? AND IsMain = 1
                LIMIT 1
                """,
                (item_id,),
            )
            row = cur.fetchone()
            return self._row_to_picture(row) if row else None
        finally:
            conn.close()

    def set_main(self, picture_id: int) -> None:
        """
        Sets a picture as main for its item (and unsets others).
        """
        conn = get_connection()
        try:
            # Find which item this picture belongs to
            cur = conn.execute(
                """SELECT ItemID FROM Picture WHERE ID = ?""",
                (picture_id,),
            )
            row = cur.fetchone()
            if not row:
                raise ValueError("Picture not found")

            item_id = int(row["ItemID"])

            # Set this one to main, unset the rest
            conn.execute(
                """UPDATE Picture SET IsMain = 1 WHERE ID = ?""",
                (picture_id,),
            )
            conn.execute(
                """UPDATE Picture SET IsMain = 0 WHERE ItemID = ? AND ID != ?""",
                (item_id, picture_id),
            )
            conn.commit()
        finally:
            conn.close()

    def delete(self, picture_id: int) -> None:
        conn = get_connection()
        try:
            conn.execute(
                """DELETE FROM Picture WHERE ID = ?""",
                (picture_id,),
            )
            conn.commit()
        finally:
            conn.close()
