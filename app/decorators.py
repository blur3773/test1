"""Декораторы для проверки прав доступа."""

from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt
from app.models.user import UserRole


def get_role_names(*roles: UserRole) -> str:
    """
    Получить строку с названиями ролей для Swagger.
    
    Args:
        *roles: Роли пользователя (UserRole.ADMIN, UserRole.MANAGER, etc.)
    
    Returns:
        Строка с названиями ролей на русском языке
    """
    role_names = {
        UserRole.ADMIN.value: 'администратор',
        UserRole.MANAGER.value: 'менеджер',
        UserRole.CASHIER.value: 'кассир',
        UserRole.CLIENT.value: 'клиент'
    }
    
    names = [role_names.get(role.value if isinstance(role, UserRole) else role, str(role)) for role in roles]
    
    if len(names) == 1:
        return names[0]
    elif len(names) == 2:
        return f'{names[0]} или {names[1]}'
    else:
        return ', '.join(names[:-1]) + f' или {names[-1]}'


def role_required(*roles: UserRole):
    """
    Декоратор для проверки роли пользователя.
    
    Args:
        *roles: Разрешённые роли (UserRole.ADMIN, UserRole.MANAGER, etc.)
    
    Example:
        @role_required(UserRole.ADMIN, UserRole.MANAGER)
        def admin_only_route():
            ...
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            # Проверяем наличие и валидность JWT токена
            verify_jwt_in_request()
            
            # Получаем claims из токена
            claims = get_jwt()
            user_role = claims.get('role')
            
            if not user_role:
                return jsonify({'message': 'Роль пользователя не определена'}), 403
            
            # Проверяем, есть ли роль в списке разрешённых
            if user_role not in [role.value for role in roles]:
                return jsonify({'message': 'Недостаточно прав для выполнения этой операции'}), 403
            
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def admin_required(fn):
    """Декоратор для доступа только администратору."""
    return role_required(UserRole.ADMIN)(fn)


def manager_or_admin_required(fn):
    """Декоратор для доступа менеджеру или администратору."""
    return role_required(UserRole.MANAGER, UserRole.ADMIN)(fn)


def cashier_or_higher_required(fn):
    """Декоратор для доступа кассиру, менеджеру или администратору."""
    return role_required(UserRole.CASHIER, UserRole.MANAGER, UserRole.ADMIN)(fn)
