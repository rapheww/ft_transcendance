import pytest
from unittest.mock import AsyncMock, MagicMock
from backend.websocket.connection_manager import ConnectionManager


@pytest.mark.asyncio
async def test_connect_accepts_websocket():
    manager = ConnectionManager()
    websocket = MagicMock()
    websocket.accept = AsyncMock()

    await manager.connect(1, 10, websocket)

    websocket.accept.assert_awaited_once()
    assert manager.get_connection(1, 10) is websocket


@pytest.mark.asyncio
async def test_reconnect_closes_old_socket():
    manager = ConnectionManager()

    old_socket = MagicMock()
    old_socket.accept = AsyncMock()
    old_socket.close = AsyncMock()

    new_socket = MagicMock()
    new_socket.accept = AsyncMock()

    await manager.connect(1, 10, old_socket)
    await manager.connect(1, 10, new_socket)

    old_socket.close.assert_awaited_once_with(
        code=4001, reason="replaced by new connection")
    assert manager.get_connection(1, 10) is new_socket


def test_old_socket_cannot_disconnect_replacement():
    manager = ConnectionManager()

    old_socket = MagicMock()
    new_socket = MagicMock()

    manager.connections[1] = {10: new_socket}

    removed = manager.disconnect(1, 10, old_socket)

    assert removed is False
    assert manager.get_connection(1, 10) is new_socket


def test_disconnect_removes_empty_game():
    manager = ConnectionManager()
    websocket = MagicMock()
    manager.connections[1] = {10: websocket}

    removed = manager.disconnect(1, 10, websocket)

    assert removed is True
    assert 1 not in manager.connections


def test_valid_event_rejects_unknown_events():
    manager = ConnectionManager()

    assert manager.valid_event("move") is True
    assert manager.valid_event("chat") is True
    assert manager.valid_event("ping") is False
    assert manager.valid_event("admin") is False
    assert manager.valid_event(None) is False
