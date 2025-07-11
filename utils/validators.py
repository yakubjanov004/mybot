import re
import phonenumbers
from typing import Optional, Dict, Any, List, Union
from datetime import datetime, date
from phonenumbers import NumberParseException
from utils.logger import setup_module_logger

logger = setup_module_logger("validators")

class ValidationError(Exception):
    """Custom validation error"""
    def __init__(self, message: str, field: str = None):
        self.message = message
        self.field = field
        super().__init__(self.message)

class Validator:
    """Base validator class"""
    
    def __init__(self, required: bool = True, allow_empty: bool = False):
        self.required = required
        self.allow_empty = allow_empty
    
    def validate(self, value: Any, field_name: str = None) -> Any:
        """Validate value"""
        if value is None or (isinstance(value, str) and value.strip() == ""):
            if self.required and not self.allow_empty:
                raise ValidationError(f"Field is required", field_name)
            return value
        
        return self._validate_value(value, field_name)
    
    def _validate_value(self, value: Any, field_name: str = None) -> Any:
        """Override in subclasses"""
        return value

class StringValidator(Validator):
    """String validator"""
    
    def __init__(self, min_length: int = 0, max_length: int = None, 
                 pattern: str = None, **kwargs):
        super().__init__(**kwargs)
        self.min_length = min_length
        self.max_length = max_length
        self.pattern = re.compile(pattern) if pattern else None
    
    def _validate_value(self, value: Any, field_name: str = None) -> str:
        if not isinstance(value, str):
            value = str(value)
        
        value = value.strip()
        
        if len(value) < self.min_length:
            raise ValidationError(
                f"Minimum length is {self.min_length} characters", 
                field_name
            )
        
        if self.max_length and len(value) > self.max_length:
            raise ValidationError(
                f"Maximum length is {self.max_length} characters", 
                field_name
            )
        
        if self.pattern and not self.pattern.match(value):
            raise ValidationError(
                f"Invalid format", 
                field_name
            )
        
        return value

class IntegerValidator(Validator):
    """Integer validator"""
    
    def __init__(self, min_value: int = None, max_value: int = None, **kwargs):
        super().__init__(**kwargs)
        self.min_value = min_value
        self.max_value = max_value
    
    def _validate_value(self, value: Any, field_name: str = None) -> int:
        try:
            if isinstance(value, str):
                value = int(value.strip())
            elif not isinstance(value, int):
                value = int(value)
        except (ValueError, TypeError):
            raise ValidationError("Must be a valid integer", field_name)
        
        if self.min_value is not None and value < self.min_value:
            raise ValidationError(
                f"Minimum value is {self.min_value}", 
                field_name
            )
        
        if self.max_value is not None and value > self.max_value:
            raise ValidationError(
                f"Maximum value is {self.max_value}", 
                field_name
            )
        
        return value

class FloatValidator(Validator):
    """Float validator"""
    
    def __init__(self, min_value: float = None, max_value: float = None, **kwargs):
        super().__init__(**kwargs)
        self.min_value = min_value
        self.max_value = max_value
    
    def _validate_value(self, value: Any, field_name: str = None) -> float:
        try:
            if isinstance(value, str):
                value = float(value.strip())
            elif not isinstance(value, (int, float)):
                value = float(value)
        except (ValueError, TypeError):
            raise ValidationError("Must be a valid number", field_name)
        
        if self.min_value is not None and value < self.min_value:
            raise ValidationError(
                f"Minimum value is {self.min_value}", 
                field_name
            )
        
        if self.max_value is not None and value > self.max_value:
            raise ValidationError(
                f"Maximum value is {self.max_value}", 
                field_name
            )
        
        return float(value)

class EmailValidator(Validator):
    """Email validator"""
    
    EMAIL_PATTERN = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
    
    def _validate_value(self, value: Any, field_name: str = None) -> str:
        if not isinstance(value, str):
            value = str(value)
        
        value = value.strip().lower()
        
        if not self.EMAIL_PATTERN.match(value):
            raise ValidationError("Invalid email format", field_name)
        
        return value

class PhoneValidator(Validator):
    """Phone number validator"""
    
    def __init__(self, country_code: str = None, **kwargs):
        super().__init__(**kwargs)
        self.country_code = country_code
    
    def _validate_value(self, value: Any, field_name: str = None) -> str:
        if not isinstance(value, str):
            value = str(value)
        
        value = value.strip()
        
        try:
            # Parse phone number
            parsed = phonenumbers.parse(value, self.country_code)
            
            # Validate
            if not phonenumbers.is_valid_number(parsed):
                raise ValidationError("Invalid phone number", field_name)
            
            # Format to international format
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
            
        except NumberParseException:
            # Fallback validation for Uzbek numbers
            if self._validate_uzbek_phone(value):
                return self._format_uzbek_phone(value)
            
            raise ValidationError("Invalid phone number format", field_name)
    
    def _validate_uzbek_phone(self, phone: str) -> bool:
        """Validate Uzbek phone number"""
        # Remove all non-digit characters
        digits = re.sub(r'\D', '', phone)
        
        # Check patterns
        patterns = [
            r'^998\d{9}$',  # +998XXXXXXXXX
            r'^998\d{8}$',   # +998XXXXXXXX (old format)
            r'^\d{9}$',      # XXXXXXXXX (without country code)
            r'^\d{8}$'       # XXXXXXXX (old format without country code)
        ]
        
        for pattern in patterns:
            if re.match(pattern, digits):
                return True
        
        return False
    
    def _format_uzbek_phone(self, phone: str) -> str:
        """Format Uzbek phone number"""
        digits = re.sub(r'\D', '', phone)
        
        if digits.startswith('998'):
            return f"+{digits}"
        else:
            return f"+998{digits}"

class DateValidator(Validator):
    """Date validator"""
    
    def __init__(self, min_date: date = None, max_date: date = None, 
                 date_format: str = "%Y-%m-%d", **kwargs):
        super().__init__(**kwargs)
        self.min_date = min_date
        self.max_date = max_date
        self.date_format = date_format
    
    def _validate_value(self, value: Any, field_name: str = None) -> date:
        if isinstance(value, datetime):
            value = value.date()
        elif isinstance(value, date):
            pass
        elif isinstance(value, str):
            try:
                value = datetime.strptime(value.strip(), self.date_format).date()
            except ValueError:
                raise ValidationError(
                    f"Invalid date format. Expected: {self.date_format}", 
                    field_name
                )
        else: 
            raise ValidationError("Invalid date type", field_name)
        
        if self.min_date and value < self.min_date:
            raise ValidationError(
                f"Date must be after {self.min_date}", 
                field_name
            )
        
        if self.max_date and value > self.max_date:
            raise ValidationError(
                f"Date must be before {self.max_date}", 
                field_name
            )
        
        return value

class ChoiceValidator(Validator):
    """Choice validator"""
    
    def __init__(self, choices: List[Any], **kwargs):
        super().__init__(**kwargs)
        self.choices = choices
    
    def _validate_value(self, value: Any, field_name: str = None) -> Any:
        if value not in self.choices:
            raise ValidationError(
                f"Must be one of: {', '.join(map(str, self.choices))}", 
                field_name
            )
        
        return value

class ListValidator(Validator):
    """List validator"""
    
    def __init__(self, item_validator: Validator = None, 
                 min_items: int = 0, max_items: int = None, **kwargs):
        super().__init__(**kwargs)
        self.item_validator = item_validator
        self.min_items = min_items
        self.max_items = max_items
    
    def _validate_value(self, value: Any, field_name: str = None) -> List[Any]:
        if not isinstance(value, list):
            raise ValidationError("Must be a list", field_name)
        
        if len(value) < self.min_items:
            raise ValidationError(
                f"Minimum {self.min_items} items required", 
                field_name
            )
        
        if self.max_items and len(value) > self.max_items:
            raise ValidationError(
                f"Maximum {self.max_items} items allowed", 
                field_name
            )
        
        if self.item_validator:
            validated_items = []
            for i, item in enumerate(value):
                try:
                    validated_item = self.item_validator.validate(
                        item, f"{field_name}[{i}]" if field_name else f"item[{i}]"
                    )
                    validated_items.append(validated_item)
                except ValidationError as e:
                    raise ValidationError(
                        f"Item {i}: {e.message}", 
                        field_name
                    )
            return validated_items
        
        return value

class DictValidator(Validator):
    """Dictionary validator"""
    
    def __init__(self, schema: Dict[str, Validator], **kwargs):
        super().__init__(**kwargs)
        self.schema = schema
    
    def _validate_value(self, value: Any, field_name: str = None) -> Dict[str, Any]:
        if not isinstance(value, dict):
            raise ValidationError("Must be a dictionary", field_name)
        
        validated_data = {}
        errors = {}
        
        # Validate each field in schema
        for field_name, validator in self.schema.items():
            try:
                field_value = value.get(field_name)
                validated_data[field_name] = validator.validate(field_value, field_name)
            except ValidationError as e:
                errors[field_name] = e.message
        
        if errors:
            error_messages = [f"{field}: {msg}" for field, msg in errors.items()]
            raise ValidationError("; ".join(error_messages), field_name)
        
        return validated_data

# Predefined validators
class CommonValidators:
    """Common validator instances"""
    
    # String validators
    NAME = StringValidator(min_length=2, max_length=100)
    DESCRIPTION = StringValidator(min_length=10, max_length=1000)
    SHORT_TEXT = StringValidator(max_length=255)
    LONG_TEXT = StringValidator(max_length=5000)
    
    # Number validators
    POSITIVE_INT = IntegerValidator(min_value=1)
    NON_NEGATIVE_INT = IntegerValidator(min_value=0)
    ID = IntegerValidator(min_value=1)
    
    # Contact validators
    EMAIL = EmailValidator()
    PHONE = PhoneValidator(country_code="UZ")
    
    # Date validators
    BIRTH_DATE = DateValidator(
        min_date=date(1900, 1, 1),
        max_date=date.today()
    )
    FUTURE_DATE = DateValidator(min_date=date.today())
    
    # Choice validators
    STATUS = ChoiceValidator([
        'new', 'pending', 'assigned', 'in_progress', 'completed', 'cancelled'
    ])
    ROLE = ChoiceValidator([
        'client', 'technician', 'manager', 'junior_manager', 'admin', 'call_center', 'warehouse', 'controller'
    ])
    LANGUAGE = ChoiceValidator(['uz', 'ru'])
    PRIORITY = ChoiceValidator(['low', 'medium', 'high', 'urgent'])

# Validation schemas
class ValidationSchemas:
    """Predefined validation schemas"""
    
    USER_REGISTRATION = DictValidator({
        'full_name': CommonValidators.NAME,
        'phone': CommonValidators.PHONE,
        'language': CommonValidators.LANGUAGE
    })
    
    ZAYAVKA_CREATE = DictValidator({
        'description': CommonValidators.DESCRIPTION,
        'address': StringValidator(min_length=10, max_length=500),
        'phone': CommonValidators.PHONE,
        'priority': CommonValidators.PRIORITY
    })
    
    USER_UPDATE = DictValidator({
        'full_name': StringValidator(min_length=2, max_length=100, required=False),
        'phone': PhoneValidator(required=False),
        'language': ChoiceValidator(['uz', 'ru'], required=False)
    })
    
    MATERIAL_CREATE = DictValidator({
        'name': CommonValidators.NAME,
        'description': StringValidator(max_length=500, required=False),
        'quantity': CommonValidators.NON_NEGATIVE_INT,
        'unit': StringValidator(max_length=20),
        'price': FloatValidator(min_value=0, required=False)
    })

# Utility functions
def validate_data(data: Dict[str, Any], schema: DictValidator) -> Dict[str, Any]:
    """Validate data against schema"""
    return schema.validate(data)

def validate_field(value: Any, validator: Validator, field_name: str = None) -> Any:
    """Validate single field"""
    return validator.validate(value, field_name)

def is_valid_telegram_id(telegram_id: Any) -> bool:
    """Validate Telegram user ID"""
    try:
        tid = int(telegram_id)
        return 1 <= tid <= 2147483647  # Telegram ID range
    except (ValueError, TypeError):
        return False

def is_valid_zayavka_id(zayavka_id: Any) -> bool:
    """Validate zayavka ID"""
    try:
        zid = int(zayavka_id)
        return zid > 0
    except (ValueError, TypeError):
        return False

def sanitize_input(text: str) -> str:
    """Sanitize user input"""
    if not isinstance(text, str):
        text = str(text)
    
    # Remove potentially dangerous characters
    text = re.sub(r'[<>"\']', '', text)
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def validate_file_upload(file_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate file upload data"""
    schema = DictValidator({
        'file_name': StringValidator(min_length=1, max_length=255),
        'file_size': IntegerValidator(min_value=1, max_value=50*1024*1024),  # Max 50MB
        'mime_type': StringValidator(min_length=1, max_length=100)
    })
    
    return schema.validate(file_data)

def validate_search_query(query: str) -> str:
    """Validate search query"""
    validator = StringValidator(min_length=2, max_length=100)
    return validator.validate(query, 'search_query')

def validate_pagination(page: Any, per_page: Any) -> tuple[int, int]:
    """Validate pagination parameters"""
    page_validator = IntegerValidator(min_value=1, max_value=1000)
    per_page_validator = IntegerValidator(min_value=1, max_value=100)
    
    validated_page = page_validator.validate(page, 'page')
    validated_per_page = per_page_validator.validate(per_page, 'per_page')
    
    return validated_page, validated_per_page

# Custom validation decorators
def validate_input(schema: DictValidator):
    """Decorator to validate handler input"""
    def decorator(func):
        async def wrapper(message_or_callback, *args, **kwargs):
            try:
                # Extract data from message or callback
                if hasattr(message_or_callback, 'text'):
                    # For text messages, create simple validation
                    data = {'text': message_or_callback.text}
                else:
                    # For callbacks, extract from callback_data
                    data = kwargs.get('data', {})
                
                # Validate data
                validated_data = schema.validate(data)
                kwargs['validated_data'] = validated_data
                
                return await func(message_or_callback, *args, **kwargs)
                
            except ValidationError as e:
                error_message = f"Validation error: {e.message}"
                if hasattr(message_or_callback, 'answer'):
                    await message_or_callback.answer(error_message, show_alert=True)
                else:
                    await message_or_callback.reply(error_message)
                return None
        
        return wrapper
    return decorator

# Batch validation
def validate_batch(data_list: List[Dict[str, Any]], 
                  schema: DictValidator) -> tuple[List[Dict[str, Any]], List[Dict[str, str]]]:
    """Validate batch of data"""
    validated_data = []
    errors = []
    
    for i, data in enumerate(data_list):
        try:
            validated_item = schema.validate(data)
            validated_data.append(validated_item)
            errors.append(None)
        except ValidationError as e:
            validated_data.append(None)
            errors.append({'index': i, 'error': e.message})
    
    return validated_data, [e for e in errors if e is not None]

# Validation result class
class ValidationResult:
    """Validation result container"""
    
    def __init__(self, is_valid: bool, data: Any = None, errors: Dict[str, str] = None):
        self.is_valid = is_valid
        self.data = data
        self.errors = errors or {}
    
    def add_error(self, field: str, message: str):
        """Add validation error"""
        self.errors[field] = message
        self.is_valid = False
    
    def has_errors(self) -> bool:
        """Check if has validation errors"""
        return bool(self.errors)
    
    def get_error_message(self) -> str:
        """Get formatted error message"""
        if not self.errors:
            return ""
        
        return "; ".join([f"{field}: {msg}" for field, msg in self.errors.items()])

def safe_validate(data: Any, validator: Validator, field_name: str = None) -> ValidationResult:
    """Safe validation that returns result object"""
    try:
        validated_data = validator.validate(data, field_name)
        return ValidationResult(is_valid=True, data=validated_data)
    except ValidationError as e:
        return ValidationResult(
            is_valid=False, 
            errors={e.field or field_name or 'field': e.message}
        )

# Regex patterns
PHONE_PATTERN = re.compile(r'^\+?[1-9]\d{1,14}$')
EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
TELEGRAM_ID_PATTERN = re.compile(r'^\d{5,12}$')

# Valid roles
VALID_ROLES = [
    'admin', 'manager', 'junior_manager', 'controller', 'call_center', 
    'warehouse', 'technician', 'client', 'blocked'
]

# Valid languages
VALID_LANGUAGES = ['uz', 'ru']

# Valid zayavka statuses
VALID_ZAYAVKA_STATUSES = [
    'yangi', 'qabul_qilindi', 'jarayonda', 'tugallandi', 
    'bekor_qilindi', 'kechiktirildi'
]

def validate_address(address: str) -> bool:
    """
    Validate if the address is properly formatted.
    
    Requirements:
    - Must contain at least 10 characters
    - Must contain at least one space
    - Must not be empty
    """
    if not address:
        return False
    
    # Basic validation
    if len(address) < 10:
        return False
    
    # Must contain at least one space
    if " " not in address:
        return False
    
    # Check for common address components
    address_lower = address.lower()
    if any(word in address_lower for word in ['street', 'st.', 'st', 'avenue', 'ave', 'road', 'rd', 'rd.', 'boulevard', 'blvd']):
        return True
    
    # If no common words, check for numbers (building numbers)
    if any(char.isdigit() for char in address):
        return True
    
    return False

class DataValidator:
    """Data validation utility"""
    
    @staticmethod
    def validate_telegram_id(telegram_id: Union[str, int]) -> int:
        """Validate Telegram ID"""
        try:
            telegram_id = int(telegram_id)
            if telegram_id <= 0:
                raise ValidationError("Telegram ID must be positive")
            if not TELEGRAM_ID_PATTERN.match(str(telegram_id)):
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
            if not PHONE_PATTERN.match(phone):
                raise ValidationError("Invalid phone number format")
            return phone
    
    @staticmethod
    def validate_email(email: str) -> str:
        """Validate email address"""
        if not email or not isinstance(email, str):
            raise ValidationError("Email is required")
        
        email = email.strip().lower()
        if not EMAIL_PATTERN.match(email):
            raise ValidationError("Invalid email format")
        
        return email
    
    @staticmethod
    def validate_role(role: str) -> str:
        """Validate user role"""
        if not role or not isinstance(role, str):
            raise ValidationError("Role is required")
        
        role = role.strip().lower()
        if role not in VALID_ROLES:
            raise ValidationError(f"Invalid role. Must be one of: {', '.join(VALID_ROLES)}")
        
        return role
    
    @staticmethod
    def validate_language(language: str) -> str:
        """Validate language code"""
        if not language or not isinstance(language, str):
            raise ValidationError("Language is required")
        
        language = language.strip().lower()
        if language not in VALID_LANGUAGES:
            raise ValidationError(f"Invalid language. Must be one of: {', '.join(VALID_LANGUAGES)}")
        
        return language
    
    @staticmethod
    def validate_zayavka_status(status: str) -> str:
        """Validate zayavka status"""
        if not status or not isinstance(status, str):
            raise ValidationError("Status is required")
        
        status = status.strip().lower()
        if status not in VALID_ZAYAVKA_STATUSES:
            raise ValidationError(f"Invalid status. Must be one of: {', '.join(VALID_ZAYAVKA_STATUSES)}")
        
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
