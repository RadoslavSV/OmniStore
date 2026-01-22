from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict

from app.repositories.favorites_repository import FavoritesRepository
from app.repositories.item_repository import ItemRepository


class FavoritesError(Exception):
    pass


class FavoriteItemNotFoundError(FavoritesError):
    pass


@dataclass
class FavoritesService:
    favorites_repo: FavoritesRepository
    item_repo: ItemRepository

    def add_favorite(self, customer_user_id: int, item_id: int) -> None:
        if self.item_repo.get_by_id(item_id) is None:
            raise FavoriteItemNotFoundError(f"Item {item_id} does not exist")
        self.favorites_repo.add(customer_user_id, item_id)

    def remove_favorite(self, customer_user_id: int, item_id: int) -> None:
        self.favorites_repo.remove(customer_user_id, item_id)

    def is_favorite(self, customer_user_id: int, item_id: int) -> bool:
        return self.favorites_repo.is_favorite(customer_user_id, item_id)

    def list_favorites(self, customer_user_id: int) -> List[Dict]:
        """
        Returns list of dicts with basic item info for UI.
        """
        ids = self.favorites_repo.list_item_ids(customer_user_id)
        result: List[Dict] = []

        for item_id in ids:
            item = self.item_repo.get_by_id(item_id)
            if item is None:
                continue  # safety if item deleted
            result.append(
                {
                    "item_id": item.id,
                    "name": item.name,
                    "price": item.price,
                }
            )

        return result
