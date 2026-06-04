from app.models import UserRole
from app.services.auth_service import AuthService


UNIT_PASSWORD = "unit-test-password"


def test_register_hashes_password_and_login_returns_tokens(app):
    user, error = AuthService.register(
        email="unit-client@local.test",
        username="client",
        password=UNIT_PASSWORD,
    )

    assert error is None
    assert user.id is not None
    assert user.role == UserRole.CLIENT
    assert user.password_hash != UNIT_PASSWORD
    assert user.check_password(UNIT_PASSWORD)

    tokens, login_error = AuthService.login("unit-client@local.test", UNIT_PASSWORD)

    assert login_error is None
    assert tokens["access_token"]
    assert tokens["refresh_token"]


def test_register_rejects_duplicate_email_and_username(app):
    user, error = AuthService.register(
        email="duplicate@local.test",
        username="duplicate",
        password=UNIT_PASSWORD,
    )
    assert error is None
    assert user is not None

    duplicate_email_user, duplicate_email_error = AuthService.register(
        email="duplicate@local.test",
        username="another_name",
        password=UNIT_PASSWORD,
    )
    assert duplicate_email_user is None
    assert duplicate_email_error["message"] == "Email уже зарегистрирован"

    duplicate_username_user, duplicate_username_error = AuthService.register(
        email="another@local.test",
        username="duplicate",
        password=UNIT_PASSWORD,
    )
    assert duplicate_username_user is None
    assert duplicate_username_error["message"] == "Имя пользователя уже занято"


def test_deactivated_user_cannot_login(app):
    user, error = AuthService.register(
        email="inactive@local.test",
        username="inactive",
        password=UNIT_PASSWORD,
    )
    assert error is None

    deactivated, deactivate_error = AuthService.deactivate_user(user.id)
    assert deactivate_error is None
    assert deactivated.is_active is False

    tokens, login_error = AuthService.login("inactive@local.test", UNIT_PASSWORD)

    assert tokens is None
    assert login_error["message"] == "Аккаунт деактивирован"


def test_admin_can_change_user_role(app):
    user, error = AuthService.register(
        email="role@local.test",
        username="role_user",
        password=UNIT_PASSWORD,
    )
    assert error is None

    updated_user, role_error = AuthService.set_user_role(user.id, UserRole.MANAGER)

    assert role_error is None
    assert updated_user.role == UserRole.MANAGER
