from aiogram import F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from database.warehouse_queries import (
    get_warehouse_user_by_telegram_id, get_all_inventory_items, 
    add_new_inventory_item, update_inventory_item_data,
    search_inventory_items, get_low_stock_inventory_items,
    get_out_of_stock_items, update_inventory_quantity,
    get_inventory_item_by_id
)
from keyboards.warehouse_buttons import warehouse_inventory_menu, inventory_actions_keyboard, inventory_actions_inline, update_item_fields_inline
from states.warehouse_states import WarehouseInventoryStates, WarehouseMainMenuStates
from utils.logger import logger
from utils.role_router import get_role_router
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Paginatsiya uchun yordamchi funksiya
def build_pagination_keyboard(page: int, total_pages: int, lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    prev = "⬅️ Avvalgi" if lang == 'uz' else "⬅️ Предыдущая"
    next_ = "Keyingisi ➡️" if lang == 'uz' else "Следующая ➡️"
    if page > 1:
        builder.button(text=prev, callback_data=f"inventory_page_{page-1}")
    if page < total_pages:
        builder.button(text=next_, callback_data=f"inventory_page_{page+1}")
    return builder.as_markup()

# Barcha mahsulotlar reply uchun paginatsiyali handler
def chunked(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def get_warehouse_inventory_router():
    router = get_role_router("warehouse")

    @router.message(F.text.in_(["📦 Inventarizatsiya", "📦 Инвентаризация"]))
    async def inventory_management_handler(message: Message, state: FSMContext):
        user = await get_warehouse_user_by_telegram_id(message.from_user.id)
        if not user:
            return
        lang = user.get('language', 'uz')
        await state.update_data(lang=lang)
        inventory_text = "📦 Inventarizatsiya boshqaruvi" if lang == 'uz' else "📦 Управление инвентаризацией"
        await message.answer(
            inventory_text,
            reply_markup=warehouse_inventory_menu(lang)
        )
        await state.set_state(WarehouseInventoryStates.inventory_menu)

    @router.callback_query(F.data == "view_inventory_list")
    async def view_inventory_list(callback: CallbackQuery, state: FSMContext):
        """View complete inventory list"""
        try:
            user = await get_warehouse_user_by_telegram_id(callback.from_user.id)
            lang = user.get('language', 'uz')
            
            items = await get_all_inventory_items()
            
            if items:
                inventory_text = "📋 Inventar ro'yxati:" if lang == 'uz' else "📋 Список инвентаря:"
                text = f"{inventory_text}\n\n"
                
                for item in items:
                    status_icon = "✅" if item['quantity'] > item.get('min_quantity', 0) else "⚠️"
                    text += f"{status_icon} **{item['name']}**\n"
                    text += f"   📦 Miqdor: {item['quantity']} {item.get('unit', 'dona')}\n"
                    text += f"   💰 Narx: {item.get('price', 0):,} so'm\n"
                    if item.get('min_quantity'):
                        text += f"   ⚠️ Min: {item['min_quantity']}\n"
                    if item.get('category'):
                        text += f"   🏷️ Kategoriya: {item['category']}\n"
                    text += "\n"
                    
                    # Limit text length to avoid Telegram message limits
                    if len(text) > 3500:
                        text += "... va boshqalar"
                        break
            else:
                text = "📭 Inventar ro'yxati bo'sh" if lang == 'uz' else "📭 Список инвентаря пуст"
            
            await callback.message.edit_text(text, parse_mode="Markdown")
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Error viewing inventory list: {str(e)}")
            error_text = "Inventar ro'yxatini olishda xatolik" if lang == 'uz' else "Ошибка при получении списка инвентаря"
            await callback.message.edit_text(error_text)
            await callback.answer()

    @router.callback_query(F.data == "add_inventory_item")
    async def add_inventory_item_handler(callback: CallbackQuery, state: FSMContext):
        """Start adding inventory item"""
        try:
            user = await get_warehouse_user_by_telegram_id(callback.from_user.id)
            lang = user.get('language', 'uz')
            
            await state.set_state(WarehouseInventoryStates.adding_item_name)
            text = "📝 Mahsulot nomini kiriting:" if lang == 'uz' else "📝 Введите название товара:"
            await callback.message.edit_text(text)
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Error in add inventory item: {str(e)}")

    @router.message(StateFilter(WarehouseInventoryStates.adding_item_name))
    async def get_item_name(message: Message, state: FSMContext):
        await state.update_data(item_name=message.text)
        await state.set_state(WarehouseInventoryStates.adding_item_quantity)
        await message.answer("🔢 Miqdorni kiriting:")

    @router.message(StateFilter(WarehouseInventoryStates.adding_item_quantity))
    async def get_item_quantity(message: Message, state: FSMContext):
        try:
            quantity = int(message.text)
            if quantity < 0:
                raise ValueError
            await state.update_data(item_quantity=quantity)
            await state.set_state(WarehouseInventoryStates.adding_item_price)
            await message.answer("💰 Narxni kiriting (so'm):")
        except ValueError:
            await message.answer("❌ Noto'g'ri miqdor. Musbat raqam kiriting.")

    @router.message(StateFilter(WarehouseInventoryStates.adding_item_price))
    async def get_item_price(message: Message, state: FSMContext):
        try:
            price = float(message.text)
            if price < 0:
                raise ValueError
            await state.update_data(item_price=price)
            data = await state.get_data()
            lang = data.get('lang', 'uz')
            await state.set_state(WarehouseInventoryStates.adding_item_description)
            await message.answer(
                "�� Mahsulot tavsifini kiriting (ixtiyoriy, o'tkazib yuborish uchun -)" if lang == 'uz' else "📝 Введите описание товара (необязательно, для пропуска -)"
            )
        except ValueError:
            data = await state.get_data()
            lang = data.get('lang', 'uz')
            await message.answer("❌ Noto'g'ri narx. Musbat raqam kiriting." if lang == 'uz' else "❌ Неверная цена. Введите положительное число.")

    @router.message(StateFilter(WarehouseInventoryStates.adding_item_description))
    async def get_item_description(message: Message, state: FSMContext):
        data = await state.get_data()
        lang = data.get('lang', 'uz')
        description = message.text if message.text.strip() != '-' else ''
        item_data = {
            'name': data['item_name'],
            'quantity': data['item_quantity'],
            'price': data['item_price'],
            'unit': 'dona',
            'category': 'general',
            'description': description
        }
        item_id = await add_new_inventory_item(item_data)
        if item_id:
            await message.answer(f"✅ Mahsulot muvaffaqiyatli qo'shildi!\n📦 Nom: {item_data['name']}\n🔢 Miqdor: {item_data['quantity']}\n💰 Narx: {item_data['price']:,} so'm" if lang == 'uz' else f"✅ Товар успешно добавлен!\n📦 Название: {item_data['name']}\n🔢 Количество: {item_data['quantity']}\n💰 Цена: {item_data['price']:,} сум")
        else:
            await message.answer("❌ Mahsulot qo'shishda xatolik" if lang == 'uz' else "❌ Ошибка при добавлении товара")
        await state.set_state(WarehouseInventoryStates.inventory_menu)
        await message.answer(
            "📦 Inventarizatsiya menyusi:" if lang == 'uz' else "📦 Меню инвентаризации:",
            reply_markup=warehouse_inventory_menu(lang)
        )

    @router.callback_query(F.data == "update_inventory_item")
    async def update_inventory_item_handler(callback: CallbackQuery, state: FSMContext):
        """Start updating inventory item"""
        try:
            user = await get_warehouse_user_by_telegram_id(callback.from_user.id)
            lang = user.get('language', 'uz')
            
            items = await get_all_inventory_items()
            
            if items:
                text = "🔄 Yangilanadigan mahsulotni tanlang:\n\n" if lang == 'uz' else "🔄 Выберите товар для обновления:\n\n"
                
                for i, item in enumerate(items[:10], 1):  # Show first 10 items
                    text += f"{i}. **{item['name']}** (Miqdor: {item['quantity']})\n"
                
                text += f"\n📝 Mahsulot raqamini kiriting:" if lang == 'uz' else f"\n📝 Введите номер товара:"
                
                await callback.message.edit_text(text, parse_mode="Markdown")
                await state.update_data(available_items=items)
                await state.set_state(WarehouseInventoryStates.selecting_item_to_update)
            else:
                text = "�� Yangilanadigan mahsulotlar yo'q" if lang == 'uz' else "📭 Нет товаров для обновления"
                await callback.message.edit_text(text)
            
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Error in update inventory item: {str(e)}")

    async def format_item_info(item: dict, lang: str) -> str:
        if not item:
            return "❌ Mahsulot topilmadi." if lang == 'uz' else "❌ Товар не найден."
        text = f"📦 {item['name']}\n"
        text += f"🔢 Miqdor: {item['quantity']}\n"
        text += f"💰 Narx: {item.get('price', 0):,} so'm\n"
        text += f"📝 Tavsif: {item.get('description', '') or '-'}\n"
        return text

    # Yangilash uchun tanlash bosqichida mahsulot ma'lumotlarini chiqarish
    @router.message(StateFilter(WarehouseInventoryStates.selecting_item_to_update))
    async def select_item_to_update(message: Message, state: FSMContext):
        try:
            item_number = int(message.text)
            data = await state.get_data()
            items = data.get('available_items', [])
            lang = data.get('lang', 'uz')
            if 1 <= item_number <= len(items):
                selected_item = items[item_number - 1]
                await state.update_data(selected_item=selected_item)
                info = await format_item_info(selected_item, lang)
                await message.answer(("🔎 Tanlangan mahsulot ma'lumotlari:\n" if lang == 'uz' else "🔎 Информация о выбранном товаре:\n") + info)
                await message.answer(
                    f"🛠️ Qaysi maydonni yangilamoqchisiz?" if lang == 'uz' else "🛠️ Какое поле хотите обновить?",
                    reply_markup=update_item_fields_inline(selected_item['id'], lang)
                )
                await state.set_state(WarehouseInventoryStates.updating_item_info)
            else:
                await message.answer("❌ Noto'g'ri raqam. Qaytadan kiriting.")
        except ValueError:
            await message.answer("❌ Noto'g'ri format. Raqam kiriting.")

    @router.message(StateFilter(WarehouseInventoryStates.updating_item_quantity))
    async def update_item_quantity(message: Message, state: FSMContext):
        try:
            quantity = int(message.text)
            if quantity < 0:
                raise ValueError
            data = await state.get_data()
            selected_item = data.get('selected_item')
            item_id = selected_item['id']
            success = await update_inventory_item_data(item_id, {'quantity': quantity})
            if success:
                await message.answer(f"✅ Miqdor yangilandi: {quantity}")
            else:
                await message.answer("❌ Miqdorni yangilashda xatolik")
            await state.set_state(WarehouseInventoryStates.inventory_menu)
            lang = 'uz' if "Mahsulot" in message.text else 'ru'
            await message.answer(
                "📦 Inventarizatsiya menyusi:" if lang == 'uz' else "📦 Меню инвентаризации:",
                reply_markup=warehouse_inventory_menu(lang)
            )
        except ValueError:
            await message.answer("❌ Noto'g'ri miqdor. Musbat raqam kiriting.")

    @router.callback_query(F.data == "low_stock_report")
    async def low_stock_report_handler(callback: CallbackQuery, state: FSMContext):
        """Show low stock report"""
        try:
            user = await get_warehouse_user_by_telegram_id(callback.from_user.id)
            lang = user.get('language', 'uz')
            
            low_stock_items = await get_low_stock_inventory_items()
            
            if low_stock_items:
                report_text = "⚠️ Kam zaxira hisoboti:" if lang == 'uz' else "⚠️ Отчет о низком запасе:"
                text = f"{report_text}\n\n"
                
                for item in low_stock_items:
                    text += f"🔴 **{item['name']}**\n"
                    text += f"   📦 Joriy: {item['quantity']} {item.get('unit', 'dona')}\n"
                    text += f"   ⚠️ Minimal: {item.get('min_quantity', 0)}\n"
                    shortage = item.get('min_quantity', 0) - item['quantity']
                    if shortage > 0:
                        text += f"   📉 Kamomad: {shortage}\n"
                    text += "\n"
            else:
                text = "✅ Kam zaxira mahsulotlari yo'q" if lang == 'uz' else "✅ Нет товаров с низким запасом"
            
            await callback.message.edit_text(text, parse_mode="Markdown")
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Error in low stock report: {str(e)}")
            error_text = "Hisobotni olishda xatolik" if lang == 'uz' else "Ошибка при получении отчета"
            await callback.message.edit_text(error_text)
            await callback.answer()

    @router.callback_query(F.data == "inventory_search")
    async def inventory_search_handler(callback: CallbackQuery, state: FSMContext):
        """Start inventory search"""
        try:
            user = await get_warehouse_user_by_telegram_id(callback.from_user.id)
            lang = user.get('language', 'uz')
            
            await state.set_state(WarehouseInventoryStates.searching_inventory)
            search_text = "🔍 Qidiruv so'zini kiriting:" if lang == 'uz' else "🔍 Введите поисковый запрос:"
            await callback.message.edit_text(search_text)
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Error in inventory search: {str(e)}")

    @router.message(StateFilter(WarehouseInventoryStates.searching_inventory))
    async def process_inventory_search(message: Message, state: FSMContext):
        """Process inventory search"""
        try:
            user = await get_warehouse_user_by_telegram_id(message.from_user.id)
            lang = user.get('language', 'uz')
            search_query = message.text.strip()
            
            found_items = await search_inventory_items(search_query)
            
            if found_items:
                search_results_text = "🔍 Qidiruv natijalari:" if lang == 'uz' else "🔍 Результаты поиска:"
                text = f"{search_results_text}\n\n"
                
                for item in found_items:
                    status_icon = "✅" if item['quantity'] > 0 else "❌"
                    text += f"{status_icon} **{item['name']}**\n"
                    text += f"   📦 Miqdor: {item['quantity']} {item.get('unit', 'dona')}\n"
                    text += f"   💰 Narx: {item.get('price', 0):,} so'm\n"
                    if item.get('description'):
                        text += f"   📝 Tavsif: {item['description']}\n"
                    text += "\n"
            else:
                text = "❌ Hech narsa topilmadi" if lang == 'uz' else "❌ Ничего не найдено"
            
            await message.answer(text, parse_mode="Markdown")
            await state.set_state(WarehouseMainMenuStates.main_menu)
            
        except Exception as e:
            logger.error(f"Error in inventory search: {str(e)}")
            error_text = "Qidirishda xatolik" if lang == 'uz' else "Ошибка при поиске"
            await message.answer(error_text)
            await state.set_state(WarehouseMainMenuStates.main_menu)

    @router.callback_query(F.data == "inventory_out_of_stock")
    async def inventory_out_of_stock_handler(callback: CallbackQuery, state: FSMContext):
        """Show out of stock items"""
        try:
            user = await get_warehouse_user_by_telegram_id(callback.from_user.id)
            lang = user.get('language', 'uz')
            
            out_of_stock_items = await get_out_of_stock_items()
            
            if out_of_stock_items:
                out_of_stock_text = "❌ Tugagan mahsulotlar:" if lang == 'uz' else "❌ Закончившиеся товары:"
                text = f"{out_of_stock_text}\n\n"
                
                for item in out_of_stock_items:
                    text += f"🔴 **{item['name']}**\n"
                    text += f"   📦 Miqdor: 0 {item.get('unit', 'dona')}\n"
                    text += f"   💰 Narx: {item.get('price', 0):,} so'm\n"
                    if item.get('min_quantity'):
                        text += f"   ⚠️ Kerakli: {item['min_quantity']}\n"
                    text += "\n"
            else:
                text = "✅ Tugagan mahsulotlar yo'q" if lang == 'uz' else "✅ Нет закончившихся товаров"
            
            await callback.message.edit_text(text, parse_mode="Markdown")
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Error getting out of stock items: {str(e)}")
            error_text = "Ma'lumotlarni olishda xatolik" if lang == 'uz' else "Ошибка при получении данных"
            await callback.message.edit_text(error_text)
            await callback.answer()

    @router.message(F.text.in_(["➕ Mahsulot qo'shish", "➕ Добавить товар"]))
    async def add_item_handler(message: Message, state: FSMContext):
        data = await state.get_data()
        lang = data.get('lang', 'uz')
        await state.set_state(WarehouseInventoryStates.adding_item_name)
        await message.answer(
            "📝 Mahsulot nomini kiriting:" if lang == 'uz' else "📝 Введите название товара:"
        )

    @router.message(StateFilter(WarehouseInventoryStates.adding_item_name))
    async def get_item_name(message: Message, state: FSMContext):
        await state.update_data(item_name=message.text)
        await state.set_state(WarehouseInventoryStates.adding_item_quantity)
        await message.answer("🔢 Miqdorni kiriting:")

    @router.message(StateFilter(WarehouseInventoryStates.adding_item_quantity))
    async def get_item_quantity(message: Message, state: FSMContext):
        try:
            quantity = int(message.text)
            if quantity < 0:
                raise ValueError
            await state.update_data(item_quantity=quantity)
            data = await state.get_data()
            lang = data.get('lang', 'uz')
            await state.set_state(WarehouseInventoryStates.adding_item_price)
            await message.answer("💰 Narxni kiriting (so'm):" if lang == 'uz' else "💰 Введите цену (сум):")
        except ValueError:
            data = await state.get_data()
            lang = data.get('lang', 'uz')
            await message.answer("❌ Noto'g'ri miqdor. Musbat raqam kiriting." if lang == 'uz' else "❌ Неверное количество. Введите положительное число.")

    @router.message(StateFilter(WarehouseInventoryStates.adding_item_price))
    async def get_item_price(message: Message, state: FSMContext):
        try:
            price = float(message.text)
            if price < 0:
                raise ValueError
            data = await state.get_data()
            lang = data.get('lang', 'uz')
            item_data = {
                'name': data['item_name'],
                'quantity': data['item_quantity'],
                'price': price,
                'unit': 'dona',
                'category': 'general',
            }
            item_id = await add_new_inventory_item(item_data)
            if item_id:
                await message.answer(f"✅ Mahsulot muvaffaqiyatli qo'shildi!\n📦 Nom: {item_data['name']}\n🔢 Miqdor: {item_data['quantity']}\n💰 Narx: {item_data['price']:,} so'm" if lang == 'uz' else f"✅ Товар успешно добавлен!\n📦 Название: {item_data['name']}\n🔢 Количество: {item_data['quantity']}\n💰 Цена: {item_data['price']:,} сум")
            else:
                await message.answer("❌ Mahsulot qo'shishda xatolik" if lang == 'uz' else "❌ Ошибка при добавлении товара")
            await state.set_state(WarehouseInventoryStates.inventory_menu)
            await message.answer(
                "📦 Inventarizatsiya menyusi:" if lang == 'uz' else "📦 Меню инвентаризации:",
                reply_markup=warehouse_inventory_menu(lang)
            )
        except ValueError:
            data = await state.get_data()
            lang = data.get('lang', 'uz')
            await message.answer("❌ Noto'g'ri narx. Musbat raqam kiriting." if lang == 'uz' else "❌ Неверная цена. Введите положительное число.")

    @router.callback_query(F.data == "update_inventory_item")
    async def update_inventory_item_handler(callback: CallbackQuery, state: FSMContext):
        """Start updating inventory item"""
        try:
            user = await get_warehouse_user_by_telegram_id(callback.from_user.id)
            lang = user.get('language', 'uz')
            
            items = await get_all_inventory_items()
            
            if items:
                text = "🔄 Yangilanadigan mahsulotni tanlang:\n\n" if lang == 'uz' else "🔄 Выберите товар для обновления:\n\n"
                
                for i, item in enumerate(items[:10], 1):  # Show first 10 items
                    text += f"{i}. **{item['name']}** (Miqdor: {item['quantity']})\n"
                
                text += f"\n📝 Mahsulot raqamini kiriting:" if lang == 'uz' else f"\n📝 Введите номер товара:"
                
                await callback.message.edit_text(text, parse_mode="Markdown")
                await state.update_data(available_items=items)
                await state.set_state(WarehouseInventoryStates.selecting_item_to_update)
            else:
                text = "📭 Yangilanadigan mahsulotlar yo'q" if lang == 'uz' else "📭 Нет товаров для обновления"
                await callback.message.edit_text(text)
            
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Error in update inventory item: {str(e)}")

    @router.message(StateFilter(WarehouseInventoryStates.selecting_item_to_update))
    async def select_item_to_update(message: Message, state: FSMContext):
        try:
            item_number = int(message.text)
            data = await state.get_data()
            items = data.get('available_items', [])
            lang = data.get('lang', 'uz')
            if 1 <= item_number <= len(items):
                selected_item = items[item_number - 1]
                await state.update_data(selected_item=selected_item)
                await message.answer(
                    f"🛠️ Qaysi maydonni yangilamoqchisiz?" if lang == 'uz' else "🛠️ Какое поле хотите обновить?",
                    reply_markup=update_item_fields_inline(selected_item['id'], lang)
                )
                await state.set_state(WarehouseInventoryStates.updating_item_info)
            else:
                await message.answer("❌ Noto'g'ri raqam. Qaytadan kiriting.")
        except ValueError:
            await message.answer("❌ Noto'g'ri format. Raqam kiriting.")

    @router.message(StateFilter(WarehouseInventoryStates.updating_item_info))
    async def update_item_info(message: Message, state: FSMContext):
        data = await state.get_data()
        lang = data.get('lang', 'uz')
        selected_item = data.get('selected_item')
        item_id = selected_item['id']

        if message.text == "✏️ Nomi":
            await state.update_data(update_item_id=item_id)
            await message.answer("✏️ Yangi nomni kiriting:")
            await state.set_state(WarehouseInventoryStates.updating_item_name)
        elif message.text == "🔢 Miqdori":
            await state.update_data(update_item_id=item_id)
            await message.answer("🔢 Yangi miqdorni kiriting:")
            await state.set_state(WarehouseInventoryStates.updating_item_quantity)
        elif message.text == "💰 Narxi":
            await state.update_data(update_item_id=item_id)
            await message.answer("💰 Yangi narxni kiriting:")
            await state.set_state(WarehouseInventoryStates.updating_item_price)
        elif message.text == "📝 Tavsifi":
            await state.update_data(update_item_id=item_id)
            await message.answer("📝 Yangi tavsifni kiriting:")
            await state.set_state(WarehouseInventoryStates.updating_item_description)
        elif message.text == "◀️ Orqaga":
            await state.set_state(WarehouseInventoryStates.inventory_menu)
            await message.answer(
                "📦 Inventarizatsiya menyusi:" if lang == 'uz' else "📦 Меню инвентаризации:",
                reply_markup=warehouse_inventory_menu(lang)
            )

    @router.callback_query(F.data.startswith("update_name_"))
    async def update_name_start(callback: CallbackQuery, state: FSMContext):
        item_id = int(callback.data.split("_")[2])
        await state.update_data(update_item_id=item_id)
        await callback.message.answer("✏️ Yangi nomni kiriting:")
        await state.set_state(WarehouseInventoryStates.updating_item_name)
        await callback.answer()

    @router.message(StateFilter(WarehouseInventoryStates.updating_item_name))
    async def update_name_process(message: Message, state: FSMContext):
        data = await state.get_data()
        item_id = data.get('update_item_id')
        new_name = message.text.strip()
        await update_inventory_item_data(item_id, {'name': new_name})
        updated = await get_inventory_item_by_id(item_id)
        lang = data.get('lang', 'uz')
        await message.answer("✅ Nomi yangilandi!")
        await message.answer(await format_item_info(updated, lang))
        await state.set_state(WarehouseInventoryStates.inventory_menu)

    @router.callback_query(F.data.startswith("update_description_"))
    async def update_description_start(callback: CallbackQuery, state: FSMContext):
        item_id = int(callback.data.split("_")[2])
        await state.update_data(update_item_id=item_id)
        await callback.message.answer("📝 Yangi tavsifni kiriting:")
        await state.set_state(WarehouseInventoryStates.updating_item_description)
        await callback.answer()

    @router.message(StateFilter(WarehouseInventoryStates.updating_item_description))
    async def update_description_process(message: Message, state: FSMContext):
        data = await state.get_data()
        item_id = data.get('update_item_id')
        new_desc = message.text.strip()
        await update_inventory_item_data(item_id, {'description': new_desc})
        updated = await get_inventory_item_by_id(item_id)
        lang = data.get('lang', 'uz')
        await message.answer("✅ Tavsif yangilandi!")
        await message.answer(await format_item_info(updated, lang))
        await state.set_state(WarehouseInventoryStates.inventory_menu)

    @router.callback_query(F.data.startswith("update_quantity_"))
    async def update_quantity_start(callback: CallbackQuery, state: FSMContext):
        item_id = int(callback.data.split("_")[2])
        await state.update_data(update_item_id=item_id)
        await callback.message.answer("🔢 Yangi miqdorni kiriting:")
        await state.set_state(WarehouseInventoryStates.updating_item_quantity)
        await callback.answer()

    @router.message(StateFilter(WarehouseInventoryStates.updating_item_quantity))
    async def update_quantity_process(message: Message, state: FSMContext):
        data = await state.get_data()
        item_id = data.get('update_item_id')
        try:
            quantity = int(message.text)
            if quantity < 0:
                raise ValueError
            await update_inventory_item_data(item_id, {'quantity': quantity})
            updated = await get_inventory_item_by_id(item_id)
            lang = data.get('lang', 'uz')
            await message.answer("✅ Miqdor yangilandi!")
            await message.answer(await format_item_info(updated, lang))
            await state.set_state(WarehouseInventoryStates.inventory_menu)
        except ValueError:
            await message.answer("❌ Noto'g'ri miqdor. Musbat raqam kiriting.")

    @router.callback_query(F.data.startswith("update_price_"))
    async def update_price_start(callback: CallbackQuery, state: FSMContext):
        item_id = int(callback.data.split("_")[2])
        await state.update_data(update_item_id=item_id)
        await callback.message.answer("💰 Yangi narxni kiriting:")
        await state.set_state(WarehouseInventoryStates.updating_item_price)
        await callback.answer()

    @router.message(StateFilter(WarehouseInventoryStates.updating_item_price))
    async def update_price_process(message: Message, state: FSMContext):
        data = await state.get_data()
        item_id = data.get('update_item_id')
        try:
            price = float(message.text)
            if price < 0:
                raise ValueError
            await update_inventory_item_data(item_id, {'price': price})
            updated = await get_inventory_item_by_id(item_id)
            lang = data.get('lang', 'uz')
            await message.answer("✅ Narx yangilandi!")
            await message.answer(await format_item_info(updated, lang))
            await state.set_state(WarehouseInventoryStates.inventory_menu)
        except ValueError:
            await message.answer("❌ Noto'g'ri narx. Musbat raqam kiriting.")

    @router.callback_query(F.data.in_(["update_name_", "update_quantity_", "update_price_", "update_description_"]))
    async def update_item_info_handler(callback: CallbackQuery, state: FSMContext):
        data = await state.get_data()
        lang = data.get('lang', 'uz')
        selected_item = data.get('selected_item')
        item_id = selected_item['id']

        if callback.data.startswith("update_name_"):
            await state.update_data(update_item_id=item_id)
            await callback.message.answer("✏️ Yangi nomni kiriting:")
            await state.set_state(WarehouseInventoryStates.updating_item_name)
        elif callback.data.startswith("update_quantity_"):
            await state.update_data(update_item_id=item_id)
            await callback.message.answer("🔢 Yangi miqdorni kiriting:")
            await state.set_state(WarehouseInventoryStates.updating_item_quantity)
        elif callback.data.startswith("update_price_"):
            await state.update_data(update_item_id=item_id)
            await callback.message.answer("💰 Yangi narxni kiriting:")
            await state.set_state(WarehouseInventoryStates.updating_item_price)
        elif callback.data.startswith("update_description_"):
            await state.update_data(update_item_id=item_id)
            await callback.message.answer("📝 Yangi tavsifni kiriting:")
            await state.set_state(WarehouseInventoryStates.updating_item_description)
        await callback.answer()

    @router.message(F.text.in_(["⚠️ Kam zaxira", "⚠️ Низкий запас"]))
    async def low_stock_handler(message: Message, state: FSMContext):
        user = await get_warehouse_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        items = await get_low_stock_inventory_items()
        if items:
            text = "⚠️ Kam zaxira mahsulotlar:\n" if lang == 'uz' else "⚠️ Товары с низким запасом:\n"
            for item in items:
                text += f"- {item['name']} ({item['quantity']})\n"
        else:
            text = "Barcha mahsulotlar yetarli." if lang == 'uz' else "Все товары в достаточном количестве."
        await message.answer(text)

    @router.message(F.text.in_(["❌ Tugagan mahsulotlar", "❌ Нет в наличии"]))
    async def out_of_stock_handler(message: Message, state: FSMContext):
        user = await get_warehouse_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        items = await get_out_of_stock_items()
        if items:
            text = "❌ Tugagan mahsulotlar:\n" if lang == 'uz' else "❌ Нет в наличии:\n"
            for item in items:
                text += f"- {item['name']}\n"
        else:
            text = "Barcha mahsulotlarda zaxira bor." if lang == 'uz' else "Все товары в наличии."
        await message.answer(text)

    @router.message(F.text.in_(["🔍 Qidirish", "🔍 Поиск"]))
    async def search_inventory_start(message: Message, state: FSMContext):
        user = await get_warehouse_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        await state.set_state(WarehouseInventoryStates.searching_inventory)
        await message.answer("🔍 Qidiriladigan mahsulot nomini kiriting:" if lang == 'uz' else "🔍 Введите название товара для поиска:")

    @router.message(StateFilter(WarehouseInventoryStates.searching_inventory))
    async def process_inventory_search(message: Message, state: FSMContext):
        user = await get_warehouse_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        items = await search_inventory_items(message.text)
        if items:
            text = "🔍 Qidiruv natijalari:\n" if lang == 'uz' else "🔍 Результаты поиска:\n"
            for item in items[:10]:
                text += f"- {item['name']} ({item['quantity']})\n"
        else:
            text = "Hech narsa topilmadi." if lang == 'uz' else "Ничего не найдено."
        await message.answer(text)
        await state.set_state(WarehouseInventoryStates.inventory_menu)

    @router.message(F.text.in_(["📋 Barcha mahsulotlar", "📋 Все товары"]))
    async def view_all_inventory_handler(message: Message, state: FSMContext):
        user = await get_warehouse_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        items = await get_all_inventory_items()
        if not items:
            await message.answer("Inventar bo‘sh." if lang == 'uz' else "Инвентарь пуст.")
            return
        await state.update_data(inventory_items=items)
        await state.update_data(inventory_page=1)
        await send_inventory_page(message, state, page=1, lang=lang)

    @router.callback_query(F.data.startswith("inventory_page_"))
    async def inventory_pagination_callback(callback: CallbackQuery, state: FSMContext):
        user = await get_warehouse_user_by_telegram_id(callback.from_user.id)
        lang = user.get('language', 'uz')
        items = await state.get_data()
        items = items.get('inventory_items', [])
        page = int(callback.data.split('_')[-1])
        await state.update_data(inventory_page=page)
        await send_inventory_page(callback.message, state, page=page, lang=lang, edit=True, callback=callback)

    async def send_inventory_page(message_or_callback, state: FSMContext, page: int, lang: str, edit=False, callback=None):
        user = await get_warehouse_user_by_telegram_id(message_or_callback.from_user.id)
        lang = user.get('language', 'uz')
        items = await state.get_data()
        items = items.get('inventory_items', [])
        per_page = 5
        total_pages = (len(items) + per_page - 1) // per_page
        page = max(1, min(page, total_pages))
        start = (page - 1) * per_page
        end = start + per_page
        page_items = items[start:end]
        texts = []
        for item in page_items:
            texts.append(await format_item_info(item, lang))
        text = f"\n{'-'*20}\n".join(texts)
        text = (f"📋 Barcha mahsulotlar (sahifa {page}/{total_pages}):\n\n" if lang == 'uz' else f"📋 Все товары (страница {page}/{total_pages}):\n\n") + text
        keyboard = build_pagination_keyboard(page, total_pages, lang)
        if edit and callback:
            await callback.message.edit_text(text, reply_markup=keyboard)
            await callback.answer()
        else:
            await message_or_callback.answer(text, reply_markup=keyboard)

    @router.callback_query(F.data.startswith("increase_"))
    async def increase_quantity_handler(callback: CallbackQuery, state: FSMContext):
        user = await get_warehouse_user_by_telegram_id(callback.from_user.id)
        lang = user.get('language', 'uz')
        item_id = int(callback.data.split("_")[1])
        await state.update_data(action_item_id=item_id, action_type="increase")
        await callback.message.answer("➕ Qancha kirim qilmoqchisiz?")
        await state.set_state(WarehouseInventoryStates.updating_item_quantity)
        await callback.answer()

    @router.callback_query(F.data.startswith("decrease_"))
    async def decrease_quantity_handler(callback: CallbackQuery, state: FSMContext):
        user = await get_warehouse_user_by_telegram_id(callback.from_user.id)
        lang = user.get('language', 'uz')
        item_id = int(callback.data.split("_")[1])
        await state.update_data(action_item_id=item_id, action_type="decrease")
        await callback.message.answer("➖ Qancha chiqim qilmoqchisiz?")
        await state.set_state(WarehouseInventoryStates.updating_item_quantity)
        await callback.answer()

    @router.message(StateFilter(WarehouseInventoryStates.updating_item_quantity))
    async def process_quantity_change(message: Message, state: FSMContext):
        user = await get_warehouse_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        data = await state.get_data()
        item_id = data.get("action_item_id")
        action_type = data.get("action_type")
        try:
            amount = int(message.text)
            if amount < 0:
                raise ValueError
            item = await get_inventory_item_by_id(item_id)
            if not item:
                await message.answer("Mahsulot topilmadi.")
                return
            new_quantity = item['quantity'] + amount if action_type == "increase" else item['quantity'] - amount
            if new_quantity < 0:
                await message.answer("Chiqim miqdori mavjud zaxiradan oshib ketdi.")
                return
            await update_inventory_item_data(item_id, {'quantity': new_quantity})
            await message.answer(f"✅ Yangi miqdor: {new_quantity}")
            await state.set_state(WarehouseInventoryStates.inventory_menu)
        except ValueError:
            await message.answer("Faqat musbat raqam kiriting.")

    @router.callback_query(F.data.startswith("delete_"))
    async def delete_item_handler(callback: CallbackQuery, state: FSMContext):
        user = await get_warehouse_user_by_telegram_id(callback.from_user.id)
        lang = user.get('language', 'uz')
        item_id = int(callback.data.split("_")[1])
        success = await update_inventory_item_data(item_id, {'is_active': False})
        if success:
            await callback.message.answer("🗑️ Mahsulot o‘chirildi.")
        else:
            await callback.message.answer("❌ O‘chirishda xatolik.")
        await callback.answer()

    @router.message(F.text.in_(["◀️ Orqaga", "◀️ Назад"]))
    async def back_to_main_menu_handler(message: Message, state: FSMContext):
        user = await get_warehouse_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        from keyboards.warehouse_buttons import warehouse_main_menu
        await state.set_state(WarehouseMainMenuStates.main_menu)
        await message.answer(
            " Ombor paneliga qaytdingiz." if lang == 'uz' else "🏢 Вы вернулись в панель склада.",
            reply_markup=warehouse_main_menu(lang)
        )

    @router.message(F.text.in_(["✏️ Mahsulotni yangilash", "✏️ Обновить товар"]))
    async def update_item_handler(message: Message, state: FSMContext):
        user = await get_warehouse_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        items = await get_all_inventory_items()
        if items:
            text = "🔄 Yangilanadigan mahsulotni tanlang:\n\n" if lang == 'uz' else "🔄 Выберите товар для обновления:\n\n"
            for i, item in enumerate(items[:10], 1):
                text += f"{i}. {item['name']} (Miqdor: {item['quantity']})\n"
            text += "\n📝 Mahsulot raqamini kiriting:" if lang == 'uz' else "\n📝 Введите номер товара:"
            await message.answer(text)
            await state.update_data(available_items=items)
            await state.set_state(WarehouseInventoryStates.selecting_item_to_update)
        else:
            await message.answer("📭 Yangilanadigan mahsulotlar yo'q" if lang == 'uz' else "📭 Нет товаров для обновления")

    # UNIVERSAL HANDLER: Agar foydalanuvchi selecting_item_to_update holatida raqamdan boshqa tugma/buyruq yuborsa, FSM tugaydi va asosiy menyu ko‘rsatiladi
    @router.message(StateFilter(WarehouseInventoryStates.selecting_item_to_update))
    async def universal_selecting_item_to_update_handler(message: Message, state: FSMContext):
        # Faqat raqam kiritilganini tekshirish uchun
        if message.text.isdigit():
            # Raqam bo‘lsa, eski handler ishlaydi (bu universal handlerdan pastroqda bo‘lishi kerak)
            return
        # Aks holda FSM tugatilib, asosiy menyu ko‘rsatiladi
        data = await state.get_data()
        lang = data.get('lang')
        if not lang:
            # Foydalanuvchi ma'lumotidan aniqlashga harakat qilamiz
            from database.warehouse_queries import get_warehouse_user_by_telegram_id
            user = await get_warehouse_user_by_telegram_id(message.from_user.id)
            lang = user.get('language', 'uz') if user else 'uz'
        await state.clear()
        await message.answer(
            "📦 Inventarizatsiya menyusi:" if lang == 'uz' else "📦 Меню инвентаризации:",
            reply_markup=warehouse_inventory_menu(lang)
        )

    return router
