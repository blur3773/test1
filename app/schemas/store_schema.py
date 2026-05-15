

from marshmallow import Schema, fields, validate


class BookSchema(Schema):


    id = fields.Int(dump_only=True)
    title = fields.Str(required=True, validate=validate.Length(max=200))
    title_ru = fields.Str(load_default=None, allow_none=True, validate=validate.Length(max=200))
    author = fields.Str(required=True, validate=validate.Length(max=100))
    isbn = fields.Str(required=True, validate=validate.Length(max=20))
    publisher = fields.Str(load_default=None, validate=validate.Length(max=100))
    year = fields.Int(load_default=None)
    publication_place = fields.Str(load_default=None, allow_none=True, validate=validate.Length(max=120))
    page_count = fields.Int(load_default=None, allow_none=True)
    weight_grams = fields.Int(load_default=None, allow_none=True)
    print_run = fields.Int(load_default=None, allow_none=True)
    genre = fields.Str(load_default=None, allow_none=True, validate=validate.Length(max=255))
    price = fields.Decimal(required=True, places=2)
    description = fields.Str(load_default=None)
    cover_url = fields.Str(dump_only=True, allow_none=True)
    source_url = fields.Str(load_default=None, allow_none=True, validate=validate.Length(max=500))
    status = fields.Method('get_status', dump_only=True)
    stock_quantity = fields.Int(dump_only=True)
    available_quantity = fields.Int(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    def get_status(self, obj):

        status = getattr(obj, 'status', None)
        return status.value if hasattr(status, 'value') else status


class BookStockSchema(Schema):


    id = fields.Int(dump_only=True)
    book_id = fields.Int(required=True)
    quantity = fields.Int(required=True)
    reserved = fields.Int(load_default=0)
    available = fields.Int(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class SaleItemSchema(Schema):


    id = fields.Int(dump_only=True)
    book_id = fields.Int(required=True)
    book_title = fields.Str(dump_only=True)
    quantity = fields.Int(required=True)
    price = fields.Decimal(required=True, places=2)
    subtotal = fields.Decimal(dump_only=True)


class SaleSchema(Schema):


    id = fields.Int(dump_only=True)
    cashier_id = fields.Int(required=True)
    cashier_name = fields.Str(dump_only=True)
    client_id = fields.Int(load_default=None, allow_none=True)
    client_name = fields.Str(dump_only=True, allow_none=True)
    total_amount = fields.Decimal(dump_only=True)
    status = fields.Method('get_status', dump_only=True)
    items = fields.Nested(SaleItemSchema, many=True, load_default=[])
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    def get_status(self, obj):

        status = getattr(obj, 'status', None)
        return status.value if hasattr(status, 'value') else status


class OrderItemSchema(Schema):


    id = fields.Int(dump_only=True)
    book_id = fields.Int(required=True)
    book_title = fields.Str(dump_only=True)
    quantity = fields.Int(required=True)
    price = fields.Decimal(dump_only=True, places=2)
    subtotal = fields.Decimal(dump_only=True, places=2)


class OrderSchema(Schema):


    id = fields.Int(dump_only=True)
    user_id = fields.Int(dump_only=True)
    user_name = fields.Method('get_user_name', dump_only=True)
    client_id = fields.Int(dump_only=True, allow_none=True)
    manager_id = fields.Int(dump_only=True, allow_none=True)
    manager_name = fields.Method('get_manager_name', dump_only=True, allow_none=True)
    sale_id = fields.Int(dump_only=True, allow_none=True)
    total_amount = fields.Decimal(dump_only=True, places=2)
    status = fields.Method('get_status', dump_only=True)
    customer_comment = fields.Str(load_default=None, allow_none=True)
    manager_comment = fields.Str(dump_only=True, allow_none=True)
    items = fields.Nested(OrderItemSchema, many=True, load_default=[])
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    def get_status(self, obj):

        status = getattr(obj, 'status', None)
        return status.value if hasattr(status, 'value') else status

    def get_user_name(self, obj):

        user = getattr(obj, 'user', None)
        return getattr(user, 'username', None)

    def get_manager_name(self, obj):

        manager = getattr(obj, 'manager', None)
        return getattr(manager, 'username', None)


class ManagerQuestionSchema(Schema):


    id = fields.Int(dump_only=True)
    user_id = fields.Int(dump_only=True, allow_none=True)
    user_name = fields.Method('get_user_name', dump_only=True, allow_none=True)
    manager_id = fields.Int(dump_only=True, allow_none=True)
    manager_name = fields.Method('get_manager_name', dump_only=True, allow_none=True)
    name = fields.Str(required=True, validate=validate.Length(max=120))
    email = fields.Email(load_default=None, allow_none=True)
    phone = fields.Str(load_default=None, allow_none=True, validate=validate.Length(max=20))
    topic = fields.Str(load_default=None, allow_none=True, validate=validate.Length(max=200))
    message = fields.Str(required=True, validate=validate.Length(max=1000))
    status = fields.Method('get_status', dump_only=True)
    manager_comment = fields.Str(load_default=None, allow_none=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    def get_status(self, obj):

        status = getattr(obj, 'status', None)
        return status.value if hasattr(status, 'value') else status

    def get_user_name(self, obj):

        user = getattr(obj, 'user', None)
        return getattr(user, 'username', None)

    def get_manager_name(self, obj):

        manager = getattr(obj, 'manager', None)
        return getattr(manager, 'username', None)


class ClientSchema(Schema):


    id = fields.Int(dump_only=True)
    user_id = fields.Int(load_default=None, allow_none=True)
    first_name = fields.Str(required=True, validate=validate.Length(max=50))
    last_name = fields.Str(required=True, validate=validate.Length(max=50))
    middle_name = fields.Str(load_default=None, allow_none=True, validate=validate.Length(max=50))
    phone = fields.Str(load_default=None, validate=validate.Length(max=20))
    email = fields.Email(load_default=None)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
