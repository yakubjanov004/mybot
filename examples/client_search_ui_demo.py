"""
Client Search and Selection UI Demo
Demonstrates the functionality of the client search and selection system for staff application creation
"""

import asyncio
import logging
import sys
import os
from typing import Dict, Any
from datetime import datetime

# Add the parent directory to the path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the client search and selection components
from keyboards.client_search_buttons import (
    get_client_search_method_keyboard,
    get_client_selection_keyboard,
    get_client_confirmation_keyboard,
    get_new_client_form_keyboard,
    get_new_client_confirmation_keyboard,
    get_client_details_keyboard,
    format_client_display_text,
    get_search_prompt_text,
    get_new_client_form_prompt
)
from utils.client_selection import (
    ClientValidator,
    ClientSearchEngine,
    ClientManager,
    ClientSearchResult,
    ClientValidationError,
    ClientSelectionError
)
from database.models import ClientSelectionData
from utils.role_permissions import (
    get_role_permissions,
    can_create_application,
    can_select_client,
    can_create_client,
    validate_application_creation_permission
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ClientSearchUIDemo:
    """Demo class for client search and selection UI"""
    
    def __init__(self):
        self.client_manager = ClientManager()
        self.client_validator = ClientValidator()
        
    def demo_keyboard_generation(self):
        """Demonstrate keyboard generation for different languages"""
        print("=== Client Search UI Keyboard Demo ===\n")
        
        # Search method selection keyboards
        print("1. Search Method Selection Keyboards:")
        
        uz_keyboard = get_client_search_method_keyboard('uz')
        print(f"   Uzbek keyboard buttons: {len(uz_keyboard.inline_keyboard)} rows")
        for i, row in enumerate(uz_keyboard.inline_keyboard):
            print(f"   Row {i+1}: {[btn.text for btn in row]}")
        
        ru_keyboard = get_client_search_method_keyboard('ru')
        print(f"\n   Russian keyboard buttons: {len(ru_keyboard.inline_keyboard)} rows")
        for i, row in enumerate(ru_keyboard.inline_keyboard):
            print(f"   Row {i+1}: {[btn.text for btn in row]}")
        
        # Client selection keyboard with sample data
        print("\n2. Client Selection Keyboard:")
        sample_clients = [
            {
                'id': 1,
                'full_name': 'Ahmad Karimov',
                'phone_number': '+998901234567'
            },
            {
                'id': 2,
                'full_name': 'Olga Petrova',
                'phone_number': '+998907654321'
            },
            {
                'id': 3,
                'full_name': 'Sardor Rahimov',
                'phone_number': '+998909876543'
            }
        ]
        
        selection_keyboard = get_client_selection_keyboard(sample_clients, 'uz')
        print(f"   Selection keyboard: {len(selection_keyboard.inline_keyboard)} rows")
        for i, row in enumerate(selection_keyboard.inline_keyboard):
            print(f"   Row {i+1}: {[btn.text for btn in row]}")
        
        # New client form keyboards
        print("\n3. New Client Form Keyboards:")
        for step in ['name', 'phone', 'address']:
            keyboard = get_new_client_form_keyboard(step, 'uz')
            print(f"   {step.capitalize()} step: {len(keyboard.keyboard)} buttons")
            for row in keyboard.keyboard:
                print(f"     {[btn.text for btn in row]}")
    
    def demo_client_display_formatting(self):
        """Demonstrate client data display formatting"""
        print("\n=== Client Display Formatting Demo ===\n")
        
        sample_clients = [
            {
                'id': 1,
                'full_name': 'Ahmad Karimov',
                'phone_number': '+998901234567',
                'address': 'Tashkent, Yunusobod district',
                'language': 'uz',
                'created_at': datetime(2024, 1, 15, 10, 30)
            },
            {
                'id': 2,
                'full_name': 'Ольга Петрова',
                'phone_number': '+998907654321',
                'address': 'Самарканд, центр',
                'language': 'ru',
                'created_at': datetime(2024, 2, 20, 14, 45)
            }
        ]
        
        for i, client in enumerate(sample_clients, 1):
            print(f"{i}. Client Display (Uzbek):")
            uz_display = format_client_display_text(client, 'uz')
            print(uz_display)
            
            print(f"\n{i}. Client Display (Russian):")
            ru_display = format_client_display_text(client, 'ru')
            print(ru_display)
            print("-" * 50)
    
    def demo_search_prompts(self):
        """Demonstrate search prompt text generation"""
        print("\n=== Search Prompt Demo ===\n")
        
        search_methods = ['phone', 'name', 'id']
        languages = ['uz', 'ru']
        
        for method in search_methods:
            print(f"Search Method: {method.upper()}")
            for lang in languages:
                prompt = get_search_prompt_text(method, lang)
                print(f"  {lang.upper()}: {prompt}")
            print()
    
    def demo_form_prompts(self):
        """Demonstrate new client form prompt generation"""
        print("\n=== New Client Form Prompt Demo ===\n")
        
        form_steps = ['name', 'phone', 'address']
        languages = ['uz', 'ru']
        
        for step in form_steps:
            print(f"Form Step: {step.upper()}")
            for lang in languages:
                prompt = get_new_client_form_prompt(step, lang)
                print(f"  {lang.upper()}: {prompt}")
            print()
    
    def demo_client_validation(self):
        """Demonstrate client data validation"""
        print("\n=== Client Validation Demo ===\n")
        
        # Test phone number validation
        print("1. Phone Number Validation:")
        test_phones = [
            "+998901234567",  # Valid
            "998901234567",   # Valid
            "901234567",      # Valid
            "+1234567890",    # Invalid
            "123",            # Invalid
            "abc123"          # Invalid
        ]
        
        for phone in test_phones:
            is_valid = self.client_validator.validate_phone_number(phone)
            normalized = self.client_validator.normalize_phone_number(phone) if is_valid else "N/A"
            print(f"   {phone:<15} -> Valid: {is_valid:<5} | Normalized: {normalized}")
        
        # Test name validation
        print("\n2. Full Name Validation:")
        test_names = [
            "Ahmad Karimov",      # Valid
            "Ольга Петрова",      # Valid
            "O'tkir Rahimov",     # Valid
            "A",                  # Invalid (too short)
            "John@Doe",           # Invalid (special chars)
            "A" * 101             # Invalid (too long)
        ]
        
        for name in test_names:
            is_valid = self.client_validator.validate_full_name(name)
            display_name = name if len(name) <= 20 else name[:20] + "..."
            print(f"   {display_name:<25} -> Valid: {is_valid}")
        
        # Test complete client data validation
        print("\n3. Complete Client Data Validation:")
        test_data_sets = [
            {
                'name': 'Valid Data',
                'data': {
                    'full_name': 'Ahmad Karimov',
                    'phone_number': '+998901234567',
                    'language': 'uz',
                    'address': 'Tashkent, Yunusobod'
                }
            },
            {
                'name': 'Invalid Data',
                'data': {
                    'full_name': 'A',  # Too short
                    'phone_number': '123',  # Invalid format
                    'language': 'invalid',  # Invalid language
                    'address': 'A' * 501  # Too long
                }
            }
        ]
        
        for test_set in test_data_sets:
            print(f"   {test_set['name']}:")
            errors = self.client_validator.validate_client_data(test_set['data'])
            if errors:
                for error in errors:
                    print(f"     - {error}")
            else:
                print("     - No errors")
    
    def demo_role_permissions(self):
        """Demonstrate role-based permissions for client operations"""
        print("\n=== Role Permissions Demo ===\n")
        
        roles = ['manager', 'junior_manager', 'controller', 'call_center', 'client', 'technician']
        
        print("Role Permissions Matrix:")
        print(f"{'Role':<20} {'Create App':<12} {'Select Client':<15} {'Create Client':<15}")
        print("-" * 65)
        
        for role in roles:
            try:
                can_create = can_create_application(role, 'connection_request') or can_create_application(role, 'technical_service')
                can_select = can_select_client(role)
                can_create_new = can_create_client(role)
                
                print(f"{role:<20} {'✅' if can_create else '❌':<12} {'✅' if can_select else '❌':<15} {'✅' if can_create_new else '❌':<15}")
            except Exception as e:
                print(f"{role:<20} {'❌':<12} {'❌':<15} {'❌':<15}")
        
        # Detailed permissions for staff roles
        print("\nDetailed Staff Role Permissions:")
        staff_roles = ['manager', 'junior_manager', 'controller', 'call_center']
        
        for role in staff_roles:
            try:
                permissions = get_role_permissions(role)
                print(f"\n{role.upper()}:")
                print(f"  - Connection Requests: {'✅' if permissions.can_create_connection else '❌'}")
                print(f"  - Technical Service: {'✅' if permissions.can_create_technical else '❌'}")
                print(f"  - Direct Assignment: {'✅' if permissions.can_assign_directly else '❌'}")
                print(f"  - Client Selection: {'✅' if permissions.can_select_client else '❌'}")
                print(f"  - Client Creation: {'✅' if permissions.can_create_client else '❌'}")
                print(f"  - Notification Level: {permissions.notification_level}")
                print(f"  - Daily Limit: {permissions.max_applications_per_day or 'Unlimited'}")
            except Exception as e:
                print(f"{role}: Error - {e}")
    
    async def demo_search_simulation(self):
        """Simulate client search operations"""
        print("\n=== Client Search Simulation Demo ===\n")
        
        # Note: This is a simulation since we don't have actual database connection
        print("Simulating client search operations...")
        
        # Simulate search results
        mock_search_results = [
            ClientSearchResult(
                found=True,
                client={
                    'id': 1,
                    'full_name': 'Ahmad Karimov',
                    'phone_number': '+998901234567',
                    'language': 'uz',
                    'address': 'Tashkent'
                }
            ),
            ClientSearchResult(
                found=True,
                multiple_matches=[
                    {'id': 2, 'full_name': 'Ahmad Ali', 'phone_number': '+998901111111'},
                    {'id': 3, 'full_name': 'Ahmad Umar', 'phone_number': '+998902222222'}
                ]
            ),
            ClientSearchResult(
                found=False,
                error="Client not found"
            )
        ]
        
        scenarios = [
            "Single client found",
            "Multiple clients found",
            "No client found"
        ]
        
        for i, (scenario, result) in enumerate(zip(scenarios, mock_search_results), 1):
            print(f"{i}. {scenario}:")
            
            if result.error:
                print(f"   Error: {result.error}")
            elif not result.found:
                print("   No results")
            elif result.multiple_matches:
                print(f"   Found {len(result.multiple_matches)} matches:")
                for match in result.multiple_matches:
                    print(f"     - {match['full_name']} ({match['phone_number']})")
            elif result.client:
                print(f"   Found: {result.client['full_name']} ({result.client['phone_number']})")
            
            print()
    
    def demo_client_selection_data(self):
        """Demonstrate ClientSelectionData model usage"""
        print("\n=== Client Selection Data Model Demo ===\n")
        
        # Create different types of client selection data
        selection_examples = [
            {
                'name': 'Phone Search',
                'data': ClientSelectionData(
                    search_method='phone',
                    search_value='+998901234567',
                    client_id=123,
                    verified=True
                )
            },
            {
                'name': 'Name Search',
                'data': ClientSelectionData(
                    search_method='name',
                    search_value='Ahmad Karimov',
                    client_id=456,
                    verified=True
                )
            },
            {
                'name': 'New Client Creation',
                'data': ClientSelectionData(
                    search_method='new',
                    new_client_data={
                        'full_name': 'New Client',
                        'phone_number': '+998909999999',
                        'language': 'uz'
                    },
                    verified=False
                )
            }
        ]
        
        for example in selection_examples:
            print(f"{example['name']}:")
            data = example['data']
            data_dict = data.to_dict()
            
            print(f"  Search Method: {data.search_method}")
            print(f"  Search Value: {data.search_value}")
            print(f"  Client ID: {data.client_id}")
            print(f"  Verified: {data.verified}")
            if data.new_client_data:
                print(f"  New Client Data: {data.new_client_data}")
            print(f"  Dictionary: {data_dict}")
            print()
    
    def run_all_demos(self):
        """Run all demonstration functions"""
        print("🚀 Starting Client Search and Selection UI Demo\n")
        
        try:
            self.demo_keyboard_generation()
            self.demo_client_display_formatting()
            self.demo_search_prompts()
            self.demo_form_prompts()
            self.demo_client_validation()
            self.demo_role_permissions()
            asyncio.run(self.demo_search_simulation())
            self.demo_client_selection_data()
            
            print("\n✅ All demos completed successfully!")
            
        except Exception as e:
            print(f"\n❌ Demo failed with error: {e}")
            logger.exception("Demo error")


def main():
    """Main function to run the demo"""
    demo = ClientSearchUIDemo()
    demo.run_all_demos()


if __name__ == '__main__':
    main()