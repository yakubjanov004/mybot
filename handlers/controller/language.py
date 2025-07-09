from aiogram import F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from filters.role_filter import RoleFilter
from utils.role_router import get_role_router
from database.base_queries import get_user_by_telegram_id, update_user_language
from keyboards.controllers_buttons import language_keyboard, controllers_main_menu
from states.controllers_states import ControllersStates
from utils.logger import logger

def get_controller_language_router():
    router = get_role_router("controller")

    @router.message(F.text.in_(["🌐 Til o'zgartirish", "🌐 Изменить язык"]))
    async def change_language_menu(message: Message, state: FSMContext):
        """Til o'zgartirish menyusi"""
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user or user['role'] != 'controller':
            return
        
        lang = user.get('language', 'uz')
        await state.set_state(ControllersStates.selecting_language)
        
        if lang == 'uz':
            text = """🌐 <b>Til tanlash</b>

Hozirgi til: O'zbek tili 🇺🇿

Kerakli tilni tanlang:"""
        else:
            text = """🌐 <b>Выбор языка</b>

Текущий язык: Русский язык 🇷🇺

Выберите нужный язык:"""
        
        await message.answer(
            text,
            reply_markup=language_keyboard(),
            parse_mode='HTML'
        )

    @router.message(F.text.in_(["🇺🇿 O'zbek tili", "🇺🇿 Узбекский язык"]))
    async def set_uzbek_language(message: Message, state: FSMContext):
        """O'zbek tilini o'rnatish"""
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user or user['role'] != 'controller':
            return
        
        success = await update_user_language(user['id'], 'uz')
        
        if success:
            text = """✅ <b>Til muvaffaqiyatli o'zgartirildi!</b>

Hozir siz O'zbek tilidan foydalanmoqdasiz 🇺🇿

Bosh menyuga qaytish uchun tugmani bosing."""
            
            await message.answer(
                text,
                reply_markup=controllers_main_menu('uz'),
                parse_mode='HTML'
            )
            await state.set_state(ControllersStates.main_menu)
            logger.info(f"Controller {user['id']} changed language to Uzbek")
        else:
            text = "❌ Tilni o'zgartirishda xatolik yuz berdi."
            await message.answer(text)

    @router.message(F.text.in_(["🇷🇺 Русский язык", "🇷🇺 Rus tili"]))
    async def set_russian_language(message: Message, state: FSMContext):
        """Rus tilini o'rnatish"""
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user or user['role'] != 'controller':
            return
        
        success = await update_user_language(user['id'], 'ru')
        
        if success:
            text = """✅ <b>Язык успешно изменен!</b>

Теперь вы используете русский язык 🇷🇺

Нажмите кнопку для возврата в главное меню."""
            
            await message.answer(
                text,
                reply_markup=controllers_main_menu('ru'),
                parse_mode='HTML'
            )
            await state.set_state(ControllersStates.main_menu)
            logger.info(f"Controller {user['id']} changed language to Russian")
        else:
            text = "❌ Произошла ошибка при изменении языка."
            await message.answer(text)

    @router.message(F.text.in_(["◀️ Orqaga", "◀️ Назад"]))
    async def back_from_language(message: Message, state: FSMContext):
        """Til menyusidan orqaga qaytish"""
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user or user['role'] != 'controller':
            return
        
        lang = user.get('language', 'uz')
        await state.set_state(ControllersStates.main_menu)
        
        if lang == 'uz':
            welcome_text = "🎛️ Nazoratchi paneliga xush kelibsiz!"
        else:
            welcome_text = "🎛️ Добро пожаловать в панель контроллера!"
        
        await message.answer(
            welcome_text,
            reply_markup=controllers_main_menu(lang)
        )

    return router
