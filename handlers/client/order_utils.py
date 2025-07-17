from datetime import datetime

def format_group_zayavka_message(order_type, public_id, user, phone, address, description, tariff=None, abonent_type=None, abonent_id=None, geo=None, media=None):
    if order_type == 'service':
        title = '🛠️ <b>Yangi texnik xizmat arizasi</b>'
        type_line = '🛠️ <b>Ariza turi:</b> Texnik xizmat'
    else:
        title = '🔌 <b>Yangi ulanish arizasi</b>'
        type_line = '🔌 <b>Ariza turi:</b> Ulanish'
    
    abonent_block = ''
    if abonent_type or abonent_id:
        abonent_block = f"\n👤 <b>Abonent turi:</b> {abonent_type or '-'}\n🆔 <b>Abonent ID:</b> {abonent_id or '-'}"
    
    tariff_block = f"\n💳 <b>Tarif:</b> {tariff}" if tariff else ''
    geo_block = f"📍 <b>Geolokatsiya:</b> {'✅ Yuborilgan' if geo else '❌ Yuborilmagan'}"
    media_block = f"🖼 <b>Media:</b> {'✅ Yuborilgan' if media else '❌ Yuborilmagan'}"
    
    msg = (
        f"{title}\n"
        f"{type_line}\n"
        f"🆔 <b>ID:</b> {public_id or '-'}"
        f"\n👤 <b>Foydalanuvchi:</b> {user.get('full_name', '-') if user else '-'}"
        f"\n📞 <b>Telefon:</b> {phone or '-'}"
        f"\n🏠 <b>Manzil:</b> {address or '-'}"
        f"\n📝 <b>Tavsif:</b> {description or '-'}"
        f"{tariff_block}"
        f"{abonent_block}"
        f"\n{geo_block}"
        f"\n{media_block}"
        f"\n⏰ <b>Sana:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    )
    return msg