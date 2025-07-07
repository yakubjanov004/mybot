from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from datetime import datetime

from database.queries import (
    UserQueries,
    ReportQueries,
    FeedbackQueries
)
from keyboards.controllers_buttons import quality_control_menu, back_to_controllers_menu
from states.controllers_states import ControllersStates
from utils.logger import logger

def get_controller_quality_router():
    router = Router()

    @router.message(F.text.in_(["🎯 Sifat nazorati", "🎯 Контроль качества"]))
    async def quality_control_menu_handler(message: Message, state: FSMContext):
        """Sifat nazorati menyusi"""
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user or user['role'] != 'controller':
            return
        
        lang = user.get('language', 'uz')
        await state.set_state(ControllersStates.quality_control)
        
        # Sifat ko'rsatkichlarini olish
        quality_metrics = await get_service_quality_metrics()
        
        if lang == 'uz':
            text = f"""🎯 <b>Sifat nazorati</b>

⭐ <b>Xizmat sifati ko'rsatkichlari:</b>
• O'rtacha baho: {quality_metrics.get('avg_rating', 0):.1f}/5.0
• Jami sharhlar: {quality_metrics.get('total_reviews', 0)}
• Mijoz qoniqishi: {quality_metrics.get('satisfaction_rate', 0)}%

Kerakli bo'limni tanlang:"""
        else:
            text = f"""🎯 <b>Контроль качества</b>

⭐ <b>Показатели качества услуг:</b>
• Средняя оценка: {quality_metrics.get('avg_rating', 0):.1f}/5.0
• Всего отзывов: {quality_metrics.get('total_reviews', 0)}
• Удовлетворенность клиентов: {quality_metrics.get('satisfaction_rate', 0)}%

Выберите нужный раздел:"""
        
        await message.answer(
            text,
            reply_markup=quality_control_menu(lang),
            parse_mode='HTML'
        )

    @router.message(F.text.in_(["💬 Mijoz fikrlari", "💬 Отзывы клиентов"]))
    async def customer_feedback_view(message: Message, state: FSMContext):
        """Mijoz fikrilarini ko'rish"""
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user or user['role'] != 'controller':
            return
        
        lang = user.get('language', 'uz')
        feedback_list = await get_recent_feedback(days=7)
        
        if lang == 'uz':
            text = "💬 <b>So'nggi mijoz fikrlari (7 kun):</b>\n\n"
        else:
            text = "💬 <b>Последние отзывы клиентов (7 дней):</b>\n\n"
        
        if feedback_list:
            for feedback in feedback_list[:10]:
                stars = "⭐" * feedback['rating']
                client_name = feedback.get('client_name', 'Noma\'lum')
                comment = feedback.get('comment', '')
                created_date = feedback.get('created_at', '')
                
                text += f"{stars} <b>{client_name}</b>\n"
                if comment:
                    comment_preview = comment[:80] + "..." if len(comment) > 80 else comment
                    text += f"💭 {comment_preview}\n"
                text += f"📅 {created_date}\n\n"
        else:
            no_feedback_text = "So'nggi fikrlar topilmadi" if lang == 'uz' else "Последние отзывы не найдены"
            text += no_feedback_text
        
        await message.answer(text, parse_mode='HTML')

    @router.message(F.text.in_(["⚠️ Muammoli holatlar", "⚠️ Проблемные ситуации"]))
    async def unresolved_issues_view(message: Message, state: FSMContext):
        """Muammoli holatlarni ko'rish"""
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user or user['role'] != 'controller':
            return
        
        lang = user.get('language', 'uz')
        issues = await get_unresolved_issues()
        
        if lang == 'uz':
            text = "⚠️ <b>Hal etilmagan muammolar:</b>\n\n"
        else:
            text = "⚠️ <b>Нерешенные проблемы:</b>\n\n"
        
        if issues:
            for issue in issues[:10]:
                order_id = issue.get('id', 'N/A')
                client_name = issue.get('client_name', 'Noma\'lum')
                description = issue.get('description', '')
                days_pending = issue.get('days_pending', 0)
                
                urgency_icon = "🔴" if days_pending > 5 else "🟡" if days_pending > 2 else "🟢"
                
                text += f"{urgency_icon} <b>#{order_id}</b> - {client_name}\n"
                if description:
                    desc_preview = description[:60] + "..." if len(description) > 60 else description
                    text += f"📝 {desc_preview}\n"
                
                pending_text = "kun kutmoqda" if lang == 'uz' else "дней ожидания"
                text += f"⏱️ {days_pending} {pending_text}\n\n"
        else:
            no_issues_text = "Hal etilmagan muammolar yo'q" if lang == 'uz' else "Нет нерешенных проблем"
            text += no_issues_text
        
        await message.answer(text, parse_mode='HTML')

    @router.message(F.text.in_(["📊 Sifat baholash", "📊 Оценка качества"]))
    async def service_quality_assessment(message: Message, state: FSMContext):
        """Xizmat sifatini baholash"""
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user or user['role'] != 'controller':
            return
        
        lang = user.get('language', 'uz')
        quality_metrics = await get_service_quality_metrics()
        
        if lang == 'uz':
            text = f"""📊 <b>Xizmat sifatini baholash</b>

⭐ <b>Umumiy ko'rsatkichlar:</b>
• O'rtacha baho: {quality_metrics.get('avg_rating', 0):.1f}/5.0
• Jami sharhlar: {quality_metrics.get('total_reviews', 0)}
• Mijoz qoniqishi: {quality_metrics.get('satisfaction_rate', 0)}%

📈 <b>Baholar taqsimoti:</b>"""
        else:
            text = f"""📊 <b>Оценка качества услуг</b>

⭐ <b>Общие показатели:</b>
• Средняя оценка: {quality_metrics.get('avg_rating', 0):.1f}/5.0
• Всего отзывов: {quality_metrics.get('total_reviews', 0)}
• Удовлетворенность клиентов: {quality_metrics.get('satisfaction_rate', 0)}%

📈 <b>Распределение оценок:</b>"""
        
        # Baholar taqsimoti
        rating_distribution = quality_metrics.get('rating_distribution', {})
        total_reviews = quality_metrics.get('total_reviews', 0)
        
        for rating in range(5, 0, -1):
            count = rating_distribution.get(rating, 0)
            percentage = (count / total_reviews * 100) if total_reviews > 0 else 0
            stars = "⭐" * rating
            text += f"\n{stars} {count} ({percentage:.1f}%)"
        
        # Tavsiyalar
        recommendations_text = "\n\n💡 <b>Tavsiyalar:</b>" if lang == 'uz' else "\n\n💡 <b>Рекомендации:</b>"
        text += recommendations_text
        
        avg_rating = quality_metrics.get('avg_rating', 0)
        if avg_rating < 3.0:
            rec_text = "\n• Xizmat sifatini yaxshilash zarur" if lang == 'uz' else "\n• Необходимо улучшить качество обслуживания"
            text += rec_text
        elif avg_rating < 4.0:
            rec_text = "\n• Yaxshi natija, lekin yaxshilash mumkin" if lang == 'uz' else "\n• Хороший результат, но есть место для улучшения"
            text += rec_text
        else:
            rec_text = "\n• A'lo xizmat sifati saqlanmoqda" if lang == 'uz' else "\n• Отличное качество обслуживания поддерживается"
            text += rec_text
        
        await message.answer(text, parse_mode='HTML')

    @router.message(F.text.in_(["📈 Sifat tendensiyalari", "�� Тенденции качества"]))
    async def quality_trends_view(message: Message, state: FSMContext):
        """Sifat tendensiyalarini ko'rish"""
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user or user['role'] != 'controller':
            return
        
        lang = user.get('language', 'uz')
        trends = await get_quality_trends()
        
        if lang == 'uz':
            text = "📈 <b>Sifat tendensiyalari:</b>\n\n"
        else:
            text = "📈 <b>Тенденции качества:</b>\n\n"
        
        if trends:
            for period in trends[:8]:  # So'nggi 8 hafta
                period_name = period.get('period', '')
                rating = period.get('avg_rating', 0)
                change = period.get('change', 0)
                review_count = period.get('review_count', 0)
                
                trend_icon = "📈" if change > 0 else "📉" if change < 0 else "➡️"
                
                text += f"{trend_icon} <b>{period_name}</b>\n"
                text += f"⭐ Baho: {rating:.1f}"
                
                if change != 0:
                    change_text = f" ({change:+.1f})"
                    text += change_text
                
                reviews_text = "sharh" if lang == 'uz' else "отзывов"
                text += f"\n💬 {review_count} {reviews_text}\n\n"
        else:
            no_trends_text = "Tendensiya ma'lumotlari yo'q" if lang == 'uz' else "Нет данных о тенденциях"
            text += no_trends_text
        
        await message.answer(text, parse_mode='HTML')

    @router.message(F.text.in_(["📋 Sifat hisoboti", "📋 Отчет по качеству"]))
    async def quality_report(message: Message, state: FSMContext):
        """Sifat hisoboti yaratish"""
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user or user['role'] != 'controller':
            return
        
        lang = user.get('language', 'uz')
        
        # Ma'lumotlarni yig'ish
        quality_metrics = await get_service_quality_metrics()
        recent_feedback = await get_recent_feedback(days=30)
        unresolved_issues = await get_unresolved_issues()
        
        if lang == 'uz':
            text = f"""📋 <b>Sifat hisoboti</b>
📅 <b>Sana:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}

⭐ <b>Umumiy ko'rsatkichlar:</b>
• O'rtacha baho: {quality_metrics.get('avg_rating', 0):.1f}/5.0
• Jami sharhlar: {quality_metrics.get('total_reviews', 0)}
• Mijoz qoniqishi: {quality_metrics.get('satisfaction_rate', 0)}%

📈 <b>So'nggi 30 kun faolligi:</b>
• Yangi fikrlar: {len(recent_feedback)}
• Hal etilmagan muammolar: {len(unresolved_issues)}

💡 <b>Tavsiyalar:</b>"""
        else:
            text = f"""📋 <b>Отчет по качеству</b>
📅 <b>Дата:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}

⭐ <b>Общие показатели:</b>
• Средняя оценка: {quality_metrics.get('avg_rating', 0):.1f}/5.0
• Всего отзывов: {quality_metrics.get('total_reviews', 0)}
• Удовлетворенность клиентов: {quality_metrics.get('satisfaction_rate', 0)}%

📈 <b>Активность за последние 30 дней:</b>
• Новые отзывы: {len(recent_feedback)}
• Нерешенные проблемы: {len(unresolved_issues)}

💡 <b>Рекомендации:</b>"""
        
        # Tavsiyalar
        avg_rating = quality_metrics.get('avg_rating', 0)
        if avg_rating < 3.0:
            rec_text = "\n• Xizmat sifatini yaxshilash zarur" if lang == 'uz' else "\n• Необходимо улучшить качество обслуживания"
            text += rec_text
        elif avg_rating < 4.0:
            rec_text = "\n• Yaxshi natija, lekin yaxshilash mumkin" if lang == 'uz' else "\n• Хороший результат, но есть место для улучшения"
            text += rec_text
        else:
            rec_text = "\n• A'lo xizmat sifati saqlanmoqda" if lang == 'uz' else "\n• Отличное качество обслуживания поддерживается"
            text += rec_text
        
        if len(unresolved_issues) > 5:
            urgent_text = "\n• Hal etilmagan muammolarga e'tibor bering" if lang == 'uz' else "\n• Обратите внимание на нерешенные проблемы"
            text += urgent_text
        
        await message.answer(text, parse_mode='HTML')

    return router
