from database.models import Zayavka
from loader import bot

async def get_pending_applications(status: str) -> list[dict]:
    """Get all pending applications for junior manager."""
    applications = await bot.db.get_zayavkas_by_status(status)
    return [{
        'public_id': app.public_id,
        'description': app.description,
        'id': app.id
    } for app in applications]

async def get_application_by_id(app_id: int) -> dict:
    """Get application details by ID."""
    application = await bot.db.get_zayavka_by_id(app_id)
    if not application:
        return None
    
    return {
        'public_id': application.public_id,
        'description': application.description,
        'id': application.id,
        'status': application.status
    }