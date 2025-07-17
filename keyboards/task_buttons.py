from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters.callback_data import CallbackData

class TaskCallbackFactory(CallbackData, prefix="task"):
    action: str
    task_id: int

def get_task_keyboard(task_id: int) -> InlineKeyboardMarkup:
    """
    Create keyboard for task actions
    """
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    keyboard.add(
        InlineKeyboardButton(
            text="👁️ Ko'rish",
            callback_data=TaskCallbackFactory(
                action='view',
                task_id=task_id
            ).pack()
        ),
        InlineKeyboardButton(
            text="✅ Bajarildi",
            callback_data=TaskCallbackFactory(
                action='complete',
                task_id=task_id
            ).pack()
        )
    )
    
    return keyboard
