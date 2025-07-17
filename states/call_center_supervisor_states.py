from aiogram.fsm.state import StatesGroup, State

class CallCenterSupervisorInboxStates(StatesGroup):
    inbox = State()

class CallCenterSupervisorOrdersStates(StatesGroup):
    orders = State()

class CallCenterSupervisorStatisticsStates(StatesGroup):
    statistics = State()

class CallCenterSupervisorFeedbackStates(StatesGroup):
    feedback = State()

class CallCenterSupervisorLanguageStates(StatesGroup):
    language = State()
