from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters.callback_data import CallbackData

class SupportChatCallbackFactory(CallbackData, prefix="chat"):
    action: str
    request_id: str
    user_id: str

def get_chat_start_keyboard(request_id: str, user_id: str) -> InlineKeyboardMarkup:
    """
    Initial keyboard for starting chat
    """
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    keyboard.add(
        InlineKeyboardButton(
            text="✍️ Javob yozish",
            callback_data=SupportChatCallbackFactory(
                action='reply',
                request_id=request_id,
                user_id=user_id
            ).pack()
        )
    )
    
    return keyboard

def get_chat_actions_keyboard(request_id: str, user_id: str) -> InlineKeyboardMarkup:
    """
    Keyboard with chat actions
    """
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    keyboard.add(
        InlineKeyboardButton(
            text="🔗 Arizaga bog'lash",
            callback_data=SupportChatCallbackFactory(
                action='link',
                request_id=request_id,
                user_id=user_id
            ).pack()
        ),
        InlineKeyboardButton(
            text="❌ Chatni yopish",
            callback_data=SupportChatCallbackFactory(
                action='close',
                request_id=request_id,
                user_id=user_id
            ).pack()
        )
    )
    
    keyboard.add(
        InlineKeyboardButton(
            text="📎 Fayl yuborish",
            callback_data=SupportChatCallbackFactory(
                action='file',
                request_id=request_id,
                user_id=user_id
            ).pack()
        )
    )
    
    return keyboard

def get_chat_close_confirm_keyboard(request_id: str, user_id: str) -> InlineKeyboardMarkup:
    """
    Confirmation keyboard for closing chat
    """
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    keyboard.add(
        InlineKeyboardButton(
            text="✅ Ha",
            callback_data=SupportChatCallbackFactory(
                action='close_confirm',
                request_id=request_id,
                user_id=user_id
            ).pack()
        ),
        InlineKeyboardButton(
            text="❌ Yo'q",
            callback_data=SupportChatCallbackFactory(
                action='close_cancel',
                request_id=request_id,
                user_id=user_id
            ).pack()
        )
    )
    
    return keyboard 