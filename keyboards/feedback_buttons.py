from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters.callback_data import CallbackData

class FeedbackCallbackFactory(CallbackData, prefix="feedback"):
    action: str
    request_id: str
    rating: str

def get_rating_keyboard(request_id: str) -> InlineKeyboardMarkup:
    """
    Create rating keyboard with stars (1-5)
    """
    keyboard = InlineKeyboardMarkup(row_width=5)
    
    buttons = []
    for i in range(1, 6):
        stars = "⭐" * i
        buttons.append(
            InlineKeyboardButton(
                text=stars,
                callback_data=FeedbackCallbackFactory(
                    action='rate',
                    request_id=request_id,
                    rating=str(i)
                ).pack()
            )
        )
    
    keyboard.add(*buttons)
    return keyboard

def get_feedback_comment_keyboard(request_id: str) -> InlineKeyboardMarkup:
    """
    Keyboard for adding comment to feedback
    """
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    keyboard.add(
        InlineKeyboardButton(
            text="💬 Izoh qoldirish",
            callback_data=FeedbackCallbackFactory(
                action='comment',
                request_id=request_id,
                rating='0'
            ).pack()
        ),
        InlineKeyboardButton(
            text="➡️ Tashlab ketish",
            callback_data=FeedbackCallbackFactory(
                action='skip',
                request_id=request_id,
                rating='0'
            ).pack()
        )
    )
    
    return keyboard

def get_feedback_complete_keyboard() -> InlineKeyboardMarkup:
    """
    Final keyboard shown after feedback is complete
    """
    keyboard = InlineKeyboardMarkup()
    
    keyboard.add(
        InlineKeyboardButton(
            text="🙏 Rahmat!",
            callback_data=FeedbackCallbackFactory(
                action='thanks',
                request_id='0',
                rating='0'
            ).pack()
        )
    )
    
    return keyboard 