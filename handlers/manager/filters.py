from aiogram import F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from datetime import date, timedelta, datetime
from utils.inline_cleanup import answer_and_cleanup, safe_delete_message
from keyboards.manager_buttons import (
    get_manager_filter_reply_keyboard,
    get_status_filter_inline_keyboard,
    get_date_filter_inline_keyboard,
    get_tech_filter_inline_keyboard,
    get_pagination_inline_keyboard
)
from database.manager_queries import get_filtered_applications
from database.base_queries import get_user_by_telegram_id, get_zayavka_by_id
from database.base_queries import get_user_lang
from utils.logger import setup_logger
from utils.role_router import get_role_router
from loader import bot

def get_manager_filters_router():
    logger = setup_logger('bot.manager.filters')
    router = get_role_router("manager")

    @router.message(F.text.in_(["🔍 Filtrlar", "🔍 Фильтры"]))
    async def show_filter_menu(message: Message, state: FSMContext):
        lang = await get_user_lang(message.from_user.id)
        await message.answer(
            "Filtrlash uchun parametrni tanlang:" if lang == 'uz' else "Выберите параметр для фильтрации:",
            reply_markup=get_manager_filter_reply_keyboard(lang)
        )
        await state.set_data({"filter_step": "main"})

    @router.message(lambda m: m.text in ["🟢 Status bo'yicha", "🟢 По статусу"])
    async def filter_by_status(message: Message, state: FSMContext):
        lang = await get_user_lang(message.from_user.id)
        try:
            await message.delete()
        except Exception:
            pass
        await message.answer(
            "Statusni tanlang:" if lang == 'uz' else "Выберите статус:",
            reply_markup=None
        )
        msg = await message.answer(
            "⬇️", reply_markup=get_status_filter_inline_keyboard(lang)
        )
        await state.set_data({"filter_step": "status", "last_result_message_id": msg.message_id})

    @router.message(lambda m: m.text in ["📅 Sana bo'yicha", "📅 По дате"])
    async def filter_by_date(message: Message, state: FSMContext):
        lang = await get_user_lang(message.from_user.id)
        try:
            await message.delete()
        except Exception:
            pass
        await message.answer(
            "Sanani tanlang:" if lang == 'uz' else "Выберите дату:",
            reply_markup=None
        )
        msg = await message.answer(
            "⬇️", reply_markup=get_date_filter_inline_keyboard(lang)
        )
        await state.set_data({"filter_step": "date", "last_result_message_id": msg.message_id})

    @router.message(lambda m: m.text in ["👨‍🔧 Texnik biriktirilganligi bo'yicha", "👨‍🔧 По назначению техника"])
    async def filter_by_tech(message: Message, state: FSMContext):
        lang = await get_user_lang(message.from_user.id)
        try:
            await message.delete()
        except Exception:
            pass
        await message.answer(
            "Texnik biriktirilganlikni tanlang:" if lang == 'uz' else "Выберите назначение техника:",
            reply_markup=None
        )
        msg = await message.answer(
            "⬇️", reply_markup=get_tech_filter_inline_keyboard(lang)
        )
        await state.set_data({"filter_step": "tech", "last_result_message_id": msg.message_id})

    @router.message(lambda m: m.text in ["◀️ Orqaga", "◀️ Назад"])
    async def filter_back_to_main(message: Message, state: FSMContext):
        lang = await get_user_lang(message.from_user.id)
        chat_id = message.chat.id
        try:
            await message.delete()
        except Exception:
            pass
        await bot.send_message(
            chat_id,
            "Filtr menyusiga qaytdingiz." if lang == 'uz' else "Вы вернулись в меню фильтров.",
            reply_markup=get_manager_filter_reply_keyboard(lang)
        )
        await state.set_data({"filter_step": "main"})

    @router.callback_query(F.data.startswith("filter_status_"))
    async def filter_status_callback(callback: CallbackQuery, state: FSMContext):
        lang = await get_user_lang(callback.from_user.id)
        status = callback.data.split('_')[-1]
        page = 1
        result = await get_filtered_applications(
            pool=bot.db,
            statuses=[status] if status != 'all' else None,
            page=page,
            limit=5
        )
        applications = result.get('applications', [])
        total = result.get('total', 0)
        total_pages = result.get('total_pages', 1)
        current_page = result.get('page', 1)
        start = (current_page - 1) * 5 + 1
        end = start + len(applications) - 1
        text = f"🟢 Status: {status.capitalize()}\nKo'rsatilmoqda: {start}-{end} / {total} (Jami: {total})\n\n"
        for app in applications:
            text += f"ID: {app['id']} | Mijoz: {app['user_name']} | Tel: {app['client_phone']}\nManzil: {app['address']}\nIzoh: {app['description']}\nTexnik: {app.get('technician_name', 'Biriktirilmagan')}\nYaratilgan: {app['created_at']}\n━━━━━━━━━━━━━━━━━━━━━━\n"
        has_prev = current_page > 1
        has_next = current_page < total_pages
        await callback.message.edit_text(
            text,
            reply_markup=get_pagination_inline_keyboard(current_page, total_pages, lang, has_prev, has_next)
        )
        await state.set_data({"filter_step": "status_result", "status": status, "page": current_page})

    @router.callback_query(F.data.startswith("filter_date_"))
    async def filter_date_callback(callback: CallbackQuery, state: FSMContext):
        lang = await get_user_lang(callback.from_user.id)
        date_type = callback.data.split('_')[-1]
        today = date.today()
        if date_type == 'today':
            date_from = date_to = today
        elif date_type == 'yesterday':
            date_from = date_to = today - timedelta(days=1)
        elif date_type == 'week':
            date_from = today - timedelta(days=today.weekday())
            date_to = today
        elif date_type == 'month':
            date_from = today.replace(day=1)
            date_to = today
        else:
            date_from = date_to = today

        await state.update_data(date_from=date_from, date_to=date_to)

        result = await get_filtered_applications(
            pool=bot.db,
            date_from=date_from,
            date_to=date_to,
            page=1,
            limit=5
        )
        applications = result.get('applications', [])
        total = result.get('total', 0)
        total_pages = result.get('total_pages', 1)
        current_page = result.get('page', 1)
        start = (current_page - 1) * 5 + 1
        end = start + len(applications) - 1
        text = f"📅 Sana: {date_type.capitalize()}\nKo'rsatilmoqda: {start}-{end} / {total} (Jami: {total})\n\n"
        for app in applications:
            text += f"ID: {app['id']} | Mijoz: {app['user_name']} | Tel: {app['client_phone']}\nManzil: {app['address']}\nIzoh: {app['description']}\nTexnik: {app.get('technician_name', 'Biriktirilmagan')}\nYaratilgan: {app['created_at']}\n━━━━━━━━━━━━━━━━━━━━━━\n"
        has_prev = current_page > 1
        has_next = current_page < total_pages
        await callback.message.edit_text(
            text,
            reply_markup=get_pagination_inline_keyboard(current_page, total_pages, lang, has_prev, has_next)
        )
        await state.set_data({"filter_step": "date_result", "date_type": date_type, "date_from": str(date_from), "date_to": str(date_to), "page": current_page})

    @router.callback_query(F.data.startswith("filter_page_prev_"))
    async def filter_page_prev_callback(callback: CallbackQuery, state: FSMContext):
        data = await state.get_data()
        step = data.get("filter_step")
        lang = await get_user_lang(callback.from_user.id)
        page = int(callback.data.split('_')[-1])
        if step == "status_result":
            status = data.get("status")
            result = await get_filtered_applications(
                pool=bot.db,
                statuses=[status] if status != 'all' else None,
                page=page,
                limit=5
            )
        elif step == "date_result":
            date_from = data.get("date_from")
            date_to = data.get("date_to")
            date_type = data.get("date_type")
            result = await get_filtered_applications(
                pool=bot.db,
                date_from=date_from,
                date_to=date_to,
                page=page,
                limit=5
            )
        else:
            return
        applications = result.get('applications', [])
        total = result.get('total', 0)
        total_pages = result.get('total_pages', 1)
        current_page = result.get('page', 1)
        start = (current_page - 1) * 5 + 1
        end = start + len(applications) - 1
        if step == "status_result":
            text = f"🟢 Status: {data.get('status').capitalize()}\nKo'rsatilmoqda: {start}-{end} / {total} (Jami: {total})\n\n"
        elif step == "date_result":
            text = f"📅 Sana: {data.get('date_type').capitalize()}\nKo'rsatilmoqda: {start}-{end} / {total} (Jami: {total})\n\n"
        else:
            text = ""
        for app in applications:
            text += f"ID: {app['id']} | Mijoz: {app['user_name']} | Tel: {app['client_phone']}\nManzil: {app['address']}\nIzoh: {app['description']}\nTexnik: {app.get('technician_name', 'Biriktirilmagan')}\nYaratilgan: {app['created_at']}\n━━━━━━━━━━━━━━━━━━━━━━\n"
        has_prev = current_page > 1
        has_next = current_page < total_pages
        await callback.message.edit_text(
            text,
            reply_markup=get_pagination_inline_keyboard(current_page, total_pages, lang, has_prev, has_next)
        )
        await state.set_data({**data, "page": current_page})

    @router.callback_query(F.data.startswith("filter_page_next_"))
    async def filter_page_next_callback(callback: CallbackQuery, state: FSMContext):
        data = await state.get_data()
        step = data.get("filter_step")
        lang = await get_user_lang(callback.from_user.id)
        page = int(callback.data.split('_')[-1])
        if step == "status_result":
            status = data.get("status")
            result = await get_filtered_applications(
                pool=bot.db,
                statuses=[status] if status != 'all' else None,
                page=page,
                limit=5
            )
        elif step == "date_result":
            date_from = data.get("date_from")
            date_to = data.get("date_to")
            date_type = data.get("date_type")
            result = await get_filtered_applications(
                pool=bot.db,
                date_from=date_from,
                date_to=date_to,
                page=page,
                limit=5
            )
        else:
            return
        applications = result.get('applications', [])
        total = result.get('total', 0)
        total_pages = result.get('total_pages', 1)
        current_page = result.get('page', 1)
        start = (current_page - 1) * 5 + 1
        end = start + len(applications) - 1
        if step == "status_result":
            text = f"🟢 Status: {data.get('status').capitalize()}\nKo'rsatilmoqda: {start}-{end} / {total} (Jami: {total})\n\n"
        elif step == "date_result":
            text = f"📅 Sana: {data.get('date_type').capitalize()}\nKo'rsatilmoqda: {start}-{end} / {total} (Jami: {total})\n\n"
        else:
            text = ""
        for app in applications:
            text += f"ID: {app['id']} | Mijoz: {app['user_name']} | Tel: {app['client_phone']}\nManzil: {app['address']}\nIzoh: {app['description']}\nTexnik: {app.get('technician_name', 'Biriktirilmagan')}\nYaratilgan: {app['created_at']}\n━━━━━━━━━━━━━━━━━━━━━━\n"
        has_prev = current_page > 1
        has_next = current_page < total_pages
        await callback.message.edit_text(
            text,
            reply_markup=get_pagination_inline_keyboard(current_page, total_pages, lang, has_prev, has_next)
        )
        await state.set_data({**data, "page": current_page})

    @router.callback_query(F.data == "filter_back")
    async def filter_back_inline_callback(callback: CallbackQuery, state: FSMContext):
        lang = await get_user_lang(callback.from_user.id)
        data = await state.get_data()
        step = data.get("filter_step")
        # Status bo'yicha inlinega qaytish
        if step == "status_result":
            await callback.message.edit_text(
                "Statusni tanlang:" if lang == 'uz' else "Выберите статус:",
                reply_markup=get_status_filter_inline_keyboard(lang)
            )
            await state.set_data({"filter_step": "status"})
        # Sana bo'yicha inlinega qaytish
        elif step == "date_result":
            await callback.message.edit_text(
                "Sanani tanlang:" if lang == 'uz' else "Выберите дату:",
                reply_markup=get_date_filter_inline_keyboard(lang)
            )
            await state.set_data({"filter_step": "date"})
        # Texnik bo'yicha inlinega qaytish
        elif step == "tech_result":
            await callback.message.edit_text(
                "Texnik biriktirilganligini tanlang:" if lang == 'uz' else "Выберите назначение техника:",
                reply_markup=get_tech_filter_inline_keyboard(lang)
            )
            await state.set_data({"filter_step": "tech"})
        # Aks holda, faqat Filtrlar replyga qaytadi
        else:
            await callback.message.delete()
            await callback.message.answer(
                "Filtrlash uchun parametrni tanlang:" if lang == 'uz' else "Выберите параметр для фильтрации:",
                reply_markup=get_manager_filter_reply_keyboard(lang)
            )
            await state.clear()

    @router.callback_query(F.data.startswith("view_application_"))
    async def view_filtered_application(callback: CallbackQuery):
        await answer_and_cleanup(callback, cleanup_after=True)
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass
        """Show detailed information about filtered application"""
        lang = await get_user_lang(callback.from_user.id)
        
        try:
            from database.queries import get_zayavka_by_id
            app_id = int(callback.data.replace("view_application_", ""))
            app = await get_zayavka_by_id(app_id)
            
            if not app:
                await callback.answer(f"{'Ariza topilmadi.' if lang == 'uz' else 'Заявка не найдена.'}", show_alert=True)
                return
            
            status_emoji = {
                'new': '🆕',
                'in_progress': '⏳',
                'completed': '✅',
                'cancelled': '❌'
            }.get(app.get('status', 'new'), '')
            
            # 2ta tilda app_text_uz va app_text_ru chiroyli formatda

            app_text_uz = (
                f" <b>Ariza ma'lumotlari</b>\n\n"
                f" <b>ID:</b> {app['id']}\n"
                f" <b>Mijoz:</b> {app.get('user_name', '-')}\n"
                f" <b>Telefon:</b> {app.get('client_phone', '-')}\n"
                f" <b>Tavsif:</b> {app.get('description', '-')}\n"
                f" <b>Manzil:</b> {app.get('address', '-')}\n"
                f" <b>Sana:</b> {app.get('created_at', '-')}\n"
                f" <b>Status:</b> {status_emoji} {app.get('status', '-')}"
            )

            app_text_ru = (
                f" <b>Информация о заявке</b>\n\n"
                f" <b>ID:</b> {app['id']}\n"
                f" <b>Клиент:</b> {app.get('user_name', '-')}\n"
                f" <b>Телефон:</b> {app.get('client_phone', '-')}\n"
                f" <b>Описание:</b> {app.get('description', '-')}\n"
                f" Адрес: {app.get('address', '-')}\n"
                f" Дата: {app.get('created_at', '-')}\n"
                f" Статус: {status_emoji} {app.get('status', '-')}"
            )

            app_text = app_text_uz if lang == 'uz' else app_text_ru
            
            # Show application info with back to filter button
            await callback.message.edit_text(
                app_text,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                    InlineKeyboardButton(
                        text=f" {'Filtrlashga qaytish' if lang == 'uz' else 'Вернуться к фильтрам'}", 
                        callback_data="filter_clear"
                    )
                ]])
            )
            
        except Exception as e:
            logger.error(f"Error viewing filtered application: {str(e)}", exc_info=True)
            await callback.answer(f"{'Xatolik yuz berdi' if lang == 'uz' else 'Произошла ошибка'}", show_alert=True)
        
        await callback.answer()

    @router.callback_query(F.data.startswith("date_result_page_"))
    async def date_result_pagination_callback(callback: CallbackQuery, state: FSMContext):
        lang = await get_user_lang(callback.from_user.id)
        data = await state.get_data()
        page = int(callback.data.split('_')[-1])
        date_from = data.get('date_from')
        date_to = data.get('date_to')
        if isinstance(date_from, str):
            date_from = datetime.strptime(date_from, "%Y-%m-%d").date()
        if isinstance(date_to, str):
            date_to = datetime.strptime(date_to, "%Y-%m-%d").date()
        result = await get_filtered_applications(
            pool=bot.db,
            date_from=date_from,
            date_to=date_to,
            page=page,
            limit=5
        )
        applications = result.get('applications', [])
        total = result.get('total', 0)
        total_pages = result.get('total_pages', 1)
        current_page = result.get('page', 1)
        start = (current_page - 1) * 5 + 1
        end = start + len(applications) - 1
        text = f"📅 Sana: {data.get('date_type').capitalize()}\nKo'rsatilmoqda: {start}-{end} / {total} (Jami: {total})\n\n"
        for app in applications:
            text += f"ID: {app['id']} | Mijoz: {app['user_name']} | Tel: {app['client_phone']}\nManzil: {app['address']}\nIzoh: {app['description']}\nTexnik: {app.get('technician_name', 'Biriktirilmagan')}\nYaratilgan: {app['created_at']}\n━━━━━━━━━━━━━━━━━━━━━━\n"
        has_prev = current_page > 1
        has_next = current_page < total_pages
        await callback.message.edit_text(
            text,
            reply_markup=get_pagination_inline_keyboard(current_page, total_pages, lang, has_prev, has_next)
        )
        await state.set_data({**data, "page": current_page})

    @router.callback_query(F.data.in_(["filter_tech_assigned", "filter_tech_unassigned"]))
    async def filter_tech_callback(callback: CallbackQuery, state: FSMContext):
        lang = await get_user_lang(callback.from_user.id)
        tech_type = callback.data.split('_')[-1]  # 'assigned' yoki 'unassigned'
        assigned_only = True if tech_type == 'assigned' else False
        page = 1
        result = await get_filtered_applications(
            pool=bot.db,
            assigned_only=assigned_only,
            page=page,
            limit=5
        )
        applications = result.get('applications', [])
        total = result.get('total', 0)
        total_pages = result.get('total_pages', 1)
        current_page = result.get('page', 1)
        start = (current_page - 1) * 5 + 1
        end = start + len(applications) - 1
        text = f"👨‍🔧 Texnik: {'Biriktirilgan' if assigned_only else 'Biriktirilmagan'}\nKo'rsatilmoqda: {start}-{end} / {total} (Jami: {total})\n\n"
        for app in applications:
            text += f"ID: {app['id']} | Mijoz: {app['user_name']} | Tel: {app['client_phone']}\nManzil: {app['address']}\nIzoh: {app['description']}\nTexnik: {app.get('technician_name', 'Biriktirilmagan')}\nYaratilgan: {app['created_at']}\n━━━━━━━━━━━━━━━━━━━━━━\n"
        has_prev = current_page > 1
        has_next = current_page < total_pages
        await callback.message.edit_text(
            text,
            reply_markup=get_pagination_inline_keyboard(current_page, total_pages, lang, has_prev, has_next)
        )
        await state.set_data({"filter_step": "tech_result", "tech_type": tech_type, "page": current_page})

    return router
