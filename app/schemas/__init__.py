"""Схемы приложения."""

from app.schemas.auth_schema import (
    UserSchema,
    RegisterSchema,
    LoginSchema,
    TokenSchema,
    TokenRefreshSchema,
    MessageSchema
)
from app.schemas.store_schema import (
    BookSchema,
    BookStockSchema,
    SaleItemSchema,
    SaleSchema,
    OrderItemSchema,
    OrderSchema,
    ManagerQuestionSchema,
    ClientSchema
)

__all__ = [
    'UserSchema',
    'RegisterSchema',
    'LoginSchema',
    'TokenSchema',
    'TokenRefreshSchema',
    'MessageSchema',
    'BookSchema',
    'BookStockSchema',
    'SaleItemSchema',
    'SaleSchema',
    'OrderItemSchema',
    'OrderSchema',
    'ManagerQuestionSchema',
    'ClientSchema'
]
