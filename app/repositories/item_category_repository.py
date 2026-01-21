from __future__ import annotations

from typing import List

from app.db.connection import get_connection
from app.models.category import Category
from app.models.item import Item
from app.models.product import Dimensions


class ItemCategoryRepository:
    def add(self, item_id: int, category_id: int) -> None:
        conn = get_connection()
        try:
            conn.execute(
                """
                INSERT OR IGNORE INTO Item_Category (ItemID, CategoryID)
                VALUES (?, ?)
                """,
                (item_id, category_id),
            )
            conn.commit()
        finally:
            conn.close()

    def remove(self, item_id: int, category_id: int) -> None:
        conn = get_connection()
        try:
            conn.execute(
                """
                DELETE FROM Item_Category
                WHERE ItemID = ? AND CategoryID = ?
                """,
                (item_id, category_id),
            )
            conn.commit()
        finally:
            conn.close()

    def list_categories_for_item(self, item_id: int) -> List[Category]:
        conn = get_connection()
        try:
            cur = conn.execute(
                """
                SELECT c.ID, c.Name
                FROM Category c
                JOIN Item_Category ic ON ic.CategoryID = c.ID
                WHERE ic.ItemID = ?
                ORDER BY c.Name ASC
                """,
                (item_id,),
            )
            rows = cur.fetchall()
            return [Category(id=r["ID"], name=r["Name"]) for r in rows]
        finally:
            conn.close()

    def list_items_for_category(self, category_id: int) -> List[Item]:
        conn = get_connection()
        try:
            cur = conn.execute(
                """
                SELECT i.ID, i.AdminUserID, i.Name, i.Description, i.Height, i.Width, i.Depth, i.Weight, i.Price
                FROM Item i
                JOIN Item_Category ic ON ic.ItemID = i.ID
                WHERE ic.CategoryID = ?
                ORDER BY i.ID ASC
                """,
                (category_id,),
            )
            rows = cur.fetchall()
            items: List[Item] = []
            for r in rows:
                items.append(
                    Item(
                        id=r["ID"],
                        admin_user_id=r["AdminUserID"],
                        name=r["Name"],
                        description=r["Description"],
                        dimensions=Dimensions(
                            length=float(r["Depth"]),
                            width=float(r["Width"]),
                            height=float(r["Height"]),
                        ),
                        weight=float(r["Weight"]),
                        price=float(r["Price"]),
                    )
                )
            return items
        finally:
            conn.close()
