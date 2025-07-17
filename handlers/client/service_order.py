from aiogram import F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from keyboards.client_buttons import (
    zayavka_type_keyboard, media_attachment_keyboard,
    geolocation_keyboard, confirmation_keyboard
)
from states.client_states import OrderStates
from database.base_queries import get_user_by_telegram_id, create_zayavka
from utils.logger import setup_logger
from utils.inline_cleanup import answer_and_cleanup
from loader import bot, ZAYAVKA_GROUP_ID, inline_message_manager
from utils.role_router import get_role_router
from database.manager_queries import get_users_by_role
from .order_utils import format_group_zayavka_message

def get_service_order_router():
    logger = setup_logger('bot.client.service')
    router = get_role_router("client")

    @router.message(F.text.in_(["🆕 Texnik xizmat", "🆕 Техническая поддержка"]))
    async def new_service_request(message: Message, state: FSMContext):
        user = await get_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        sent_message = await message.answer(
            "Abonent turini tanlang:" if lang == 'uz' else "Выберите тип абонента:",
            reply_markup=zayavka_type_keyboard(lang)
        )
        await state.update_data(last_message_id=sent_message.message_id)
        await state.set_state(OrderStates.selecting_order_type)
        await inline_message_manager.track(message.from_user.id, sent_message.message_id)

    @router.callback_query(F.data.startswith("zayavka_type_"), StateFilter(OrderStates.selecting_order_type))
    async def select_abonent_type(callback: CallbackQuery, state: FSMContext):
        await answer_and_cleanup(callback, cleanup_after=True)
        abonent_type = callback.data.split("_")[-1]
        await state.update_data(abonent_type=abonent_type)
        user = await get_user_by_telegram_id(callback.from_user.id)
        lang = user.get('language', 'uz')
        sent_message = await callback.message.answer(
            "Abonent ID raqamini kiriting:" if lang == 'uz' else "Введите ID абонента:",
        )
        await state.update_data(last_message_id=sent_message.message_id)
        await state.set_state(OrderStates.waiting_for_contact)
        await inline_message_manager.track(callback.from_user.id, sent_message.message_id)

    @router.message(StateFilter(OrderStates.waiting_for_contact))
    async def get_abonent_id(message: Message, state: FSMContext):
        await state.update_data(abonent_id=message.text)
        user = await get_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        sent_message = await message.answer(
            "Muammo tavsifini kiriting:" if lang == 'uz' else "Опишите проблему:",
        )
        await state.update_data(last_message_id=sent_message.message_id)
        await state.set_state(OrderStates.entering_description)
        await inline_message_manager.track(message.from_user.id, sent_message.message_id)

    @router.message(StateFilter(OrderStates.entering_description))
    async def get_service_description(message: Message, state: FSMContext):
        await state.update_data(description=message.text)
        user = await get_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        sent_message = await message.answer(
            "Foto yoki video yuborasizmi?" if lang == 'uz' else "Отправите фото или видео?",
            reply_markup=media_attachment_keyboard(lang)
        )
        await state.update_data(last_message_id=sent_message.message_id)
        await state.set_state(OrderStates.asking_for_media)
        await inline_message_manager.track(message.from_user.id, sent_message.message_id)

    @router.callback_query(F.data.in_(["attach_media_yes", "attach_media_no"]), StateFilter(OrderStates.asking_for_media))
    async def ask_for_media(callback: CallbackQuery, state: FSMContext):
        await answer_and_cleanup(callback, cleanup_after=True)
        if callback.data == "attach_media_yes":
            user = await get_user_by_telegram_id(callback.from_user.id)
            lang = user.get('language', 'uz')
            sent_message = await callback.message.answer(
                "Foto yoki videoni yuboring:" if lang == 'uz' else "Отправьте фото или видео:",
            )
            await state.update_data(last_message_id=sent_message.message_id)
            await state.set_state(OrderStates.waiting_for_media)
            await inline_message_manager.track(callback.from_user.id, sent_message.message_id)
        else:
            await ask_for_address(callback, state)

    @router.message(StateFilter(OrderStates.waiting_for_media), F.photo | F.video)
    async def process_media(message: Message, state: FSMContext):
        media_file_id = message.photo[-1].file_id if message.photo else message.video.file_id
        await state.update_data(media=media_file_id)
        await ask_for_address(message, state)

    async def ask_for_address(message_or_callback, state: FSMContext):
        user_id = message_or_callback.from_user.id
        user = await get_user_by_telegram_id(user_id)
        lang = user.get('language', 'uz')
        if hasattr(message_or_callback, "message"):
            sent_message = await message_or_callback.message.answer(
                "Xizmat ko‘rsatiladigan manzilni kiriting:" if lang == 'uz' else "Введите адрес обслуживания:",
            )
        else:
            sent_message = await message_or_callback.answer(
                "Xizmat ko‘rsatiladigan manzilni kiriting:" if lang == 'uz' else "Введите адрес обслуживания:",
            )
        await state.update_data(last_message_id=sent_message.message_id)
        await state.set_state(OrderStates.entering_address)
        await inline_message_manager.track(user_id, sent_message.message_id)

    @router.message(StateFilter(OrderStates.entering_address))
    async def get_service_address(message: Message, state: FSMContext):
        await state.update_data(address=message.text)
        user = await get_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        sent_message = await message.answer(
            "Geolokatsiya yuborasizmi?" if lang == 'uz' else "Отправите геолокацию?",
            reply_markup=geolocation_keyboard(lang)
        )
        await state.update_data(last_message_id=sent_message.message_id)
        await state.set_state(OrderStates.asking_for_location)
        await inline_message_manager.track(message.from_user.id, sent_message.message_id)

    @router.callback_query(F.data.in_(["send_location_yes", "send_location_no"]), StateFilter(OrderStates.asking_for_location))
    async def ask_for_geo(callback: CallbackQuery, state: FSMContext):
        await answer_and_cleanup(callback, cleanup_after=True)
        if callback.data == "send_location_yes":
            user = await get_user_by_telegram_id(callback.from_user.id)
            lang = user.get('language', 'uz')
            sent_message = await callback.message.answer(
                "Geolokatsiyani yuboring:" if lang == 'uz' else "Отправьте геолокацию:",
            )
            await state.update_data(last_message_id=sent_message.message_id)
            await state.set_state(OrderStates.waiting_for_location)
            await inline_message_manager.track(callback.from_user.id, sent_message.message_id)
        else:
            await show_service_confirmation(callback, state)

    @router.message(StateFilter(OrderStates.waiting_for_location), F.location)
    async def get_geo(message: Message, state: FSMContext):
        await state.update_data(geo=message.location)
        await show_service_confirmation(message, state)

    async def show_service_confirmation(message_or_callback, state: FSMContext):
        data = await state.get_data()
        user_id = message_or_callback.from_user.id
        user = await get_user_by_telegram_id(user_id)
        lang = user.get('language', 'uz')
        abonent_type = data.get('abonent_type', '-')
        abonent_id = data.get('abonent_id', '-')
        description = data.get('description', '-')
        address = data.get('address', '-')
        geo = data.get('geo', None)
        media = data.get('media', None)
        text = (
            f"👤 <b>Abonent turi:</b> {abonent_type}\n"
            f"🆔 <b>Abonent ID:</b> {abonent_id}\n"
            f"📝 <b>Muammo tavsifi:</b> {description}\n"
            f"🏠 <b>Manzil:</b> {address}\n"
            f"📍 <b>Geolokatsiya:</b> {'✅ Yuborilgan' if geo else '❌ Yuborilmagan'}\n"
            f"🖼 <b>Media:</b> {'✅ Yuborilgan' if media else '❌ Yuborilmagan'}"
        )
        if hasattr(message_or_callback, "message"):
            sent_message = await message_or_callback.message.answer(
                text,
                parse_mode='HTML',
                reply_markup=confirmation_keyboard(lang)
            )
        else:
            sent_message = await message_or_callback.answer(
                text,
                parse_mode='HTML',
                reply_markup=confirmation_keyboard(lang)
            )
        await state.update_data(last_message_id=sent_message.message_id)
        await state.set_state(OrderStates.confirming_order)
        await inline_message_manager.track(user_id, sent_message.message_id)

    @router.callback_query(F.data == "confirm_zayavka", StateFilter(OrderStates.confirming_order))
    async def confirm_service_order(callback: CallbackQuery, state: FSMContext):
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass
        await answer_and_cleanup(callback, cleanup_after=True)
        data = await state.get_data()
        user = await get_user_by_telegram_id(callback.from_user.id)
        
        zayavka_data = {
            'user_id': user['id'],
            'description': data.get('description', '-'),
            'address': data.get('address', '-'),
            'phone_number': user.get('phone_number'),
            'media': data.get('media'),
            'zayavka_type': 'tx',
            'latitude': data.get('geo').latitude if data.get('geo') else None,
            'longitude': data.get('geo').longitude if data.get('geo') else None,
            'created_by': user['id'],
            'created_by_role': user.get('role'),
            'status': 'pending_controller' # Initial status for service request
        }
        zayavka_id, public_id = await create_zayavka(**zayavka_data)

        await bot.send_message(callback.from_user.id, "✅ Arizangiz qabul qilindi! Operatorlar tez orada siz bilan bog'lanadi.")
        
        if zayavka_id and public_id:
            group_msg = format_group_zayavka_message(
                order_type='service',
                public_id=public_id,
                user=user,
                phone=user.get('phone_number'),
                address=data.get('address', '-'),
                description=data.get('description', '-'),
                abonent_type=data.get('abonent_type', '-'),
                abonent_id=data.get('abonent_id', '-'),
                geo=data.get('geo'),
                media=data.get('media')
            )
            if ZAYAVKA_GROUP_ID:
                try:
                    if data.get('media'):
                        await bot.send_photo(ZAYAVKA_GROUP_ID, data.get('media'), caption=group_msg, parse_mode='HTML')
                    else:
                        await bot.send_message(ZAYAVKA_GROUP_ID, group_msg, parse_mode='HTML')
                except Exception as e:
                    logger.error(f"Group notification error: {str(e)}")
            
            short_msg = f"🛠️ Yangi texnik xizmat arizasi! ID: {public_id}"
            pool = bot.db
            controllers = await get_users_by_role(pool, 'controller')
            for c in controllers:
                if c.get('telegram_id'):
                    try:
                        await bot.send_message(c['telegram_id'], short_msg)
                    except Exception:
                        pass
        await state.clear()

    return router
