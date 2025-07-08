from aiogram import F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from datetime import datetime, timedelta
from keyboards.technician_buttons import get_back_technician_keyboard, get_reports_keyboard
from states.technician_states import TechnicianStates
from database.technician_queries import get_technician_stats, get_zayavki_by_assigned
from database.base_queries import get_user_by_telegram_id, get_user_lang
from utils.inline_cleanup import cleanup_user_inline_messages, answer_and_cleanup
from utils.logger import setup_logger
from utils.role_router import get_role_router
import functools

def get_technician_reports_router():
    logger = setup_logger('bot.technician.reports')
    router = get_role_router("technician")

    def require_technician(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                message_or_call = args[0] if args else kwargs.get('message_or_call')
                user_id = message_or_call.from_user.id
                user = await get_technician_by_telegram_id(user_id)
                if not user:
                    lang = await get_user_lang(user_id)
                    text = "Sizda montajchi huquqi yo'q." if lang == 'uz' else "У вас нет прав монтажника."
                    if hasattr(message_or_call, 'answer'):
                        await message_or_call.answer(text)
                    else:
                        await message_or_call.message.answer(text)
                    return
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in require_technician decorator: {str(e)}", exc_info=True)
                if args and hasattr(args[0], 'answer'):
                    lang = await get_user_lang(args[0].from_user.id)
                    await args[0].answer("Xatolik yuz berdi!" if lang == 'uz' else "Произошла ошибка!")
        return wrapper

    @router.message(F.text.in_(["📊 Hisobot", "📊 Hisobotlar", "📊 Отчет", "📊 Отчеты"]))
    @require_technician
    async def reports(message: Message, state: FSMContext):
        """Show technician's completed work stats with a single 'Batafsil'/'Подробнее' button (multilingual)"""
        await cleanup_user_inline_messages(message.from_user.id)
        try:
            user = await get_technician_by_telegram_id(message.from_user.id)
            lang = user.get('language', 'uz')
            
            # Get statistics
            stats = await get_technician_stats(user['id'])
            
            if lang == "ru":
                stat_text = (
                    f"📝 Ваши отчеты\n"
                    f"✅ Всего завершено: {stats['total']}\n"
                    f"📅 Сегодня: {stats['today']}\n"
                    f"🗓️ За неделю: {stats['week']}\n"
                    f"📆 За месяц: {stats['month']}\n"
                )
                details_btn_text = "🔎 Подробнее"
            else:
                stat_text = (
                    f"📝 Hisobotlaringiz\n"
                    f"✅ Jami yakunlangan: {stats['total']} ta\n"
                    f"📅 Bugun: {stats['today']} ta\n"
                    f"🗓️ Haftada: {stats['week']} ta\n"
                    f"📆 Oyda: {stats['month']} ta\n"
                )
                details_btn_text = "🔎 Batafsil"
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=details_btn_text, callback_data="techreport_page_1")]
            ])
            await message.answer(stat_text, reply_markup=keyboard)
        except Exception as e:
            logger.error(f"Error in reports: {str(e)}", exc_info=True)
            lang = await get_user_lang(message.from_user.id)
            await message.answer("Xatolik yuz berdi!" if lang == 'uz' else "Произошла ошибка!")

    @router.callback_query(F.data.startswith("techreport_page_"))
    async def techreport_page_callback(callback: CallbackQuery, state: FSMContext):
        await answer_and_cleanup(callback)
        try:
            page = int(callback.data.split('_')[-1])
            user = await get_technician_by_telegram_id(callback.from_user.id)
            lang = user.get('language', 'uz')
            
            # Get completed tasks
            tasks = await get_zayavki_by_assigned(user['id'])
            completed = [t for t in tasks if t['status'] == 'completed']
            
            PAGE_SIZE = 3
            total_pages = (len(completed) + PAGE_SIZE - 1) // PAGE_SIZE
            start = (page - 1) * PAGE_SIZE
            end = start + PAGE_SIZE
            page_tasks = completed[start:end]
            
            if not page_tasks:
                no_reports_text = "Hisobotlar yo'q." if lang == 'uz' else "Отчетов нет."
                await callback.message.edit_text(no_reports_text)
                return
            
            lines = []
            for t in page_tasks:
                date_str = t['completed_at'].strftime('%d.%m.%Y %H:%M') if t.get('completed_at') else '-'
                created_str = t['created_at'].strftime('%d.%m.%Y %H:%M') if t.get('created_at') else '-'
                solution = t.get('solution', '-')
                
                if lang == 'uz':
                    lines.append(
                        f"📝 Vazifa tafsilotlari #{t['id']}\n"
                        f"👤 Foydalanuvchi: {t.get('user_name', '-')}\n"
                        f"📞 Buyurtma holati: {t.get('client_phone', '-')}\n"
                        f"📝 Vazifa tavsifi: {t.get('description', '-')}\n"
                        f"📍 Manzil: {t.get('address', '-')}\n"
                        f"📅 Vazifa sanasi: {created_str}\n"
                        f"📊 Vazifa holati: Yakunlangan\n"
                        f"🕑 Yakunlangan: {date_str}\n"
                        f"💬 Yechim: {solution}\n"
                        "-----------------------------"
                    )
                elif lang == 'ru':
                    lines.append(
                        f"📝 Детали задачи #{t['id']}\n"
                        f"👤 Пользователь: {t.get('user_name', '-')}\n"
                        f"📞 Статус заказа: {t.get('client_phone', '-')}\n"
                        f"📝 Описание задачи: {t.get('description', '-')}\n"
                        f"📍 Адрес: {t.get('address', '-')}\n"
                        f"📅 Дата задачи: {created_str}\n"
                        f"📊 Статус задачи: Завершено\n"
                        f"🕑 Завершено: {date_str}\n"
                        f"💬 Решение: {solution}\n"
                        "-----------------------------"
                    )
            
            reports_list_text = "Hisobotlar ro'yxati:" if lang == 'uz' else "Список отчетов:"
            text = reports_list_text + "\n\n" + "\n".join(lines)
            
            # Navigation buttons
            nav_buttons = []
            if page > 1:
                nav_buttons.append(InlineKeyboardButton(
                    text="⬅️ Orqaga" if lang == "uz" else "⬅️ Назад",
                    callback_data=f"techreport_page_{page-1}"
                ))
            if end < len(completed):
                nav_buttons.append(InlineKeyboardButton(
                    text="Oldinga ➡️" if lang == "uz" else "Вперёд ➡️",
                    callback_data=f"techreport_page_{page+1}"
                ))
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[nav_buttons] if nav_buttons else [])
            await callback.message.edit_text(text, reply_markup=keyboard)
        except Exception as e:
            logger.error(f"Error in report_details_page: {str(e)}", exc_info=True)
            await callback.message.answer("Xatolik yuz berdi!")

    return router
