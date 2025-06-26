import re
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import phonenumbers
from phonenumbers import NumberParseException
from utils.logger import logger

class ValidationError(Exception):
    """Custom validation error"""
    pass

class DataValidator:
    """Data validation utility"""
    
    # Regex patterns
    PHONE_PATTERN = re.compile(r'^\+?[1-9]\d{1,14}$')
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    TELEGRAM_ID_PATTERN = re.compile(r'^\d{5,12}$')
    
    # Valid roles
    VALID_ROLES = [
        'admin', 'manager', 'controller', 'call_center', 
        'warehouse', 'technician', 'client', 'blocked'
    ]
    
    # Valid languages
    VALID_LANGUAGES = ['uz', 'ru']
    
    # Valid zayavka statuses
    VALID_ZAYAVKA_STATUSES = [
        'yangi', 'qabul_qilindi', 'jarayonda', 'tugallandi', 
        'bekor_qilindi', 'kechiktirildi'
    ]
    
    @staticmethod
    def validate_telegram_id(telegram_id: Union[str, int]) -> int:
        """Validate Telegram ID"""
        try:
            telegram_id = int(telegram_id)
            if telegram_id <= 0:
                raise ValidationError("Telegram ID must be positive")
            if not DataValidator.TELEGRAM_ID_PATTERN.match(str(telegram_id)):
                raise ValidationError("Invalid Telegram ID format")
            return telegram_id
        except (ValueError, TypeError):
            raise ValidationError("Telegram ID must be a valid integer")
    
    @staticmethod
    def validate_phone(phone: str) -> str:
        """Validate phone number"""
        if not phone or not isinstance(phone, str):
            raise ValidationError("Phone number is required")
        
        # Clean phone number
        phone = re.sub(r'[^\d+]', '', phone.strip())
        
        if not phone:
            raise ValidationError("Phone number cannot be empty")
        
        # Add + if not present
        if not phone.startswith('+'):
            if phone.startswith('998'):
                phone = '+' + phone
            else:
                phone = '+998' + phone
        
        try:
            # Parse with phonenumbers library
            parsed = phonenumbers.parse(phone, None)
            if not phonenumbers.is_valid_number(parsed):
                raise ValidationError("Invalid phone number")
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        except NumberParseException:
            # Fallback to regex validation
            if not DataValidator.PHONE_PATTERN.match(phone):
                raise ValidationError("Invalid phone number format")
            return phone
    
    @staticmethod
    def validate_email(email: str) -> str:
        """Validate email address"""
        if not email or not isinstance(email, str):
            raise ValidationError("Email is required")
        
        email = email.strip().lower()
        if not DataValidator.EMAIL_PATTERN.match(email):
            raise ValidationError("Invalid email format")
        
        return email
    
    @staticmethod
    def validate_role(role: str) -> str:
        """Validate user role"""
        if not role or not isinstance(role, str):
            raise ValidationError("Role is required")
        
        role = role.strip().lower()
        if role not in DataValidator.VALID_ROLES:
            raise ValidationError(f"Invalid role. Must be one of: {', '.join(DataValidator.VALID_ROLES)}")
        
        return role
    
    @staticmethod
    def validate_language(language: str) -> str:
        """Validate language code"""
        if not language or not isinstance(language, str):
            raise ValidationError("Language is required")
        
        language = language.strip().lower()
        if language not in DataValidator.VALID_LANGUAGES:
            raise ValidationError(f"Invalid language. Must be one of: {', '.join(DataValidator.VALID_LANGUAGES)}")
        
        return language
    
    @staticmethod
    def validate_zayavka_status(status: str) -> str:
        """Validate zayavka status"""
        if not status or not isinstance(status, str):
            raise ValidationError("Status is required")
        
        status = status.strip().lower()
        if status not in DataValidator.VALID_ZAYAVKA_STATUSES:
            raise ValidationError(f"Invalid status. Must be one of: {', '.join(DataValidator.VALID_ZAYAVKA_STATUSES)}")
        
        return status
    
    @staticmethod
    def validate_text(text: str, min_length: int = 1, max_length: int = 1000, field_name: str = "Text") -> str:
        """Validate text field"""
        if not text or not isinstance(text, str):
            raise ValidationError(f"{field_name} is required")
        
        text = text.strip()
        if len(text) < min_length:
            raise ValidationError(f"{field_name} must be at least {min_length} characters long")
        
        if len(text) > max_length:
            raise ValidationError(f"{field_name} must be no more than {max_length} characters long")
        
        return text
    
    @staticmethod
    def validate_callback_data(callback_data: str) -> Dict[str, str]:
        """Validate and parse callback data"""
        if not callback_data or not isinstance(callback_data, str):
            raise ValidationError("Callback data is required")
        
        # Telegram callback data limit is 64 bytes
        if len(callback_data.encode('utf-8')) > 64:
            raise ValidationError("Callback data too long (max 64 bytes)")
        
        # Parse callback data (format: action_param1_param2)
        parts = callback_data.split('_')
        if len(parts) < 1:
            raise ValidationError("Invalid callback data format")
        
        result = {'action': parts[0]}
        for i, part in enumerate(parts[1:], 1):
            result[f'param{i}'] = part
        
        return result
    
    @staticmethod
    def sanitize_input(text: str) -> str:
        """Sanitize user input"""
        if not text or not isinstance(text, str):
            return ""
        
        # Remove potentially dangerous characters
        text = re.sub(r'[<>"\']', '', text)
        
        # Remove excessive whitespace
        text = ' '.join(text.split())
        
        return text.strip()
    
    @staticmethod
    def validate_coordinates(lat: float, lon: float) -> tuple:
        """Validate GPS coordinates"""
        try:
            lat = float(lat)
            lon = float(lon)
        except (ValueError, TypeError):
            raise ValidationError("Coordinates must be valid numbers")
        
        if not (-90 <= lat <= 90):
            raise ValidationError("Latitude must be between -90 and 90")
        
        if not (-180 <= lon <= 180):
            raise ValidationError("Longitude must be between -180 and 180")
        
        return lat, lon
    
    @staticmethod
    def validate_date(date_str: str, date_format: str = "%Y-%m-%d") -> datetime:
        """Validate date string"""
        if not date_str or not isinstance(date_str, str):
            raise ValidationError("Date is required")
        
        try:
            return datetime.strptime(date_str.strip(), date_format)
        except ValueError:
            raise ValidationError(f"Invalid date format. Expected: {date_format}")
    
    @staticmethod
    def validate_user_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate user registration data"""
        validated = {}
        
        # Required fields
        if 'telegram_id' in data:
            validated['telegram_id'] = DataValidator.validate_telegram_id(data['telegram_id'])
        
        if 'full_name' in data:
            validated['full_name'] = DataValidator.validate_text(
                data['full_name'], min_length=2, max_length=100, field_name="Full name"
            )
        
        if 'phone' in data:
            validated['phone'] = DataValidator.validate_phone(data['phone'])
        
        # Optional fields
        if 'email' in data and data['email']:
            validated['email'] = DataValidator.validate_email(data['email'])
        
        if 'role' in data:
            validated['role'] = DataValidator.validate_role(data['role'])
        
        if 'language' in data:
            validated['language'] = DataValidator.validate_language(data['language'])
        
        return validated
    
    @staticmethod
    def validate_zayavka_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate zayavka creation data"""
        validated = {}
        
        # Required fields
        if 'description' in data:
            validated['description'] = DataValidator.validate_text(
                data['description'], min_length=10, max_length=1000, field_name="Description"
            )
        
        if 'address' in data:
            validated['address'] = DataValidator.validate_text(
                data['address'], min_length=5, max_length=200, field_name="Address"
            )
        
        # Optional fields
        if 'phone' in data and data['phone']:
            validated['phone'] = DataValidator.validate_phone(data['phone'])
        
        if 'status' in data:
            validated['status'] = DataValidator.validate_zayavka_status(data['status'])
        
        if 'latitude' in data and 'longitude' in data:
            lat, lon = DataValidator.validate_coordinates(data['latitude'], data['longitude'])
            validated['latitude'] = lat
            validated['longitude'] = lon
        
        return validated

# Validation decorators
def validate_input(validation_func):
    """Decorator for input validation"""
    def decorator(handler_func):
        async def wrapper(*args, **kwargs):
            try:
                # Apply validation
                validated_data = validation_func(*args, **kwargs)
                if validated_data:
                    kwargs.update(validated_data)
                return await handler_func(*args, **kwargs)
            except ValidationError as e:
                logger.error(f"Validation error in {handler_func.__name__}: {str(e)}")
                # Handle validation error (send message to user)
                if args and hasattr(args[0], 'reply'):
                    await args[0].reply(f"❌ Xatolik: {str(e)}")
                elif args and hasattr(args[0], 'answer'):
                    await args[0].answer(f"❌ Xatolik: {str(e)}", show_alert=True)
                return
            except Exception as e:
                logger.error(f"Unexpected error in validation: {str(e)}", exc_info=True)
                return await handler_func(*args, **kwargs)
        
        return wrapper
    return decorator
