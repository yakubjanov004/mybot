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
