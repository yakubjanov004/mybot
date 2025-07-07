from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from datetime import date, timedelta
from utils.inline_cleanup import answer_and_cleanup, safe_delete_message
from keyboards.manager_buttons import get_filter_keyboard
from database.manager_queries import get_filtered_applications
from database.base_queries import get_user_by_telegram_id, get_zayavka_by_id
from database.base_queries import get_user_lang
from utils.logger import setup_logger

def get_manager_filters_router():
    logger = setup_logger('bot.manager.filters')
    router = Router()

    @router.message(lambda m: m.text in [" Filtrlar", " Фильтры"])
    async def show_filter_menu(message: Message, state: FSMContext):
        await safe_delete_message(message.bot, message.chat.id, message.message_id)
        # Delete previous menu message if exists
        data = await state.get_data()
        last_msg_id = data.get('last_menu_msg_id')
        if last_msg_id:
            try:
                await message.bot.delete_message(chat_id=message.chat.id, message_id=last_msg_id)
            except Exception:
                pass
        lang = await get_user_lang(message.from_user.id)
        try:
            filter_text = f" {'Kerakli filtrlarni tanlang:' if lang == 'uz' else 'Выберите нужные фильтры:'}"
            sent_msg = await message.answer(filter_text, reply_markup=get_filter_keyboard(lang))
            await state.update_data(last_menu_msg_id=sent_msg.message_id)
        except Exception as e:
            logger.error(f"Filter menu error: {str(e)}", exc_info=True)
            await message.answer(f"{'Xatolik yuz berdi' if lang == 'uz' else 'Произошла ошибка'}")

    @router.callback_query(F.data.startswith("filter_"))
    async def process_filter(callback: CallbackQuery, state: FSMContext):
        await answer_and_cleanup(callback, cleanup_after=True)
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass
        lang = await get_user_lang(callback.from_user.id)
        try:
            parts = callback.data.split('_')
            filter_type = parts[1]
            page = 1
            if len(parts) > 2 and parts[-1].isdigit():
                page = int(parts[-1])
            result = None
            filter_kwargs = {'page': page, 'limit': 5}
            # --- Filter label logic ---
            filter_label = ""
            if filter_type == 'status':
                status = '_'.join(parts[2:-1]) if parts[-1].isdigit() else '_'.join(parts[2:])
                if status == 'all':
                    filter_label = f" {'Barcha statuslar' if lang == 'uz' else 'Все статусы'}"
                    result = await get_filtered_applications(**filter_kwargs)
                else:
                    status_emoji = {
                        'new': '',
                        'in_progress': '',
                        'completed': '',
                        'cancelled': ''
                    }.get(status, '')
                    status_label = {
                        'new': 'Yangi' if lang == 'uz' else 'Новый',
                        'in_progress': 'Jarayonda' if lang == 'uz' else 'В процессе',
                        'completed': 'Yakunlandi' if lang == 'uz' else 'Завершено',
                        'cancelled': 'Bekor qilindi' if lang == 'uz' else 'Отменено'
                    }.get(status, status)
                    filter_label = f"{status_emoji} {'Status:' if lang == 'uz' else 'Статус:'} {status_label}"
                    result = await get_filtered_applications(statuses=[status], **filter_kwargs)
            elif filter_type == 'date':
                date_type = parts[2]
                today = date.today()
                # 2ta tilda (uz va ru) date_labels lug'ati va ishlatishda to'g'ri tilni tanlash
                date_labels = {
                    'today': {
                        'uz': " Bugun",
                        'ru': " Сегодня"
                    },
                    'yesterday': {
                        'uz': " Kecha",
                        'ru': " Вчера"
                    },
                    'week': {
                        'uz': " Bu hafta",
                        'ru': " На этой неделе"
                    },
                    'month': {
                        'uz': " Bu oy",
                        'ru': " В этом месяце"
                    }
                }
                filter_label = date_labels.get(date_type, {}).get(lang, f" {date_type}")
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
                result = await get_filtered_applications(date_from=date_from, date_to=date_to, **filter_kwargs)
            elif filter_type == 'tech':
                tech_type = parts[2]
                if tech_type == 'assigned':
                    filter_label = f" {'Biriktirilgan' if lang == 'uz' else 'Назначенные'}"
                    result = await get_filtered_applications(assigned_only=True, **filter_kwargs)
                elif tech_type == 'unassigned':
                    filter_label = f" {'Biriktirilmagan' if lang == 'uz' else 'Не назначенные'}"
                    result = await get_filtered_applications(technician_id=0, **filter_kwargs)
            elif filter_type == 'clear':
                filter_text = f" {'Kerakli filtrlarni tanlang:' if lang == 'uz' else 'Выберите нужные фильтры:'}"
                try:
                    await callback.message.edit_text(
                        filter_text,
                        reply_markup=get_filter_keyboard(lang)
                    )
                except Exception as e:
                    logger.error(f"Edit text error (clear): {str(e)}", exc_info=True)
                    await callback.answer(f"{'Xatolik yuz berdi' if lang == 'uz' else 'Произошла ошибка'}", show_alert=True)
                    return
                await callback.answer()
                return
            applications = result['applications'] if result and result.get('applications') else []
            total_pages = result.get('total_pages', 1) if result else 1
            current_page = result.get('page', 1) if result else 1
            status_emojis = {
                'new': '',
                'in_progress': '',
                'completed': '',
                'cancelled': ''
            }
            # 2ta tilda, emojilar bilan
            labels_uz = {
                'status': " Status:",
                'client': " Mijoz:",
                'address': " Manzil:",
                'description': " Izoh:",
                'technician': " Texnik:",
                'created': " Yaratilgan:",
                'no_technician': " Texnik biriktirilmagan",
                'no_address': " Manzil ko'rsatilmagan",
                'filtered': " Filtrlangan arizalar",
                'no_applications': " Arizalar topilmadi",
                'clear_filter': " Filterni tozalash",
            }
            labels_ru = {
                'status': " Статус:",
                'client': " Клиент:",
                'address': " Адрес:",
                'description': " Описание:",
                'technician': " Техник:",
                'created': " Создано:",
                'no_technician': " Не назначен",
                'no_address': " Адрес не указан",
                'filtered': " Отфильтрованные заявки",
                'no_applications': " Заявки не найдены",
                'clear_filter': " Сбросить фильтр",
            }
            labels = labels_uz if lang == 'uz' else labels_ru
            applications_text = f"{filter_label} ({current_page}/{total_pages}):\n\n"
            if applications:
                for app in applications:
                    status = app.get('status', 'new')
                    status_emoji = status_emojis.get(status, '')
                    # 2 tilda, emoji bilan chiroyli formatda chiqaramiz
                    if lang == 'uz':
                        applications_text += (
                            f"{status_emoji} <b>Status:</b> <i>{status_label if 'status_label' in locals() else status}</i>\n"
                            f" <b>Mijoz:</b> <i>{app.get('user_name',)}</i> |  <b>Tel:</b> <i>{app.get('client_phone', '-')}</i>\n"
                            f" <b>Manzil:</b> <i>{app.get('address') or labels['no_address']}</i>\n"
                            f" <b>Izoh:</b> <i>{app.get('description', '')[:100]}</i>\n"
                            f" <b>Texnik:</b> <i>{app.get('technician_name', labels['no_technician'])}</i> |  <i>{app.get('technician_phone', '-')}</i>\n"
                            f" <b>Yaratilgan:</b> <i>{app.get('created_at', '')}</i>\n"
                            f" <b>ID:</b> <code>{app.get('id', '-')}</code>\n"
                            "━━━━━━━━━━━━━━━━━━━━━━\n"
                        )
                    else:
                        applications_text += (
                            f"{status_emoji} <b>Статус:</b> <i>{status_label if 'status_label' in locals() else status}</i>\n"
                            f" <b>Клиент:</b> <i>{app.get('user_name')}</i> |  <b>Тел:</b> <i>{app.get('client_phone', '-')}</i>\n"
                            f" <b>Адрес:</b> <i>{app.get('address') or labels['no_address']}</i>\n"
                            f" <b>Описание:</b> <i>{app.get('description', '')[:100]}</i>\n"
                            f" <b>Техник:</b> <i>{app.get('technician_name', labels['no_technician'])}</i> |  <i>{app.get('technician_phone', '-')}</i>\n"
                            f" <b>Создано:</b> <i>{app.get('created_at', '')}</i>\n"
                            f" <b>ID:</b> <code>{app.get('id', '-')}</code>\n"
                            "━━━━━━━━━━━━━━━━━━━━━━\n"
                        )
            else:
                applications_text += f"{labels['no_applications']}\n\n"
            # Pagination buttons
            inline_keyboard = []
            if total_pages > 1:
                nav_buttons = []
                if current_page > 1:
                    nav_buttons.append(InlineKeyboardButton(
                        text="", callback_data=f"filter_{filter_type}_{'_'.join(parts[2:-1]) if parts[-1].isdigit() else '_'.join(parts[2:])}_{current_page-1}"
                    ))
                nav_buttons.append(InlineKeyboardButton(
                    text=f"{current_page}/{total_pages}", callback_data="noop"
                ))
                if current_page < total_pages:
                    nav_buttons.append(InlineKeyboardButton(
                        text="", callback_data=f"filter_{filter_type}_{'_'.join(parts[2:-1]) if parts[-1].isdigit() else '_'.join(parts[2:])}_{current_page+1}"
                    ))
                inline_keyboard.append(nav_buttons)
            # Always show clear button
            inline_keyboard.append([
                InlineKeyboardButton(
                    text=f" {labels['clear_filter']}",
                    callback_data="filter_clear"
                )
            ])
            keyboard = InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
            try:
                await callback.message.edit_text(applications_text, reply_markup=keyboard)
            except Exception as e:
                logger.error(f"Edit text error: {str(e)}", exc_info=True)
                await callback.answer(f"{'Xatolik yuz berdi' if lang == 'uz' else 'Произошла ошибка'}", show_alert=True)
                return
            await callback.answer()
        except Exception as e:
            logger.error(f"Error processing filter: {str(e)}", exc_info=True)
            await callback.answer(
                f"{'Xatolik yuz berdi' if lang == 'uz' else 'Произошла ошибка'}",
                show_alert=True
            )

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

    return router
