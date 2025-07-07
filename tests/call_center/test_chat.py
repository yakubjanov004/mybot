import pytest
from unittest.mock import AsyncMock, Mock
from handlers.call_center.chat import get_call_center_chat_router

class DummyMessage:
    def __init__(self, text, user_id=1):
        self.text = text
        self.from_user = type('User', (), {'id': user_id})()
        self.answer = AsyncMock()

def make_state(data):
    state = Mock()
    state.get_data = AsyncMock(return_value=data)
    return state

@pytest.mark.asyncio
async def test_operator_message_forwarded_and_saved(monkeypatch):
    message = DummyMessage('hello', user_id=10)
    router = get_call_center_chat_router()
    process_chat_message = next(h.callback for h in router.message.handlers if h.callback.__name__ == 'process_chat_message')
    state = make_state({'chat_id': 5, 'client_id': 2})

    monkeypatch.setattr('handlers.call_center.chat.get_user_by_telegram_id', AsyncMock(return_value={'id': 10, 'role': 'call_center', 'language': 'uz'}))
    monkeypatch.setattr('handlers.call_center.chat.get_user_by_id', AsyncMock(return_value={'telegram_id': 20}))
    save_mock = AsyncMock(return_value=True)
    monkeypatch.setattr('handlers.call_center.chat.save_chat_message', save_mock)
    send_mock = AsyncMock()
    monkeypatch.setattr('handlers.call_center.chat.bot.send_message', send_mock)

    await process_chat_message(message, state)

    save_mock.assert_called_once()
    send_mock.assert_called_once_with(chat_id=20, text='hello')
    message.answer.assert_called_once()

@pytest.mark.asyncio
async def test_client_message_forwarded_and_saved(monkeypatch):
    message = DummyMessage('hi', user_id=20)
    router = get_call_center_chat_router()
    process_chat_message = next(h.callback for h in router.message.handlers if h.callback.__name__ == 'process_chat_message')
    state = make_state({'chat_id': 6, 'operator_id': 30})

    monkeypatch.setattr('handlers.call_center.chat.get_user_by_telegram_id', AsyncMock(return_value={'id': 20, 'role': 'client', 'language': 'uz'}))
    monkeypatch.setattr('handlers.call_center.chat.get_user_by_id', AsyncMock(return_value={'telegram_id': 40}))
    save_mock = AsyncMock(return_value=True)
    monkeypatch.setattr('handlers.call_center.chat.save_chat_message', save_mock)
    send_mock = AsyncMock()
    monkeypatch.setattr('handlers.call_center.chat.bot.send_message', send_mock)

    await process_chat_message(message, state)

    save_mock.assert_called_once()
    send_mock.assert_called_once_with(chat_id=40, text='hi')
    message.answer.assert_called_once()
