

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import os
from app.models.user import User, UserRole
from app.schemas import UserSchema
from app.services import AuthService
from app.decorators import admin_required
from app.utils import log_admin_action

user_bp = Blueprint('users', __name__, url_prefix='/api/users')


@user_bp.route('', methods=['GET'])
@jwt_required()
@admin_required
def get_all_users():

    users = AuthService.get_all_users()
    log_admin_action("users_list", f"count={len(users)}")
    return jsonify({
        'users': UserSchema(many=True).dump(users)
    }), 200


@user_bp.route('/<int:user_id>', methods=['GET'])
@jwt_required()
@admin_required
def get_user(user_id: int):

    user = AuthService.get_user_by_id(user_id)
    if not user:
        return jsonify({'message': 'Пользователь не найден'}), 404

    log_admin_action("user_view", f"user_id={user_id}")
    return jsonify({
        'user': UserSchema().dump(user)
    }), 200


@user_bp.route('/<int:user_id>/role', methods=['PUT'])
@jwt_required()
@admin_required
def update_user_role(user_id: int):

    data = request.get_json()
    role_str = data.get('role')

    if not role_str or role_str not in ['admin', 'manager', 'cashier', 'client']:
        return jsonify({'message': 'Некорректная роль'}), 400

    role = UserRole(role_str)
    user, error = AuthService.set_user_role(user_id, role)

    if error:
        return jsonify(error), 404

    log_admin_action("user_role_update", f"user_id={user_id}, role={role.value}")
    return jsonify({
        'message': 'Роль пользователя обновлена',
        'user': UserSchema().dump(user)
    }), 200


@user_bp.route('/<int:user_id>/deactivate', methods=['POST'])
@jwt_required()
@admin_required
def deactivate_user(user_id: int):

    user, error = AuthService.deactivate_user(user_id)

    if error:
        return jsonify(error), 404

    log_admin_action("user_deactivate", f"user_id={user_id}")
    return jsonify({
        'message': 'Пользователь деактивирован',
        'user': UserSchema().dump(user)
    }), 200


@user_bp.route('/<int:user_id>/activate', methods=['POST'])
@jwt_required()
@admin_required
def activate_user(user_id: int):

    user, error = AuthService.activate_user(user_id)

    if error:
        return jsonify(error), 404

    log_admin_action("user_activate", f"user_id={user_id}")
    return jsonify({
        'message': 'Пользователь активирован',
        'user': UserSchema().dump(user)
    }), 200


@user_bp.route('/<int:user_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_user(user_id: int):
    current_user_id = get_jwt_identity()
    if current_user_id == user_id:
        return jsonify({'message': 'Администратор не может удалить свой аккаунт'}), 400

    success, error = AuthService.delete_user(user_id)

    if error:
        return jsonify(error), 404

    log_admin_action("user_delete", f"user_id={user_id}")
    return jsonify({
        'message': 'Пользователь удалён'
    }), 200


@user_bp.route('/admin-logs', methods=['GET'])
@jwt_required()
@admin_required
def get_admin_logs():

    limit = request.args.get('limit', 200, type=int)
    limit = max(1, min(limit, 1000))
    log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs', 'admin_audit.log')

    if not os.path.exists(log_path):
        return jsonify({'logs': []}), 200

    with open(log_path, 'r', encoding='utf-8') as log_file:
        lines = log_file.readlines()

    log_admin_action("admin_logs_view", f"limit={limit}")
    return jsonify({'logs': [line.rstrip('\n') for line in lines[-limit:]]}), 200


@user_bp.route('/activity-logs', methods=['GET'])
@jwt_required()
@admin_required
def get_activity_logs():

    limit = request.args.get('limit', 300, type=int)
    limit = max(1, min(limit, 2000))
    log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs', 'user_activity.log')

    if not os.path.exists(log_path):
        return jsonify({'logs': []}), 200

    with open(log_path, 'r', encoding='utf-8') as log_file:
        lines = log_file.readlines()

    log_admin_action("activity_logs_view", f"limit={limit}")
    return jsonify({'logs': [line.rstrip('\n') for line in lines[-limit:]]}), 200
