from __future__ import annotations

import sqlite3
from typing import List, Optional

from app.db.connection import get_connection
from app.models.item import Item
from app.models.product import Dimensions


class ItemRepository:
    @staticmethod
    def _row_to_item(row: sqlite3.Row) -> Item:
        return Item(
            id=row["ID"],
            admin_user_id=row["AdminUserID"],
            name=row["Name"],
            description=row["Description"],
            dimensions=Dimensions(
                length=float(row["Depth"]),   # Depth = length (по смисъл)
                width=float(row["Width"]),
                height=float(row["Height"]),
            ),
            weight=float(row["Weight"]),
            price=float(row["Price"]),
        )

    def create(self, item: Item) -> int:
        conn = get_connection()
        try:
            cur = conn.execute(
                """
                INSERT INTO "Item" (
                    AdminUserID, Name, Description,
                    Height, Width, Depth, Weight, Price
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.admin_user_id,
                    item.name,
                    item.description,
                    item.dimensions.height,
                    item.dimensions.width,
                    item.dimensions.length,
                    item.weight,
                    item.price,
                ),
            )
            conn.commit()
            return int(cur.lastrowid)
        finally:
            conn.close()

    def get_by_id(self, item_id: int) -> Optional[Item]:
        conn = get_connection()
        try:
            cur = conn.execute(
                """
                SELECT ID, AdminUserID, Name, Description, Height, Width, Depth, Weight, Price
                FROM "Item"
                WHERE ID = ?
                """,
                (item_id,),
            )
            row = cur.fetchone()
            return self._row_to_item(row) if row else None
        finally:
            conn.close()

    def list_all(self) -> List[Item]:
        conn = get_connection()
        try:
            cur = conn.execute(
                """
                SELECT ID, AdminUserID, Name, Description, Height, Width, Depth, Weight, Price
                FROM "Item"
                ORDER BY ID ASC
                """
            )
            return [self._row_to_item(r) for r in cur.fetchall()]
        finally:
            conn.close()

    def list_by_admin(self, admin_user_id: int) -> List[Item]:
        conn = get_connection()
        try:
            cur = conn.execute(
                """
                SELECT ID, AdminUserID, Name, Description, Height, Width, Depth, Weight, Price
                FROM "Item"
                WHERE AdminUserID = ?
                ORDER BY ID ASC
                """,
                (admin_user_id,),
            )
            return [self._row_to_item(r) for r in cur.fetchall()]
        finally:
            conn.close()

    def update(self, item: Item) -> None:
        if item.id is None:
            raise ValueError("Cannot update item without id")

        conn = get_connection()
        try:
            conn.execute(
                """
                UPDATE "Item"
                SET Name = ?,
                    Description = ?,
                    Height = ?,
                    Width = ?,
                    Depth = ?,
                    Weight = ?,
                    Price = ?
                WHERE ID = ?
                """,
                (
                    item.name,
                    item.description,
                    item.dimensions.height,
                    item.dimensions.width,
                    item.dimensions.length,
                    item.weight,
                    item.price,
                    item.id,
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def delete(self, item_id: int) -> None:
        conn = get_connection()
        try:
            conn.execute(
                """DELETE FROM "Item" WHERE ID = ?""",
                (item_id,),
            )
            conn.commit()
        finally:
            conn.close()
