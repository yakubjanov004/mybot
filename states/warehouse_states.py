from aiogram.fsm.state import State, StatesGroup

class WarehouseStates(StatesGroup):
    main_menu = State()
    inventory_menu = State()
    orders_menu = State()
    
    # Inventory management states
    add_item_name = State()
    add_item_quantity = State()
    add_item_unit = State()
    add_item_min_quantity = State()
    
    update_item_quantity = State()
    update_item_min_quantity = State()
    
    # Order management states
    order_details = State()
    update_order_status = State()
    add_order_notes = State()
