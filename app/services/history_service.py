from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Dict

from app.repositories.history_repository import HistoryRepository
from app.repositories.item_repository import ItemRepository


class HistoryError(Exception):
    pass


class HistoryItemNotFoundError(HistoryError):
    pass


@dataclass
class HistoryService:
    history_repo: HistoryRepository
    item_repo: ItemRepository

    def record_view(self, customer_user_id: int, item_id: int) -> None:
        if self.item_repo.get_by_id(item_id) is None:
            raise HistoryItemNotFoundError(f"Item {item_id} does not exist")

        viewed_at = datetime.now(timezone.utc).isoformat()
        self.history_repo.add_view(customer_user_id, item_id, viewed_at)

    def list_history(self, customer_user_id: int, limit: int = 50) -> List[Dict]:
        views = self.history_repo.list_views(customer_user_id, limit=limit, newest_first=True)

        result: List[Dict] = []
        for item_id, viewed_at in views:
            item = self.item_repo.get_by_id(item_id)
            if item is None:
                continue  # safety if item deleted
            result.append(
                {
                    "item_id": item.id,
                    "name": item.name,
                    "viewed_at": viewed_at,  # UTC ISO string
                }
            )

        return result

    def clear_history(self, customer_user_id: int) -> None:
        self.history_repo.clear(customer_user_id)
