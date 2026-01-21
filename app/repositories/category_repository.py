from __future__ import annotations

import sqlite3
from typing import List, Optional

from app.db.connection import get_connection
from app.models.category import Category


class CategoryRepository:
    @staticmethod
    def _row_to_category(row: sqlite3.Row) -> Category:
        return Category(
            id=row["ID"],
            name=row["Name"],
        )

    def create(self, name: str) -> int:
        name = (name or "").strip()
        if not name:
            raise ValueError("Category name cannot be empty")

        conn = get_connection()
        try:
            cur = conn.execute(
                """INSERT INTO Category (Name) VALUES (?)""",
                (name,),
            )
            conn.commit()
            return int(cur.lastrowid)
        finally:
            conn.close()

    def get_by_id(self, category_id: int) -> Optional[Category]:
        conn = get_connection()
        try:
            cur = conn.execute(
                """SELECT ID, Name FROM Category WHERE ID = ?""",
                (category_id,),
            )
            row = cur.fetchone()
            return self._row_to_category(row) if row else None
        finally:
            conn.close()

    def get_by_name(self, name: str) -> Optional[Category]:
        name = (name or "").strip()
        if not name:
            return None

        conn = get_connection()
        try:
            cur = conn.execute(
                """SELECT ID, Name FROM Category WHERE Name = ?""",
                (name,),
            )
            row = cur.fetchone()
            return self._row_to_category(row) if row else None
        finally:
            conn.close()

    def list_all(self) -> List[Category]:
        conn = get_connection()
        try:
            cur = conn.execute(
                """SELECT ID, Name FROM Category ORDER BY Name ASC"""
            )
            return [self._row_to_category(r) for r in cur.fetchall()]
        finally:
            conn.close()

    def update_name(self, category_id: int, new_name: str) -> None:
        new_name = (new_name or "").strip()
        if not new_name:
            raise ValueError("New category name cannot be empty")

        conn = get_connection()
        try:
            conn.execute(
                """UPDATE Category SET Name = ? WHERE ID = ?""",
                (new_name, category_id),
            )
            conn.commit()
        finally:
            conn.close()

    def delete(self, category_id: int) -> None:
        conn = get_connection()
        try:
            conn.execute(
                """DELETE FROM Category WHERE ID = ?""",
                (category_id,),
            )
            conn.commit()
        finally:
            conn.close()

    def exists_name(self, name: str) -> bool:
        name = (name or "").strip()
        if not name:
            return False

        conn = get_connection()
        try:
            cur = conn.execute(
                """SELECT 1 FROM Category WHERE Name = ? LIMIT 1""",
                (name,),
            )
            return cur.fetchone() is not None
        finally:
            conn.close()
