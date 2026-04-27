"""Роуты для управления пользователями (только для администратора)."""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.user import User, UserRole
from app.schemas import UserSchema
from app.services import AuthService
from app.decorators import admin_required

user_bp = Blueprint('users', __name__, url_prefix='/api/users')


@user_bp.route('', methods=['GET'])
@jwt_required()
@admin_required
def get_all_users():
    """
    Список всех пользователей (администратор)

    ---
    tags:
      - Users
    summary: Список всех пользователей
    description: Возвращает список всех зарегистрированных пользователей
    security:
      - BearerAuth: 0
    responses:
      200:
        description: Список пользователей
        content:
          application/json:
            schema:
              type: object
              properties:
                users:
                  type: array
                  items:
                    $ref: '#/components/schemas/User'
      401:
        description: Токен не предоставлен или недействителен
      403:
        description: Недостаточно прав
    """
    users = AuthService.get_all_users()
    return jsonify({
        'users': UserSchema(many=True).dump(users)
    }), 200


@user_bp.route('/<int:user_id>', methods=['GET'])
@jwt_required()
@admin_required
def get_user(user_id: int):
    """
    Данные пользователя по ID (администратор)

    ---
    tags:
      - Users
    summary: Данные пользователя по ID
    description: Возвращает информацию о пользователе по его ID
    security:
      - BearerAuth: 0
    parameters:
      - in: path
        name: user_id
        required: true
        schema:
          type: integer
        description: ID пользователя
    responses:
      200:
        description: Данные пользователя
        content:
          application/json:
            schema:
              type: object
              properties:
                user:
                  $ref: '#/components/schemas/User'
      404:
        description: Пользователь не найден
      403:
        description: Недостаточно прав
    """
    user = AuthService.get_user_by_id(user_id)
    if not user:
        return jsonify({'message': 'Пользователь не найден'}), 404

    return jsonify({
        'user': UserSchema().dump(user)
    }), 200


@user_bp.route('/<int:user_id>/role', methods=['PUT'])
@jwt_required()
@admin_required
def update_user_role(user_id: int):
    """
    Изменение роли пользователя (администратор)

    ---
    tags:
      - Users
    summary: Изменить роль пользователя
    description: Изменяет роль пользователя
    security:
      - BearerAuth: 0
    parameters:
      - in: path
        name: user_id
        required: true
        schema:
          type: integer
        description: ID пользователя
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required:
              - role
            properties:
              role:
                type: string
                enum: [admin, manager, cashier, client]
                example: manager
    responses:
      200:
        description: Роль успешно обновлена
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: Роль пользователя обновлена
                user:
                  $ref: '#/components/schemas/User'
      404:
        description: Пользователь не найден
      403:
        description: Недостаточно прав
    """
    data = request.get_json()
    role_str = data.get('role')

    if not role_str or role_str not in ['admin', 'manager', 'cashier', 'client']:
        return jsonify({'message': 'Некорректная роль'}), 400

    role = UserRole(role_str)
    user, error = AuthService.set_user_role(user_id, role)

    if error:
        return jsonify(error), 404

    return jsonify({
        'message': 'Роль пользователя обновлена',
        'user': UserSchema().dump(user)
    }), 200


@user_bp.route('/<int:user_id>/deactivate', methods=['POST'])
@jwt_required()
@admin_required
def deactivate_user(user_id: int):
    """
    Деактивация пользователя (администратор)

    ---
    tags:
      - Users
    summary: Деактивировать пользователя
    description: Деактивирует аккаунт пользователя
    security:
      - BearerAuth: 0
    parameters:
      - in: path
        name: user_id
        required: true
        schema:
          type: integer
        description: ID пользователя
    responses:
      200:
        description: Пользователь деактивирован
      404:
        description: Пользователь не найден
      403:
        description: Недостаточно прав
    """
    user, error = AuthService.deactivate_user(user_id)

    if error:
        return jsonify(error), 404

    return jsonify({
        'message': 'Пользователь деактивирован',
        'user': UserSchema().dump(user)
    }), 200


@user_bp.route('/<int:user_id>/activate', methods=['POST'])
@jwt_required()
@admin_required
def activate_user(user_id: int):
    """
    Активация пользователя (администратор)

    ---
    tags:
      - Users
    summary: Активировать пользователя
    description: Активирует аккаунт пользователя
    security:
      - BearerAuth: 0
    parameters:
      - in: path
        name: user_id
        required: true
        schema:
          type: integer
        description: ID пользователя
    responses:
      200:
        description: Пользователь активирован
      404:
        description: Пользователь не найден
      403:
        description: Недостаточно прав
    """
    user, error = AuthService.activate_user(user_id)

    if error:
        return jsonify(error), 404

    return jsonify({
        'message': 'Пользователь активирован',
        'user': UserSchema().dump(user)
    }), 200


@user_bp.route('/<int:user_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_user(user_id: int):
    """
    Удаление пользователя (администратор)

    ---
    tags:
      - Users
    summary: Удалить пользователя
    description: Удаляет аккаунт пользователя
    security:
      - BearerAuth: 0
    parameters:
      - in: path
        name: user_id
        required: true
        schema:
          type: integer
        description: ID пользователя
    responses:
      200:
        description: Пользователь удалён
      404:
        description: Пользователь не найден
      403:
        description: Недостаточно прав
    """
    success, error = AuthService.delete_user(user_id)

    if error:
        return jsonify(error), 404

    return jsonify({
        'message': 'Пользователь удалён'
    }), 200
