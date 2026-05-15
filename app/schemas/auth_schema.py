

from marshmallow import Schema, fields, validate


class UserSchema(Schema):


    id = fields.Int(dump_only=True)
    email = fields.Email(required=True)
    username = fields.Str(required=True, validate=validate.Length(min=3, max=80))
    first_name = fields.Method('get_first_name', dump_only=True, allow_none=True)
    last_name = fields.Method('get_last_name', dump_only=True, allow_none=True)
    role = fields.Method('get_role', dump_only=True)
    is_active = fields.Bool(dump_only=True)
    is_verified = fields.Bool(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    def get_role(self, obj):

        role = getattr(obj, 'role', None)
        return role.value if hasattr(role, 'value') else role

    def _get_client_profile(self, obj):
        client_profile = getattr(obj, 'client_profile', None)
        if not client_profile:
            return None
        if isinstance(client_profile, list):
            return client_profile[0] if client_profile else None
        return client_profile

    def get_first_name(self, obj):

        client_profile = self._get_client_profile(obj)
        return getattr(client_profile, 'first_name', None)

    def get_last_name(self, obj):

        client_profile = self._get_client_profile(obj)
        return getattr(client_profile, 'last_name', None)


class RegisterSchema(Schema):


    email = fields.Email(required=True)
    username = fields.Str(required=True, validate=validate.Length(min=3, max=80))
    password = fields.Str(required=True, validate=validate.Length(min=8))
    role = fields.Str(load_default='client', validate=validate.OneOf(['admin', 'manager', 'cashier', 'client']))


class LoginSchema(Schema):


    email = fields.Email(required=True)
    password = fields.Str(required=True)


class TokenSchema(Schema):


    access_token = fields.Str(required=True)
    refresh_token = fields.Str(required=True)


class TokenRefreshSchema(Schema):


    refresh_token = fields.Str(required=True)


class MessageSchema(Schema):


    message = fields.Str(required=True)
