from __future__ import annotations

import sqlite3
from typing import Optional

from app.db.connection import get_connection
from app.models.cart import Cart


class CartRepository:
    @staticmethod
    def _row_to_cart(row: sqlite3.Row) -> Cart:
        return Cart(
            id=row["ID"],
            customer_user_id=row["CustomerUserID"],
        )

    def create_for_customer(self, customer_user_id: int) -> int:
        """
        Creates a cart for a customer. CustomerUserID is UNIQUE:
        - if a cart already exists, this will raise sqlite constraint error
          unless you call get_or_create_for_customer().
        """
        conn = get_connection()
        try:
            cur = conn.execute(
                """
                INSERT INTO Cart (CustomerUserID)
                VALUES (?)
                """,
                (customer_user_id,),
            )
            conn.commit()
            return int(cur.lastrowid)
        finally:
            conn.close()

    def get_by_id(self, cart_id: int) -> Optional[Cart]:
        conn = get_connection()
        try:
            cur = conn.execute(
                """SELECT ID, CustomerUserID FROM Cart WHERE ID = ?""",
                (cart_id,),
            )
            row = cur.fetchone()
            return self._row_to_cart(row) if row else None
        finally:
            conn.close()

    def get_by_customer(self, customer_user_id: int) -> Optional[Cart]:
        conn = get_connection()
        try:
            cur = conn.execute(
                """SELECT ID, CustomerUserID FROM Cart WHERE CustomerUserID = ?""",
                (customer_user_id,),
            )
            row = cur.fetchone()
            return self._row_to_cart(row) if row else None
        finally:
            conn.close()

    def get_or_create_for_customer(self, customer_user_id: int) -> Cart:
        existing = self.get_by_customer(customer_user_id)
        if existing:
            return existing

        new_id = self.create_for_customer(customer_user_id)
        created = self.get_by_id(new_id)
        if created is None:
            raise RuntimeError("Failed to create cart")
        return created

    def delete(self, cart_id: int) -> None:
        conn = get_connection()
        try:
            conn.execute(
                """DELETE FROM Cart WHERE ID = ?""",
                (cart_id,),
            )
            conn.commit()
        finally:
            conn.close()
