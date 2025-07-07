from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from database.warehouse_queries import (
    get_warehouse_user_by_telegram_id, get_all_inventory_items, 
    add_new_inventory_item, update_inventory_item_data,
    search_inventory_items, get_low_stock_inventory_items,
    get_out_of_stock_items, update_inventory_quantity
)
from keyboards.warehouse_buttons import (
    inventory_menu, inventory_detailed_list_menu, inventory_actions_keyboard
)
from states.warehouse_states import WarehouseStates
from utils.logger import logger

router = Router()

@router.message(F.text.in_(["📦 Inventarizatsiya boshqaruvi", "📦 Управление инвентаризацией"]))
async def inventory_management_handler(message: Message, state: FSMContext):
    """Handle inventory management"""
    try:
        user = await get_warehouse_user_by_telegram_id(message.from_user.id)
        if not user:
            return
        
        lang = user.get('language', 'uz')
        inventory_text = "📦 Inventarizatsiya boshqaruvi" if lang == 'uz' else "📦 Управление инвентаризацией"
        
        await message.answer(
            inventory_text,
            reply_markup=inventory_detailed_list_menu(lang)
        )
        await state.set_state(WarehouseStates.inventory_menu)
        
    except Exception as e:
        logger.error(f"Error in inventory management: {str(e)}")

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
        
        await state.set_state(WarehouseStates.adding_item_name)
        text = "📝 Mahsulot nomini kiriting:" if lang == 'uz' else "📝 Введите название товара:"
        await callback.message.edit_text(text)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in add inventory item: {str(e)}")

@router.message(StateFilter(WarehouseStates.adding_item_name))
async def get_item_name(message: Message, state: FSMContext):
    """Get item name for new inventory item"""
    try:
        user = await get_warehouse_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        
        await state.update_data(item_name=message.text)
        await state.set_state(WarehouseStates.adding_item_quantity)
        text = "🔢 Miqdorni kiriting:" if lang == 'uz' else "🔢 Введите количество:"
        await message.answer(text)
        
    except Exception as e:
        logger.error(f"Error getting item name: {str(e)}")

@router.message(StateFilter(WarehouseStates.adding_item_quantity))
async def get_item_quantity(message: Message, state: FSMContext):
    """Get item quantity for new inventory item"""
    try:
        user = await get_warehouse_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        
        try:
            quantity = int(message.text)
            if quantity < 0:
                raise ValueError("Negative quantity")
                
            await state.update_data(item_quantity=quantity)
            await state.set_state(WarehouseStates.adding_item_price)
            text = "💰 Narxni kiriting (so'm):" if lang == 'uz' else "💰 Введите цену (сум):"
            await message.answer(text)
            
        except ValueError:
            text = "❌ Noto'g'ri miqdor. Musbat raqam kiriting." if lang == 'uz' else "❌ Неверное количество. Введите положительное число."
            await message.answer(text)
            
    except Exception as e:
        logger.error(f"Error getting item quantity: {str(e)}")

@router.message(StateFilter(WarehouseStates.adding_item_price))
async def get_item_price(message: Message, state: FSMContext):
    """Get item price and save item"""
    try:
        user = await get_warehouse_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        
        try:
            price = float(message.text)
            if price < 0:
                raise ValueError("Negative price")
                
            data = await state.get_data()
            
            item_data = {
                'name': data['item_name'],
                'quantity': data['item_quantity'],
                'price': price,
                'added_by': user['id'],
                'category': 'general',
                'unit': 'dona'
            }
            
            item_id = await add_new_inventory_item(item_data)
            
            if item_id:
                success_text = f"✅ Mahsulot muvaffaqiyatli qo'shildi!\n\n"
                success_text += f"📦 Nom: {item_data['name']}\n"
                success_text += f"🔢 Miqdor: {item_data['quantity']}\n"
                success_text += f"💰 Narx: {item_data['price']:,} so'm"
                
                if lang == 'ru':
                    success_text = f"✅ Товар успешно добавлен!\n\n"
                    success_text += f"📦 Название: {item_data['name']}\n"
                    success_text += f"🔢 Количество: {item_data['quantity']}\n"
                    success_text += f"💰 Цена: {item_data['price']:,} сум"
                
                await message.answer(success_text)
                logger.info(f"Inventory item added by warehouse user {user['id']}: {item_data}")
            else:
                error_text = "❌ Mahsulot qo'shishda xatolik" if lang == 'uz' else "❌ Ошибка при добавлении товара"
                await message.answer(error_text)
            
            await state.set_state(WarehouseStates.main_menu)
            
        except ValueError:
            text = "❌ Noto'g'ri narx. Musbat raqam kiriting." if lang == 'uz' else "❌ Неверная цена. Введите положительное число."
            await message.answer(text)
            
    except Exception as e:
        logger.error(f"Error getting item price: {str(e)}")

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
            await state.set_state(WarehouseStates.selecting_item_to_update)
        else:
            text = "📭 Yangilanadigan mahsulotlar yo'q" if lang == 'uz' else "📭 Нет товаров для обновления"
            await callback.message.edit_text(text)
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in update inventory item: {str(e)}")

@router.message(StateFilter(WarehouseStates.selecting_item_to_update))
async def select_item_to_update(message: Message, state: FSMContext):
    """Select item to update"""
    try:
        user = await get_warehouse_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        
        try:
            item_number = int(message.text)
            data = await state.get_data()
            items = data.get('available_items', [])
            
            if 1 <= item_number <= len(items):
                selected_item = items[item_number - 1]
                await state.update_data(selected_item=selected_item)
                
                text = f"📦 **Tanlangan mahsulot:** {selected_item['name']}\n"
                text += f"🔢 **Joriy miqdor:** {selected_item['quantity']}\n"
                text += f"💰 **Joriy narx:** {selected_item.get('price', 0):,} so'm\n\n"
                text += "🔢 Yangi miqdorni kiriting:"
                
                if lang == 'ru':
                    text = f"📦 **Выбранный товар:** {selected_item['name']}\n"
                    text += f"🔢 **Текущее количество:** {selected_item['quantity']}\n"
                    text += f"💰 **Текущая цена:** {selected_item.get('price', 0):,} сум\n\n"
                    text += "🔢 Введите новое количество:"
                
                await message.answer(text, parse_mode="Markdown")
                await state.set_state(WarehouseStates.updating_item_quantity)
            else:
                text = "❌ Noto'g'ri raqam. Qaytadan kiriting." if lang == 'uz' else "❌ Неверный номер. Введите снова."
                await message.answer(text)
                
        except ValueError:
            text = "❌ Noto'g'ri format. Raqam kiriting." if lang == 'uz' else "❌ Неверный формат. Введите число."
            await message.answer(text)
            
    except Exception as e:
        logger.error(f"Error selecting item to update: {str(e)}")

@router.message(StateFilter(WarehouseStates.updating_item_quantity))
async def update_item_quantity(message: Message, state: FSMContext):
    """Update item quantity"""
    try:
        user = await get_warehouse_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        
        try:
            new_quantity = int(message.text)
            if new_quantity < 0:
                raise ValueError("Negative quantity")
                
            data = await state.get_data()
            selected_item = data.get('selected_item')
            
            if selected_item:
                success = await update_inventory_item_data(selected_item['id'], {'quantity': new_quantity})
                
                if success:
                    success_text = f"✅ Mahsulot miqdori yangilandi!\n\n"
                    success_text += f"📦 **Mahsulot:** {selected_item['name']}\n"
                    success_text += f"🔢 **Eski miqdor:** {selected_item['quantity']}\n"
                    success_text += f"🔢 **Yangi miqdor:** {new_quantity}"
                    
                    if lang == 'ru':
                        success_text = f"✅ Количество товара обновлено!\n\n"
                        success_text += f"📦 **Товар:** {selected_item['name']}\n"
                        success_text += f"🔢 **Старое количество:** {selected_item['quantity']}\n"
                        success_text += f"🔢 **Новое количество:** {new_quantity}"
                    
                    await message.answer(success_text, parse_mode="Markdown")
                    logger.info(f"Inventory item {selected_item['id']} updated by warehouse user {user['id']}")
                else:
                    error_text = "❌ Yangilashda xatolik" if lang == 'uz' else "❌ Ошибка при обновлении"
                    await message.answer(error_text)
            
            await state.set_state(WarehouseStates.main_menu)
            
        except ValueError:
            text = "❌ Noto'g'ri miqdor. Musbat raqam kiriting." if lang == 'uz' else "❌ Неверное количество. Введите положительное число."
            await message.answer(text)
            
    except Exception as e:
        logger.error(f"Error updating item quantity: {str(e)}")

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
        
        await state.set_state(WarehouseStates.searching_inventory)
        search_text = "🔍 Qidiruv so'zini kiriting:" if lang == 'uz' else "🔍 Введите поисковый запрос:"
        await callback.message.edit_text(search_text)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in inventory search: {str(e)}")

@router.message(StateFilter(WarehouseStates.searching_inventory))
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
        await state.set_state(WarehouseStates.main_menu)
        
    except Exception as e:
        logger.error(f"Error in inventory search: {str(e)}")
        error_text = "Qidirishda xatolik" if lang == 'uz' else "Ошибка при поиске"
        await message.answer(error_text)
        await state.set_state(WarehouseStates.main_menu)

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
