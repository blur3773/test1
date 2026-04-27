import os
from datetime import timedelta


class Config:
    """Базовая конфигурация приложения."""

    # Flask
    ENV = os.environ.get('FLASK_ENV', 'development')
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 5001))

    # База данных
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///flask_auth.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    # Безопасность паролей
    PASSWORD_MIN_LENGTH = 8


class DevelopmentConfig(Config):
    """Конфигурация для разработки."""
    ENV = 'development'
    DEBUG = True


class ProductionConfig(Config):
    """Конфигурация для продакшена."""
    ENV = 'production'
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
