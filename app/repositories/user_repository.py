from __future__ import annotations

import sqlite3
from typing import Optional

from app.db.connection import get_connection
from app.models.user import User


class UserRepository:
    """
    Data access for the User table.
    Works only with base user data (id, username, email, password_hash, name).
    Roles/admin/customer-specific data will be handled by separate repositories/services.
    """

    @staticmethod
    def _row_to_user(row: sqlite3.Row) -> User:
        # DB columns: ID, Username, Password, Name, Email
        return User(
            id=row["ID"],
            username=row["Username"],
            email=row["Email"],
            password_hash=row["Password"],
            role="USER",  # role is derived from Admin/Customer tables later
        )

    def create(
        self,
        username: str,
        email: str,
        password_hash: str,
        name: str,
    ) -> int:
        """
        Inserts a new user into the database and returns the new user ID.
        """
        conn = get_connection()
        try:
            cur = conn.execute(
                """
                INSERT INTO "User" (Username, Password, Name, Email)
                VALUES (?, ?, ?, ?)
                """,
                (username, password_hash, name, email),
            )
            conn.commit()
            return int(cur.lastrowid)
        finally:
            conn.close()

    def get_by_id(self, user_id: int) -> Optional[User]:
        conn = get_connection()
        try:
            cur = conn.execute(
                """SELECT ID, Username, Password, Name, Email FROM "User" WHERE ID = ?""",
                (user_id,),
            )
            row = cur.fetchone()
            return self._row_to_user(row) if row else None
        finally:
            conn.close()

    def get_by_email(self, email: str) -> Optional[User]:
        conn = get_connection()
        try:
            cur = conn.execute(
                """SELECT ID, Username, Password, Name, Email FROM "User" WHERE Email = ?""",
                (email,),
            )
            row = cur.fetchone()
            return self._row_to_user(row) if row else None
        finally:
            conn.close()

    def get_by_username(self, username: str) -> Optional[User]:
        conn = get_connection()
        try:
            cur = conn.execute(
                """SELECT ID, Username, Password, Name, Email FROM "User" WHERE Username = ?""",
                (username,),
            )
            row = cur.fetchone()
            return self._row_to_user(row) if row else None
        finally:
            conn.close()

    def exists_email(self, email: str) -> bool:
        conn = get_connection()
        try:
            cur = conn.execute(
                """SELECT 1 FROM "User" WHERE Email = ? LIMIT 1""",
                (email,),
            )
            return cur.fetchone() is not None
        finally:
            conn.close()

    def exists_username(self, username: str) -> bool:
        conn = get_connection()
        try:
            cur = conn.execute(
                """SELECT 1 FROM "User" WHERE Username = ? LIMIT 1""",
                (username,),
            )
            return cur.fetchone() is not None
        finally:
            conn.close()
