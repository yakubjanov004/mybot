from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from functools import wraps
import logging

from database.admin_queries import (
    is_admin, get_system_settings, update_system_setting,
    get_notification_templates, update_notification_template, log_admin_action
)
from keyboards.admin_buttons import get_settings_keyboard
from states.admin_states import AdminStates
from database.base_queries import get_user_by_telegram_id, get_user_lang
from utils.inline_cleanup import safe_delete_message, answer_and_cleanup
from utils.logger import setup_logger
from utils.role_checks import admin_only
from loader import inline_message_manager
from aiogram.filters import StateFilter

# Setup logger
logger = setup_logger('bot.admin.settings')

def get_admin_settings_router():
    router = Router()

    @router.message(StateFilter(AdminStates.main_menu), F.text.in_(["⚙️ Sozlamalar", "⚙️ Настройки"]))
    @admin_only
    async def settings_menu(message: Message, state: FSMContext):
        """Settings main menu"""
        try:
            await safe_delete_message(message.bot, message.chat.id, message.message_id)
            lang = await get_user_lang(message.from_user.id)
            
            text = "Sozlamalar bo'limi (stub)." if lang == 'uz' else "Раздел настроек (заглушка)."
            
            sent_message = await message.answer(
                text,
                reply_markup=get_settings_keyboard(lang)
            )
            await inline_message_manager.track(message.from_user.id, sent_message.message_id)
            await state.set_state(AdminStates.settings)
            
        except Exception as e:
            logger.error(f"Error in settings menu: {e}")
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi." if lang == 'uz' else "Произошла ошибка."
            await message.answer(error_text)

    @router.message(F.text.in_(["🔧 Tizim sozlamalari", "🔧 Системные настройки"]))
    @admin_only
    async def system_settings(message: Message):
        """Show system settings"""
        try:
            await safe_delete_message(message.bot, message.chat.id, message.message_id)
            lang = await get_user_lang(message.from_user.id)
            
            # Get system settings
            settings = await get_system_settings()
            
            if not settings:
                text = "Tizim sozlamalari topilmadi." if lang == 'uz' else "Системные настройки не найдены."
                await message.answer(text)
                return
            
            if lang == 'uz':
                text = f"🔧 <b>Tizim sozlamalari</b>\n\n"
            else:
                text = f"🔧 <b>Системные настройки</b>\n\n"
            
            for key, setting in settings.items():
                setting_name = {
                    'max_orders_per_technician': 'Texnik uchun maksimal zayavkalar' if lang == 'uz' else 'Максимум заявок на техника',
                    'order_timeout_hours': 'Zayavka timeout (soat)' if lang == 'uz' else 'Таймаут заявки (часы)',
                    'notification_enabled': 'Bildirishnomalar yoqilgan' if lang == 'uz' else 'Уведомления включены',
                    'auto_assign_enabled': 'Avtomatik tayinlash' if lang == 'uz' else 'Автоназначение',
                    'maintenance_mode': 'Texnik xizmat rejimi' if lang == 'uz' else 'Режим обслуживания'
                }.get(key, key)
                
                text += f"• <b>{setting_name}:</b> {setting['value']}\n"
                if setting.get('description'):
                    text += f"  <i>{setting['description']}</i>\n"
                text += "\n"
            
            # Add management buttons
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✏️ Sozlamani o'zgartirish" if lang == 'uz' else "✏️ Изменить настройку",
                        callback_data="edit_system_setting"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔄 Yangilash" if lang == 'uz' else "🔄 Обновить",
                        callback_data="refresh_system_settings"
                    )
                ]
            ])
            
            await message.answer(text, reply_markup=keyboard)
            
        except Exception as e:
            logger.error(f"Error showing system settings: {e}")
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi." if lang == 'uz' else "Произошла ошибка."
            await message.answer(error_text)

    @router.message(F.text.in_(["📢 Bildirishnoma shablonlari", "📢 Шаблоны уведомлений"]))
    @admin_only
    async def notification_templates(message: Message):
        """Show notification templates"""
        try:
            await safe_delete_message(message.bot, message.chat.id, message.message_id)
            lang = await get_user_lang(message.from_user.id)
            
            # Get notification templates
            templates = await get_notification_templates()
            
            if not templates:
                text = "Bildirishnoma shablonlari topilmadi." if lang == 'uz' else "Шаблоны уведомлений не найдены."
                await message.answer(text)
                return
            
            if lang == 'uz':
                text = f"📢 <b>Bildirishnoma shablonlari</b>\n\n"
            else:
                text = f"📢 <b>Шаблоны уведомлений</b>\n\n"
            
            # Group templates by type
            template_groups = {}
            for template in templates:
                template_type = template['template_type']
                if template_type not in template_groups:
                    template_groups[template_type] = []
                template_groups[template_type].append(template)
            
            for template_type, group_templates in template_groups.items():
                type_name = {
                    'order_created': 'Zayavka yaratildi' if lang == 'uz' else 'Заявка создана',
                    'order_assigned': 'Zayavka tayinlandi' if lang == 'uz' else 'Заявка назначена',
                    'order_completed': 'Zayavka bajarildi' if lang == 'uz' else 'Заявка выполнена',
                    'welcome_message': 'Xush kelibsiz xabari' if lang == 'uz' else 'Приветственное сообщение'
                }.get(template_type, template_type)
                
                text += f"📋 <b>{type_name}:</b>\n"
                
                for template in group_templates:
                    lang_name = "O'zbek" if template['language'] == 'uz' else "Русский"
                    text += f"  • {lang_name}: {template['content'][:50]}...\n"
                
                text += "\n"
            
            # Add management buttons
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✏️ Shablonni tahrirlash" if lang == 'uz' else "✏️ Редактировать шаблон",
                        callback_data="edit_notification_template"
                    )
                ]
            ])
            
            await message.answer(text, reply_markup=keyboard)
            
        except Exception as e:
            logger.error(f"Error showing notification templates: {e}")
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi." if lang == 'uz' else "Произошла ошибка."
            await message.answer(error_text)

    @router.message(F.text.in_(["🔐 Xavfsizlik sozlamalari", "🔐 Настройки безопасности"]))
    @admin_only
    async def security_settings(message: Message):
        """Show security settings"""
        try:
            await safe_delete_message(message.bot, message.chat.id, message.message_id)
            lang = await get_user_lang(message.from_user.id)
            
            if lang == 'uz':
                text = (
                    f"🔐 <b>Xavfsizlik sozlamalari</b>\n\n"
                    f"🔒 <b>Joriy sozlamalar:</b>\n"
                    f"• Admin huquqlari: Faol\n"
                    f"• Avtorizatsiya: Telegram ID bo'yicha\n"
                    f"• Sessiya muddati: Cheksiz\n"
                    f"• Loglar saqlanishi: 30 kun\n\n"
                    f"⚠️ <b>Xavfsizlik choralari:</b>\n"
                    f"• Barcha admin amallar loglanadi\n"
                    f"• Foydalanuvchi rollari nazorat qilinadi\n"
                    f"• Tizimga kirish kuzatiladi\n\n"
                    f"📋 <b>Tavsiyalar:</b>\n"
                    f"• Admin huquqlarini faqat ishonchli odamlarga bering\n"
                    f"• Muntazam ravishda loglarni tekshiring\n"
                    f"• Shubhali faollikni darhol xabar qiling"
                )
            else:
                text = (
                    f"🔐 <b>Настройки безопасности</b>\n\n"
                    f"🔒 <b>Текущие настройки:</b>\n"
                    f"• Права администратора: Активны\n"
                    f"• Авторизация: По Telegram ID\n"
                    f"• Срок сессии: Неограничен\n"
                    f"• Хранение логов: 30 дней\n\n"
                    f"⚠️ <b>Меры безопасности:</b>\n"
                    f"• Все действия админов логируются\n"
                    f"• Роли пользователей контролируются\n"
                    f"• Доступ к системе отслеживается\n\n"
                    f"📋 <b>Рекомендации:</b>\n"
                    f"• Давайте права админа только доверенным лицам\n"
                    f"• Регулярно проверяйте логи\n"
                    f"• Немедленно сообщайте о подозрительной активности"
                )
            
            await message.answer(text)
            
        except Exception as e:
            logger.error(f"Error showing security settings: {e}")
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi." if lang == 'uz' else "Произошла ошибка."
            await message.answer(error_text)

    @router.message(F.text.in_(["🔄 Backup va tiklash", "🔄 Резервное копирование"]))
    @admin_only
    async def backup_restore(message: Message):
        """Show backup and restore options"""
        try:
            await safe_delete_message(message.bot, message.chat.id, message.message_id)
            lang = await get_user_lang(message.from_user.id)
            
            if lang == 'uz':
                text = (
                    f"🔄 <b>Backup va tiklash</b>\n\n"
                    f"💾 <b>Avtomatik backup:</b>\n"
                    f"• Kunlik backup: Yoqilgan\n"
                    f"• Backup vaqti: 02:00\n"
                    f"• Saqlanish muddati: 30 kun\n\n"
                    f"📁 <b>Backup ma'lumotlari:</b>\n"
                    f"• Foydalanuvchilar ma'lumotlari\n"
                    f"• Zayavkalar tarixi\n"
                    f"• Tizim sozlamalari\n"
                    f"• Loglar\n\n"
                    f"⚠️ <b>Diqqat:</b>\n"
                    f"Manual backup va tiklash funksiyalari\n"
                    f"faqat server administratori tomonidan\n"
                    f"amalga oshirilishi mumkin."
                )
            else:
                text = (
                    f"🔄 <b>Резервное копирование и восстановление</b>\n\n"
                    f"💾 <b>Автоматический backup:</b>\n"
                    f"• Ежедневный backup: Включен\n"
                    f"• Время backup: 02:00\n"
                    f"• Срок хранения: 30 дней\n\n"
                    f"📁 <b>Данные backup:</b>\n"
                    f"• Данные пользователей\n"
                    f"• История заявок\n"
                    f"• Настройки системы\n"
                    f"• Логи\n\n"
                    f"⚠️ <b>Внимание:</b>\n"
                    f"Функции ручного backup и восстановления\n"
                    f"могут выполняться только администратором\n"
                    f"сервера."
                )
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📤 Ma'lumotlarni eksport" if lang == 'uz' else "📤 Экспорт данных",
                        callback_data="export_all_data"
                    )
                ]
            ])
            
            await message.answer(text, reply_markup=keyboard)
            
        except Exception as e:
            logger.error(f"Error showing backup restore: {e}")
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi." if lang == 'uz' else "Произошла ошибка."
            await message.answer(error_text)

    @router.callback_query(F.data == "edit_system_setting")
    @admin_only
    async def edit_system_setting_menu(call: CallbackQuery, state: FSMContext):
        """Show system settings edit menu"""
        try:
            await answer_and_cleanup(call, cleanup_after=True)
            lang = await get_user_lang(call.from_user.id)
            
            # Get system settings
            settings = await get_system_settings()
            
            if not settings:
                text = "Sozlamalar topilmadi." if lang == 'uz' else "Настройки не найдены."
                await call.message.edit_text(text)
                return
            
            text = "O'zgartirish uchun sozlamani tanlang:" if lang == 'uz' else "Выберите настройку для изменения:"
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[])
            for key, setting in list(settings.items())[:10]:  # Show first 10 settings
                setting_name = {
                    'max_orders_per_technician': 'Maksimal zayavkalar' if lang == 'uz' else 'Макс. заявок',
                    'order_timeout_hours': 'Timeout (soat)' if lang == 'uz' else 'Таймаут (ч)',
                    'notification_enabled': 'Bildirishnomalar' if lang == 'uz' else 'Уведомления',
                    'auto_assign_enabled': 'Avto-tayinlash' if lang == 'uz' else 'Авто-назначение'
                }.get(key, key[:20])
                
                keyboard.inline_keyboard.append([
                    InlineKeyboardButton(
                        text=f"{setting_name}: {setting['value']}",
                        callback_data=f"edit_setting_{key}"
                    )
                ])
            
            await call.message.edit_text(text, reply_markup=keyboard)
            await state.set_state(AdminStates.editing_setting)
            
        except Exception as e:
            logger.error(f"Error showing edit system setting menu: {e}")
            await call.answer("Xatolik yuz berdi!" if await get_user_lang(call.from_user.id) == 'uz' else "Произошла ошибка!")

    @router.callback_query(F.data.startswith("edit_setting_"), AdminStates.editing_setting)
    @admin_only
    async def edit_setting_value(call: CallbackQuery, state: FSMContext):
        """Edit setting value"""
        try:
            lang = await get_user_lang(call.from_user.id)
            setting_key = call.data.split("edit_setting_")[1]
            
            await state.update_data(setting_key=setting_key)
            
            text = f"'{setting_key}' sozlamasi uchun yangi qiymatni kiriting:" if lang == 'uz' else f"Введите новое значение для настройки '{setting_key}':"
            
            await call.message.edit_text(text)
            await state.set_state(AdminStates.waiting_for_setting_value)
            
        except Exception as e:
            logger.error(f"Error editing setting value: {e}")
            await call.answer("Xatolik yuz berdi!" if await get_user_lang(call.from_user.id) == 'uz' else "Произошла ошибка!")

    @router.message(AdminStates.waiting_for_setting_value)
    @admin_only
    async def process_setting_value(message: Message, state: FSMContext):
        """Process new setting value"""
        try:
            lang = await get_user_lang(message.from_user.id)
            data = await state.get_data()
            setting_key = data.get('setting_key')
            new_value = message.text.strip()
            
            if not new_value:
                text = "Qiymat bo'sh bo'lishi mumkin emas." if lang == 'uz' else "Значение не может быть пустым."
                await message.answer(text)
                return
            
            # Update setting
            success = await update_system_setting(setting_key, new_value, message.from_user.id)
            
            if success:
                # Log admin action
                await log_admin_action(message.from_user.id, "update_system_setting", {
                    "setting_key": setting_key,
                    "new_value": new_value
                })
                
                text = f"✅ '{setting_key}' sozlamasi '{new_value}' ga o'zgartirildi." if lang == 'uz' else f"✅ Настройка '{setting_key}' изменена на '{new_value}'."
            else:
                text = "Sozlamani o'zgartirishda xatolik." if lang == 'uz' else "Ошибка при изменении настройки."
            
            await message.answer(text)
            await state.clear()
            
        except Exception as e:
            logger.error(f"Error processing setting value: {e}")
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi." if lang == 'uz' else "Произошла ошибка."
            await message.answer(error_text)
            await state.clear()

    @router.callback_query(F.data == "refresh_system_settings")
    @admin_only
    async def refresh_system_settings(call: CallbackQuery):
        """Refresh system settings"""
        try:
            lang = await get_user_lang(call.from_user.id)
            
            # Get fresh system settings
            settings = await get_system_settings()
            
            if not settings:
                text = "Tizim sozlamalari topilmadi." if lang == 'uz' else "Системные настройки не найдены."
                await call.message.edit_text(text)
                return
            
            if lang == 'uz':
                text = f"🔄 <b>Yangilangan tizim sozlamalari</b>\n\n"
            else:
                text = f"🔄 <b>Обновленные системные настройки</b>\n\n"
            
            for key, setting in settings.items():
                setting_name = {
                    'max_orders_per_technician': 'Texnik uchun maksimal zayavkalar' if lang == 'uz' else 'Максимум заявок на техника',
                    'order_timeout_hours': 'Zayavka timeout (soat)' if lang == 'uz' else 'Таймаут заявки (часы)',
                    'notification_enabled': 'Bildirishnomalar yoqilgan' if lang == 'uz' else 'Уведомления включены',
                    'auto_assign_enabled': 'Avtomatik tayinlash' if lang == 'uz' else 'Автоназначение'
                }.get(key, key)
                
                text += f"• <b>{setting_name}:</b> {setting['value']}\n"
            
            text += f"\n🕐 Yangilangan: {datetime.now().strftime('%H:%M:%S')}" if lang == 'uz' else f"\n🕐 Обновлено: {datetime.now().strftime('%H:%M:%S')}"
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✏️ Sozlamani o'zgartirish" if lang == 'uz' else "✏️ Изменить настройку",
                        callback_data="edit_system_setting"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔄 Yangilash" if lang == 'uz' else "🔄 Обновить",
                        callback_data="refresh_system_settings"
                    )
                ]
            ])
            
            await call.message.edit_text(text, reply_markup=keyboard)
            await call.answer("Sozlamalar yangilandi!" if lang == 'uz' else "Настройки обновлены!")
            
        except Exception as e:
            logger.error(f"Error refreshing system settings: {e}")
            await call.answer("Xatolik yuz berdi!" if await get_user_lang(call.from_user.id) == 'uz' else "Произошла ошибка!")

    @router.callback_query(F.data == "export_all_data")
    @admin_only
    async def export_all_data(call: CallbackQuery):
        """Export all system data"""
        try:
            lang = await get_user_lang(call.from_user.id)
            
            processing_text = "Barcha ma'lumotlar eksport qilinmoqda..." if lang == 'uz' else "Экспорт всех данных..."
            await call.message.edit_text(processing_text)
            
            # Export different types of data
            export_types = ['users', 'orders', 'logs']
            exported_files = []
            
            for export_type in export_types:
                file_path = await export_admin_data(export_type)
                if file_path:
                    exported_files.append((export_type, file_path))
            
            if exported_files:
                # Log admin action
                await log_admin_action(call.from_user.id, "export_all_data", {
                    "exported_types": [et[0] for et in exported_files]
                })
                
                success_text = f"✅ {len(exported_files)} ta fayl eksport qilindi!" if lang == 'uz' else f"✅ Экспортировано {len(exported_files)} файлов!"
                await call.message.edit_text(success_text)
                
                # Send each file
                for export_type, file_path in exported_files:
                    try:
                        with open(file_path, 'rb') as file:
                            await call.message.answer_document(
                                file,
                                caption=f"📤 {export_type.title()} ma'lumotlari" if lang == 'uz' else f"📤 Данные {export_type}"
                            )
                        
                        # Clean up file
                        import os
                        os.unlink(file_path)
                        
                    except Exception as file_error:
                        logger.error(f"Error sending exported file {export_type}: {file_error}")
            else:
                error_text = "Eksport qilishda xatolik." if lang == 'uz' else "Ошибка при экспорте."
                await call.message.edit_text(error_text)
            
            await call.answer()
            
        except Exception as e:
            logger.error(f"Error exporting all data: {e}")
            await call.answer("Xatolik yuz berdi!" if await get_user_lang(call.from_user.id) == 'uz' else "Произошла ошибка!")

    return router
