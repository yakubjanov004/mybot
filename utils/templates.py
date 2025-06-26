from utils.i18n import i18n

async def get_template_text(lang: str, role: str, key: str, **kwargs):
    print(f"get_template_text: lang={lang}, role={role}, key={key}")
    return i18n.get_template(lang, role, key, **kwargs)