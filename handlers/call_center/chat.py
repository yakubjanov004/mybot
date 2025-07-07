from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from database.base_queries import get_user_by_telegram_id, get_user_by_id
from database.call_center_queries import (
    create_chat_session, get_active_chat_sessions, 
    close_chat_session, save_chat_message
)
from keyboards.support_chat_buttons import (
    get_chat_start_keyboard,
    get_chat_actions_keyboard,
    get_chat_close_confirm_keyboard
)
from states.call_center import CallCenterStates
from utils.logger import logger
from loader import bot

def get_call_center_chat_router():
    router = Router()

    @router.message(F.text.in_(["💬 Chat", "💬 Чат"]))
    async def reply_chat(message: Message, state: FSMContext):
        """Start chat from reply keyboard"""
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user or user['role'] != 'call_center':
            lang = user.get('language', 'uz') if user else 'uz'
            text = "Sizda ruxsat yo'q." if lang == 'uz' else "У вас нет доступа."
            await message.answer(text)
            return
        
        lang = user.get('language', 'uz')
        data = await state.get_data()
        
        if not data.get('client_id'):
            text = "❌ Avval mijozni tanlang" if lang == 'uz' else "❌ Сначала выберите клиента"
            await message.answer(text)
            return
        
        try:
            # Check active chat sessions
            active_chats = await get_active_chat_sessions(data['client_id'])
            if active_chats:
                text = "⚠️ Mijoz bilan faol chat mavjud" if lang == 'uz' else "⚠️ Есть активный чат с клиентом"
                await message.answer(text)
                return
            
            # Create new chat session
            chat_data = {
                'client_id': data['client_id'],
                'operator_id': user['id'],
                'status': 'active'
            }
            chat_id = await create_chat_session(chat_data)
            
            if chat_id:
                await state.update_data(chat_id=chat_id)
                await state.set_state(CallCenterStates.in_chat)
                text = "💬 Chat sessiyasi boshlandi. Xabaringizni yuboring:" if lang == 'uz' else "💬 Сессия чата начата. Отправьте ваше сообщение:"
                await message.answer(
                    text,
                    reply_markup=get_chat_actions_keyboard(str(chat_id), str(data['client_id']))
                )
            else:
                text = "❌ Chat sessiyasini boshlab bo'lmadi" if lang == 'uz' else "❌ Не удалось начать сессию чата"
                await message.answer(text)
            
        except Exception as e:
            logger.error(f"Error starting chat: {str(e)}")
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)

    @router.callback_query(F.data == "start_chat")
    async def start_support_chat(callback: CallbackQuery, state: FSMContext):
        """Start support chat session"""
        user = await get_user_by_telegram_id(callback.from_user.id)
        if not user or user['role'] != 'call_center':
            await callback.answer("Access denied", show_alert=True)
            return
        
        lang = user.get('language', 'uz')
        data = await state.get_data()
        
        if not data.get('client_id'):
            text = "Avval mijozni tanlang" if lang == 'uz' else "Сначала выберите клиента"
            await callback.answer(text, show_alert=True)
            return
        
        try:
            # Check active chat sessions
            active_chats = await get_active_chat_sessions(data['client_id'])
            if active_chats:
                text = "Mijoz bilan faol chat mavjud" if lang == 'uz' else "Есть активный чат с клиентом"
                await callback.answer(text, show_alert=True)
                return
            
            # Create new chat session
            chat_data = {
                'client_id': data['client_id'],
                'operator_id': user['id'],
                'status': 'active'
            }
            chat_id = await create_chat_session(chat_data)
            
            if chat_id:
                await state.update_data(chat_id=chat_id)
                await state.set_state(CallCenterStates.in_chat)
                text = "💬 Chat sessiyasi boshlandi" if lang == 'uz' else "💬 Сессия чата начата"
                await callback.message.edit_text(
                    text,
                    reply_markup=get_chat_actions_keyboard(str(chat_id), str(data['client_id']))
                )
            else:
                text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
                await callback.answer(text, show_alert=True)
            
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Error starting chat session: {str(e)}")
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await callback.message.edit_text(error_text)
            await callback.answer()

    @router.message(StateFilter(CallCenterStates.in_chat))
    async def process_chat_message(message: Message, state: FSMContext):
        """Process chat message"""
        user = await get_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        data = await state.get_data()
        
        if not data.get('chat_id'):
            text = "❌ Chat sessiyasi topilmadi" if lang == 'uz' else "❌ Сессия чата не найдена"
            await message.answer(text)
            return
        
        try:
            # Save message to database
            message_data = {
                'session_id': data['chat_id'],
                'sender_id': user['id'],
                'message_text': message.text,
                'message_type': 'text'
            }
            
            success = await save_chat_message(message_data)

            if success:
                # Forward message depending on sender role
                if user['role'] == 'call_center':
                    client = await get_user_by_id(data.get('client_id'))
                    if client and client.get('telegram_id'):
                        await bot.send_message(chat_id=client['telegram_id'], text=message.text)
                elif user['role'] == 'client':
                    operator = await get_user_by_id(data.get('operator_id'))
                    if operator and operator.get('telegram_id'):
                        await bot.send_message(chat_id=operator['telegram_id'], text=message.text)

                sent_text = "✅ Xabar yuborildi" if lang == 'uz' else "✅ Сообщение отправлено"
                await message.answer(sent_text)

                logger.info(
                    f"Chat message sent by {user['role']} {user['id']} in session {data['chat_id']}"
                )
            else:
                text = "❌ Xabarni yuborib bo'lmadi" if lang == 'uz' else "❌ Не удалось отправить сообщение"
                await message.answer(text)
            
        except Exception as e:
            logger.error(f"Error processing chat message: {str(e)}")
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)

    @router.callback_query(F.data.startswith("chat:close:"))
    async def confirm_close_chat(callback: CallbackQuery, state: FSMContext):
        """Confirm closing chat"""
        user = await get_user_by_telegram_id(callback.from_user.id)
        if not user or user['role'] != 'call_center':
            await callback.answer("Access denied", show_alert=True)
            return
        
        lang = user.get('language', 'uz')
        _, _, chat_id = callback.data.split(':')
        
        text = "❓ Chatni yopishni tasdiqlaysizmi?" if lang == 'uz' else "❓ Подтверждаете закрытие чата?"
        await callback.message.edit_text(
            text,
            reply_markup=get_chat_close_confirm_keyboard(chat_id, str(user['id']))
        )

    @router.callback_query(F.data.startswith("chat:confirm_close:"))
    async def close_chat_confirmed(callback: CallbackQuery, state: FSMContext):
        """Close chat after confirmation"""
        user = await get_user_by_telegram_id(callback.from_user.id)
        if not user or user['role'] != 'call_center':
            await callback.answer("Access denied", show_alert=True)
            return
        
        lang = user.get('language', 'uz')
        
        try:
            _, _, chat_id, operator_id = callback.data.split(':')
            
            if int(operator_id) != user['id']:
                text = "Faqat chat boshlagan operator yopa oladi" if lang == 'uz' else "Только оператор, начавший чат, может его закрыть"
                await callback.answer(text, show_alert=True)
                return
            
            success = await close_chat_session(int(chat_id))
            
            if success:
                await state.set_state(CallCenterStates.main_menu)
                text = "✅ Chat yopildi" if lang == 'uz' else "✅ Чат закрыт"
                await callback.message.edit_text(text)
                
                logger.info(f"Chat session {chat_id} closed by operator {user['id']}")
            else:
                text = "❌ Chatni yopishda xatolik yuz berdi" if lang == 'uz' else "❌ Ошибка при закрытии чата"
                await callback.message.edit_text(text)
            
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Error closing chat: {str(e)}")
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await callback.message.edit_text(error_text)
            await callback.answer()

    @router.callback_query(F.data.startswith("chat:cancel_close:"))
    async def cancel_close_chat(callback: CallbackQuery, state: FSMContext):
        """Cancel closing chat"""
        user = await get_user_by_telegram_id(callback.from_user.id)
        if not user or user['role'] != 'call_center':
            await callback.answer("Access denied", show_alert=True)
            return
        
        lang = user.get('language', 'uz')
        data = await state.get_data()
        
        text = "�� Chat davom etmoqda" if lang == 'uz' else "💬 Чат продолжается"
        await callback.message.edit_text(
            text,
            reply_markup=get_chat_actions_keyboard(str(data.get('chat_id', '')), str(data.get('client_id', '')))
        )
        await callback.answer()

    return router
