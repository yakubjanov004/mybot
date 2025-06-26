from aiogram.types import Message, CallbackQuery
from aiogram import Bot

MAX_MESSAGE_LENGTH = 4096

def split_message(text):
    return [text[i:i+MAX_MESSAGE_LENGTH] for i in range(0, len(text), MAX_MESSAGE_LENGTH)]

async def safe_answer_message(message: Message, text: str, **kwargs):
    for part in split_message(text):
        await message.answer(part, **kwargs)

async def safe_send_message(bot: Bot, chat_id, text: str, **kwargs):
    for part in split_message(text):
        await bot.send_message(chat_id=chat_id, text=part, **kwargs) 