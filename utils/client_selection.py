"""
Client Selection and Validation System for Staff Application Creation

This module provides functionality for staff members to search for existing clients
or create new client records when creating applications on behalf of clients.
"""

import re
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import logging
from dataclasses import dataclass

from database.models import User, ClientSelectionData, ModelConstants
from database.base_queries import get_user_by_telegram_id, get_user_by_id, create_user
from loader import bot

logger = logging.getLogger(__name__)


class ClientValidationError(Exception):
    """Exception raised when client validation fails"""
    
    def __init__(self, field: str, value: str, reason: str):
        self.field = field
        self.value = value
        self.reason = reason
        super().__init__(f"Client validation failed for {field}: {reason}")


class ClientSelectionError(Exception):
    """Exception raised when client selection fails"""
    
    def __init__(self, search_method: str, search_value: str, reason: str):
        self.search_method = search_method
        self.search_value = search_value
        self.reason = reason
        super().__init__(f"Client selection failed for {search_method}={search_value}: {reason}")


@dataclass
class ClientSearchResult:
    """Result of client search operation"""
    found: bool
    client: Optional[Dict[str, Any]] = None
    multiple_matches: List[Dict[str, Any]] = None
    error: Optional[str] = None


class ClientValidator:
    """Validates client data for staff-created applications"""
    
    @staticmethod
    def validate_phone_number(phone: str) -> bool:
        """Validate phone number format"""
        if not phone:
            return False
        
        # Remove all non-digit characters
        digits_only = re.sub(r'\D', '', phone)
        
        # Check if it's a valid Uzbek phone number
        # Uzbek numbers: +998XXXXXXXXX (13 digits total) or 998XXXXXXXXX (12 digits)
        if len(digits_only) == 12 and digits_only.startswith('998'):
            return True
        elif len(digits_only) == 13 and digits_only.startswith('998'):
            return True
        elif len(digits_only) == 9:  # Local format without country code
            return True
        
        return False
    
    @staticmethod
    def normalize_phone_number(phone: str) -> str:
        """Normalize phone number to standard format"""
        if not phone:
            return ""
        
        # Remove all non-digit characters
        digits_only = re.sub(r'\D', '', phone)
        
        # Add country code if missing
        if len(digits_only) == 9:
            digits_only = '998' + digits_only
        elif len(digits_only) == 12 and digits_only.startswith('998'):
            pass  # Already correct
        elif len(digits_only) == 13 and digits_only.startswith('998'):
            digits_only = digits_only[1:]  # Remove leading digit
        
        return '+' + digits_only
    
    @staticmethod
    def validate_full_name(name: str) -> bool:
        """Validate full name"""
        if not name or len(name.strip()) < 2:
            return False
        
        if len(name) > ModelConstants.MAX_NAME_LENGTH:
            return False
        
        # Check for valid characters (letters, spaces, hyphens, apostrophes)
        # Include Latin, Cyrillic, and common Uzbek characters
        if not re.match(r"^[a-zA-ZА-Яа-яЁёўҳқғшчжўҳ\u0400-\u04FF\s\-']+$", name.strip()):
            return False
        
        return True
    
    @staticmethod
    def validate_client_data(client_data: Dict[str, Any]) -> List[str]:
        """Validate complete client data and return list of errors"""
        errors = []
        
        # Validate full name
        full_name = client_data.get('full_name', '').strip()
        if not ClientValidator.validate_full_name(full_name):
            errors.append("Invalid full name: must be 2-100 characters, letters only")
        
        # Validate phone number
        phone = client_data.get('phone_number', '').strip()
        if not ClientValidator.validate_phone_number(phone):
            errors.append("Invalid phone number: must be valid Uzbek phone number")
        
        # Validate language
        language = client_data.get('language', 'uz')
        if language not in ['uz', 'ru']:
            errors.append("Invalid language: must be 'uz' or 'ru'")
        
        # Validate address (optional but if provided, must be reasonable)
        address = client_data.get('address', '').strip()
        if address and len(address) > ModelConstants.MAX_ADDRESS_LENGTH:
            errors.append(f"Address too long: maximum {ModelConstants.MAX_ADDRESS_LENGTH} characters")
        
        return errors


class ClientSearchEngine:
    """Handles client search operations"""
    
    @staticmethod
    async def search_by_phone(phone: str) -> ClientSearchResult:
        """Search for client by phone number"""
        try:
            # Normalize phone number
            normalized_phone = ClientValidator.normalize_phone_number(phone)
            
            if not ClientValidator.validate_phone_number(normalized_phone):
                return ClientSearchResult(
                    found=False,
                    error="Invalid phone number format"
                )
            
            # Search in database
            async with bot.db.acquire() as conn:
                query = """
                    SELECT id, telegram_id, full_name, phone_number, role, language, 
                           is_active, address, created_at, updated_at
                    FROM users 
                    WHERE phone_number = $1 OR phone_number = $2
                    ORDER BY created_at DESC
                """
                
                # Try both with and without + prefix
                phone_variants = [normalized_phone, normalized_phone.lstrip('+')]
                results = await conn.fetch(query, normalized_phone, normalized_phone.lstrip('+'))
                
                if not results:
                    return ClientSearchResult(found=False)
                
                if len(results) == 1:
                    return ClientSearchResult(
                        found=True,
                        client=dict(results[0])
                    )
                else:
                    return ClientSearchResult(
                        found=True,
                        multiple_matches=[dict(row) for row in results]
                    )
                    
        except Exception as e:
            logger.error(f"Error searching client by phone {phone}: {e}")
            return ClientSearchResult(
                found=False,
                error=f"Database error: {str(e)}"
            )
    
    @staticmethod
    async def search_by_name(name: str) -> ClientSearchResult:
        """Search for client by full name (fuzzy search)"""
        try:
            if not name or len(name.strip()) < 2:
                return ClientSearchResult(
                    found=False,
                    error="Name must be at least 2 characters"
                )
            
            name = name.strip()
            
            async with bot.db.acquire() as conn:
                # Use ILIKE for case-insensitive partial matching
                query = """
                    SELECT id, telegram_id, full_name, phone_number, role, language, 
                           is_active, address, created_at, updated_at
                    FROM users 
                    WHERE full_name ILIKE $1
                    ORDER BY 
                        CASE WHEN full_name ILIKE $2 THEN 1 ELSE 2 END,
                        created_at DESC
                    LIMIT 10
                """
                
                # Search patterns: exact match gets priority, then partial
                exact_pattern = name
                partial_pattern = f"%{name}%"
                
                results = await conn.fetch(query, partial_pattern, exact_pattern)
                
                if not results:
                    return ClientSearchResult(found=False)
                
                if len(results) == 1:
                    return ClientSearchResult(
                        found=True,
                        client=dict(results[0])
                    )
                else:
                    return ClientSearchResult(
                        found=True,
                        multiple_matches=[dict(row) for row in results]
                    )
                    
        except Exception as e:
            logger.error(f"Error searching client by name {name}: {e}")
            return ClientSearchResult(
                found=False,
                error=f"Database error: {str(e)}"
            )
    
    @staticmethod
    async def search_by_id(client_id: int) -> ClientSearchResult:
        """Search for client by database ID"""
        try:
            if not isinstance(client_id, int) or client_id <= 0:
                return ClientSearchResult(
                    found=False,
                    error="Invalid client ID"
                )
            
            client_data = await get_user_by_id(client_id)
            
            if client_data:
                return ClientSearchResult(
                    found=True,
                    client=client_data
                )
            else:
                return ClientSearchResult(found=False)
                
        except Exception as e:
            logger.error(f"Error searching client by ID {client_id}: {e}")
            return ClientSearchResult(
                found=False,
                error=f"Database error: {str(e)}"
            )


class ClientManager:
    """Main class for client selection and management"""
    
    def __init__(self):
        self.validator = ClientValidator()
        self.search_engine = ClientSearchEngine()
    
    async def search_client(self, search_method: str, search_value: str) -> ClientSearchResult:
        """Search for client using specified method"""
        if search_method not in ModelConstants.SEARCH_METHODS:
            raise ClientSelectionError(
                search_method, search_value, 
                f"Invalid search method. Must be one of: {ModelConstants.SEARCH_METHODS}"
            )
        
        if search_method == "phone":
            return await self.search_engine.search_by_phone(search_value)
        elif search_method == "name":
            return await self.search_engine.search_by_name(search_value)
        elif search_method == "id":
            try:
                client_id = int(search_value)
                return await self.search_engine.search_by_id(client_id)
            except ValueError:
                return ClientSearchResult(
                    found=False,
                    error="Invalid ID format"
                )
        else:
            raise ClientSelectionError(
                search_method, search_value,
                f"Search method {search_method} not implemented"
            )
    
    async def create_new_client(self, client_data: Dict[str, Any]) -> Tuple[bool, Optional[int], List[str]]:
        """
        Create a new client record
        
        Returns:
            Tuple of (success, client_id, errors)
        """
        try:
            # Validate client data
            validation_errors = self.validator.validate_client_data(client_data)
            if validation_errors:
                return False, None, validation_errors
            
            # Normalize phone number
            phone = self.validator.normalize_phone_number(client_data.get('phone_number', ''))
            
            # Check if client already exists with this phone
            existing_client = await self.search_engine.search_by_phone(phone)
            if existing_client.found:
                return False, None, ["Client with this phone number already exists"]
            
            # Create new user record
            client_id = await create_user(
                telegram_id=None,  # Will be set when client first uses bot
                full_name=client_data.get('full_name', '').strip(),
                username=None,
                phone_number=phone,
                role='client',
                language=client_data.get('language', 'uz')
            )
            
            if client_id:
                # Update additional fields if provided
                if client_data.get('address'):
                    from database.base_queries import update_client_info
                    await update_client_info(client_id, {'address': client_data['address']})
                
                logger.info(f"Created new client {client_id} with phone {phone}")
                return True, client_id, []
            else:
                return False, None, ["Failed to create client record"]
                
        except Exception as e:
            logger.error(f"Error creating new client: {e}")
            return False, None, [f"Database error: {str(e)}"]
    
    async def validate_client_selection(self, selection_data: ClientSelectionData) -> List[str]:
        """Validate client selection data"""
        errors = []
        
        # Validate search method
        if selection_data.search_method not in ModelConstants.SEARCH_METHODS:
            errors.append(f"Invalid search method: {selection_data.search_method}")
        
        # Validate search value for non-new methods
        if selection_data.search_method != "new":
            if not selection_data.search_value:
                errors.append("Search value is required for non-new search methods")
        
        # Validate new client data
        if selection_data.search_method == "new":
            if not selection_data.new_client_data:
                errors.append("New client data is required when search method is 'new'")
            else:
                client_validation_errors = self.validator.validate_client_data(
                    selection_data.new_client_data
                )
                errors.extend(client_validation_errors)
        
        # Validate client_id if provided
        if selection_data.client_id is not None:
            if not isinstance(selection_data.client_id, int) or selection_data.client_id <= 0:
                errors.append("Invalid client ID")
        
        return errors
    
    async def process_client_selection(self, selection_data: ClientSelectionData) -> Tuple[bool, Optional[Dict[str, Any]], List[str]]:
        """
        Process client selection and return client data
        
        Returns:
            Tuple of (success, client_data, errors)
        """
        try:
            # Validate selection data
            validation_errors = await self.validate_client_selection(selection_data)
            if validation_errors:
                return False, None, validation_errors
            
            if selection_data.search_method == "new":
                # Create new client
                success, client_id, errors = await self.create_new_client(
                    selection_data.new_client_data
                )
                if success:
                    # Fetch the created client data
                    client_data = await get_user_by_id(client_id)
                    return True, client_data, []
                else:
                    return False, None, errors
            
            else:
                # Search for existing client
                search_result = await self.search_client(
                    selection_data.search_method,
                    selection_data.search_value
                )
                
                if search_result.error:
                    return False, None, [search_result.error]
                
                if not search_result.found:
                    return False, None, ["Client not found"]
                
                if search_result.multiple_matches:
                    return False, None, ["Multiple clients found - please be more specific"]
                
                return True, search_result.client, []
                
        except Exception as e:
            logger.error(f"Error processing client selection: {e}")
            return False, None, [f"Processing error: {str(e)}"]
    
    def format_client_display(self, client_data: Dict[str, Any], language: str = 'uz') -> str:
        """Format client data for display"""
        if not client_data:
            return "No client data"
        
        name = client_data.get('full_name', 'Unknown')
        phone = client_data.get('phone_number', 'No phone')
        client_id = client_data.get('id', 'Unknown ID')
        
        if language == 'uz':
            return f"👤 {name}\n📞 {phone}\n🆔 ID: {client_id}"
        else:
            return f"👤 {name}\n📞 {phone}\n🆔 ID: {client_id}"
    
    def format_multiple_clients_display(self, clients: List[Dict[str, Any]], language: str = 'uz') -> str:
        """Format multiple clients for selection display"""
        if not clients:
            return "No clients found"
        
        header = "Найдено несколько клиентов:" if language == 'ru' else "Bir nechta mijoz topildi:"
        lines = [header, ""]
        
        for i, client in enumerate(clients[:5], 1):  # Limit to 5 results
            name = client.get('full_name', 'Unknown')
            phone = client.get('phone_number', 'No phone')
            client_id = client.get('id', 'Unknown')
            lines.append(f"{i}. {name} - {phone} (ID: {client_id})")
        
        if len(clients) > 5:
            more_text = "и еще..." if language == 'ru' else "va yana..."
            lines.append(f"... {more_text}")
        
        return "\n".join(lines)


# Convenience functions for easy usage
async def search_client_by_phone(phone: str) -> ClientSearchResult:
    """Convenience function to search client by phone"""
    manager = ClientManager()
    return await manager.search_client("phone", phone)


async def search_client_by_name(name: str) -> ClientSearchResult:
    """Convenience function to search client by name"""
    manager = ClientManager()
    return await manager.search_client("name", name)


async def search_client_by_id(client_id: int) -> ClientSearchResult:
    """Convenience function to search client by ID"""
    manager = ClientManager()
    return await manager.search_client("id", str(client_id))


async def create_client_from_data(client_data: Dict[str, Any]) -> Tuple[bool, Optional[int], List[str]]:
    """Convenience function to create new client"""
    manager = ClientManager()
    return await manager.create_new_client(client_data)


# Export main classes and functions
__all__ = [
    'ClientValidationError',
    'ClientSelectionError', 
    'ClientSearchResult',
    'ClientValidator',
    'ClientSearchEngine',
    'ClientManager',
    'search_client_by_phone',
    'search_client_by_name', 
    'search_client_by_id',
    'create_client_from_data'
]