from aiogram import F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from database.warehouse_queries import (
    get_warehouse_user_by_telegram_id, get_warehouse_daily_statistics,
    get_warehouse_weekly_statistics, get_warehouse_monthly_statistics,
    get_inventory_turnover_statistics, get_low_stock_inventory_items
)
from keyboards.warehouse_buttons import warehouse_main_menu, warehouse_statistics_menu, statistics_period_menu
from states.warehouse_states import WarehouseStates
from utils.logger import logger
from utils.role_router import get_role_router
from aiogram.fsm.state import State

# Define states for navigation
class NavigationStates(State):
    MAIN_MENU = "warehouse_main_menu"
    STATISTICS_MENU = "warehouse_statistics_menu"
    PERIOD_MENU = "warehouse_period_menu"
    VIEWING_STATS = "warehouse_viewing_stats"

def get_warehouse_statistics_router():
    router = get_role_router("warehouse")

    @router.message(F.text.in_(["📊 Statistikalar", "📊 Статистика"]))
    async def statistics_handler(message: Message, state: FSMContext):
        """Handle statistics and reports"""
        try:
            user = await get_warehouse_user_by_telegram_id(message.from_user.id)
            if not user:
                return
            
            lang = user.get('language', 'uz')
            stats_text = "📊 Statistika va hisobotlar" if lang == 'uz' else "📊 Статистика и отчеты"
            
            await message.answer(
                stats_text,
                reply_markup=warehouse_statistics_menu(lang)
            )
            await state.set_state(NavigationStates.STATISTICS_MENU)
            
        except Exception as e:
            logger.error(f"Error in statistics handler: {str(e)}")

    @router.callback_query(F.data == "daily_statistics")
    async def daily_statistics_handler(callback: CallbackQuery, state: FSMContext):
        """Show daily statistics"""
        try:
            user = await get_warehouse_user_by_telegram_id(callback.from_user.id)
            lang = user.get('language', 'uz')
            
            stats = await get_warehouse_daily_statistics()
            
            if stats:
                daily_text = "📊 Bugungi statistika:" if lang == 'uz' else "📊 Статистика за сегодня:"
                text = f"{daily_text}\n\n"
                text += f"📦 Qo'shilgan mahsulotlar: {stats.get('items_added', 0)}\n"
                text += f"📤 Chiqarilgan mahsulotlar: {stats.get('items_issued', 0)}\n"
                text += f"💰 Umumiy qiymat: {stats.get('total_value', 0):,.0f} so'm\n"
                text += f"⚠️ Kam zaxira: {stats.get('low_stock_count', 0)} ta\n"
                text += f"🔄 Aylanma tezligi: {stats.get('turnover_rate', 0)}%\n"
                
                if lang == 'ru':
                    text = f"{daily_text}\n\n"
                    text += f"📦 Добавлено товаров: {stats.get('items_added', 0)}\n"
                    text += f"📤 Выдано товаров: {stats.get('items_issued', 0)}\n"
                    text += f"💰 Общая стоимость: {stats.get('total_value', 0):,.0f} сум\n"
                    text += f"⚠️ Низкий запас: {stats.get('low_stock_count', 0)} шт\n"
                    text += f"🔄 Оборачиваемость: {stats.get('turnover_rate', 0)}%\n"
            else:
                text = "❌ Statistika ma'lumotlari topilmadi" if lang == 'uz' else "❌ Статистические данные не найдены"
            
            await callback.message.edit_text(text)
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Error getting daily statistics: {str(e)}")
            error_text = "Statistikani olishda xatolik" if lang == 'uz' else "Ошибка при получении статистики"
            await callback.message.edit_text(error_text)
            await callback.answer()

    @router.callback_query(F.data == "weekly_statistics")
    async def weekly_statistics_handler(callback: CallbackQuery, state: FSMContext):
        """Show weekly statistics"""
        try:
            user = await get_warehouse_user_by_telegram_id(callback.from_user.id)
            lang = user.get('language', 'uz')
            
            stats = await get_warehouse_weekly_statistics()
            
            if stats:
                weekly_text = "📊 Haftalik statistika:" if lang == 'uz' else "📊 Статистика за неделю:"
                text = f"{weekly_text}\n\n"
                text += f"📦 Qo'shilgan mahsulotlar: {stats.get('items_added', 0)}\n"
                text += f"📤 Chiqarilgan mahsulotlar: {stats.get('items_issued', 0)}\n"
                text += f"💰 Umumiy qiymat: {stats.get('total_value', 0):,.0f} so'm\n"
                text += f"⚠️ Kam zaxira: {stats.get('low_stock_count', 0)} ta\n"
                text += f"🔄 Aylanma tezligi: {stats.get('turnover_rate', 0)}%\n"
                
                if lang == 'ru':
                    text = f"{weekly_text}\n\n"
                    text += f"📦 Добавлено товаров: {stats.get('items_added', 0)}\n"
                    text += f"📤 Выдано товаров: {stats.get('items_issued', 0)}\n"
                    text += f"💰 Общая стоимость: {stats.get('total_value', 0):,.0f} сум\n"
                    text += f"⚠️ Низкий запас: {stats.get('low_stock_count', 0)} шт\n"
                    text += f"🔄 Оборачиваемость: {stats.get('turnover_rate', 0)}%\n"
            else:
                text = "❌ Statistika ma'lumotlari topilmadi" if lang == 'uz' else "❌ Статистические данные не найдены"
            
            await callback.message.edit_text(text)
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Error getting weekly statistics: {str(e)}")
            error_text = "Statistikani olishda xatolik" if lang == 'uz' else "Ошибка при получении статистики"
            await callback.message.edit_text(error_text)
            await callback.answer()

    @router.callback_query(F.data == "monthly_statistics")
    async def monthly_statistics_handler(callback: CallbackQuery, state: FSMContext):
        """Show monthly statistics"""
        try:
            user = await get_warehouse_user_by_telegram_id(callback.from_user.id)
            lang = user.get('language', 'uz')
            
            stats = await get_warehouse_monthly_statistics()
            
            if stats:
                monthly_text = "📊 Oylik statistika:" if lang == 'uz' else "📊 Статистика за месяц:"
                text = f"{monthly_text}\n\n"
                text += f"📦 Qo'shilgan mahsulotlar: {stats.get('items_added', 0)}\n"
                text += f"📤 Chiqarilgan mahsulotlar: {stats.get('items_issued', 0)}\n"
                text += f"💰 Umumiy qiymat: {stats.get('total_value', 0):,.0f} so'm\n"
                text += f"⚠️ Kam zaxira: {stats.get('low_stock_count', 0)} ta\n"
                text += f"🔄 Aylanma tezligi: {stats.get('turnover_rate', 0)}%\n"
                
                if lang == 'ru':
                    text = f"{monthly_text}\n\n"
                    text += f"📦 Добавлено товаров: {stats.get('items_added', 0)}\n"
                    text += f"📤 Выдано товаров: {stats.get('items_issued', 0)}\n"
                    text += f"💰 Общая стоимость: {stats.get('total_value', 0):,.0f} сум\n"
                    text += f"⚠️ Низкий запас: {stats.get('low_stock_count', 0)} шт\n"
                    text += f"🔄 Оборачиваемость: {stats.get('turnover_rate', 0)}%\n"
            else:
                text = "❌ Statistika ma'lumotlari topilmadi" if lang == 'uz' else "❌ Статистические данные не найдены"
            
            await callback.message.edit_text(text)
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Error getting monthly statistics: {str(e)}")
            error_text = "Statistikani olishda xatolik" if lang == 'uz' else "Ошибка при получении статистики"
            await callback.message.edit_text(error_text)
            await callback.answer()

    @router.callback_query(F.data == "turnover_statistics")
    async def turnover_statistics_handler(callback: CallbackQuery, state: FSMContext):
        """Show inventory turnover statistics"""
        try:
            user = await get_warehouse_user_by_telegram_id(callback.from_user.id)
            lang = user.get('language', 'uz')
            
            stats = await get_inventory_turnover_statistics()
            
            if stats and stats.get('top_turnover_items'):
                turnover_text = "🔄 Aylanma statistikasi:" if lang == 'uz' else "🔄 Статистика оборачиваемости:"
                text = f"{turnover_text}\n\n"
                text += f"📊 O'rtacha aylanma: {stats.get('turnover_rate', 0)}%\n\n"
                text += f"🔝 Eng ko'p aylangan mahsulotlar:\n" if lang == 'uz' else f"🔝 Наиболее оборачиваемые товары:\n"
                
                for i, item in enumerate(stats['top_turnover_items'][:5], 1):
                    text += f"{i}. **{item['name']}**\n"
                    text += f"   📦 Zaxira: {item['current_stock']}\n"
                    text += f"   📤 Chiqarilgan: {item['issued_quantity']}\n"
                    text += f"   🔄 Aylanma: {item['turnover_rate']}%\n\n"
            else:
                text = "❌ Aylanma statistikasi topilmadi" if lang == 'uz' else "❌ Статистика оборачиваемости не найдена"
            
            await callback.message.edit_text(text, parse_mode="Markdown")
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Error getting turnover statistics: {str(e)}")
            error_text = "Statistikani olishda xatolik" if lang == 'uz' else "Ошибка при получении статистики"
            await callback.message.edit_text(error_text)
            await callback.answer()

    @router.callback_query(F.data == "performance_report")
    async def performance_report_handler(callback: CallbackQuery, state: FSMContext):
        """Show performance report"""
        try:
            user = await get_warehouse_user_by_telegram_id(callback.from_user.id)
            lang = user.get('language', 'uz')
            
            # Get all statistics for comprehensive report
            daily_stats = await get_warehouse_daily_statistics()
            weekly_stats = await get_warehouse_weekly_statistics()
            monthly_stats = await get_warehouse_monthly_statistics()
            
            performance_text = "📈 Samaradorlik hisoboti:" if lang == 'uz' else "📈 Отчет о производительности:"
            text = f"{performance_text}\n\n"
            
            # Daily performance
            text += f"📅 **Bugun:**\n" if lang == 'uz' else f"📅 **Сегодня:**\n"
            text += f"   📦 Qo'shilgan: {daily_stats.get('items_added', 0)}\n"
            text += f"   📤 Chiqarilgan: {daily_stats.get('items_issued', 0)}\n"
            text += f"   🔄 Aylanma: {daily_stats.get('turnover_rate', 0)}%\n\n"
            
            # Weekly performance
            text += f"📅 **Bu hafta:**\n" if lang == 'uz' else f"📅 **На этой неделе:**\n"
            text += f"   📦 Qo'shilgan: {weekly_stats.get('items_added', 0)}\n"
            text += f"   📤 Chiqarilgan: {weekly_stats.get('items_issued', 0)}\n"
            text += f"   🔄 Aylanma: {weekly_stats.get('turnover_rate', 0)}%\n\n"
            
            # Monthly performance
            text += f"📅 **Bu oy:**\n" if lang == 'uz' else f"📅 **В этом месяце:**\n"
            text += f"   📦 Qo'shilgan: {monthly_stats.get('items_added', 0)}\n"
            text += f"   📤 Chiqarilgan: {monthly_stats.get('items_issued', 0)}\n"
            text += f"   🔄 Aylanma: {monthly_stats.get('turnover_rate', 0)}%\n\n"
            
            # Overall status
            total_value = monthly_stats.get('total_value', 0)
            low_stock = monthly_stats.get('low_stock_count', 0)
            
            text += f"💰 **Umumiy qiymat:** {total_value:,.0f} so'm\n"
            text += f"⚠️ **Kam zaxira:** {low_stock} ta mahsulot\n"
            
            if lang == 'ru':
                text = text.replace('Bugun:', 'Сегодня:')
                text = text.replace('Bu hafta:', 'На этой неделе:')
                text = text.replace('Bu oy:', 'В этом месяце:')
                text = text.replace('Qo\'shilgan:', 'Добавлено:')
                text = text.replace('Chiqarilgan:', 'Выдано:')
                text = text.replace('Aylanma:', 'Оборачиваемость:')
                text = text.replace('Umumiy qiymat:', 'Общая стоимость:')
                text = text.replace('Kam zaxira:', 'Низкий запас:')
                text = text.replace('ta mahsulot', 'товаров')
            
            await callback.message.edit_text(text, parse_mode="Markdown")
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Error getting performance report: {str(e)}")
            error_text = "Hisobotni olishda xatolik" if lang == 'uz' else "Ошибка при получении отчета"
            await callback.message.edit_text(error_text)
            await callback.answer()

    @router.message(F.text.in_(['📦 Inventarizatsiya statistikasi', '📦 Статистика инвентаризации']))
    async def inventory_stats_reply_handler(message: Message, state: FSMContext):
        user = await get_warehouse_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        stats = await get_warehouse_daily_statistics()
        if stats:
            if lang == 'uz':
                text = (
                    "📦 Inventarizatsiya statistikasi (bugun):\n\n"
                    f"📦 Qo'shilgan mahsulotlar: {stats.get('items_added', 0)}\n"
                    f"📤 Chiqarilgan mahsulotlar: {stats.get('items_issued', 0)}\n"
                    f"💰 Umumiy qiymat: {stats.get('total_value', 0):,.0f} so'm\n"
                    f"⚠️ Kam zaxira: {stats.get('low_stock_count', 0)} ta\n"
                    f"🔄 Aylanma tezligi: {stats.get('turnover_rate', 0)}%\n"
                )
            else:
                text = (
                    "📦 Статистика инвентаризации (сегодня):\n\n"
                    f"📦 Добавлено товаров: {stats.get('items_added', 0)}\n"
                    f"📤 Выдано товаров: {stats.get('items_issued', 0)}\n"
                    f"💰 Общая стоимость: {stats.get('total_value', 0):,.0f} сум\n"
                    f"⚠️ Низкий запас: {stats.get('low_stock_count', 0)} шт\n"
                    f"🔄 Оборачиваемость: {stats.get('turnover_rate', 0)}%\n"
                )
        else:
            text = "❌ Statistika ma'lumotlari topilmadi" if lang == 'uz' else "❌ Статистические данные не найдены"
        await message.answer(text, reply_markup=warehouse_statistics_menu(lang))
        await state.set_state(WarehouseStates.statistics_menu)

    @router.message(F.text.in_(["📋 Buyurtmalar statistikasi", "📋 Статистика заказов"]))
    async def orders_stats_reply_handler(message: Message, state: FSMContext):
        user = await get_warehouse_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        stats = await get_warehouse_weekly_statistics()
        if stats:
            if lang == 'uz':
                text = (
                    "📋 Buyurtmalar statistikasi (hafta):\n\n"
                    f"📦 Qo'shilgan mahsulotlar: {stats.get('items_added', 0)}\n"
                    f"📤 Chiqarilgan mahsulotlar: {stats.get('items_issued', 0)}\n"
                    f"💰 Umumiy qiymat: {stats.get('total_value', 0):,.0f} so'm\n"
                    f"⚠️ Kam zaxira: {stats.get('low_stock_count', 0)} ta\n"
                    f"🔄 Aylanma tezligi: {stats.get('turnover_rate', 0)}%\n"
                )
            else:
                text = (
                    "📋 Статистика заказов (неделя):\n\n"
                    f"📦 Добавлено товаров: {stats.get('items_added', 0)}\n"
                    f"📤 Выдано товаров: {stats.get('items_issued', 0)}\n"
                    f"💰 Общая стоимость: {stats.get('total_value', 0):,.0f} сум\n"
                    f"⚠️ Низкий запас: {stats.get('low_stock_count', 0)} шт\n"
                    f"🔄 Оборачиваемость: {stats.get('turnover_rate', 0)}%\n"
                )
        else:
            text = "❌ Statistika ma'lumotlari topilmadi" if lang == 'uz' else "❌ Статистические данные не найдены"
        await message.answer(text, reply_markup=warehouse_statistics_menu(lang))
        await state.set_state(WarehouseStates.statistics_menu)

    @router.message(F.text.in_(["⚠️ Kam zaxira statistikasi", "⚠️ Статистика низкого запаса"]))
    async def low_stock_stats_reply_handler(message: Message, state: FSMContext):
        user = await get_warehouse_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        items = await get_low_stock_inventory_items()
        if items:
            if lang == 'uz':
                text = f"⚠️ Kam zaxira statistikasi:\n\n" + "\n".join([
                    f"{i+1}. {item['name']} — {item['quantity']} dona (min: {item['min_quantity']})" for i, item in enumerate(items)
                ])
            else:
                text = f"⚠️ Статистика низкого запаса:\n\n" + "\n".join([
                    f"{i+1}. {item['name']} — {item['quantity']} шт (мин: {item['min_quantity']})" for i, item in enumerate(items)
                ])
        else:
            text = "📦 Barcha mahsulotlar zaxirasi yetarli" if lang == 'uz' else "📦 Все товары в достаточном количестве"
        await message.answer(text, reply_markup=warehouse_statistics_menu(lang))
        await state.set_state(WarehouseStates.statistics_menu)

    @router.message(F.text.in_(["💰 Moliyaviy hisobot", "💰 Финансовый отчет"]))
    async def financial_stats_reply_handler(message: Message, state: FSMContext):
        user = await get_warehouse_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        stats = await get_warehouse_monthly_statistics()
        if stats:
            if lang == 'uz':
                text = (
                    "💰 Moliyaviy hisobot (oy):\n\n"
                    f"📦 Omborga kiritilgan mahsulotlar: {stats.get('items_added', 0)} dona\n"
                    f"📤 Ombordan chiqarilgan mahsulotlar: {stats.get('items_issued', 0)} dona\n"
                    f"💰 Umumiy qiymat: {stats.get('total_value', 0):,.0f} so'm\n"
                )
            else:
                text = (
                    "💰 Финансовый отчет (месяц):\n\n"
                    f"📦 Поступило на склад: {stats.get('items_added', 0)} шт\n"
                    f"📤 Выдано со склада: {stats.get('items_issued', 0)} шт\n"
                    f"💰 Общая стоимость: {stats.get('total_value', 0):,.0f} сум\n"
                )
        else:
            text = "❌ Statistika ma'lumotlari topilmadi" if lang == 'uz' else "❌ Статистические данные не найдены"
        await message.answer(text, reply_markup=warehouse_statistics_menu(lang))
        await state.set_state(WarehouseStates.statistics_menu)

    @router.message(F.text.in_(["📆 Vaqt oralig'idagi statistika", "📆 Статистика за период"]))
    async def period_stats_reply_handler(message: Message, state: FSMContext):
        user = await get_warehouse_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        await message.answer(
            "Qaysi davr uchun statistikani ko'rmoqchisiz?" if lang == 'uz' else "За какой период показать статистику?",
            reply_markup=statistics_period_menu(lang)
        )
        await state.set_state(NavigationStates.PERIOD_MENU)

    @router.message(F.text.in_(['📈 Oylik statistika', '📈 Месячная статистика']))
    async def monthly_stats_reply_handler(message: Message, state: FSMContext):
        user = await get_warehouse_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        stats = await get_warehouse_monthly_statistics()
        if stats:
            if lang == 'uz':
                text = (
                    "📈 Oylik statistika:\n\n"
                    f"📦 Qo'shilgan mahsulotlar: {stats.get('items_added', 0)}\n"
                    f"📤 Chiqarilgan mahsulotlar: {stats.get('items_issued', 0)}\n"
                    f"💰 Umumiy qiymat: {stats.get('total_value', 0):,.0f} so'm\n"
                    f"⚠️ Kam zaxira: {stats.get('low_stock_count', 0)} ta\n"
                    f"🔄 Aylanma tezligi: {stats.get('turnover_rate', 0)}%\n"
                )
            else:
                text = (
                    "📈 Месячная статистика:\n\n"
                    f"📦 Добавлено товаров: {stats.get('items_added', 0)}\n"
                    f"📤 Выдано товаров: {stats.get('items_issued', 0)}\n"
                    f"💰 Общая стоимость: {stats.get('total_value', 0):,.0f} сум\n"
                    f"⚠️ Низкий запас: {stats.get('low_stock_count', 0)} шт\n"
                    f"🔄 Оборачиваемость: {stats.get('turnover_rate', 0)}%\n"
                )
        else:
            text = "❌ Statistika ma'lumotlari topilmadi" if lang == 'uz' else "❌ Статистические данные не найдены"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Orqaga" if lang == 'uz' else "◀️ Назад", callback_data="back")]
        ])
        await message.answer(text, reply_markup=keyboard)
        await state.set_state(NavigationStates.VIEWING_STATS)

    @router.message(F.text.in_(['📅 Kunlik statistika', '📅 Ежедневная статистика']))
    async def daily_stats_reply_handler(message: Message, state: FSMContext):
        user = await get_warehouse_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        stats = await get_warehouse_daily_statistics()
        if stats:
            if lang == 'uz':
                text = (
                    "📅 Kunlik statistika:\n\n"
                    f"📦 Qo'shilgan mahsulotlar: {stats.get('items_added', 0)}\n"
                    f"📤 Chiqarilgan mahsulotlar: {stats.get('items_issued', 0)}\n"
                    f"💰 Umumiy qiymat: {stats.get('total_value', 0):,.0f} so'm\n"
                    f"⚠️ Kam zaxira: {stats.get('low_stock_count', 0)} ta\n"
                    f"🔄 Aylanма tezligи: {stats.get('turnover_rate', 0)}%\n"
                )
            else:
                text = (
                    "📅 Ежедневная статистика:\n\n"
                    f"📦 Добавлено товаров: {stats.get('items_added', 0)}\n"
                    f"📤 Выдано товаров: {stats.get('items_issued', 0)}\n"
                    f"💰 Общая стоимость: {stats.get('total_value', 0):,.0f} сум\n"
                    f"⚠️ Низкий запас: {stats.get('low_stock_count', 0)} шт\n"
                    f"🔄 Оборачиваемость: {stats.get('turnover_rate', 0)}%\n"
                )
        else:
            text = "❌ Statistika ma'lumotlari topilmadi" if lang == 'uz' else "❌ Статистические данные не найдены"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Orqaga" if lang == 'uz' else "◀️ Назад", callback_data="back")]
        ])
        await message.answer(text, reply_markup=keyboard)
        await state.set_state(NavigationStates.VIEWING_STATS)

    @router.message(F.text.in_(['📊 Haftalik statistika', '📊 Недельная статистика']))
    async def weekly_stats_reply_handler(message: Message, state: FSMContext):
        user = await get_warehouse_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        stats = await get_warehouse_weekly_statistics()
        if stats:
            if lang == 'uz':
                text = (
                    "📊 Haftalik statistika:\n\n"
                    f"📦 Qo'shilgan mahsulotlar: {stats.get('items_added', 0)}\n"
                    f"📤 Chiqarilgan mahsulotlar: {stats.get('items_issued', 0)}\n"
                    f"💰 Umumiy qiymat: {stats.get('total_value', 0):,.0f} so'm\n"
                    f"⚠️ Kam zaxira: {stats.get('low_stock_count', 0)} ta\n"
                    f"🔄 Aylanма tezligи: {stats.get('turnover_rate', 0)}%\n"
                )
            else:
                text = (
                    "📊 Недельная статистика:\n\n"
                    f"📦 Добавлено товаров: {stats.get('items_added', 0)}\n"
                    f"📤 Выдано товаров: {stats.get('items_issued', 0)}\n"
                    f"💰 Общая стоимость: {stats.get('total_value', 0):,.0f} сум\n"
                    f"⚠️ Низкий запас: {stats.get('low_stock_count', 0)} шт\n"
                    f"🔄 Оборачиваемость: {stats.get('turnover_rate', 0)}%\n"
                )
        else:
            text = "❌ Statistika ma'lumotlari topilmadi" if lang == 'uz' else "❌ Статистические данные не найдены"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Orqaga" if lang == 'uz' else "◀️ Назад", callback_data="back")]
        ])
        await message.answer(text, reply_markup=keyboard)
        await state.set_state(NavigationStates.VIEWING_STATS)

    @router.message(F.text.in_(['🗓 Yillik statistika', '🗓 Годовая статистика']))
    async def yearly_stats_reply_handler(message: Message, state: FSMContext):
        user = await get_warehouse_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        # Yillik statistika uchun alohida query kerak bo'lishi mumkin
        text = "🗓 Yillik statistika: tez orada to'liq statistikalar qo'shiladi." if lang == 'uz' else "🗓 Годовая статистика: скоро будет добавлена."
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Orqaga" if lang == 'uz' else "◀️ Назад", callback_data="back")]
        ])
        await message.answer(text, reply_markup=keyboard)
        await state.set_state(NavigationStates.VIEWING_STATS)

    @router.callback_query(F.data == "back")
    async def statistics_back_reply_handler(callback: CallbackQuery, state: FSMContext):
        user = await get_warehouse_user_by_telegram_id(callback.from_user.id)
        lang = user.get('language', 'uz')
        current_state = await state.get_state()


        if current_state == NavigationStates.VIEWING_STATS:
            # Go back to period menu
            await callback.message.edit_text(
                "Qaysi davr uchun statistikani ko'rmoqchisiz?" if lang == 'uz' else "За какой период показать статистику?",
                reply_markup=statistics_period_menu(lang)
            )
            await state.set_state(NavigationStates.PERIOD_MENU)

        elif current_state == NavigationStates.PERIOD_MENU:
            # Go back to statistics menu
            await callback.message.edit_text(
                "Statistikalar menyusi" if lang == 'uz' else "Меню статистики",
                reply_markup=warehouse_statistics_menu(lang)
            )
            await state.set_state(NavigationStates.STATISTICS_MENU)

        elif current_state == NavigationStates.STATISTICS_MENU:
            # Go back to main menu
            await callback.message.edit_text(
                "Ombor bosh menyusi" if lang == 'uz' else "Главное меню склада",
                reply_markup=warehouse_main_menu(lang)
            )
            await state.set_state(NavigationStates.MAIN_MENU)

    return router
