import pytest


@pytest.mark.security
@pytest.mark.admin
@pytest.mark.skip(reason="Security-тесты роли Администратор отложены — вернёмся к ним позже.")
def test_security_admin_placeholder():
    pass
