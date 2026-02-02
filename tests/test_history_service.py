import pytest

from app.services.history_service import HistoryService, HistoryItemNotFoundError


class FakeItem:
    def __init__(self, item_id, name):
        self.id = item_id
        self.name = name


class FakeItemRepo:
    def __init__(self, items):
        self.items = items

    def get_by_id(self, item_id):
        return self.items.get(item_id)


class FakeHistoryRepo:
    def __init__(self, views=None):
        self.views = views or []
        self.add_calls = []
        self.clear_calls = []

    def add_view(self, customer_user_id, item_id, viewed_at):
        self.add_calls.append((customer_user_id, item_id, viewed_at))

    def list_views(self, customer_user_id, limit=50, newest_first=True):
        return list(self.views)[:limit]

    def clear(self, customer_user_id):
        self.clear_calls.append(customer_user_id)


def test_record_view_raises_if_item_missing():
    svc = HistoryService(
        history_repo=FakeHistoryRepo(),
        item_repo=FakeItemRepo(items={}),
    )

    with pytest.raises(HistoryItemNotFoundError):
        svc.record_view(customer_user_id=1, item_id=999)


def test_record_view_calls_repo_add_view_with_timestamp():
    hist_repo = FakeHistoryRepo()
    svc = HistoryService(
        history_repo=hist_repo,
        item_repo=FakeItemRepo(items={1: FakeItem(1, "Desk")}),
    )

    svc.record_view(customer_user_id=10, item_id=1)

    assert len(hist_repo.add_calls) == 1
    assert hist_repo.add_calls[0][0] == 10
    assert hist_repo.add_calls[0][1] == 1
    assert isinstance(hist_repo.add_calls[0][2], str)  # ISO timestamp string


def test_list_history_maps_fields_and_keeps_viewed_at():
    hist_repo = FakeHistoryRepo(views=[(1, "2025-01-01T10:00:00Z"), (2, "2025-01-02T10:00:00Z")])
    item_repo = FakeItemRepo(items={1: FakeItem(1, "Desk"), 2: FakeItem(2, "Lamp")})

    svc = HistoryService(history_repo=hist_repo, item_repo=item_repo)

    rows = svc.list_history(customer_user_id=10, limit=50)

    assert len(rows) == 2
    assert rows[0]["item_id"] == 1
    assert rows[0]["name"] == "Desk"
    assert rows[0]["viewed_at"] == "2025-01-01T10:00:00Z"


def test_list_history_skips_deleted_items():
    hist_repo = FakeHistoryRepo(views=[(1, "t1"), (999, "t2")])
    item_repo = FakeItemRepo(items={1: FakeItem(1, "Desk")})

    svc = HistoryService(history_repo=hist_repo, item_repo=item_repo)

    rows = svc.list_history(customer_user_id=10, limit=50)

    assert len(rows) == 1
    assert rows[0]["item_id"] == 1


def test_clear_history_delegates_to_repo():
    hist_repo = FakeHistoryRepo()
    svc = HistoryService(history_repo=hist_repo, item_repo=FakeItemRepo(items={}))

    svc.clear_history(customer_user_id=55)
    assert hist_repo.clear_calls == [55]
