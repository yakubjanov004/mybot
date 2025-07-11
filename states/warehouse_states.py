from aiogram.fsm.state import State, StatesGroup

class WarehouseMainMenuStates(StatesGroup):
    main_menu = State()

class WarehouseInventoryStates(StatesGroup):
    inventory_menu = State()
    viewing_inventory = State()
    searching_inventory = State()
    adding_item_name = State()
    adding_item_quantity = State()
    adding_item_price = State()
    adding_item_description = State()
    adding_item_category = State()
    selecting_item_to_update = State()
    updating_item_quantity = State()
    updating_item_price = State()
    updating_item_info = State()
    updating_item_description = State()
    updating_item_name = State()
    checking_low_stock = State()
    restocking_items = State()
    receiving_shipment = State()
    verifying_shipment = State()
    updating_inventory_from_shipment = State()
    managing_suppliers = State()
    adding_supplier = State()

class WarehouseOrdersStates(StatesGroup):
    orders_menu = State()
    viewing_orders = State()
    processing_order = State()
    updating_order_status = State()

class WarehouseStatisticsStates(StatesGroup):
    viewing_statistics = State()
    generating_reports = State()
    statistics_menu = State()
    statistics_period_menu = State()

class WarehouseExportStates(StatesGroup):
    selecting_export_format = State()
    exporting_data = State()
    export_menu = State()

class WarehouseQualityStates(StatesGroup):
    quality_check = State()
    damaged_items_report = State()

class WarehouseSettingsStates(StatesGroup):
    selecting_language = State()
