"""
Admin Interface for Workflow Recovery

This module provides admin handlers for:
- Detecting and viewing stuck workflows
- Performing workflow recovery actions
- Monitoring system health
- Managing error recovery processes

Requirements implemented: Task 12 - Create comprehensive error handling and recovery
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from typing import Dict, Any, List
import json
from datetime import datetime

from database.models import UserRole
from utils.error_recovery import ComprehensiveErrorRecoverySystem
from utils.workflow_engine import WorkflowEngine
from utils.state_manager import StateManager
from utils.notification_system import NotificationSystem
from utils.inventory_manager import InventoryManager
from utils.logger import setup_module_logger
from filters.role_filter import RoleFilter

logger = setup_module_logger("admin_workflow_recovery")
router = Router()

# Apply role filter to ensure only admins can access these handlers
router.message.filter(RoleFilter([UserRole.ADMIN]))
router.callback_query.filter(RoleFilter([UserRole.ADMIN]))


class WorkflowRecoveryStates(StatesGroup):
    """States for workflow recovery process"""
    VIEWING_STUCK_WORKFLOWS = State()
    SELECTING_RECOVERY_ACTION = State()
    ENTERING_RECOVERY_DATA = State()
    CONFIRMING_RECOVERY = State()


# Initialize recovery system (will be properly initialized in loader.py)
recovery_system = None


def get_recovery_system():
    """Get or create recovery system instance"""
    global recovery_system
    if recovery_system is None:
        from loader import bot
        state_manager = StateManager()
        notification_system = NotificationSystem()
        inventory_manager = InventoryManager()
        workflow_engine = WorkflowEngine(state_manager, notification_system, inventory_manager)
        recovery_system = ComprehensiveErrorRecoverySystem(
            state_manager, notification_system, inventory_manager, workflow_engine
        )
    return recovery_system


@router.message(Command("workflow_recovery"))
async def workflow_recovery_menu(message: Message, state: FSMContext):
    """Main workflow recovery menu"""
    try:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔍 Detect Stuck Workflows", callback_data="detect_stuck_workflows")],
            [InlineKeyboardButton(text="📊 System Health", callback_data="system_health")],
            [InlineKeyboardButton(text="🔄 Inventory Reconciliation", callback_data="inventory_reconciliation")],
            [InlineKeyboardButton(text="📈 Error Statistics", callback_data="error_statistics")],
            [InlineKeyboardButton(text="🔔 Notification Retries", callback_data="notification_retries")],
            [InlineKeyboardButton(text="❌ Close", callback_data="close_menu")]
        ])
        
        await message.answer(
            "🛠 <b>Workflow Recovery & System Management</b>\n\n"
            "Select an option to manage system recovery and monitoring:",
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        
    except Exception as e:
        logger.error(f"Error in workflow recovery menu: {e}")
        await message.answer("❌ Error accessing workflow recovery menu. Please try again.")


@router.callback_query(F.data == "detect_stuck_workflows")
async def detect_stuck_workflows(callback: CallbackQuery, state: FSMContext):
    """Detect and display stuck workflows"""
    try:
        await callback.answer("🔍 Detecting stuck workflows...")
        
        recovery_sys = get_recovery_system()
        stuck_workflows = await recovery_sys.workflow_recovery_manager.detect_stuck_workflows()
        
        if not stuck_workflows:
            await callback.message.edit_text(
                "✅ <b>No Stuck Workflows Found</b>\n\n"
                "All workflows are progressing normally.",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Back to Menu", callback_data="back_to_recovery_menu")]
                ])
            )
            return
        
        # Display stuck workflows
        text = f"⚠️ <b>Found {len(stuck_workflows)} Stuck Workflows</b>\n\n"
        
        keyboard_buttons = []
        for i, workflow in enumerate(stuck_workflows[:10]):  # Limit to 10 for display
            duration_hours = int(workflow['stuck_duration_hours'])
            text += (
                f"<b>{i+1}. {workflow['workflow_type'].replace('_', ' ').title()}</b>\n"
                f"   📋 ID: <code>{workflow['request_id'][:8]}...</code>\n"
                f"   👤 Role: {workflow['role_current ']}\n"
                f"   ⏰ Stuck: {duration_hours}h\n"
                f"   📝 {workflow['description'][:50]}...\n\n"
            )
            
            keyboard_buttons.append([
                InlineKeyboardButton(
                    text=f"🔧 Recover #{i+1}",
                    callback_data=f"recover_workflow_{workflow['request_id']}"
                )
            ])
        
        keyboard_buttons.append([
            InlineKeyboardButton(text="🔙 Back to Menu", callback_data="back_to_recovery_menu")
        ])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        
        await callback.message.edit_text(text, parse_mode='HTML', reply_markup=keyboard)
        await state.set_state(WorkflowRecoveryStates.VIEWING_STUCK_WORKFLOWS)
        
    except Exception as e:
        logger.error(f"Error detecting stuck workflows: {e}")
        await callback.answer("❌ Error detecting stuck workflows", show_alert=True)


@router.callback_query(F.data.startswith("recover_workflow_"))
async def select_recovery_action(callback: CallbackQuery, state: FSMContext):
    """Select recovery action for a specific workflow"""
    try:
        request_id = callback.data.split("_", 2)[2]
        
        recovery_sys = get_recovery_system()
        recovery_options = await recovery_sys.workflow_recovery_manager.get_recovery_options(request_id)
        
        if not recovery_options:
            await callback.answer("❌ No recovery options available for this workflow", show_alert=True)
            return
        
        # Store request_id in state data
        await state.update_data(request_id=request_id)
        
        text = f"🔧 <b>Recovery Options for Workflow</b>\n\n"
        text += f"📋 Request ID: <code>{request_id[:8]}...</code>\n\n"
        text += "Select a recovery action:"
        
        keyboard_buttons = []
        for option in recovery_options:
            action_text = {
                'force_transition': '➡️ Force Transition',
                'reset_to_previous_state': '⏪ Reset to Previous',
                'complete_workflow': '✅ Force Complete',
                'reassign_role': '👥 Reassign User'
            }.get(option['action'], option['action'])
            
            keyboard_buttons.append([
                InlineKeyboardButton(
                    text=action_text,
                    callback_data=f"recovery_action_{option['action']}"
                )
            ])
        
        keyboard_buttons.append([
            InlineKeyboardButton(text="🔙 Back to Workflows", callback_data="detect_stuck_workflows")
        ])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        
        await callback.message.edit_text(text, parse_mode='HTML', reply_markup=keyboard)
        await state.set_state(WorkflowRecoveryStates.SELECTING_RECOVERY_ACTION)
        
    except Exception as e:
        logger.error(f"Error selecting recovery action: {e}")
        await callback.answer("❌ Error loading recovery options", show_alert=True)


@router.callback_query(F.data.startswith("recovery_action_"))
async def execute_recovery_action(callback: CallbackQuery, state: FSMContext):
    """Execute the selected recovery action"""
    try:
        action = callback.data.split("_", 2)[2]
        state_data = await state.get_data()
        request_id = state_data.get('request_id')
        
        if not request_id:
            await callback.answer("❌ Request ID not found", show_alert=True)
            return
        
        recovery_sys = get_recovery_system()
        admin_user_id = callback.from_user.id
        
        # Handle different recovery actions
        if action == "force_transition":
            # For force transition, we need to get available roles
            recovery_options = await recovery_sys.workflow_recovery_manager.get_recovery_options(request_id)
            force_option = next((opt for opt in recovery_options if opt['action'] == 'force_transition'), None)
            
            if not force_option or not force_option.get('available_roles'):
                await callback.answer("❌ No available roles for transition", show_alert=True)
                return
            
            # For simplicity, use the first available role
            target_role = force_option['available_roles'][0]
            recovery_data = {'target_role': target_role}
            
        elif action == "complete_workflow":
            recovery_data = {
                'rating': 3,  # Neutral rating
                'feedback': f'Workflow completed by admin recovery at {datetime.now().strftime("%Y-%m-%d %H:%M")}'
            }
            
        elif action == "reset_to_previous_state":
            recovery_data = {}
            
        elif action == "reassign_role":
            # For simplicity, we'll skip user selection and just log the action
            recovery_data = {'target_user_id': admin_user_id}
            
        else:
            await callback.answer("❌ Unknown recovery action", show_alert=True)
            return
        
        # Execute recovery
        await callback.answer("🔄 Executing recovery action...")
        
        success = await recovery_sys.workflow_recovery_manager.recover_workflow(
            request_id, action, admin_user_id, recovery_data
        )
        
        if success:
            await callback.message.edit_text(
                f"✅ <b>Recovery Successful</b>\n\n"
                f"📋 Request ID: <code>{request_id[:8]}...</code>\n"
                f"🔧 Action: {action.replace('_', ' ').title()}\n"
                f"👤 Performed by: Admin\n"
                f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                f"The workflow has been recovered successfully.",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Back to Menu", callback_data="back_to_recovery_menu")]
                ])
            )
        else:
            await callback.message.edit_text(
                f"❌ <b>Recovery Failed</b>\n\n"
                f"📋 Request ID: <code>{request_id[:8]}...</code>\n"
                f"🔧 Action: {action.replace('_', ' ').title()}\n\n"
                f"The recovery action could not be completed. Please check the logs for more details.",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Back to Menu", callback_data="back_to_recovery_menu")]
                ])
            )
        
        await state.clear()
        
    except Exception as e:
        logger.error(f"Error executing recovery action: {e}")
        await callback.answer("❌ Error executing recovery action", show_alert=True)


@router.callback_query(F.data == "system_health")
async def show_system_health(callback: CallbackQuery):
    """Display system health information"""
    try:
        await callback.answer("📊 Loading system health...")
        
        recovery_sys = get_recovery_system()
        health = recovery_sys.get_system_health()
        
        # Get additional health metrics
        error_stats = health.get('error_statistics', {})
        retry_stats = health.get('notification_retries', {})
        
        status_emoji = {
            'healthy': '✅',
            'degraded': '⚠️',
            'critical': '🔴'
        }.get(health.get('system_status', 'unknown'), '❓')
        
        text = f"{status_emoji} <b>System Health Status</b>\n\n"
        text += f"🔄 <b>Overall Status:</b> {health.get('system_status', 'Unknown').title()}\n\n"
        
        text += f"📊 <b>Active Requests:</b> {health.get('active_transactions', 0)}\n"
        text += f"🔔 <b>Pending Retries:</b> {retry_stats.get('pending_retries', 0)}\n"
        text += f"❌ <b>Recent Errors (24h):</b> {error_stats.get('recent_errors_24h', 0)}\n"
        text += f"📈 <b>Total Errors:</b> {error_stats.get('total_errors', 0)}\n\n"
        
        if error_stats.get('category_counts'):
            text += "<b>Error Categories:</b>\n"
            for category, count in error_stats['category_counts'].items():
                if count > 0:
                    text += f"  • {category.title()}: {count}\n"
            text += "\n"
        
        text += f"🕐 <b>Last Check:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Refresh", callback_data="system_health")],
            [InlineKeyboardButton(text="🔙 Back to Menu", callback_data="back_to_recovery_menu")]
        ])
        
        await callback.message.edit_text(text, parse_mode='HTML', reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Error showing system health: {e}")
        await callback.answer("❌ Error loading system health", show_alert=True)


@router.callback_query(F.data == "inventory_reconciliation")
async def run_inventory_reconciliation(callback: CallbackQuery):
    """Run inventory reconciliation process"""
    try:
        await callback.answer("🔄 Running inventory reconciliation...")
        
        recovery_sys = get_recovery_system()
        result = await recovery_sys.inventory_reconciliation_manager.run_full_reconciliation()
        
        duration = result.get('duration_seconds', 0)
        
        text = f"📦 <b>Inventory Reconciliation Complete</b>\n\n"
        text += f"⏱ <b>Duration:</b> {duration:.2f} seconds\n"
        text += f"🔍 <b>Discrepancies Found:</b> {result.get('total_discrepancies', 0)}\n"
        text += f"✅ <b>Fixed:</b> {result.get('fixed_count', 0)}\n"
        text += f"❌ <b>Failed:</b> {result.get('failed_count', 0)}\n\n"
        
        if result.get('discrepancies'):
            text += "<b>Discrepancy Details:</b>\n"
            for i, discrepancy in enumerate(result['discrepancies'][:5]):  # Show first 5
                text += f"{i+1}. {discrepancy.get('type', 'Unknown').replace('_', ' ').title()}\n"
                if 'material_name' in discrepancy:
                    text += f"   📦 {discrepancy['material_name']}\n"
                text += f"   📊 {discrepancy.get('description', 'No description')}\n"
            
            if len(result['discrepancies']) > 5:
                text += f"   ... and {len(result['discrepancies']) - 5} more\n"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Run Again", callback_data="inventory_reconciliation")],
            [InlineKeyboardButton(text="🔙 Back to Menu", callback_data="back_to_recovery_menu")]
        ])
        
        await callback.message.edit_text(text, parse_mode='HTML', reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Error running inventory reconciliation: {e}")
        await callback.answer("❌ Error running inventory reconciliation", show_alert=True)


@router.callback_query(F.data == "error_statistics")
async def show_error_statistics(callback: CallbackQuery):
    """Display error statistics"""
    try:
        await callback.answer("📈 Loading error statistics...")
        
        recovery_sys = get_recovery_system()
        stats = recovery_sys.error_handler.get_error_statistics()
        
        text = f"📈 <b>Error Statistics</b>\n\n"
        text += f"📊 <b>Total Errors:</b> {stats.get('total_errors', 0)}\n"
        text += f"🕐 <b>Recent (24h):</b> {stats.get('recent_errors_24h', 0)}\n"
        text += f"✅ <b>Resolved:</b> {stats.get('resolved_errors', 0)}\n\n"
        
        if stats.get('category_counts'):
            text += "<b>By Category:</b>\n"
            for category, count in stats['category_counts'].items():
                if count > 0:
                    emoji = {
                        'transient': '🔄',
                        'data': '📝',
                        'business_logic': '⚖️',
                        'system': '🖥',
                        'inventory': '📦',
                        'notification': '🔔'
                    }.get(category, '❓')
                    text += f"  {emoji} {category.title()}: {count}\n"
            text += "\n"
        
        if stats.get('severity_counts'):
            text += "<b>By Severity:</b>\n"
            for severity, count in stats['severity_counts'].items():
                if count > 0:
                    emoji = {
                        'low': '🟢',
                        'medium': '🟡',
                        'high': '🟠',
                        'critical': '🔴'
                    }.get(severity, '⚪')
                    text += f"  {emoji} {severity.title()}: {count}\n"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Refresh", callback_data="error_statistics")],
            [InlineKeyboardButton(text="🔙 Back to Menu", callback_data="back_to_recovery_menu")]
        ])
        
        await callback.message.edit_text(text, parse_mode='HTML', reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Error showing error statistics: {e}")
        await callback.answer("❌ Error loading error statistics", show_alert=True)


@router.callback_query(F.data == "notification_retries")
async def show_notification_retries(callback: CallbackQuery):
    """Display notification retry information"""
    try:
        await callback.answer("🔔 Loading notification retries...")
        
        recovery_sys = get_recovery_system()
        retry_stats = recovery_sys.notification_retry_manager.get_retry_stats()
        
        text = f"🔔 <b>Notification Retry Queue</b>\n\n"
        text += f"📊 <b>Pending Retries:</b> {retry_stats.get('pending_retries', 0)}\n\n"
        
        if retry_stats.get('retry_items'):
            text += "<b>Retry Items:</b>\n"
            for i, item in enumerate(retry_stats['retry_items'][:10]):  # Show first 10
                next_retry = item.get('next_retry_at')
                if isinstance(next_retry, datetime):
                    next_retry_str = next_retry.strftime('%H:%M:%S')
                else:
                    next_retry_str = str(next_retry)
                
                text += (
                    f"{i+1}. Request: <code>{item.get('request_id', 'Unknown')[:8]}...</code>\n"
                    f"   🔄 Retry #{item.get('retry_count', 0)}\n"
                    f"   ⏰ Next: {next_retry_str}\n"
                    f"   ❌ Error: {item.get('error', 'Unknown')[:50]}...\n\n"
                )
            
            if len(retry_stats['retry_items']) > 10:
                text += f"... and {len(retry_stats['retry_items']) - 10} more items\n"
        else:
            text += "✅ No pending retries"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Refresh", callback_data="notification_retries")],
            [InlineKeyboardButton(text="🔙 Back to Menu", callback_data="back_to_recovery_menu")]
        ])
        
        await callback.message.edit_text(text, parse_mode='HTML', reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Error showing notification retries: {e}")
        await callback.answer("❌ Error loading notification retries", show_alert=True)


@router.callback_query(F.data == "back_to_recovery_menu")
async def back_to_recovery_menu(callback: CallbackQuery, state: FSMContext):
    """Return to main recovery menu"""
    await state.clear()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Detect Stuck Workflows", callback_data="detect_stuck_workflows")],
        [InlineKeyboardButton(text="📊 System Health", callback_data="system_health")],
        [InlineKeyboardButton(text="🔄 Inventory Reconciliation", callback_data="inventory_reconciliation")],
        [InlineKeyboardButton(text="📈 Error Statistics", callback_data="error_statistics")],
        [InlineKeyboardButton(text="🔔 Notification Retries", callback_data="notification_retries")],
        [InlineKeyboardButton(text="❌ Close", callback_data="close_menu")]
    ])
    
    await callback.message.edit_text(
        "🛠 <b>Workflow Recovery & System Management</b>\n\n"
        "Select an option to manage system recovery and monitoring:",
        reply_markup=keyboard,
        parse_mode='HTML'
    )


@router.callback_query(F.data == "close_menu")
async def close_menu(callback: CallbackQuery, state: FSMContext):
    """Close the recovery menu"""
    await state.clear()
    await callback.message.delete()
    await callback.answer("Menu closed")


# Export router for registration
__all__ = ['router']