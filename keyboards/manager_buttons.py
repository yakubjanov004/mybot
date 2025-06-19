from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

def get_manager_main_keyboard(locale):
    """Generate main keyboard for manager"""
    keyboard = [
        [KeyboardButton(text=locale["manager"]["create_application"]),
         KeyboardButton(text=locale["manager"]["view_applications"])],
        [KeyboardButton(text=locale["manager"]["filter_applications"]),
         KeyboardButton(text=locale["manager"]["change_status"])],
        [KeyboardButton(text=locale["manager"]["assign_responsible"]),
         KeyboardButton(text=locale["manager"]["generate_report"])],
        [KeyboardButton(text=locale["manager"]["equipment_issuance"]),
         KeyboardButton(text=locale["manager"]["ready_for_installation"])],
        [KeyboardButton(text=locale["manager"]["view_equipment_applications"])]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_status_keyboard(statuses, locale):
    """Generate inline keyboard for status selection"""
    builder = InlineKeyboardBuilder()
    for status in statuses:
        builder.add(InlineKeyboardButton(
            text=locale["statuses"][status],
            callback_data=f"status_{status}"
        ))
    builder.adjust(2)
    return builder.as_markup()

def get_report_type_keyboard(locale):
    """Generate inline keyboard for report type selection"""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text=locale["manager"]["report_word"],
            callback_data="report_word"
        ),
        InlineKeyboardButton(
            text=locale["manager"]["report_pdf"],
            callback_data="report_pdf"
        )
    )
    return builder.as_markup()

def get_equipment_keyboard(equipment_list, locale):
    """Generate inline keyboard for equipment selection"""
    builder = InlineKeyboardBuilder()
    for equipment in equipment_list:
        builder.add(InlineKeyboardButton(
            text=equipment["name"],
            callback_data=f"equipment_{equipment['id']}"
        ))
    builder.adjust(1)
    return builder.as_markup()

def get_assign_technician_keyboard(application_id, technicians):
    """Generate inline keyboard for assigning a technician to an application"""
    builder = InlineKeyboardBuilder()
    for tech in technicians:
        text = f"👨‍🔧 {tech['full_name']}"
        builder.add(InlineKeyboardButton(
            text=text,
            callback_data=f"assign_zayavka_{application_id}_{tech['id']}"
        ))
    builder.adjust(1)
    return builder.as_markup()
