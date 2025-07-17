"""
Demonstration of staff notification system extensions
"""

import asyncio
from datetime import datetime
from utils.notification_system import NotificationSystem


async def demo_staff_notification_system():
    """Demonstrate staff notification system functionality"""
    
    print("=== Staff Notification System Demo ===\n")
    
    # Initialize notification system
    notification_system = NotificationSystem()
    
    # 1. Demonstrate template loading
    print("1. Template Structure:")
    templates = notification_system.staff_notification_templates
    
    print(f"   - Template categories: {list(templates.keys())}")
    print(f"   - Languages supported: {list(templates['client_notification'].keys())}")
    print(f"   - Application types: {list(templates['client_notification']['uz'].keys())}")
    print()
    
    # 2. Demonstrate creator role formatting
    print("2. Creator Role Formatting:")
    roles = ['manager', 'junior_manager', 'controller', 'call_center']
    
    for role in roles:
        uz_format = notification_system._format_creator_role(role, 'uz')
        ru_format = notification_system._format_creator_role(role, 'ru')
        print(f"   - {role}: UZ='{uz_format}', RU='{ru_format}'")
    print()
    
    # 3. Demonstrate template content
    print("3. Sample Template Content:")
    
    # Client notification template (Uzbek)
    client_template_uz = templates['client_notification']['uz']['connection_request']
    print("   Client Notification (Uzbek):")
    print(f"   Title: {client_template_uz['title']}")
    print(f"   Button: {client_template_uz['button']}")
    print()
    
    # Staff confirmation template (Russian)
    staff_template_ru = templates['staff_confirmation']['ru']['technical_service']
    print("   Staff Confirmation (Russian):")
    print(f"   Title: {staff_template_ru['title']}")
    print(f"   Button: {staff_template_ru['button']}")
    print()
    
    # Workflow participant template (Uzbek)
    workflow_template_uz = templates['workflow_participant']['uz']['connection_request']
    print("   Workflow Participant (Uzbek):")
    print(f"   Title: {workflow_template_uz['title']}")
    print(f"   Button: {workflow_template_uz['button']}")
    print()
    
    # 4. Demonstrate notification ID generation
    print("4. Notification ID Generation:")
    ids = [notification_system._generate_notification_id() for _ in range(3)]
    for i, notification_id in enumerate(ids, 1):
        print(f"   ID {i}: {notification_id}")
    print()
    
    # 5. Demonstrate template formatting
    print("5. Template Formatting Example:")
    
    sample_data = {
        'client_name': 'Alisher Karimov',
        'description': 'Internet ulanishini o\'rnatish',
        'location': 'Toshkent sh., Chilonzor t., 5-uy',
        'creator_role': notification_system._format_creator_role('manager', 'uz'),
        'request_id': 'REQ12345',
        'created_at': datetime.now().strftime('%d.%m.%Y %H:%M')
    }
    
    formatted_message = client_template_uz['body'].format(**sample_data)
    print("   Formatted Client Notification:")
    print(f"   {formatted_message}")
    print()
    
    # 6. Demonstrate excluded roles
    print("6. Excluded Roles:")
    print(f"   Excluded from notifications: {notification_system.excluded_roles}")
    print()
    
    print("=== Demo Complete ===")
    print("\nThe staff notification system extensions include:")
    print("✅ Client notification templates for staff-created applications")
    print("✅ Staff confirmation notifications")
    print("✅ Workflow participant notifications with staff creation context")
    print("✅ Support for both Uzbek and Russian languages")
    print("✅ Role-based formatting and localization")
    print("✅ Integration with existing workflow engine")


if __name__ == '__main__':
    asyncio.run(demo_staff_notification_system())