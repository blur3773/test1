

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.schemas import ClientSchema
from app.services import ClientService
from app.decorators import role_required, UserRole, cashier_or_higher_required, manager_or_admin_required

client_bp = Blueprint('clients', __name__, url_prefix='/api/clients')


@client_bp.route('', methods=['GET'])
@jwt_required()
@cashier_or_higher_required
def get_all_clients():

    clients = ClientService.get_all_clients()
    return jsonify({
        'clients': ClientSchema(many=True).dump(clients)
    }), 200


@client_bp.route('/<int:client_id>', methods=['GET'])
@jwt_required()
@cashier_or_higher_required
def get_client(client_id: int):

    client = ClientService.get_client_by_id(client_id)
    if not client:
        return jsonify({'message': 'Клиент не найден'}), 404

    return jsonify({
        'client': ClientSchema().dump(client)
    }), 200


@client_bp.route('', methods=['POST'])
@jwt_required()
@cashier_or_higher_required
def create_client():

    data = request.get_json() or {}

    required_fields = ['first_name', 'last_name']
    for field in required_fields:
        if field not in data:
            return jsonify({'message': f'Поле {field} обязательно'}), 400

    client, error = ClientService.create_client(
        first_name=data['first_name'],
        last_name=data['last_name'],
        middle_name=data.get('middle_name'),
        phone=data.get('phone'),
        email=data.get('email'),
        user_id=data.get('user_id')
    )

    if error:
        return jsonify(error), 400

    return jsonify({
        'message': 'Клиент успешно создан',
        'client': ClientSchema().dump(client)
    }), 201


@client_bp.route('/<int:client_id>', methods=['PUT'])
@jwt_required()
@manager_or_admin_required
def update_client(client_id: int):

    data = request.get_json() or {}

    client, error = ClientService.update_client(
        client_id=client_id,
        first_name=data.get('first_name'),
        last_name=data.get('last_name'),
        middle_name=data.get('middle_name'),
        phone=data.get('phone'),
        email=data.get('email')
    )

    if error:
        status_code = 404 if error.get('message') == 'Клиент не найден' else 400
        return jsonify(error), status_code

    return jsonify({
        'message': 'Данные клиента обновлены',
        'client': ClientSchema().dump(client)
    }), 200


@client_bp.route('/<int:client_id>', methods=['DELETE'])
@jwt_required()
@manager_or_admin_required
def delete_client(client_id: int):

    success, error = ClientService.delete_client(client_id)

    if error:
        return jsonify(error), 404

    return jsonify({
        'message': 'Клиент успешно удалён'
    }), 200


@client_bp.route('/me', methods=['GET'])
@jwt_required()
def get_my_client_profile():

    current_user_id = get_jwt_identity()

    client = ClientService.get_client_by_user_id(current_user_id)
    if not client:
        return jsonify({'message': 'Профиль клиента не найден'}), 404

    return jsonify({
        'client': ClientSchema().dump(client)
    }), 200


@client_bp.route('/me', methods=['PUT'])
@jwt_required()
def update_my_client_profile():

    current_user_id = get_jwt_identity()

    data = request.get_json() or {}
    client = ClientService.get_client_by_user_id(current_user_id)
    if not client:
        client, error = ClientService.create_client(
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            middle_name=data.get('middle_name'),
            phone=data.get('phone'),
            email=data.get('email'),
            user_id=current_user_id
        )

        if error:
            return jsonify(error), 400

        return jsonify({
            'message': 'Профиль клиента создан',
            'client': ClientSchema().dump(client)
        }), 201

    client, error = ClientService.update_client(
        client_id=client.id,
        first_name=data.get('first_name'),
        last_name=data.get('last_name'),
        middle_name=data.get('middle_name'),
        phone=data.get('phone'),
        email=data.get('email')
    )

    if error:
        status_code = 404 if error.get('message') == 'Клиент не найден' else 400
        return jsonify(error), status_code

    return jsonify({
        'message': 'Профиль обновлён',
        'client': ClientSchema().dump(client)
    }), 200
