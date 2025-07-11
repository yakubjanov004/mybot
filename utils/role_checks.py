from functools import wraps
from typing import List, Union, Callable, Any
from aiogram.types import Message, CallbackQuery
from aiogram import Bot

from database.base_queries import get_user_by_telegram_id, get_user_lang
from config import config
from utils.logger import setup_module_logger

logger = setup_module_logger("role_checks")

async def get_user_role(user_id: int) -> str:
    """Get user role from database"""
    try:
        # Check if user is admin first
        if config.is_admin(user_id):
            return 'admin'
        
        # Get from database
        db_user = await get_user_by_telegram_id(user_id)
        if db_user and db_user.get('role'):
            return db_user['role']
        
        return 'client'
        
    except Exception as e:
        logger.error(f"Error getting user role for {user_id}: {str(e)}")
        return 'client'

def admin_only(handler: Callable) -> Callable:
    """Decorator to restrict access to admins only"""
    @wraps(handler)
    async def wrapper(update: Union[Message, CallbackQuery], *args, **kwargs):
        try:
            user_id = update.from_user.id
            
            # Check if user is admin
            if not config.is_admin(user_id):
                logger.warning(f"Non-admin user {user_id} tried to access admin function")
                
                # Get user language for error message
                try:
                    lang = await get_user_lang(user_id)
                except:
                    lang = 'ru'
                
                error_text = (
                    "❌ Sizda bu funksiyaga kirish huquqi yo'q!" 
                    if lang == 'uz' 
                    else "❌ У вас нет доступа к этой функции!"
                )
                
                if isinstance(update, Message):
                    await update.answer(error_text)
                else:  # CallbackQuery
                    await update.answer(error_text, show_alert=True)
                
                return None
            
            # User is admin, proceed with handler
            return await handler(update, *args, **kwargs)
            
        except Exception as e:
            logger.error(f"Error in admin_only decorator: {str(e)}")
            
            error_text = "Xatolik yuz berdi!" if hasattr(update, 'from_user') else "Произошла ошибка!"
            
            if isinstance(update, Message):
                await update.answer(error_text)
            else:  # CallbackQuery
                await update.answer(error_text, show_alert=True)
            
            return None
    
    return wrapper

def role_required(required_roles: List[str]):
    """Decorator to require specific roles"""
    def decorator(handler: Callable) -> Callable:
        @wraps(handler)
        async def wrapper(update: Union[Message, CallbackQuery], *args, **kwargs):
            try:
                user_id = update.from_user.id
                user_role = await get_user_role(user_id)
                
                if user_role not in required_roles:
                    logger.warning(f"User {user_id} with role {user_role} tried to access function requiring {required_roles}")
                    
                    try:
                        lang = await get_user_lang(user_id)
                    except:
                        lang = 'ru'
                    
                    error_text = (
                        "❌ Sizda bu funksiyaga kirish huquqi yo'q!" 
                        if lang == 'uz' 
                        else "❌ У вас нет доступа к этой функции!"
                    )
                    
                    if isinstance(update, Message):
                        await update.answer(error_text)
                    else:  # CallbackQuery
                        await update.answer(error_text, show_alert=True)
                    
                    return None
                
                return await handler(update, *args, **kwargs)
                
            except Exception as e:
                logger.error(f"Error in role_required decorator: {str(e)}")
                return None
        
        return wrapper
    return decorator

def manager_or_admin(handler: Callable) -> Callable:
    """Decorator for manager, junior_manager or admin access"""
    return role_required(['admin', 'manager', 'junior_manager'])(handler)

def staff_only(handler: Callable) -> Callable:
    """Decorator for staff access (non-client roles)"""
    return role_required(['admin', 'manager', 'junior_manager', 'technician', 'call_center', 'controller', 'warehouse'])(handler)

def client_only(handler: Callable) -> Callable:
    """Decorator to restrict access to clients only"""
    @wraps(handler)
    async def wrapper(update: Union[Message, CallbackQuery], *args, **kwargs):
        try:
            user_id = update.from_user.id
            user_role = await get_user_role(user_id)
            if user_role != 'client':
                logger.warning(f"Non-client user {user_id} (role: {user_role}) tried to access client function")
                try:
                    lang = await get_user_lang(user_id)
                except:
                    lang = 'ru'
                error_text = (
                    "❌ Bu funksiya faqat mijozlar uchun!" if lang == 'uz'
                    else "❌ Эта функция только для клиентов!"
                )
                if isinstance(update, Message):
                    await update.answer(error_text)
                else:
                    await update.answer(error_text, show_alert=True)
                return None
            return await handler(update, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error in client_only decorator: {str(e)}")
            error_text = "Xatolik yuz berdi!" if hasattr(update, 'from_user') else "Произошла ошибка!"
            if isinstance(update, Message):
                await update.answer(error_text)
            else:
                await update.answer(error_text, show_alert=True)
            return None
    return wrapper

async def check_user_access(user_id: int, required_roles: List[str]) -> bool:
    """Check if user has required role access"""
    try:
        user_role = await get_user_role(user_id)
        return user_role in required_roles
    except Exception as e:
        logger.error(f"Error checking user access: {str(e)}")
        return False

async def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    return config.is_admin(user_id)

async def is_manager_or_admin(user_id: int) -> bool:
    """Check if user is manager, junior_manager or admin"""
    return await check_user_access(user_id, ['admin', 'manager', 'junior_manager'])

async def is_staff(user_id: int) -> bool:
    """Check if user is staff member"""
    return await check_user_access(user_id, ['admin', 'manager', 'junior_manager', 'technician', 'call_center', 'controller', 'warehouse'])
