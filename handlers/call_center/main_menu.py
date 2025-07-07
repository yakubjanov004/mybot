from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from database.base_queries import get_user_by_telegram_id
from database.call_center_queries import get_call_center_dashboard_stats
from keyboards.call_center_buttons import call_center_main_menu_reply
from states.call_center import CallCenterStates
from utils.logger import logger

def get_call_center_main_menu_router():
    router = Router()

    @router.message(F.text.in_(["📞 Call Center", "�� Колл-центр"]))
    async def call_center_start(message: Message, state: FSMContext):
        """Call center main menu"""
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user or user['role'] != 'call_center':
            lang = user.get('language', 'uz') if user else 'uz'
            text = "Sizda ruxsat yo'q." if lang == 'uz' else "У вас нет доступа."
            await message.answer(text)
            return
        
        await state.set_state(CallCenterStates.main_menu)
        lang = user.get('language', 'uz')
        
        # Get dashboard statistics
        try:
            stats = await get_call_center_dashboard_stats()
            
            welcome_text = "📞 Call center paneliga xush kelibsiz!" if lang == 'uz' else "📞 Добро пожаловать в панель call center!"
            
            # Dashboard info
            calls_text = "Bugungi qo'ng'iroqlar" if lang == 'uz' else "Звонки сегодня"
            orders_text = "Bugungi buyurtmalar" if lang == 'uz' else "Заказы сегодня"
            pending_text = "Kutilayotgan" if lang == 'uz' else "Ожидающие"
            chats_text = "Faol chatlar" if lang == 'uz' else "Активные чаты"
            conversion_text = "Konversiya" if lang == 'uz' else "Конверсия"
            
            dashboard_text = f"\n\n📊 Dashboard:\n"
            dashboard_text += f"📞 {calls_text}: {stats.get('calls_today', 0)}\n"
            dashboard_text += f"📋 {orders_text}: {stats.get('orders_today', 0)}\n"
            dashboard_text += f"⏳ {pending_text}: {stats.get('pending_callbacks', 0)}\n"
            dashboard_text += f"💬 {chats_text}: {stats.get('active_chats', 0)}\n"
            dashboard_text += f"🎯 {conversion_text}: {stats.get('conversion_rate', 0)}%"
            
            full_text = welcome_text + dashboard_text
            
        except Exception as e:
            logger.error(f"Error getting dashboard stats: {str(e)}")
            welcome_text = "📞 Call center paneliga xush kelibsiz!" if lang == 'uz' else "📞 Добро пожаловать в панель call center!"
            full_text = welcome_text
        
        await message.answer(
            full_text,
            reply_markup=call_center_main_menu_reply(user['language'])
        )

    @router.callback_query(F.data == "call_center_back")
    async def call_center_back(callback: CallbackQuery, state: FSMContext):
        """Go back to call center main menu"""
        user = await get_user_by_telegram_id(callback.from_user.id)
        if not user or user['role'] != 'call_center':
            await callback.answer("Access denied", show_alert=True)
            return
        
        lang = user.get('language', 'uz')
        await state.set_state(CallCenterStates.main_menu)
        
        try:
            stats = await get_call_center_dashboard_stats()
            
            welcome_text = "📞 Call center paneliga xush kelibsiz!" if lang == 'uz' else "📞 Добро пожаловать в панель call center!"
            
            # Dashboard info
            calls_text = "Bugungi qo'ng'iroqlar" if lang == 'uz' else "Звонки сегодня"
            orders_text = "Bugungi buyurtmalar" if lang == 'uz' else "Заказы сегодня"
            pending_text = "Kutilayotgan" if lang == 'uz' else "Ожидающие"
            chats_text = "Faol chatlar" if lang == 'uz' else "Активные чаты"
            conversion_text = "Konversiya" if lang == 'uz' else "Конверсия"
            
            dashboard_text = f"\n\n📊 Dashboard:\n"
            dashboard_text += f"📞 {calls_text}: {stats.get('calls_today', 0)}\n"
            dashboard_text += f"📋 {orders_text}: {stats.get('orders_today', 0)}\n"
            dashboard_text += f"⏳ {pending_text}: {stats.get('pending_callbacks', 0)}\n"
            dashboard_text += f"💬 {chats_text}: {stats.get('active_chats', 0)}\n"
            dashboard_text += f"🎯 {conversion_text}: {stats.get('conversion_rate', 0)}%"
            
            full_text = welcome_text + dashboard_text
            
        except Exception as e:
            logger.error(f"Error getting dashboard stats: {str(e)}")
            welcome_text = "📞 Call center paneliga xush kelibsiz!" if lang == 'uz' else "📞 Добро пожаловать в панель call center!"
            full_text = welcome_text
        
        await callback.message.edit_text(full_text)
        await callback.answer()

    @router.callback_query(F.data == "cc_back_main")
    async def call_center_back_to_main(callback: CallbackQuery, state: FSMContext):
        """Go back to call center main menu"""
        user = await get_user_by_telegram_id(callback.from_user.id)
        if not user or user['role'] != 'call_center':
            await callback.answer("Access denied", show_alert=True)
            return
        
        lang = user.get('language', 'uz')
        await state.set_state(CallCenterStates.main_menu)
        
        try:
            stats = await get_call_center_dashboard_stats()
            
            welcome_text = "📞 Call center paneliga xush kelibsiz!" if lang == 'uz' else "📞 Добро пожаловать в панель call center!"
            
            # Dashboard info
            calls_text = "Bugungi qo'ng'iroqlar" if lang == 'uz' else "Звонки сегодня"
            orders_text = "Bugungi buyurtmalar" if lang == 'uz' else "Заказы сегодня"
            pending_text = "Kutilayotgan" if lang == 'uz' else "Ожидающие"
            chats_text = "Faol chatlar" if lang == 'uz' else "Активные чаты"
            conversion_text = "Konversiya" if lang == 'uz' else "Конверсия"
            
            dashboard_text = f"\n\n📊 Dashboard:\n"
            dashboard_text += f"📞 {calls_text}: {stats.get('calls_today', 0)}\n"
            dashboard_text += f"📋 {orders_text}: {stats.get('orders_today', 0)}\n"
            dashboard_text += f"⏳ {pending_text}: {stats.get('pending_callbacks', 0)}\n"
            dashboard_text += f"💬 {chats_text}: {stats.get('active_chats', 0)}\n"
            dashboard_text += f"🎯 {conversion_text}: {stats.get('conversion_rate', 0)}%"
            
            full_text = welcome_text + dashboard_text
            
        except Exception as e:
            logger.error(f"Error getting dashboard stats: {str(e)}")
            welcome_text = "📞 Call center paneliga xush kelibsiz!" if lang == 'uz' else "📞 Добро пожаловать в панель call center!"
            full_text = welcome_text
        
        await callback.message.edit_text(full_text)
        await callback.answer()

    @router.callback_query(F.data == "pending_calls")
    async def show_pending_calls(callback: CallbackQuery, state: FSMContext):
        """Show pending calls and callbacks"""
        user = await get_user_by_telegram_id(callback.from_user.id)
        if not user or user['role'] != 'call_center':
            await callback.answer("Access denied", show_alert=True)
            return
        
        lang = user.get('language', 'uz')
        
        try:
            from database.call_center_queries import get_pending_calls
            pending_calls = await get_pending_calls()
            
            pending_text = "⏳ Kutilayotgan qo'ng'iroqlar" if lang == 'uz' else "⏳ Ожидающие звонки"
            text = f"{pending_text}\n\n"
            
            if pending_calls:
                for call in pending_calls:
                    text += f"📞 {call['phone_number']}"
                    if call.get('client_name'):
                        text += f" - {call['client_name']}"
                    text += f"\n⏰ {call['created_at'].strftime('%H:%M')}\n"
                    if call.get('notes'):
                        text += f"📝 {call['notes']}\n"
                    text += "\n"
            else:
                no_calls_text = "Kutilayotgan qo'ng'iroqlar yo'q." if lang == 'uz' else "Ожидающих звонков нет."
                text += no_calls_text
            
            await callback.message.edit_text(text)
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Error getting pending calls: {str(e)}")
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await callback.message.edit_text(error_text)
            await callback.answer()

    return router
