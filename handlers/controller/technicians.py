from aiogram import F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from filters.role_filter import RoleFilter
from utils.role_router import get_role_router
from keyboards.controller_buttons import get_technicians_keyboard, get_technician_details_keyboard
from database.base_queries import get_user_by_telegram_id, get_all_technicians, get_technician_details, update_technician_status
from utils.logger import logger

def get_controller_technicians_router():
    router = get_role_router("controller")

    @router.message(F.text.in_(['👨‍🔧 Tekniklar', '👨‍🔧 Техники']))
    async def show_technicians_menu(message: Message, state: FSMContext):
        """Display technicians management menu"""
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user or user['role'] != 'controller':
            return
        
        lang = user.get('language', 'uz')
        
        # Get all technicians
        technicians = await get_all_technicians()
        
        if not technicians:
            no_technicians_text = {
                'uz': "Tekniklar mavjud emas",
                'ru': "Техники отсутствуют"
            }[lang]
            await message.answer(no_technicians_text)
            return
        
        # Create technicians keyboard
        keyboard = get_technicians_keyboard(technicians, lang)
        
        menu_text = {
            'uz': "👨‍🔧 <b>Tekniklar boshqaruvi</b>",
            'ru': "👨‍🔧 <b>Управление техниками</b>"
        }[lang]
        
        await message.answer(menu_text, reply_markup=keyboard)

    @router.callback_query(F.data.startswith('technician:'))
    async def handle_technician_action(callback: CallbackQuery, state: FSMContext):
        """Handle technician-related actions"""
        user = await get_user_by_telegram_id(callback.from_user.id)
        if not user or user['role'] != 'controller':
            return
        
        lang = user.get('language', 'uz')
        action, technician_id = callback.data.split(':')[1:]
        technician_id = int(technician_id)
        
        # Get technician details
        technician = await get_technician_details(technician_id)
        if not technician:
            not_found_text = {
                'uz': "Teknik topilmadi",
                'ru': "Техник не найден"
            }[lang]
            await callback.answer(not_found_text, show_alert=True)
            return
        
        # Handle different actions
        if action == 'view':
            # Show technician details
            details_text = {
                'uz': f"👨‍🔧 <b>Teknik ma'lumotlari</b>\n\n👤 Ism: {technician['full_name']}\n📱 Telefon: {technician['phone_number']}\n📍 Manzil: {technician['address']}\n📊 Status: {technician['status']}",
                'ru': f"👨‍🔧 <b>Информация о технике</b>\n\n👤 Имя: {technician['full_name']}\n📱 Телефон: {technician['phone_number']}\n📍 Адрес: {technician['address']}\n📊 Статус: {technician['status']}"
            }[lang]
            
            keyboard = get_technician_details_keyboard(technician_id, lang)
            await callback.message.edit_text(details_text, reply_markup=keyboard)
        
        elif action == 'status':
            # Update technician status
            await update_technician_status(technician_id, not technician['is_active'])
            await callback.answer(
                {
                    'uz': "Teknik statusi yangilandi",
                    'ru': "Статус техника обновлен"
                }[lang]
            )
            await show_technicians_menu(callback.message, state)
        
        await callback.answer()

    return router
