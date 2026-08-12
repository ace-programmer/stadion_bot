from aiogram.fsm.state import State, StatesGroup


class DistrictSelect(StatesGroup):
    region = State()
    district = State()


class AddStadium(StatesGroup):
    name = State()
    region = State()
    district = State()
    address = State()
    location = State()
    phone = State()
    price = State()
    photos = State()
    confirm = State()


class SearchState(StatesGroup):
    waiting_query = State()


class FilterState(StatesGroup):
    region = State()
    price = State()


class ProfileState(StatesGroup):
    waiting_phone = State()
    waiting_location = State()


class EditStadium(StatesGroup):
    waiting_value = State()


class ManagePhotos(StatesGroup):
    waiting_photo = State()


class ManageTimes(StatesGroup):
    waiting_date = State()
