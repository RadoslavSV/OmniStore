import pytest

from app.services.favorites_service import FavoritesService, FavoriteItemNotFoundError


class FakeItem:
    def __init__(self, item_id, name, price):
        self.id = item_id
        self.name = name
        self.price = price


class FakeItemRepo:
    def __init__(self, items):
        self.items = items

    def get_by_id(self, item_id):
        return self.items.get(item_id)


class FakeFavoritesRepo:
    def __init__(self, ids=None):
        self.ids = ids or []
        self.add_calls = []
        self.remove_calls = []

    def add(self, customer_user_id, item_id):
        self.add_calls.append((customer_user_id, item_id))

    def remove(self, customer_user_id, item_id):
        self.remove_calls.append((customer_user_id, item_id))

    def is_favorite(self, customer_user_id, item_id):
        return item_id in self.ids

    def list_item_ids(self, customer_user_id):
        return list(self.ids)


def test_add_favorite_raises_if_item_missing():
    svc = FavoritesService(
        favorites_repo=FakeFavoritesRepo(),
        item_repo=FakeItemRepo(items={}),
    )

    with pytest.raises(FavoriteItemNotFoundError):
        svc.add_favorite(customer_user_id=1, item_id=999)


def test_add_favorite_calls_repo_add():
    fav_repo = FakeFavoritesRepo()
    svc = FavoritesService(
        favorites_repo=fav_repo,
        item_repo=FakeItemRepo(items={10: FakeItem(10, "Desk", 300.0)}),
    )

    svc.add_favorite(customer_user_id=1, item_id=10)
    assert fav_repo.add_calls == [(1, 10)]


def test_remove_favorite_calls_repo_remove():
    fav_repo = FakeFavoritesRepo()
    svc = FavoritesService(favorites_repo=fav_repo, item_repo=FakeItemRepo(items={}))

    svc.remove_favorite(customer_user_id=1, item_id=10)
    assert fav_repo.remove_calls == [(1, 10)]


def test_is_favorite_delegates_to_repo():
    fav_repo = FakeFavoritesRepo(ids=[5, 6])
    svc = FavoritesService(favorites_repo=fav_repo, item_repo=FakeItemRepo(items={}))

    assert svc.is_favorite(customer_user_id=1, item_id=5) is True
    assert svc.is_favorite(customer_user_id=1, item_id=7) is False


def test_list_favorites_skips_deleted_items():
    fav_repo = FakeFavoritesRepo(ids=[1, 999])
    item_repo = FakeItemRepo(items={1: FakeItem(1, "Lamp", 40.0)})

    svc = FavoritesService(favorites_repo=fav_repo, item_repo=item_repo)

    rows = svc.list_favorites(customer_user_id=1)

    assert len(rows) == 1
    assert rows[0]["item_id"] == 1
    assert rows[0]["name"] == "Lamp"
    assert rows[0]["price"] == 40.0
