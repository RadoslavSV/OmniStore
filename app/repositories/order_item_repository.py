from __future__ import annotations

import sqlite3
from typing import List, Optional

from app.db.connection import get_connection
from app.models.order_item import OrderItem


class OrderItemRepository:
    @staticmethod
    def _row_to_order_item(row: sqlite3.Row) -> OrderItem:
        return OrderItem(
            order_id=row["OrderID"],
            item_id=row["ItemID"],
            item_name=row["ItemName"],
            unit_price_base=float(row["UnitPriceBase"]),
            quantity=int(row["Quantity"]),
        )

    def add(self, order_item: OrderItem) -> None:
        conn = get_connection()
        try:
            conn.execute(
                """
                INSERT INTO OrderItem (OrderID, ItemID, ItemName, UnitPriceBase, Quantity)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    order_item.order_id,
                    order_item.item_id,
                    order_item.item_name,
                    float(order_item.unit_price_base),
                    int(order_item.quantity),
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def list_for_order(self, order_id: int) -> List[OrderItem]:
        conn = get_connection()
        try:
            cur = conn.execute(
                """
                SELECT OrderID, ItemID, ItemName, UnitPriceBase, Quantity
                FROM OrderItem
                WHERE OrderID = ?
                ORDER BY ItemName ASC
                """,
                (order_id,),
            )
            return [self._row_to_order_item(r) for r in cur.fetchall()]
        finally:
            conn.close()

    def get(self, order_id: int, item_id: Optional[int]) -> Optional[OrderItem]:
        conn = get_connection()
        try:
            cur = conn.execute(
                """
                SELECT OrderID, ItemID, ItemName, UnitPriceBase, Quantity
                FROM OrderItem
                WHERE OrderID = ? AND ItemID IS ?
                """,
                (order_id, item_id),
            )
            row = cur.fetchone()
            return self._row_to_order_item(row) if row else None
        finally:
            conn.close()
