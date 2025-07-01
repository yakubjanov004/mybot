from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

def warehouse_main_menu(language: str) -> ReplyKeyboardMarkup:
    """Warehouse main menu keyboard"""
    inventory_management_text = "📦 Inventarizatsiya boshqaruvi" if language == "uz" else "📦 Управление инвентаризацией"
    orders_management_text = "📋 Buyurtmalar boshqaruvi" if language == "uz" else "📋 Управление заказами"
    warehouse_statistics_text = "📊 Sklad statistikasi" if language == "uz" else "📊 Статистика склада"
    change_language_text = "🌐 Tilni o'zgartirish" if language == "uz" else "🌐 Изменить язык"
    keyboard = [
        [KeyboardButton(text=inventory_management_text), KeyboardButton(text=orders_management_text)],
        [KeyboardButton(text=warehouse_statistics_text)],
        [KeyboardButton(text=change_language_text)]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def inventory_menu(language: str) -> InlineKeyboardMarkup:
    """Inventory management menu"""
    add_item_text = "➕ Mahsulot qo'shish" if language == "uz" else "➕ Добавить товар"
    update_item_text = "✏️ Mahsulotni yangilash" if language == "uz" else "✏️ Обновить товар"
    low_stock_report_text = "⚠️ Kam zaxira hisoboti" if language == "uz" else "⚠️ Отчет о низком запасе"
    back_text = "◀️ Orqaga" if language == "uz" else "◀️ Назад"
    
    keyboard = [
        [
            InlineKeyboardButton(
                text=add_item_text,
                callback_data="add_inventory_item"
            )
        ],
        [
            InlineKeyboardButton(
                text=update_item_text,
                callback_data="update_inventory_item"
            )
        ],
        [
            InlineKeyboardButton(
                text=low_stock_report_text,
                callback_data="low_stock_report"
            )
        ],
        [
            InlineKeyboardButton(
                text=back_text,
                callback_data="warehouse_back"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def orders_menu(language: str) -> InlineKeyboardMarkup:
    """Orders management menu"""
    pending_orders_text = "⏳ Kutilayotgan buyurtmalar" if language == "uz" else "⏳ Ожидающие заказы"
    in_progress_orders_text = "🔄 Jarayondagi buyurtmalar" if language == "uz" else "🔄 Заказы в процессе"
    completed_orders_text = "✅ Bajarilgan buyurtmalar" if language == "uz" else "✅ Выполненные заказы"
    back_text = "◀️ Orqaga" if language == "uz" else "◀️ Назад"
    
    keyboard = [
        [
            InlineKeyboardButton(
                text=pending_orders_text,
                callback_data="pending_orders"
            )
        ],
        [
            InlineKeyboardButton(
                text=in_progress_orders_text,
                callback_data="in_progress_orders"
            )
        ],
        [
            InlineKeyboardButton(
                text=completed_orders_text,
                callback_data="completed_orders"
            )
        ],
        [
            InlineKeyboardButton(
                text=back_text,
                callback_data="warehouse_back"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def order_status_keyboard(language: str, current_status: str) -> InlineKeyboardMarkup:
    """Order status update keyboard"""
    start_processing_text = "▶️ Qayta ishlashni boshlash" if language == "uz" else "▶️ Начать обработку"
    parts_ready_text = "🔧 Ehtiyot qismlar tayyor" if language == "uz" else "🔧 Запчасти готовы"
    ready_for_technician_text = "👨‍🔧 Texnik uchun tayyor" if language == "uz" else "👨‍🔧 Готово для техника"
    back_text = "◀️ Orqaga" if language == "uz" else "◀️ Назад"
    
    keyboard = []
    
    if current_status == 'confirmed':
        keyboard.append([
            InlineKeyboardButton(
                text=start_processing_text,
                callback_data="update_order_status_in_progress"
            )
        ])
    
    if current_status == 'in_progress':
        keyboard.extend([
            [
                InlineKeyboardButton(
                    text=parts_ready_text,
                    callback_data="update_order_status_parts_ready"
                )
            ],
            [
                InlineKeyboardButton(
                    text=ready_for_technician_text,
                    callback_data="update_order_status_ready_for_tech"
                )
            ]
        ])
    
    keyboard.append([
        InlineKeyboardButton(
            text=back_text,
            callback_data="warehouse_orders"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def inventory_actions_keyboard(language: str) -> InlineKeyboardMarkup:
    """Inventory item actions keyboard"""
    update_quantity_text = "📊 Miqdorni yangilash" if language == "uz" else "📊 Обновить количество"
    set_min_quantity_text = "⚠️ Minimal miqdorni belgilash" if language == "uz" else "⚠️ Установить минимальное количество"
    delete_item_text = "🗑️ Mahsulotni o'chirish" if language == "uz" else "🗑️ Удалить товар"
    back_text = "◀️ Orqaga" if language == "uz" else "◀️ Назад"
    
    keyboard = [
        [
            InlineKeyboardButton(
                text=update_quantity_text,
                callback_data="update_quantity"
            )
        ],
        [
            InlineKeyboardButton(
                text=set_min_quantity_text,
                callback_data="set_min_quantity"
            )
        ],
        [
            InlineKeyboardButton(
                text=delete_item_text,
                callback_data="delete_item"
            )
        ],
        [
            InlineKeyboardButton(
                text=back_text,
                callback_data="warehouse_inventory"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def warehouse_detailed_statistics_menu(language: str) -> InlineKeyboardMarkup:
    """Detailed statistics menu for warehouse"""
    daily_stats = "📅 Kunlik statistika" if language == 'uz' else "📅 Ежедневная статистика"
    weekly_stats = "📊 Haftalik hisobot" if language == 'uz' else "📊 Недельный отчет"
    monthly_stats = "📈 Oylik hisobot" if language == 'uz' else "📈 Месячный отчет"
    back = "◀️ Orqaga" if language == 'uz' else "◀️ Назад"
    keyboard = [
        [InlineKeyboardButton(text=daily_stats, callback_data="warehouse_stats_daily")],
        [InlineKeyboardButton(text=weekly_stats, callback_data="warehouse_stats_weekly")],
        [InlineKeyboardButton(text=monthly_stats, callback_data="warehouse_stats_monthly")],
        [InlineKeyboardButton(text=back, callback_data="warehouse_back")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def inventory_detailed_list_menu(language: str) -> InlineKeyboardMarkup:
    """Detailed inventory list menu"""
    all_items = "📦 Barcha mahsulotlar" if language == 'uz' else "📦 Все товары"
    low_stock = "⚠️ Kam zaxira" if language == 'uz' else "⚠️ Низкий запас"
    out_of_stock = "❌ Zaxira tugagan" if language == 'uz' else "❌ Нет в наличии"
    back = "◀️ Orqaga" if language == 'uz' else "◀️ Назад"
    keyboard = [
        [InlineKeyboardButton(text=all_items, callback_data="inventory_all_items")],
        [InlineKeyboardButton(text=low_stock, callback_data="inventory_low_stock")],
        [InlineKeyboardButton(text=out_of_stock, callback_data="inventory_out_of_stock")],
        [InlineKeyboardButton(text=back, callback_data="warehouse_inventory")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def export_format_keyboard(language: str) -> InlineKeyboardMarkup:
    """Export format selection keyboard"""
    excel = "📊 Excel" if language == 'uz' else "📊 Excel"
    pdf = "📄 PDF" if language == 'uz' else "📄 PDF"
    word = "📝 Word" if language == 'uz' else "📝 Word"
    back = "◀️ Orqaga" if language == 'uz' else "◀️ Назад"
    keyboard = [
        [InlineKeyboardButton(text=excel, callback_data="export_excel")],
        [InlineKeyboardButton(text=pdf, callback_data="export_pdf")],
        [InlineKeyboardButton(text=word, callback_data="export_word")],
        [InlineKeyboardButton(text=back, callback_data="warehouse_back")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
