from aiogram.fsm.state import State, StatesGroup

class WarehouseStates(StatesGroup):
    # Main menu
    main_menu = State()
    
    # Inventory management
    inventory_menu = State()
    viewing_inventory = State()
    searching_inventory = State()
    
    # Adding items
    adding_item_name = State()
    adding_item_quantity = State()
    adding_item_price = State()
    adding_item_description = State()
    adding_item_category = State()
    
    # Updating items
    selecting_item_to_update = State()
    updating_item_quantity = State()
    updating_item_price = State()
    updating_item_info = State()
    updating_item_description = State()
    updating_item_name = State()
    
    # Orders management
    orders_menu = State()
    viewing_orders = State()
    processing_order = State()
    updating_order_status = State()
    
    # Statistics and reports
    viewing_statistics = State()
    generating_reports = State()
    
    # Low stock management
    checking_low_stock = State()
    restocking_items = State()
    
    # Export functionality
    selecting_export_format = State()
    exporting_data = State()
    
    # Receiving shipments
    receiving_shipment = State()
    verifying_shipment = State()
    updating_inventory_from_shipment = State()
    
    # Quality control
    quality_check = State()
    damaged_items_report = State()
    
    # Supplier management
    managing_suppliers = State()
    adding_supplier = State()
    
    # Language selection
    selecting_language = State()
    statistics_menu = State()
    export_menu = State()
    statistics_period_menu  = State()
