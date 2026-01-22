from __future__ import annotations

from typing import Optional
from app.db.connection import get_connection


class CustomerRepository:
    def make_customer(self, user_id: int, currency: str = "EUR") -> None:
        """
        Inserts (or replaces) a row in Customer table for the given user.
        """
        currency = (currency or "EUR").strip().upper()

        conn = get_connection()
        try:
            conn.execute(
                """
                INSERT INTO Customer (UserID, Currency)
                VALUES (?, ?)
                ON CONFLICT(UserID) DO UPDATE SET Currency = excluded.Currency
                """,
                (user_id, currency),
            )
            conn.commit()
        finally:
            conn.close()

    def is_customer(self, user_id: int) -> bool:
        conn = get_connection()
        try:
            cur = conn.execute(
                "SELECT 1 FROM Customer WHERE UserID = ? LIMIT 1",
                (user_id,),
            )
            return cur.fetchone() is not None
        finally:
            conn.close()

    def get_currency(self, user_id: int) -> Optional[str]:
        conn = get_connection()
        try:
            cur = conn.execute(
                "SELECT Currency FROM Customer WHERE UserID = ?",
                (user_id,),
            )
            row = cur.fetchone()
            return row["Currency"] if row else None
        finally:
            conn.close()

    def set_currency(self, user_id: int, currency: str) -> None:
        currency = (currency or "").strip().upper()
        if not currency:
            raise ValueError("Currency cannot be empty")

        conn = get_connection()
        try:
            conn.execute(
                "UPDATE Customer SET Currency = ? WHERE UserID = ?",
                (currency, user_id),
            )
            conn.commit()
        finally:
            conn.close()
