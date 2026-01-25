from __future__ import annotations

import sqlite3
from typing import List, Optional

from app.db.connection import get_connection
from app.models.order import Order


class OrderRepository:
    @staticmethod
    def _row_to_order(row: sqlite3.Row) -> Order:
        return Order(
            id=row["ID"],
            customer_user_id=row["CustomerUserID"],
            created_at=row["CreatedAt"],
            status=row["Status"],
            total_base=float(row["TotalBase"]),
        )

    def create(self, customer_user_id: int, created_at: str, status: str = "CREATED", total_base: float = 0.0) -> int:
        conn = get_connection()
        try:
            cur = conn.execute(
                """
                INSERT INTO "Order" (CustomerUserID, CreatedAt, Status, TotalBase)
                VALUES (?, ?, ?, ?)
                """,
                (customer_user_id, created_at, status, float(total_base)),
            )
            conn.commit()
            return int(cur.lastrowid)
        finally:
            conn.close()

    def update_status(self, order_id: int, status: str) -> None:
        conn = get_connection()
        try:
            conn.execute(
                """UPDATE "Order" SET Status = ? WHERE ID = ?""",
                (status, order_id),
            )
            conn.commit()
        finally:
            conn.close()

    def update_total_base(self, order_id: int, total_base: float) -> None:
        conn = get_connection()
        try:
            conn.execute(
                """UPDATE "Order" SET TotalBase = ? WHERE ID = ?""",
                (float(total_base), order_id),
            )
            conn.commit()
        finally:
            conn.close()

    def get_by_id(self, order_id: int) -> Optional[Order]:
        conn = get_connection()
        try:
            cur = conn.execute(
                """SELECT ID, CustomerUserID, CreatedAt, Status, TotalBase FROM "Order" WHERE ID = ?""",
                (order_id,),
            )
            row = cur.fetchone()
            return self._row_to_order(row) if row else None
        finally:
            conn.close()

    def list_for_customer(self, customer_user_id: int, limit: int = 50) -> List[Order]:
        conn = get_connection()
        try:
            cur = conn.execute(
                """
                SELECT ID, CustomerUserID, CreatedAt, Status, TotalBase
                FROM "Order"
                WHERE CustomerUserID = ?
                ORDER BY CreatedAt DESC
                LIMIT ?
                """,
                (customer_user_id, limit),
            )
            return [self._row_to_order(r) for r in cur.fetchall()]
        finally:
            conn.close()
