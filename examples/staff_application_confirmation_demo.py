"""
Staff Application Confirmation Flow Demo

This demo script demonstrates the application creation confirmation flows for staff members,
including preview, edit capabilities, submission confirmation, and error handling.

Requirements: 1.5, 2.4, 3.4, 4.4
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

# Mock aiogram components for demo
class MockMessage:
    def __init__(self, text: str = ""):
        self.text = text
        self.from_user = MockUser()
    
    async def answer(self, text: str, reply_markup=None, parse_mode=None):
        print(f"📱 Message: {text}")
        if reply_markup:
            print(f"⌨️ Keyboard: {reply_markup}")
    
    async def edit_text(self, text: str, reply_markup=None, parse_mode=None):
        print(f"✏️ Edit: {text}")
        if reply_markup:
            print(f"⌨️ Keyboard: {reply_markup}")

class MockCallbackQuery:
    def __init__(self, data: str = ""):
        self.data = data
        self.from_user = MockUser()
        self.message = MockMessage()
    
    async def answer(self, text: str = "", show_alert: bool = False):
        if text:
            print(f"💬 Callback answer: {text}")

class MockUser:
    def __init__(self, user_id: int = 12345):
        self.id = user_id

class MockFSMContext:
    def __init__(self):
        self._data = {}
        self._state = None
    
    async def get_data(self) -> Dict[str, Any]:
        return self._data.copy()
    
    async def update_data(self, data: Dict[str, Any]):
        self._data.update(data)
    
    async def set_state(self, state):
        self._state = state
        print(f"🔄 State changed to: {state}")
    
    async def clear(self):
        self._data.clear()
        self._state = None
        print("🗑️ State cleared")

# Mock utility functions
async def mock_get_user_language(user_id: int) -> str:
    return 'uz'  # Default to Uzbek

async def mock_get_user_role(user_id: int) -> str:
    return 'manager'  # Default to manager role

# Mock application handler
class MockRoleBasedApplicationHandler:
    async def validate_and_submit(self, application_data: Dict[str, Any], creator_context: Dict[str, Any]) -> Dict[str, Any]:
        # Simulate different outcomes for demo
        import random
        
        outcomes = [
            # Success case
            {
                'success': True,
                'application_id': 'APP-2024-001',
                'workflow_type': 'connection_request',
                'client_id': 123,
                'notification_sent': True,
                'created_at': datetime.now()
            },
            # Validation error case
            {
                'success': False,
                'error_type': 'validation_error',
                'error_message': 'Client data validation failed',
                'error_details': {
                    'phone': 'Invalid phone number format',
                    'address': 'Address is required'
                }
            },
            # Workflow error case
            {
                'success': False,
                'error_type': 'workflow_error',
                'error_message': 'Failed to initialize workflow',
                'error_details': {
                    'workflow_type': 'connection_request',
                    'reason': 'Workflow engine unavailable'
                }
            }
        ]
        
        # Choose outcome based on description content for predictable demo
        description = application_data.get('application_data', {}).get('description', '')
        if 'success' in description.lower():
            return outcomes[0]  # Success
        elif 'validation' in description.lower():
            return outcomes[1]  # Validation error
        elif 'workflow' in description.lower():
            return outcomes[2]  # Workflow error
        else:
            return outcomes[0]  # Default to success

# Demo data
def get_demo_application_data() -> Dict[str, Any]:
    """Get sample application data for demo"""
    return {
        'application_type': 'connection_request',
        'confirmed_client': {
            'id': 123,
            'full_name': 'John Doe',
            'phone_number': '+998901234567',
            'address': '123 Main Street, Tashkent'
        },
        'application_description': 'Need internet connection for home office',
        'application_address': '123 Main Street, Tashkent',
        'connection_type': 'Fiber Optic',
        'tariff': 'Premium 100Mbps',
        'priority': 'medium',
        'session_id': 'session-123',
        'started_at': datetime.now(),
        'media_files': ['photo1.jpg', 'photo2.jpg'],
        'location_data': {'lat': 41.2995, 'lon': 69.2401}
    }

async def demo_application_preview():
    """Demo application preview functionality"""
    print("\n" + "="*60)
    print("📋 DEMO: Application Preview")
    print("="*60)
    
    # Import the actual functions
    from keyboards.staff_confirmation_buttons import (
        format_application_preview_text,
        get_application_preview_keyboard
    )
    
    # Get demo data
    data = get_demo_application_data()
    
    # Test preview formatting
    print("\n1. Testing preview text formatting:")
    preview_text = format_application_preview_text(data, 'uz')
    print(preview_text)
    
    print("\n2. Testing preview keyboard:")
    keyboard = get_application_preview_keyboard('uz')
    print(f"Keyboard buttons: {len(keyboard.inline_keyboard)} rows")
    for row in keyboard.inline_keyboard:
        for button in row:
            print(f"  - {button.text} -> {button.callback_data}")

async def demo_submission_confirmation():
    """Demo submission confirmation functionality"""
    print("\n" + "="*60)
    print("✅ DEMO: Submission Confirmation")
    print("="*60)
    
    from keyboards.staff_confirmation_buttons import (
        format_submission_confirmation_text,
        get_submission_confirmation_keyboard
    )
    
    data = get_demo_application_data()
    
    print("\n1. Testing confirmation text:")
    confirmation_text = format_submission_confirmation_text(data, 'uz')
    print(confirmation_text)
    
    print("\n2. Testing confirmation keyboard:")
    keyboard = get_submission_confirmation_keyboard('uz')
    for row in keyboard.inline_keyboard:
        for button in row:
            print(f"  - {button.text} -> {button.callback_data}")

async def demo_success_flow():
    """Demo successful submission flow"""
    print("\n" + "="*60)
    print("🎉 DEMO: Success Flow")
    print("="*60)
    
    from keyboards.staff_confirmation_buttons import (
        format_success_message_text,
        get_submission_success_keyboard
    )
    
    # Mock successful result
    result = {
        'application_id': 'APP-2024-001',
        'workflow_type': 'connection_request',
        'client_id': 123,
        'notification_sent': True,
        'created_at': datetime.now()
    }
    
    print("\n1. Testing success message:")
    success_text = format_success_message_text(result, 'uz')
    print(success_text)
    
    print("\n2. Testing success keyboard:")
    keyboard = get_submission_success_keyboard('uz')
    for row in keyboard.inline_keyboard:
        for button in row:
            print(f"  - {button.text} -> {button.callback_data}")

async def demo_error_handling():
    """Demo error handling flows"""
    print("\n" + "="*60)
    print("❌ DEMO: Error Handling")
    print("="*60)
    
    from keyboards.staff_confirmation_buttons import (
        format_error_message_text,
        get_error_retry_keyboard
    )
    
    # Test different error types
    error_cases = [
        {
            'error_type': 'validation_error',
            'error_message': 'Data validation failed',
            'error_details': {
                'phone': 'Invalid format',
                'address': 'Required field missing'
            }
        },
        {
            'error_type': 'workflow_error',
            'error_message': 'Workflow initialization failed',
            'error_details': {
                'workflow_type': 'connection_request',
                'reason': 'Service unavailable'
            }
        },
        {
            'error_type': 'permission_denied',
            'error_message': 'Insufficient permissions',
            'error_details': {
                'role': 'junior_manager',
                'required_permission': 'create_technical_service'
            }
        }
    ]
    
    for i, error_case in enumerate(error_cases, 1):
        print(f"\n{i}. Testing {error_case['error_type']}:")
        error_text = format_error_message_text(error_case, 'uz')
        print(error_text)
        
        print(f"   Retry keyboard for {error_case['error_type']}:")
        keyboard = get_error_retry_keyboard(error_case['error_type'], 'uz')
        for row in keyboard.inline_keyboard:
            for button in row:
                print(f"     - {button.text} -> {button.callback_data}")

async def demo_edit_flows():
    """Demo edit functionality"""
    print("\n" + "="*60)
    print("📝 DEMO: Edit Flows")
    print("="*60)
    
    from keyboards.staff_confirmation_buttons import get_application_edit_keyboard
    
    edit_types = ['description', 'address', 'client', 'details']
    
    for edit_type in edit_types:
        print(f"\n1. Testing {edit_type} edit keyboard:")
        keyboard = get_application_edit_keyboard(edit_type, 'uz')
        for row in keyboard.inline_keyboard:
            for button in row:
                print(f"  - {button.text} -> {button.callback_data}")

async def demo_handler_flows():
    """Demo handler flows with mock data"""
    print("\n" + "="*60)
    print("🔄 DEMO: Handler Flows")
    print("="*60)
    
    # Mock the imports to avoid import errors
    import sys
    from unittest.mock import MagicMock
    
    # Mock modules
    sys.modules['aiogram'] = MagicMock()
    sys.modules['aiogram.types'] = MagicMock()
    sys.modules['aiogram.fsm.context'] = MagicMock()
    sys.modules['database.models'] = MagicMock()
    sys.modules['states.staff_application_states'] = MagicMock()
    sys.modules['utils.get_lang'] = MagicMock()
    sys.modules['utils.get_role'] = MagicMock()
    sys.modules['utils.logger'] = MagicMock()
    
    # Mock the handler functions
    async def mock_show_application_preview(message, state, data, lang):
        print(f"📋 Showing application preview in {lang}")
        preview_text = f"Application for {data.get('confirmed_client', {}).get('full_name', 'Unknown')}"
        print(f"Preview: {preview_text}")
    
    async def mock_prepare_application_for_submission(data, user_id, user_role):
        print(f"📦 Preparing application for submission by {user_role} (ID: {user_id})")
        return {
            'client_data': data.get('confirmed_client', {}),
            'application_data': {
                'description': data.get('application_description', ''),
                'location': data.get('application_address', '')
            }
        }
    
    # Demo scenarios
    scenarios = [
        {
            'name': 'Successful Submission',
            'data': get_demo_application_data(),
            'description_override': 'This should be successful'
        },
        {
            'name': 'Validation Error',
            'data': get_demo_application_data(),
            'description_override': 'This should cause validation error'
        },
        {
            'name': 'Workflow Error',
            'data': get_demo_application_data(),
            'description_override': 'This should cause workflow error'
        }
    ]
    
    handler = MockRoleBasedApplicationHandler()
    
    for scenario in scenarios:
        print(f"\n--- Scenario: {scenario['name']} ---")
        
        # Prepare data
        data = scenario['data'].copy()
        data['application_description'] = scenario['description_override']
        
        # Prepare application data
        application_data = await mock_prepare_application_for_submission(data, 12345, 'manager')
        
        # Create context
        creator_context = {
            'creator_id': 12345,
            'creator_role': 'manager',
            'application_type': data.get('application_type'),
            'session_id': data.get('session_id'),
            'started_at': data.get('started_at', datetime.now())
        }
        
        # Submit application
        result = await handler.validate_and_submit(application_data, creator_context)
        
        print(f"Result: {'✅ Success' if result['success'] else '❌ Error'}")
        if result['success']:
            print(f"Application ID: {result.get('application_id')}")
        else:
            print(f"Error: {result.get('error_type')} - {result.get('error_message')}")

async def demo_language_support():
    """Demo language support (Uzbek and Russian)"""
    print("\n" + "="*60)
    print("🌐 DEMO: Language Support")
    print("="*60)
    
    from keyboards.staff_confirmation_buttons import (
        format_application_preview_text,
        format_submission_confirmation_text,
        format_success_message_text,
        format_error_message_text,
        get_application_preview_keyboard
    )
    
    data = get_demo_application_data()
    
    languages = ['uz', 'ru']
    
    for lang in languages:
        print(f"\n--- Language: {lang.upper()} ---")
        
        print("1. Preview text:")
        preview_text = format_application_preview_text(data, lang)
        print(preview_text[:200] + "..." if len(preview_text) > 200 else preview_text)
        
        print("\n2. Confirmation text:")
        confirmation_text = format_submission_confirmation_text(data, lang)
        print(confirmation_text[:200] + "..." if len(confirmation_text) > 200 else confirmation_text)
        
        print("\n3. Keyboard buttons:")
        keyboard = get_application_preview_keyboard(lang)
        for row in keyboard.inline_keyboard:
            for button in row:
                print(f"  - {button.text}")

async def run_all_demos():
    """Run all demo functions"""
    print("🚀 Starting Staff Application Confirmation Flow Demo")
    print("=" * 80)
    
    demos = [
        ("Application Preview", demo_application_preview),
        ("Submission Confirmation", demo_submission_confirmation),
        ("Success Flow", demo_success_flow),
        ("Error Handling", demo_error_handling),
        ("Edit Flows", demo_edit_flows),
        ("Handler Flows", demo_handler_flows),
        ("Language Support", demo_language_support)
    ]
    
    for name, demo_func in demos:
        try:
            print(f"\n🎯 Running {name} Demo...")
            await demo_func()
            print(f"✅ {name} Demo completed successfully")
        except Exception as e:
            print(f"❌ {name} Demo failed: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("🏁 All demos completed!")

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run demos
    asyncio.run(run_all_demos())