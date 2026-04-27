"""Модели пользователей."""

from datetime import datetime
from enum import Enum
from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db


class UserRole(Enum):
    """Роли пользователей."""
    ADMIN = 'admin'       # Полный доступ ко всем функциям
    MANAGER = 'manager'   # Управление книгами, остатками, продажами, отчётами
    CASHIER = 'cashier'   # Продажи, возвраты, просмотр каталога
    CLIENT = 'client'     # Покупатель (только просмотр, редактирование своего профиля)


class User(db.Model):
    """Модель пользователя."""

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.Enum(UserRole), default=UserRole.CLIENT, nullable=False, index=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def set_password(self, password):
        """Устанавливает хэш пароля."""
        # На части систем Python 3.9 может не быть hashlib.scrypt, поэтому используем
        # совместимый метод PBKDF2.
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        """Проверяет пароль."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'
