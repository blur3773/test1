"""Схемы для авторизации."""

from marshmallow import Schema, fields, validate


class UserSchema(Schema):
    """Схема пользователя."""

    id = fields.Int(dump_only=True)
    email = fields.Email(required=True)
    username = fields.Str(required=True, validate=validate.Length(min=3, max=80))
    role = fields.Method('get_role', dump_only=True)
    is_active = fields.Bool(dump_only=True)
    is_verified = fields.Bool(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    def get_role(self, obj):
        """Сериализует Enum роли в строковое значение."""
        role = getattr(obj, 'role', None)
        return role.value if hasattr(role, 'value') else role


class RegisterSchema(Schema):
    """Схема регистрации."""

    email = fields.Email(required=True)
    username = fields.Str(required=True, validate=validate.Length(min=3, max=80))
    password = fields.Str(required=True, validate=validate.Length(min=8))
    role = fields.Str(load_default='client', validate=validate.OneOf(['admin', 'manager', 'cashier', 'client']))


class LoginSchema(Schema):
    """Схема входа."""

    email = fields.Email(required=True)
    password = fields.Str(required=True)


class TokenSchema(Schema):
    """Схема токенов."""

    access_token = fields.Str(required=True)
    refresh_token = fields.Str(required=True)


class TokenRefreshSchema(Schema):
    """Схема обновления токена."""

    refresh_token = fields.Str(required=True)


class MessageSchema(Schema):
    """Схема сообщения."""

    message = fields.Str(required=True)
