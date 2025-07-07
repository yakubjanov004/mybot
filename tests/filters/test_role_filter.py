import pytest
from filters.role_filter import RoleFilter

class MockMessage:
    def __init__(self, user_id):
        class FromUser:
            def __init__(self, id):
                self.id = id
        self.from_user = FromUser(user_id)

@pytest.mark.asyncio
async def test_role_filter_match(mocker):
    mocker.patch("utils.get_role.get_user_role", return_value="admin")
    filter = RoleFilter("admin")
    message = MockMessage(user_id=123)
    assert await filter(message) is True

@pytest.mark.asyncio
async def test_role_filter_no_match(mocker):
    mocker.patch("utils.get_role.get_user_role", return_value="client")
    filter = RoleFilter("admin")
    message = MockMessage(user_id=123)
    assert await filter(message) is False 