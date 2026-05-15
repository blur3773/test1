

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.models.user import UserRole
from app.schemas import (
    LoginSchema,
    RegisterSchema,
    TokenRefreshSchema,
    UserSchema,
)
from app.services import AuthService

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/register', methods=['POST'])
def register():

    data = request.get_json() or {}

    errors = RegisterSchema().validate(data)
    if errors:
        return jsonify({'errors': errors}), 400

    role_str = data.get('role', 'client')
    try:
        role = UserRole(role_str)
    except ValueError:
        return jsonify({'message': 'Некорректная роль'}), 400

    user, error = AuthService.register(
        email=data['email'],
        username=data['username'],
        password=data['password'],
        role=role
    )
    if error:
        return jsonify(error), 400

    tokens, _ = AuthService.login(
        email=data['email'],
        password=data['password']
    )

    return jsonify({
        'message': 'Пользователь успешно зарегистрирован',
        'user': UserSchema().dump(user),
        **(tokens or {})
    }), 201


@auth_bp.route('/login', methods=['POST'])
def login():

    data = request.get_json() or {}

    errors = LoginSchema().validate(data)
    if errors:
        return jsonify({'errors': errors}), 400

    tokens, error = AuthService.login(
        email=data['email'],
        password=data['password']
    )

    if error:
        return jsonify(error), 401

    return jsonify({
        'message': 'Вход выполнен успешно',
        **tokens
    }), 200


@auth_bp.route('/refresh', methods=['POST'])
def refresh():

    data = request.get_json() or {}

    errors = TokenRefreshSchema().validate(data)
    if errors:
        return jsonify({'errors': errors}), 400

    tokens, error = AuthService.refresh_token(data['refresh_token'])
    if error:
        return jsonify(error), 401

    return jsonify({
        'message': 'Токены успешно обновлены',
        **tokens
    }), 200


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():

    current_user_id = get_jwt_identity()
    user, error = AuthService.get_current_user(current_user_id)

    if error:
        return jsonify(error), 404

    return jsonify({
        'user': UserSchema().dump(user)
    }), 200


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():

    return jsonify({
        'message': 'Выход выполнен успешно'
    }), 200
