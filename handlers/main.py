from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from .admin import router as admin_router
from .client import router as client_router
from .technician import router as technician_router
from .manager import router as manager_router
from database.queries import get_user_by_telegram_id, create_user, db_manager
from utils.logger import logger
from aiogram.fsm.state import State, StatesGroup
from utils.inline_cleanup import safe_remove_inline
from utils.get_lang import get_user_lang
from utils.get_role import get_user_role
from .call_center import call_center_start as call_center_start
from .controllers import controllers_start as controller_start
from .warehouse import warehouse_start as warehouse_start

router = Router()

@router.message(Command("start"))
async def unified_start(message: Message, state: FSMContext):
    """Unified start command handler that routes based on user role"""
    try:
        # State ni tozalash
        await state.clear()
        
        # Foydalanuvchini tekshirish
        db_user = await get_user_by_telegram_id(message.from_user.id)
        logger.info(f"Unified start - Foydalanuvchi tekshirildi: {message.from_user.id}, natija: {db_user}")
        
        if db_user:
            # Mavjud foydalanuvchi - roliga qarab yo'naltirish
            role = db_user.get('role')
            
            if role == 'admin':
                # Admin uchun admin handler ga yo'naltirish
                from .admin import cmd_start as admin_start
                await admin_start(message, state)
                return
            elif role == 'technician':
                # Technician uchun technician handler ga yo'naltirish
                from .technician import cmd_start as technician_start
                await technician_start(message, state)
                return
            elif role == 'manager':
                # Manager uchun manager handler ga yo'naltirish
                from .manager import manager_menu
                await manager_menu(message)
                return
            elif role == 'client':
                # Client uchun client handler ga yo'naltirish
                from .client import cmd_start as client_start
                await client_start(message, state)
                return
            elif role == 'call_center':
                # Call center uchun call_center handler ga yo'naltirish
                await call_center_start(message, state)
                return
            elif role == 'controller':
                # Controller uchun controller handler ga yo'naltirish
                await controller_start(message, state)
                return
            elif role == 'warehouse':
                # Warehouse uchun warehouse handler ga yo'naltirish
                await warehouse_start(message, state)
                return
            else:
                # Noma'lum ro'l uchun client handler ga yo'naltirish (fallback)
                logger.warning(f"Noma'lum ro'l uchun client handler ga yo'naltirildi: {role}")
                from .client import cmd_start as client_start
                await client_start(message, state)
                return
        else:
            # Yangi foydalanuvchi - client sifatida yaratish
            new_user = await create_user(
                message.from_user.id,
                message.from_user.full_name,
                role='client'
            )
            logger.info(f"Yangi foydalanuvchi yaratildi: {new_user}")
            
            from .client import cmd_start as client_start
            await client_start(message, state)
        
        logger.info(f"Unified start buyrug'i muvaffaqiyatli yakunlandi: {message.from_user.id}")
        
    except Exception as e:
        logger.error(f"Unified start buyrug'ida xatolik: {str(e)}", exc_info=True)
        lang = await get_user_lang(message.from_user.id)
        await safe_remove_inline(message)
        text = "Xatolik yuz berdi. Iltimos, qayta urinib ko'ring." if lang == 'uz' else "Произошла ошибка. Пожалуйста, попробуйте еще раз."
        await message.answer(text)

# Include all other routers (language_router is already included in main.py)
router.include_router(manager_router)
router.include_router(client_router) 
router.include_router(admin_router)
router.include_router(technician_router)

class ManagerStates(StatesGroup):
    # ... mavjud statelar ...
    ASSIGN_TECHNICIAN = State()
