from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.fsm.context import FSMContext
import csv
import io
from datetime import datetime

from database.warehouse_queries import (
    get_warehouse_user_by_telegram_id, get_inventory_export_data,
    get_orders_export_data, get_issued_items_export_data
)
from keyboards.warehouse_buttons import export_menu
from states.warehouse_states import WarehouseStates
from utils.logger import logger

router = Router()

@router.message(F.text.in_(["📤 Ma'lumotlarni eksport qilish", "📤 Экспорт данных"]))
async def export_handler(message: Message, state: FSMContext):
    """Handle data export"""
    try:
        user = await get_warehouse_user_by_telegram_id(message.from_user.id)
        if not user:
            return
        
        lang = user.get('language', 'uz')
        export_text = "📤 Ma'lumotlarni eksport qilish" if lang == 'uz' else "📤 Экспорт данных"
        
        await message.answer(
            export_text,
            reply_markup=export_menu(lang)
        )
        await state.set_state(WarehouseStates.export_menu)
        
    except Exception as e:
        logger.error(f"Error in export handler: {str(e)}")

@router.callback_query(F.data == "export_inventory")
async def export_inventory_handler(callback: CallbackQuery, state: FSMContext):
    """Export inventory data to CSV"""
    try:
        user = await get_warehouse_user_by_telegram_id(callback.from_user.id)
        lang = user.get('language', 'uz')
        
        # Show processing message
        processing_text = "⏳ Ma'lumotlar tayyorlanmoqda..." if lang == 'uz' else "⏳ Подготовка данных..."
        await callback.message.edit_text(processing_text)
        
        # Get inventory data
        inventory_data = await get_inventory_export_data()
        
        if inventory_data:
            # Create CSV content
            output = io.StringIO()
            
            # CSV headers
            if lang == 'uz':
                fieldnames = ['ID', 'Nomi', 'Kategoriya', 'Miqdor', 'Birlik', 'Min_miqdor', 'Narx', 'Tavsif', 'Yaratilgan', 'Yangilangan']
            else:
                fieldnames = ['ID', 'Название', 'Категория', 'Количество', 'Единица', 'Мин_количество', 'Цена', 'Описание', 'Создано', 'Обновлено']
            
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            
            # Write data rows
            for item in inventory_data:
                row_data = {
                    fieldnames[0]: item['id'],
                    fieldnames[1]: item['name'],
                    fieldnames[2]: item.get('category', ''),
                    fieldnames[3]: item['quantity'],
                    fieldnames[4]: item.get('unit', 'dona'),
                    fieldnames[5]: item.get('min_quantity', 0),
                    fieldnames[6]: item.get('price', 0),
                    fieldnames[7]: item.get('description', ''),
                    fieldnames[8]: item['created_at'].strftime('%Y-%m-%d %H:%M:%S') if item.get('created_at') else '',
                    fieldnames[9]: item['updated_at'].strftime('%Y-%m-%d %H:%M:%S') if item.get('updated_at') else ''
                }
                writer.writerow(row_data)
            
            # Create file
            csv_content = output.getvalue().encode('utf-8-sig')  # UTF-8 with BOM for Excel compatibility
            output.close()
            
            # Generate filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"inventory_export_{timestamp}.csv"
            
            # Send file
            file = BufferedInputFile(csv_content, filename=filename)
            
            success_text = f"✅ Inventar ma'lumotlari eksport qilindi!\n📊 Jami: {len(inventory_data)} ta mahsulot"
            if lang == 'ru':
                success_text = f"✅ Данные инвентаря экспортированы!\n📊 Всего: {len(inventory_data)} товаров"
            
            await callback.message.answer_document(
                document=file,
                caption=success_text
            )
            
            logger.info(f"Inventory data exported by warehouse user {user['id']}: {len(inventory_data)} items")
        else:
            error_text = "❌ Eksport qilinadigan ma'lumotlar yo'q" if lang == 'uz' else "❌ Нет данных для экспорта"
            await callback.message.edit_text(error_text)
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error exporting inventory: {str(e)}")
        error_text = "Eksport qilishda xatolik" if lang == 'uz' else "Ошибка при экспорте"
        await callback.message.edit_text(error_text)
        await callback.answer()

@router.callback_query(F.data == "export_orders")
async def export_orders_handler(callback: CallbackQuery, state: FSMContext):
    """Export orders data to CSV"""
    try:
        user = await get_warehouse_user_by_telegram_id(callback.from_user.id)
        lang = user.get('language', 'uz')
        
        # Show processing message
        processing_text = "⏳ Ma'lumotlar tayyorlanmoqda..." if lang == 'uz' else "⏳ Подготовка данных..."
        await callback.message.edit_text(processing_text)
        
        # Get orders data
        orders_data = await get_orders_export_data()
        
        if orders_data:
            # Create CSV content
            output = io.StringIO()
            
            # CSV headers
            if lang == 'uz':
                fieldnames = ['ID', 'Tavsif', 'Holat', 'Mijoz', 'Telefon', 'Texnik', 'Yaratilgan', 'Tugallangan']
            else:
                fieldnames = ['ID', 'Описание', 'Статус', 'Клиент', 'Телефон', 'Техник', 'Создано', 'Завершено']
            
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            
            # Write data rows
            for order in orders_data:
                row_data = {
                    fieldnames[0]: order['id'],
                    fieldnames[1]: order.get('description', ''),
                    fieldnames[2]: order.get('status', ''),
                    fieldnames[3]: order.get('client_name', ''),
                    fieldnames[4]: order.get('client_phone', ''),
                    fieldnames[5]: order.get('technician_name', ''),
                    fieldnames[6]: order['created_at'].strftime('%Y-%m-%d %H:%M:%S') if order.get('created_at') else '',
                    fieldnames[7]: order['completed_at'].strftime('%Y-%m-%d %H:%M:%S') if order.get('completed_at') else ''
                }
                writer.writerow(row_data)
            
            # Create file
            csv_content = output.getvalue().encode('utf-8-sig')
            output.close()
            
            # Generate filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"orders_export_{timestamp}.csv"
            
            # Send file
            file = BufferedInputFile(csv_content, filename=filename)
            
            success_text = f"✅ Buyurtmalar ma'lumotlari eksport qilindi!\n📊 Jami: {len(orders_data)} ta buyurtma"
            if lang == 'ru':
                success_text = f"✅ Данные заказов экспортированы!\n📊 Всего: {len(orders_data)} заказов"
            
            await callback.message.answer_document(
                document=file,
                caption=success_text
            )
            
            logger.info(f"Orders data exported by warehouse user {user['id']}: {len(orders_data)} orders")
        else:
            error_text = "❌ Eksport qilinadigan buyurtmalar yo'q" if lang == 'uz' else "❌ Нет заказов для экспорта"
            await callback.message.edit_text(error_text)
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error exporting orders: {str(e)}")
        error_text = "Eksport qilishda xatolik" if lang == 'uz' else "Ошибка при экспорте"
        await callback.message.edit_text(error_text)
        await callback.answer()

@router.callback_query(F.data == "export_issued_items")
async def export_issued_items_handler(callback: CallbackQuery, state: FSMContext):
    """Export issued items data to CSV"""
    try:
        user = await get_warehouse_user_by_telegram_id(callback.from_user.id)
        lang = user.get('language', 'uz')
        
        # Show processing message
        processing_text = "⏳ Ma'lumotlar tayyorlanmoqda..." if lang == 'uz' else "⏳ Подготовка данных..."
        await callback.message.edit_text(processing_text)
        
        # Get issued items data
        issued_data = await get_issued_items_export_data()
        
        if issued_data:
            # Create CSV content
            output = io.StringIO()
            
            # CSV headers
            if lang == 'uz':
                fieldnames = ['ID', 'Mahsulot', 'Kategoriya', 'Miqdor', 'Beruvchi', 'Buyurtma_ID', 'Buyurtma_tavsif', 'Berilgan_vaqt']
            else:
                fieldnames = ['ID', 'Товар', 'Категория', 'Количество', 'Выдал', 'Заказ_ID', 'Описание_заказа', 'Время_выдачи']
            
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            
            # Write data rows
            for item in issued_data:
                row_data = {
                    fieldnames[0]: item['id'],
                    fieldnames[1]: item.get('material_name', ''),
                    fieldnames[2]: item.get('category', ''),
                    fieldnames[3]: item.get('quantity', 0),
                    fieldnames[4]: item.get('issued_by_name', ''),
                    fieldnames[5]: item.get('order_id', ''),
                    fieldnames[6]: item.get('order_description', ''),
                    fieldnames[7]: item['issued_at'].strftime('%Y-%m-%d %H:%M:%S') if item.get('issued_at') else ''
                }
                writer.writerow(row_data)
            
            # Create file
            csv_content = output.getvalue().encode('utf-8-sig')
            output.close()
            
            # Generate filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"issued_items_export_{timestamp}.csv"
            
            # Send file
            file = BufferedInputFile(csv_content, filename=filename)
            
            success_text = f"✅ Chiqarilgan mahsulotlar ma'lumotlari eksport qilindi!\n📊 Jami: {len(issued_data)} ta yozuv"
            if lang == 'ru':
                success_text = f"✅ Данные выданных товаров экспортированы!\n📊 Всего: {len(issued_data)} записей"
            
            await callback.message.answer_document(
                document=file,
                caption=success_text
            )
            
            logger.info(f"Issued items data exported by warehouse user {user['id']}: {len(issued_data)} items")
        else:
            error_text = "❌ Eksport qilinadigan ma'lumotlar yo'q" if lang == 'uz' else "❌ Нет данных для экспорта"
            await callback.message.edit_text(error_text)
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error exporting issued items: {str(e)}")
        error_text = "Eksport qilishda xatolik" if lang == 'uz' else "Ошибка при экспорте"
        await callback.message.edit_text(error_text)
        await callback.answer()

@router.callback_query(F.data == "export_full_report")
async def export_full_report_handler(callback: CallbackQuery, state: FSMContext):
    """Export full warehouse report"""
    try:
        user = await get_warehouse_user_by_telegram_id(callback.from_user.id)
        lang = user.get('language', 'uz')
        
        # Show processing message
        processing_text = "⏳ To'liq hisobot tayyorlanmoqda..." if lang == 'uz' else "⏳ Подготовка полного отчета..."
        await callback.message.edit_text(processing_text)
        
        # Get all data
        inventory_data = await get_inventory_export_data()
        orders_data = await get_orders_export_data()
        issued_data = await get_issued_items_export_data()
        
        # Create comprehensive report
        output = io.StringIO()
        
        # Write summary
        output.write("WAREHOUSE FULL REPORT\n")
        output.write("=" * 50 + "\n")
        output.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        output.write(f"Generated by: {user.get('full_name', 'Unknown')}\n\n")
        
        # Summary statistics
        output.write("SUMMARY STATISTICS\n")
        output.write("-" * 30 + "\n")
        output.write(f"Total Inventory Items: {len(inventory_data)}\n")
        output.write(f"Total Orders: {len(orders_data)}\n")
        output.write(f"Total Issued Items: {len(issued_data)}\n\n")
        
        # Inventory summary
        if inventory_data:
            total_value = sum(item.get('price', 0) * item.get('quantity', 0) for item in inventory_data)
            low_stock_count = sum(1 for item in inventory_data if item.get('quantity', 0) <= item.get('min_quantity', 0))
            
            output.write("INVENTORY SUMMARY\n")
            output.write("-" * 30 + "\n")
            output.write(f"Total Inventory Value: {total_value:,.0f} UZS\n")
            output.write(f"Low Stock Items: {low_stock_count}\n")
            output.write(f"Out of Stock Items: {sum(1 for item in inventory_data if item.get('quantity', 0) == 0)}\n\n")
        
        # Orders summary
        if orders_data:
            status_counts = {}
            for order in orders_data:
                status = order.get('status', 'unknown')
                status_counts[status] = status_counts.get(status, 0) + 1
            
            output.write("ORDERS SUMMARY\n")
            output.write("-" * 30 + "\n")
            for status, count in status_counts.items():
                output.write(f"{status.title()}: {count}\n")
            output.write("\n")
        
        # Create file
        report_content = output.getvalue().encode('utf-8-sig')
        output.close()
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"warehouse_full_report_{timestamp}.txt"
        
        # Send file
        file = BufferedInputFile(report_content, filename=filename)
        
        success_text = f"✅ To'liq hisobot tayyor!\n📊 Inventar: {len(inventory_data)}\n📋 Buyurtmalar: {len(orders_data)}\n📤 Chiqarilgan: {len(issued_data)}"
        if lang == 'ru':
            success_text = f"✅ Полный отчет готов!\n📊 Инвентарь: {len(inventory_data)}\n📋 Заказы: {len(orders_data)}\n📤 Выдано: {len(issued_data)}"
        
        await callback.message.answer_document(
            document=file,
            caption=success_text
        )
        
        logger.info(f"Full warehouse report exported by user {user['id']}")
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error exporting full report: {str(e)}")
        error_text = "Hisobotni eksport qilishda xatolik" if lang == 'uz' else "Ошибка при экспорте отчета"
        await callback.message.edit_text(error_text)
        await callback.answer()
