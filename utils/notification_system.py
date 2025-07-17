"""
Universal Notification System - Handles workflow assignment notifications
Provides single notification delivery with reply button handling for viewing all pending assignments
"""

import json
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from database.models import UserRole, ServiceRequest
from utils.logger import setup_module_logger

logger = setup_module_logger("notification_system")


class NotificationInterface(ABC):
    """Abstract interface for notification system"""
    
    @abstractmethod
    async def send_assignment_notification(self, role: str, request_id: str, workflow_type: str) -> bool:
        """Sends single notification with reply button"""
        pass
    
    @abstractmethod
    async def handle_notification_reply(self, user_id: int, callback_data: str) -> Dict[str, Any]:
        """Displays all pending assignments for user"""
        pass
    
    @abstractmethod
    async def mark_notification_handled(self, user_id: int, request_id: str) -> bool:
        """Marks notification as handled when task completed"""
        pass
    
    @abstractmethod
    async def get_pending_notifications(self, user_id: int) -> List[Dict[str, Any]]:
        """Returns all unhandled notifications for user"""
        pass


class PendingNotification:
    """Represents a pending notification"""
    
    def __init__(self, notification_id: str, user_id: int, request_id: str, 
                 workflow_type: str, role: str, created_at: datetime = None):
        self.notification_id = notification_id
        self.user_id = user_id
        self.request_id = request_id
        self.workflow_type = workflow_type
        self.role = role
        self.created_at = created_at or datetime.now()
        self.is_handled = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'notification_id': self.notification_id,
            'user_id': self.user_id,
            'request_id': self.request_id,
            'workflow_type': self.workflow_type,
            'role': self.role,
            'created_at': self.created_at,
            'is_handled': self.is_handled
        }


class NotificationSystem(NotificationInterface):
    """Universal notification system implementation"""
    
    def __init__(self, pool=None):
        self.pool = pool
        # Exclude client and admin roles from notification system as per requirements
        self.excluded_roles = {UserRole.CLIENT.value, UserRole.ADMIN.value}
        
        # Staff-created application notification templates
        self.staff_notification_templates = self._load_staff_notification_templates()
    
    def _get_pool(self):
        """Get database pool"""
        if self.pool:
            return self.pool
        # Fallback to bot's pool
        try:
            from loader import bot
            return bot.db
        except ImportError:
            logger.error("No database pool available")
            return None
    
    def _generate_notification_id(self) -> str:
        """Generate unique notification ID"""
        return str(uuid.uuid4())
    
    def _load_staff_notification_templates(self) -> Dict[str, Dict[str, Dict[str, str]]]:
        """Load notification templates for staff-created applications"""
        return {
            'client_notification': {
                'uz': {
                    'connection_request': {
                        'title': '📋 Sizning nomingizdan ariza yaratildi',
                        'body': (
                            "Hurmatli {client_name},\n\n"
                            "Sizning nomingizdan ulanish uchun ariza yaratildi.\n\n"
                            "📋 Ariza turi: Ulanish so'rovi\n"
                            "📝 Tavsif: {description}\n"
                            "📍 Manzil: {location}\n"
                            "👤 Yaratuvchi: {creator_role}\n"
                            "📅 Yaratilgan vaqt: {created_at}\n"
                            "🆔 Ariza ID: {request_id}\n\n"
                            "Ariza holati haqida xabardor bo'lib turasiz."
                        ),
                        'button': '📋 Arizani ko\'rish'
                    },
                    'technical_service': {
                        'title': '🔧 Sizning nomingizdan texnik xizmat arizasi yaratildi',
                        'body': (
                            "Hurmatli {client_name},\n\n"
                            "Sizning nomingizdan texnik xizmat arizasi yaratildi.\n\n"
                            "📋 Ariza turi: Texnik xizmat\n"
                            "📝 Tavsif: {description}\n"
                            "📍 Manzil: {location}\n"
                            "👤 Yaratuvchi: {creator_role}\n"
                            "📅 Yaratilgan vaqt: {created_at}\n"
                            "🆔 Ariza ID: {request_id}\n\n"
                            "Ariza holati haqida xabardor bo'lib turasiz."
                        ),
                        'button': '🔧 Arizani ko\'rish'
                    }
                },
                'ru': {
                    'connection_request': {
                        'title': '📋 Заявка создана от вашего имени',
                        'body': (
                            "Уважаемый(ая) {client_name},\n\n"
                            "От вашего имени создана заявка на подключение.\n\n"
                            "📋 Тип заявки: Запрос подключения\n"
                            "📝 Описание: {description}\n"
                            "📍 Адрес: {location}\n"
                            "👤 Создатель: {creator_role}\n"
                            "📅 Время создания: {created_at}\n"
                            "🆔 ID заявки: {request_id}\n\n"
                            "Вы будете уведомлены о статусе заявки."
                        ),
                        'button': '📋 Просмотр заявки'
                    },
                    'technical_service': {
                        'title': '🔧 Заявка на техническое обслуживание создана от вашего имени',
                        'body': (
                            "Уважаемый(ая) {client_name},\n\n"
                            "От вашего имени создана заявка на техническое обслуживание.\n\n"
                            "📋 Тип заявки: Техническое обслуживание\n"
                            "📝 Описание: {description}\n"
                            "📍 Адрес: {location}\n"
                            "👤 Создатель: {creator_role}\n"
                            "📅 Время создания: {created_at}\n"
                            "🆔 ID заявки: {request_id}\n\n"
                            "Вы будете уведомлены о статусе заявки."
                        ),
                        'button': '🔧 Просмотр заявки'
                    }
                }
            },
            'staff_confirmation': {
                'uz': {
                    'connection_request': {
                        'title': '✅ Ulanish arizasi muvaffaqiyatli yaratildi',
                        'body': (
                            "Ariza muvaffaqiyatli yaratildi va ishlov berishga yuborildi.\n\n"
                            "📋 Ariza turi: Ulanish so'rovi\n"
                            "👤 Mijoz: {client_name}\n"
                            "📝 Tavsif: {description}\n"
                            "📍 Manzil: {location}\n"
                            "🆔 Ariza ID: {request_id}\n"
                            "📅 Yaratilgan: {created_at}\n\n"
                            "Mijoz xabardor qilindi va ariza ish jarayoniga kiritildi."
                        ),
                        'button': '📋 Arizani kuzatish'
                    },
                    'technical_service': {
                        'title': '✅ Texnik xizmat arizasi muvaffaqiyatli yaratildi',
                        'body': (
                            "Ariza muvaffaqiyatli yaratildi va ishlov berishga yuborildi.\n\n"
                            "📋 Ariza turi: Texnik xizmat\n"
                            "👤 Mijoz: {client_name}\n"
                            "📝 Tavsif: {description}\n"
                            "📍 Manzil: {location}\n"
                            "🆔 Ariza ID: {request_id}\n"
                            "📅 Yaratilgan: {created_at}\n\n"
                            "Mijoz xabardor qilindi va ariza ish jarayoniga kiritildi."
                        ),
                        'button': '🔧 Arizani kuzatish'
                    }
                },
                'ru': {
                    'connection_request': {
                        'title': '✅ Заявка на подключение успешно создана',
                        'body': (
                            "Заявка успешно создана и отправлена на обработку.\n\n"
                            "📋 Тип заявки: Запрос подключения\n"
                            "👤 Клиент: {client_name}\n"
                            "📝 Описание: {description}\n"
                            "📍 Адрес: {location}\n"
                            "🆔 ID заявки: {request_id}\n"
                            "📅 Создано: {created_at}\n\n"
                            "Клиент уведомлен и заявка передана в работу."
                        ),
                        'button': '📋 Отслеживать заявку'
                    },
                    'technical_service': {
                        'title': '✅ Заявка на техническое обслуживание успешно создана',
                        'body': (
                            "Заявка успешно создана и отправлена на обработку.\n\n"
                            "📋 Тип заявки: Техническое обслуживание\n"
                            "👤 Клиент: {client_name}\n"
                            "📝 Описание: {description}\n"
                            "📍 Адрес: {location}\n"
                            "🆔 ID заявки: {request_id}\n"
                            "📅 Создано: {created_at}\n\n"
                            "Клиент уведомлен и заявка передана в работу."
                        ),
                        'button': '🔧 Отслеживать заявку'
                    }
                }
            },
            'workflow_participant': {
                'uz': {
                    'connection_request': {
                        'title': '🔔 Xodim tomonidan yaratilgan yangi ariza',
                        'body': (
                            "Xodim tomonidan yangi ulanish arizasi yaratildi.\n\n"
                            "📋 Ariza turi: Ulanish so'rovi\n"
                            "👤 Mijoz: {client_name}\n"
                            "📝 Tavsif: {description}\n"
                            "📍 Manzil: {location}\n"
                            "👤 Yaratuvchi: {creator_role}\n"
                            "🆔 Ariza ID: {request_id}\n"
                            "📅 Yaratilgan: {created_at}\n\n"
                            "Ariza sizga tayinlandi."
                        ),
                        'button': '📋 Arizani ko\'rib chiqish'
                    },
                    'technical_service': {
                        'title': '🔔 Xodim tomonidan yaratilgan yangi texnik ariza',
                        'body': (
                            "Xodim tomonidan yangi texnik xizmat arizasi yaratildi.\n\n"
                            "📋 Ariza turi: Texnik xizmat\n"
                            "👤 Mijoz: {client_name}\n"
                            "📝 Tavsif: {description}\n"
                            "📍 Manzil: {location}\n"
                            "👤 Yaratuvchi: {creator_role}\n"
                            "🆔 Ariza ID: {request_id}\n"
                            "📅 Yaratilgan: {created_at}\n\n"
                            "Ariza sizga tayinlandi."
                        ),
                        'button': '🔧 Arizani ko\'rib chiqish'
                    }
                },
                'ru': {
                    'connection_request': {
                        'title': '🔔 Новая заявка создана сотрудником',
                        'body': (
                            "Сотрудником создана новая заявка на подключение.\n\n"
                            "📋 Тип заявки: Запрос подключения\n"
                            "👤 Клиент: {client_name}\n"
                            "📝 Описание: {description}\n"
                            "📍 Адрес: {location}\n"
                            "👤 Создатель: {creator_role}\n"
                            "🆔 ID заявки: {request_id}\n"
                            "📅 Создано: {created_at}\n\n"
                            "Заявка назначена вам."
                        ),
                        'button': '📋 Рассмотреть заявку'
                    },
                    'technical_service': {
                        'title': '🔔 Новая техническая заявка создана сотрудником',
                        'body': (
                            "Сотрудником создана новая заявка на техническое обслуживание.\n\n"
                            "📋 Тип заявки: Техническое обслуживание\n"
                            "👤 Клиент: {client_name}\n"
                            "📝 Описание: {description}\n"
                            "📍 Адрес: {location}\n"
                            "👤 Создатель: {creator_role}\n"
                            "🆔 ID заявки: {request_id}\n"
                            "📅 Создано: {created_at}\n\n"
                            "Заявка назначена вам."
                        ),
                        'button': '🔧 Рассмотреть заявку'
                    }
                }
            }
        }
    
    async def send_assignment_notification(self, role: str, request_id: str, workflow_type: str) -> bool:
        """Sends single notification with reply button to all users with specified role"""
        # Exclude client and admin roles from notification system
        if role in self.excluded_roles:
            logger.info(f"Skipping notification for excluded role: {role}")
            return True
        
        pool = self._get_pool()
        if not pool:
            logger.error("No database pool available")
            return False
        
        try:
            async with pool.acquire() as conn:
                # Get all users with the specified role who have telegram_id
                users_query = """
                SELECT id, telegram_id, full_name, language
                FROM users 
                WHERE role = $1 AND telegram_id IS NOT NULL AND is_active = true
                """
                
                users = await conn.fetch(users_query, role)
                
                if not users:
                    logger.warning(f"No active users found for role: {role}")
                    return False
                
                # Get request details for notification content
                request_query = """
                SELECT description, priority, created_at
                FROM service_requests
                WHERE id = $1
                """
                
                request_row = await conn.fetchrow(request_query, request_id)
                if not request_row:
                    logger.error(f"Request {request_id} not found")
                    return False
                
                sent_count = 0
                
                for user in users:
                    try:
                        # Create notification record
                        notification_id = self._generate_notification_id()
                        
                        await conn.execute(
                            """
                            INSERT INTO pending_notifications 
                            (id, user_id, request_id, workflow_type, role, created_at, is_handled)
                            VALUES ($1, $2, $3, $4, $5, $6, $7)
                            """,
                            notification_id,
                            user['id'],
                            request_id,
                            workflow_type,
                            role,
                            datetime.now(),
                            False
                        )
                        
                        # Send notification message
                        await self._send_notification_message(
                            user, request_id, workflow_type, request_row, notification_id
                        )
                        
                        sent_count += 1
                        logger.info(f"Sent notification to user {user['id']} for request {request_id}")
                        
                    except Exception as e:
                        logger.error(f"Failed to send notification to user {user['id']}: {e}")
                        continue
                
                logger.info(f"Sent {sent_count} notifications for request {request_id} to role {role}")
                return sent_count > 0
                
        except Exception as e:
            logger.error(f"Error sending assignment notification: {e}", exc_info=True)
            return False
    
    async def _send_notification_message(self, user: Dict[str, Any], request_id: str, 
                                       workflow_type: str, request_data: Dict[str, Any], 
                                       notification_id: str):
        """Send notification message to user via Telegram"""
        try:
            from loader import bot
            
            lang = user.get('language', 'ru')
            
            # Create notification text based on language
            if lang == 'uz':
                title = "🔔 Yangi topshiriq"
                workflow_names = {
                    'connection_request': 'Ulanish so\'rovi',
                    'technical_service': 'Texnik xizmat',
                    'call_center_direct': 'Call-markaz xizmati'
                }
                workflow_name = workflow_names.get(workflow_type, workflow_type)
                
                notification_text = (
                    f"{title}\n\n"
                    f"📋 Tur: {workflow_name}\n"
                    f"📝 Tavsif: {request_data['description'][:100]}...\n"
                    f"⚡ Muhimlik: {request_data['priority']}\n"
                    f"📅 Yaratilgan: {request_data['created_at'].strftime('%d.%m.%Y %H:%M')}\n\n"
                    f"Barcha topshiriqlarni ko'rish uchun tugmani bosing:"
                )
                button_text = "📋 Topshiriqlarni ko'rish"
            else:
                title = "🔔 Новое задание"
                workflow_names = {
                    'connection_request': 'Запрос подключения',
                    'technical_service': 'Техническое обслуживание',
                    'call_center_direct': 'Сервис call-центра'
                }
                workflow_name = workflow_names.get(workflow_type, workflow_type)
                
                notification_text = (
                    f"{title}\n\n"
                    f"📋 Тип: {workflow_name}\n"
                    f"📝 Описание: {request_data['description'][:100]}...\n"
                    f"⚡ Приоритет: {request_data['priority']}\n"
                    f"📅 Создано: {request_data['created_at'].strftime('%d.%m.%Y %H:%M')}\n\n"
                    f"Нажмите кнопку для просмотра всех заданий:"
                )
                button_text = "📋 Просмотр заданий"
            
            # Create reply button
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text=button_text,
                    callback_data=f"view_assignments_{notification_id}"
                )]
            ])
            
            await bot.send_message(
                chat_id=user['telegram_id'],
                text=notification_text,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
            
        except Exception as e:
            logger.error(f"Error sending notification message to user {user['id']}: {e}")
            raise
    
    async def send_completion_notification(self, client_id: int, request_id: str, workflow_type: str) -> bool:
        """Sends completion notification to client with rating request"""
        pool = self._get_pool()
        if not pool:
            logger.error("No database pool available")
            return False
        
        try:
            async with pool.acquire() as conn:
                # Get client details
                user_query = """
                SELECT id, telegram_id, full_name, language
                FROM users 
                WHERE id = $1 AND telegram_id IS NOT NULL
                """
                
                user = await conn.fetchrow(user_query, client_id)
                if not user:
                    logger.error(f"Client {client_id} not found or no telegram_id")
                    return False
                
                # Get request details
                request_query = """
                SELECT description, priority, created_at, location
                FROM service_requests
                WHERE id = $1
                """
                
                request_row = await conn.fetchrow(request_query, request_id)
                if not request_row:
                    logger.error(f"Request {request_id} not found")
                    return False
                
                # Send completion notification message
                await self._send_completion_message(
                    user, request_id, workflow_type, request_row
                )
                
                logger.info(f"Sent completion notification to client {client_id} for request {request_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error sending completion notification: {e}", exc_info=True)
            return False
    
    async def _send_completion_message(self, user: Dict[str, Any], request_id: str, 
                                     workflow_type: str, request_data: Dict[str, Any]):
        """Send completion notification message to client via Telegram"""
        try:
            from loader import bot
            
            lang = user.get('language', 'ru')
            
            # Create completion notification text based on language
            if lang == 'uz':
                title = "✅ Xizmat yakunlandi!"
                workflow_names = {
                    'connection_request': 'Ulanish xizmati',
                    'technical_service': 'Texnik xizmat',
                    'call_center_direct': 'Call-markaz xizmati'
                }
                workflow_name = workflow_names.get(workflow_type, workflow_type)
                
                notification_text = (
                    f"{title}\n\n"
                    f"📋 Tur: {workflow_name}\n"
                    f"📝 Tavsif: {request_data['description'][:100]}...\n"
                    f"📅 Yaratilgan: {request_data['created_at'].strftime('%d.%m.%Y %H:%M')}\n"
                    f"🆔 Ariza ID: {request_id[:8]}\n\n"
                    f"Xizmat sifatini baholang:"
                )
                button_text = "⭐ Baholash"
            else:
                title = "✅ Услуга завершена!"
                workflow_names = {
                    'connection_request': 'Услуга подключения',
                    'technical_service': 'Техническое обслуживание',
                    'call_center_direct': 'Сервис call-центра'
                }
                workflow_name = workflow_names.get(workflow_type, workflow_type)
                
                notification_text = (
                    f"{title}\n\n"
                    f"📋 Тип: {workflow_name}\n"
                    f"📝 Описание: {request_data['description'][:100]}...\n"
                    f"📅 Создано: {request_data['created_at'].strftime('%d.%m.%Y %H:%M')}\n"
                    f"🆔 ID заявки: {request_id[:8]}\n\n"
                    f"Оцените качество обслуживания:"
                )
                button_text = "⭐ Оценить"
            
            # Create rating button
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text=button_text,
                    callback_data=f"rate_service_{request_id}"
                )]
            ])
            
            await bot.send_message(
                chat_id=user['telegram_id'],
                text=notification_text,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
            
        except Exception as e:
            logger.error(f"Error sending completion message to user {user['id']}: {e}")
            raise
    
    async def send_staff_client_notification(self, client_id: int, request_id: str, 
                                           workflow_type: str, creator_role: str, 
                                           request_data: Dict[str, Any]) -> bool:
        """Send notification to client about staff-created application"""
        pool = self._get_pool()
        if not pool:
            logger.error("No database pool available")
            return False
        
        try:
            async with pool.acquire() as conn:
                # Get client details
                user_query = """
                SELECT id, telegram_id, full_name, language
                FROM users 
                WHERE id = $1 AND telegram_id IS NOT NULL
                """
                
                user = await conn.fetchrow(user_query, client_id)
                if not user:
                    logger.error(f"Client {client_id} not found or no telegram_id")
                    return False
                
                # Send client notification message
                await self._send_staff_client_message(
                    user, request_id, workflow_type, creator_role, request_data
                )
                
                # Update client notification timestamp
                await conn.execute(
                    """
                    UPDATE service_requests 
                    SET client_notified_at = $2
                    WHERE id = $1
                    """,
                    request_id, datetime.now()
                )
                
                logger.info(f"Sent staff-created application notification to client {client_id} for request {request_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error sending staff client notification: {e}", exc_info=True)
            return False
    
    async def _send_staff_client_message(self, user: Dict[str, Any], request_id: str, 
                                       workflow_type: str, creator_role: str, 
                                       request_data: Dict[str, Any]):
        """Send staff-created application notification message to client via Telegram"""
        try:
            from loader import bot
            
            lang = user.get('language', 'ru')
            
            # Get template based on workflow type and language
            template_key = 'connection_request' if workflow_type == 'connection_request' else 'technical_service'
            template = self.staff_notification_templates['client_notification'][lang][template_key]
            
            # Format creator role for display
            creator_role_display = self._format_creator_role(creator_role, lang)
            
            # Format notification text
            notification_text = template['body'].format(
                client_name=user['full_name'],
                description=request_data.get('description', '')[:100],
                location=request_data.get('location', ''),
                creator_role=creator_role_display,
                created_at=datetime.now().strftime('%d.%m.%Y %H:%M'),
                request_id=request_id[:8]
            )
            
            # Create view button
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text=template['button'],
                    callback_data=f"view_staff_created_{request_id}"
                )]
            ])
            
            await bot.send_message(
                chat_id=user['telegram_id'],
                text=notification_text,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
            
        except Exception as e:
            logger.error(f"Error sending staff client message to user {user['id']}: {e}")
            raise
    
    async def send_staff_confirmation_notification(self, staff_id: int, request_id: str, 
                                                 workflow_type: str, client_name: str,
                                                 request_data: Dict[str, Any]) -> bool:
        """Send confirmation notification to staff member who created the application"""
        pool = self._get_pool()
        if not pool:
            logger.error("No database pool available")
            return False
        
        try:
            async with pool.acquire() as conn:
                # Get staff member details
                user_query = """
                SELECT id, telegram_id, full_name, language, role
                FROM users 
                WHERE id = $1 AND telegram_id IS NOT NULL
                """
                
                user = await conn.fetchrow(user_query, staff_id)
                if not user:
                    logger.error(f"Staff member {staff_id} not found or no telegram_id")
                    return False
                
                # Send staff confirmation message
                await self._send_staff_confirmation_message(
                    user, request_id, workflow_type, client_name, request_data
                )
                
                logger.info(f"Sent staff confirmation notification to staff {staff_id} for request {request_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error sending staff confirmation notification: {e}", exc_info=True)
            return False
    
    async def _send_staff_confirmation_message(self, user: Dict[str, Any], request_id: str, 
                                             workflow_type: str, client_name: str,
                                             request_data: Dict[str, Any]):
        """Send staff confirmation message via Telegram"""
        try:
            from loader import bot
            
            lang = user.get('language', 'ru')
            
            # Get template based on workflow type and language
            template_key = 'connection_request' if workflow_type == 'connection_request' else 'technical_service'
            template = self.staff_notification_templates['staff_confirmation'][lang][template_key]
            
            # Format notification text
            notification_text = template['body'].format(
                client_name=client_name,
                description=request_data.get('description', '')[:100],
                location=request_data.get('location', ''),
                request_id=request_id[:8],
                created_at=datetime.now().strftime('%d.%m.%Y %H:%M')
            )
            
            # Create tracking button
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text=template['button'],
                    callback_data=f"track_staff_created_{request_id}"
                )]
            ])
            
            await bot.send_message(
                chat_id=user['telegram_id'],
                text=notification_text,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
            
        except Exception as e:
            logger.error(f"Error sending staff confirmation message to user {user['id']}: {e}")
            raise
    
    async def send_staff_workflow_notification(self, role: str, request_id: str, 
                                             workflow_type: str, creator_role: str,
                                             client_name: str, request_data: Dict[str, Any]) -> bool:
        """Send notification to workflow participants about staff-created application"""
        # Exclude client and admin roles from notification system
        if role in self.excluded_roles:
            logger.info(f"Skipping workflow notification for excluded role: {role}")
            return True
        
        pool = self._get_pool()
        if not pool:
            logger.error("No database pool available")
            return False
        
        try:
            async with pool.acquire() as conn:
                # Get all users with the specified role who have telegram_id
                users_query = """
                SELECT id, telegram_id, full_name, language
                FROM users 
                WHERE role = $1 AND telegram_id IS NOT NULL AND is_active = true
                """
                
                users = await conn.fetch(users_query, role)
                
                if not users:
                    logger.warning(f"No active users found for role: {role}")
                    return False
                
                sent_count = 0
                
                for user in users:
                    try:
                        # Create notification record
                        notification_id = self._generate_notification_id()
                        
                        await conn.execute(
                            """
                            INSERT INTO pending_notifications 
                            (id, user_id, request_id, workflow_type, role, created_at, is_handled)
                            VALUES ($1, $2, $3, $4, $5, $6, $7)
                            """,
                            notification_id,
                            user['id'],
                            request_id,
                            workflow_type,
                            role,
                            datetime.now(),
                            False
                        )
                        
                        # Send workflow participant notification message
                        await self._send_staff_workflow_message(
                            user, request_id, workflow_type, creator_role, 
                            client_name, request_data, notification_id
                        )
                        
                        sent_count += 1
                        logger.info(f"Sent staff workflow notification to user {user['id']} for request {request_id}")
                        
                    except Exception as e:
                        logger.error(f"Failed to send staff workflow notification to user {user['id']}: {e}")
                        continue
                
                logger.info(f"Sent {sent_count} staff workflow notifications for request {request_id} to role {role}")
                return sent_count > 0
                
        except Exception as e:
            logger.error(f"Error sending staff workflow notification: {e}", exc_info=True)
            return False
    
    async def _send_staff_workflow_message(self, user: Dict[str, Any], request_id: str, 
                                         workflow_type: str, creator_role: str,
                                         client_name: str, request_data: Dict[str, Any],
                                         notification_id: str):
        """Send staff workflow notification message to workflow participant via Telegram"""
        try:
            from loader import bot
            
            lang = user.get('language', 'ru')
            
            # Get template based on workflow type and language
            template_key = 'connection_request' if workflow_type == 'connection_request' else 'technical_service'
            template = self.staff_notification_templates['workflow_participant'][lang][template_key]
            
            # Format creator role for display
            creator_role_display = self._format_creator_role(creator_role, lang)
            
            # Format notification text
            notification_text = template['body'].format(
                client_name=client_name,
                description=request_data.get('description', '')[:100],
                location=request_data.get('location', ''),
                creator_role=creator_role_display,
                request_id=request_id[:8],
                created_at=datetime.now().strftime('%d.%m.%Y %H:%M')
            )
            
            # Create view assignments button (reuse existing functionality)
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text=template['button'],
                    callback_data=f"view_assignments_{notification_id}"
                )]
            ])
            
            await bot.send_message(
                chat_id=user['telegram_id'],
                text=notification_text,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
            
        except Exception as e:
            logger.error(f"Error sending staff workflow message to user {user['id']}: {e}")
            raise
    
    def _format_creator_role(self, creator_role: str, lang: str) -> str:
        """Format creator role for display in notifications"""
        role_translations = {
            'uz': {
                'manager': 'Menejer',
                'junior_manager': 'Kichik menejer',
                'controller': 'Nazoratchi',
                'call_center': 'Call-markaz operatori',
                'call_center_supervisor': 'Call-markaz supervayzer'
            },
            'ru': {
                'manager': 'Менеджер',
                'junior_manager': 'Младший менеджер',
                'controller': 'Контроллер',
                'call_center': 'Оператор call-центра',
                'call_center_supervisor': 'Супервайзер call-центра'
            }
        }
        
        return role_translations.get(lang, {}).get(creator_role, creator_role)
    
    async def handle_notification_reply(self, user_id: int, callback_data: str) -> Dict[str, Any]:
        """Displays all pending assignments for user"""
        pool = self._get_pool()
        if not pool:
            logger.error("No database pool available")
            return {'success': False, 'error': 'Database unavailable'}
        
        try:
            async with pool.acquire() as conn:
                # Get user info
                user_query = """
                SELECT id, role, language, full_name
                FROM users
                WHERE id = $1
                """
                
                user = await conn.fetchrow(user_query, user_id)
                if not user:
                    return {'success': False, 'error': 'User not found'}
                
                # Get all pending requests for user's role
                requests_query = """
                SELECT sr.id, sr.workflow_type, sr.description, sr.priority, 
                       sr.created_at, sr.current_status, sr.location
                FROM service_requests sr
                WHERE sr.role_current = $1 AND sr.current_status != 'completed'
                ORDER BY sr.priority DESC, sr.created_at ASC
                """
                
                requests = await conn.fetch(requests_query, user['role'])
                
                lang = user.get('language', 'ru')
                
                if not requests:
                    if lang == 'uz':
                        message_text = (
                            f"📋 Sizga tayinlangan topshiriqlar\n\n"
                            f"❌ Hozirda sizga tayinlangan topshiriqlar yo'q."
                        )
                    else:
                        message_text = (
                            f"📋 Назначенные вам задания\n\n"
                            f"❌ В настоящее время у вас нет назначенных заданий."
                        )
                    
                    return {
                        'success': True,
                        'message_text': message_text,
                        'keyboard': None
                    }
                
                # Build assignments list
                if lang == 'uz':
                    message_text = f"📋 Sizga tayinlangan topshiriqlar ({len(requests)} ta):\n\n"
                    workflow_names = {
                        'connection_request': 'Ulanish',
                        'technical_service': 'Texnik',
                        'call_center_direct': 'Call-markaz'
                    }
                    priority_names = {
                        'low': 'Past',
                        'medium': 'O\'rta',
                        'high': 'Yuqori',
                        'urgent': 'Shoshilinch'
                    }
                else:
                    message_text = f"📋 Назначенные вам задания ({len(requests)} шт.):\n\n"
                    workflow_names = {
                        'connection_request': 'Подключение',
                        'technical_service': 'Техническое',
                        'call_center_direct': 'Call-центр'
                    }
                    priority_names = {
                        'low': 'Низкий',
                        'medium': 'Средний',
                        'high': 'Высокий',
                        'urgent': 'Срочный'
                    }
                
                # Create inline keyboard with request buttons
                keyboard_buttons = []
                
                for i, request in enumerate(requests, 1):
                    workflow_name = workflow_names.get(request['workflow_type'], request['workflow_type'])
                    priority_name = priority_names.get(request['priority'], request['priority'])
                    
                    # Priority emoji
                    priority_emoji = {
                        'low': '🟢',
                        'medium': '🟡',
                        'high': '🟠',
                        'urgent': '🔴'
                    }.get(request['priority'], '⚪')
                    
                    message_text += (
                        f"{priority_emoji} <b>{i}. {workflow_name}</b>\n"
                        f"   📝 {request['description'][:60]}...\n"
                        f"   ⚡ {priority_name} | 📅 {request['created_at'].strftime('%d.%m %H:%M')}\n"
                    )
                    
                    if request['location']:
                        location_text = "📍 Manzil" if lang == 'uz' else "📍 Адрес"
                        message_text += f"   {location_text}: {request['location'][:40]}...\n"
                    
                    message_text += "\n"
                    
                    # Add button for each request
                    button_text = f"{i}. {workflow_name} ({priority_name})"
                    keyboard_buttons.append([
                        InlineKeyboardButton(
                            text=button_text,
                            callback_data=f"handle_request_{request['id']}"
                        )
                    ])
                
                # Add refresh button
                refresh_text = "🔄 Yangilash" if lang == 'uz' else "🔄 Обновить"
                keyboard_buttons.append([
                    InlineKeyboardButton(
                        text=refresh_text,
                        callback_data=f"refresh_assignments_{user_id}"
                    )
                ])
                
                keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
                
                return {
                    'success': True,
                    'message_text': message_text,
                    'keyboard': keyboard
                }
                
        except Exception as e:
            logger.error(f"Error handling notification reply: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    async def mark_notification_handled(self, user_id: int, request_id: str) -> bool:
        """Marks notification as handled when task completed"""
        pool = self._get_pool()
        if not pool:
            logger.error("No database pool available")
            return False
        
        try:
            async with pool.acquire() as conn:
                # Mark notification as handled
                result = await conn.execute(
                    """
                    UPDATE pending_notifications 
                    SET is_handled = true, handled_at = $3
                    WHERE user_id = $1 AND request_id = $2 AND is_handled = false
                    """,
                    user_id, request_id, datetime.now()
                )
                
                logger.info(f"Marked notification as handled for user {user_id}, request {request_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error marking notification as handled: {e}", exc_info=True)
            return False
    
    async def get_pending_notifications(self, user_id: int) -> List[Dict[str, Any]]:
        """Returns all unhandled notifications for user"""
        pool = self._get_pool()
        if not pool:
            logger.error("No database pool available")
            return []
        
        try:
            async with pool.acquire() as conn:
                query = """
                SELECT pn.id, pn.request_id, pn.workflow_type, pn.role, pn.created_at,
                       sr.description, sr.priority, sr.current_status
                FROM pending_notifications pn
                JOIN service_requests sr ON pn.request_id = sr.id
                WHERE pn.user_id = $1 AND pn.is_handled = false
                ORDER BY pn.created_at DESC
                """
                
                rows = await conn.fetch(query, user_id)
                
                notifications = []
                for row in rows:
                    notifications.append({
                        'notification_id': row['id'],
                        'request_id': row['request_id'],
                        'workflow_type': row['workflow_type'],
                        'role': row['role'],
                        'created_at': row['created_at'],
                        'description': row['description'],
                        'priority': row['priority'],
                        'current_status': row['current_status']
                    })
                
                logger.info(f"Retrieved {len(notifications)} pending notifications for user {user_id}")
                return notifications
                
        except Exception as e:
            logger.error(f"Error getting pending notifications: {e}", exc_info=True)
            return []
    
    async def cleanup_handled_notifications(self, older_than_days: int = 7) -> int:
        """Cleanup old handled notifications"""
        pool = self._get_pool()
        if not pool:
            logger.error("No database pool available")
            return 0
        
        try:
            async with pool.acquire() as conn:
                # Delete handled notifications older than specified days
                result = await conn.execute(
                    """
                    DELETE FROM pending_notifications 
                    WHERE is_handled = true 
                    AND handled_at < NOW() - INTERVAL '%s days'
                    """,
                    older_than_days
                )
                
                # Extract number of deleted rows from result
                deleted_count = int(result.split()[-1]) if result.startswith('DELETE') else 0
                
                logger.info(f"Cleaned up {deleted_count} old handled notifications")
                return deleted_count
                
        except Exception as e:
            logger.error(f"Error cleaning up notifications: {e}", exc_info=True)
            return 0
    
    async def get_notification_stats(self, role: str = None) -> Dict[str, Any]:
        """Get notification statistics"""
        pool = self._get_pool()
        if not pool:
            logger.error("No database pool available")
            return {}
        
        try:
            async with pool.acquire() as conn:
                base_query = """
                SELECT 
                    COUNT(*) as total_notifications,
                    COUNT(CASE WHEN is_handled = false THEN 1 END) as pending_notifications,
                    COUNT(CASE WHEN is_handled = true THEN 1 END) as handled_notifications,
                    role
                FROM pending_notifications
                """
                
                if role:
                    base_query += " WHERE role = $1"
                    params = [role]
                else:
                    params = []
                
                base_query += " GROUP BY role"
                
                rows = await conn.fetch(base_query, *params)
                
                stats = {}
                for row in rows:
                    stats[row['role']] = {
                        'total': row['total_notifications'],
                        'pending': row['pending_notifications'],
                        'handled': row['handled_notifications']
                    }
                
                logger.info(f"Retrieved notification stats: {stats}")
                return stats
                
        except Exception as e:
            logger.error(f"Error getting notification stats: {e}", exc_info=True)
            return {}


class NotificationSystemFactory:
    """Factory for creating notification system instances"""
    
    @staticmethod
    def create_notification_system() -> NotificationSystem:
        """Creates a new notification system instance"""
        return NotificationSystem()