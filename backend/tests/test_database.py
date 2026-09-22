from unittest.mock import patch

from sqlalchemy.exc import OperationalError

from app.database import wait_for_db


class FakeOperationalError(OperationalError):
    def __init__(self):
        pass


class FakeConnection:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def test_wait_for_db_retries_with_backoff_until_connection_succeeds():
    attempts = {"count": 0}

    def fake_connect():
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise FakeOperationalError()
        return FakeConnection()

    with patch("app.database.engine.connect", side_effect=fake_connect), patch(
        "app.database.time.sleep"
    ) as mock_sleep:
        wait_for_db()

    assert attempts["count"] == 3
    assert mock_sleep.call_args_list == [((1.0,),), ((2.0,),)]


def test_wait_for_db_returns_immediately_when_db_already_reachable():
    with patch("app.database.engine.connect", return_value=FakeConnection()), patch(
        "app.database.time.sleep"
    ) as mock_sleep:
        wait_for_db()

    mock_sleep.assert_not_called()
