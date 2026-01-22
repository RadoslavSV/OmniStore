from __future__ import annotations

import sqlite3
from typing import List, Optional

from app.db.connection import get_connection
from app.models.cart_item import CartItem


class ItemCartRepository:
    @staticmethod
    def _row_to_cart_item(row: sqlite3.Row) -> CartItem:
        return CartItem(
            cart_id=row["CartID"],
            item_id=row["ItemID"],
            quantity=row["Quantity"],
        )

    def upsert_quantity(self, cart_id: int, item_id: int, quantity: int) -> None:
        """
        Inserts or updates quantity for a (cart_id, item_id).
        quantity must be positive.
        """
        if quantity <= 0:
            raise ValueError("Quantity must be positive")

        conn = get_connection()
        try:
            conn.execute(
                """
                INSERT INTO Item_Cart (CartID, ItemID, Quantity)
                VALUES (?, ?, ?)
                ON CONFLICT(CartID, ItemID) DO UPDATE SET Quantity = excluded.Quantity
                """,
                (cart_id, item_id, quantity),
            )
            conn.commit()
        finally:
            conn.close()

    def increment(self, cart_id: int, item_id: int, delta: int = 1) -> None:
        """
        Adds delta to quantity if exists, otherwise inserts with delta.
        delta must be positive.
        """
        if delta <= 0:
            raise ValueError("Delta must be positive")

        conn = get_connection()
        try:
            cur = conn.execute(
                """
                SELECT Quantity FROM Item_Cart
                WHERE CartID = ? AND ItemID = ?
                """,
                (cart_id, item_id),
            )
            row = cur.fetchone()
            if row:
                new_q = int(row["Quantity"]) + delta
                conn.execute(
                    """
                    UPDATE Item_Cart
                    SET Quantity = ?
                    WHERE CartID = ? AND ItemID = ?
                    """,
                    (new_q, cart_id, item_id),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO Item_Cart (CartID, ItemID, Quantity)
                    VALUES (?, ?, ?)
                    """,
                    (cart_id, item_id, delta),
                )
            conn.commit()
        finally:
            conn.close()

    def decrement(self, cart_id: int, item_id: int, delta: int = 1) -> None:
        """
        Subtracts delta from quantity; if it becomes 0 or less, removes row.
        delta must be positive.
        """
        if delta <= 0:
            raise ValueError("Delta must be positive")

        conn = get_connection()
        try:
            cur = conn.execute(
                """
                SELECT Quantity FROM Item_Cart
                WHERE CartID = ? AND ItemID = ?
                """,
                (cart_id, item_id),
            )
            row = cur.fetchone()
            if not row:
                return

            current = int(row["Quantity"])
            new_q = current - delta

            if new_q > 0:
                conn.execute(
                    """
                    UPDATE Item_Cart
                    SET Quantity = ?
                    WHERE CartID = ? AND ItemID = ?
                    """,
                    (new_q, cart_id, item_id),
                )
            else:
                conn.execute(
                    """
                    DELETE FROM Item_Cart
                    WHERE CartID = ? AND ItemID = ?
                    """,
                    (cart_id, item_id),
                )
            conn.commit()
        finally:
            conn.close()

    def remove_item(self, cart_id: int, item_id: int) -> None:
        conn = get_connection()
        try:
            conn.execute(
                """
                DELETE FROM Item_Cart
                WHERE CartID = ? AND ItemID = ?
                """,
                (cart_id, item_id),
            )
            conn.commit()
        finally:
            conn.close()

    def list_items(self, cart_id: int) -> List[CartItem]:
        conn = get_connection()
        try:
            cur = conn.execute(
                """
                SELECT CartID, ItemID, Quantity
                FROM Item_Cart
                WHERE CartID = ?
                ORDER BY ItemID ASC
                """,
                (cart_id,),
            )
            return [self._row_to_cart_item(r) for r in cur.fetchall()]
        finally:
            conn.close()

    def get_item(self, cart_id: int, item_id: int) -> Optional[CartItem]:
        conn = get_connection()
        try:
            cur = conn.execute(
                """
                SELECT CartID, ItemID, Quantity
                FROM Item_Cart
                WHERE CartID = ? AND ItemID = ?
                """,
                (cart_id, item_id),
            )
            row = cur.fetchone()
            return self._row_to_cart_item(row) if row else None
        finally:
            conn.close()
