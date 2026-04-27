"""Роуты для управления клиентами."""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.models import Client
from app.schemas import ClientSchema
from app.services import ClientService
from app.decorators import role_required, UserRole, cashier_or_higher_required, manager_or_admin_required

client_bp = Blueprint('clients', __name__, url_prefix='/api/clients')


@client_bp.route('', methods=['GET'])
@jwt_required()
@cashier_or_higher_required
def get_all_clients():
    """
    Список всех клиентов (кассир, менеджер, администратор)

    ---
    tags:
      - Clients
    summary: Список клиентов
    description: Возвращает список всех клиентов
    security:
      - BearerAuth: 0
    responses:
      200:
        description: Список клиентов
        content:
          application/json:
            schema:
              type: object
              properties:
                clients:
                  type: array
                  items:
                    $ref: '#/components/schemas/Client'
      403:
        description: Недостаточно прав
    """
    clients = ClientService.get_all_clients()
    return jsonify({
        'clients': ClientSchema(many=True).dump(clients)
    }), 200


@client_bp.route('/<int:client_id>', methods=['GET'])
@jwt_required()
@cashier_or_higher_required
def get_client(client_id: int):
    """
    Получение клиента по ID (кассир, менеджер, администратор)

    ---
    tags:
      - Clients
    summary: Данные клиента
    description: Возвращает информацию о клиенте по его ID
    security:
      - BearerAuth: 0
    parameters:
      - in: path
        name: client_id
        required: true
        schema:
          type: integer
        description: ID клиента
    responses:
      200:
        description: Данные клиента
        content:
          application/json:
            schema:
              type: object
              properties:
                client:
                  $ref: '#/components/schemas/Client'
      404:
        description: Клиент не найден
      403:
        description: Недостаточно прав
    """
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
    """
    Создание клиента (кассир, менеджер, администратор)

    ---
    tags:
      - Clients
    summary: Создать клиента
    description: Создаёт нового клиента
    security:
      - BearerAuth: 0
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required:
              - first_name
              - last_name
            properties:
              first_name:
                type: string
                example: "Алексей"
              last_name:
                type: string
                example: "Смирнов"
              middle_name:
                type: string
                example: "Иванович"
              phone:
                type: string
                example: "+7 (999) 123-45-67"
              email:
                type: string
                format: email
                example: "client@example.com"
              user_id:
                type: integer
                example: 1
                description: ID связанного пользователя (опционально)
    responses:
      201:
        description: Клиент успешно создан
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: Клиент успешно создан
                client:
                  $ref: '#/components/schemas/Client'
      400:
        description: Ошибка валидации данных
      403:
        description: Недостаточно прав
    """
    data = request.get_json()

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
    """
    Обновление клиента (менеджер, администратор)

    ---
    tags:
      - Clients
    summary: Обновить клиента
    description: Обновляет данные клиента
    security:
      - BearerAuth: 0
    parameters:
      - in: path
        name: client_id
        required: true
        schema:
          type: integer
        description: ID клиента
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              first_name:
                type: string
              last_name:
                type: string
              middle_name:
                type: string
              phone:
                type: string
              email:
                type: string
                format: email
    responses:
      200:
        description: Клиент успешно обновлён
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: Данные клиента обновлены
                client:
                  $ref: '#/components/schemas/Client'
      404:
        description: Клиент не найден
      403:
        description: Недостаточно прав
    """
    data = request.get_json()

    client, error = ClientService.update_client(
        client_id=client_id,
        first_name=data.get('first_name'),
        last_name=data.get('last_name'),
        middle_name=data.get('middle_name'),
        phone=data.get('phone'),
        email=data.get('email')
    )

    if error:
        return jsonify(error), 404

    return jsonify({
        'message': 'Данные клиента обновлены',
        'client': ClientSchema().dump(client)
    }), 200


@client_bp.route('/<int:client_id>', methods=['DELETE'])
@jwt_required()
@manager_or_admin_required
def delete_client(client_id: int):
    """
    Удаление клиента (менеджер, администратор)

    ---
    tags:
      - Clients
    summary: Удалить клиента
    description: Удаляет клиента
    security:
      - BearerAuth: 0
    parameters:
      - in: path
        name: client_id
        required: true
        schema:
          type: integer
        description: ID клиента
    responses:
      200:
        description: Клиент успешно удалён
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: Клиент успешно удалён
      404:
        description: Клиент не найден
      403:
        description: Недостаточно прав
    """
    success, error = ClientService.delete_client(client_id)

    if error:
        return jsonify(error), 404

    return jsonify({
        'message': 'Клиент успешно удалён'
    }), 200


@client_bp.route('/me', methods=['GET'])
@jwt_required()
def get_my_client_profile():
    """
    Мой профиль клиента (все авторизованные)

    ---
    tags:
      - Clients
    summary: Мой профиль клиента
    description: Возвращает профиль клиента, связанный с текущим пользователем
    security:
      - BearerAuth: 0
    responses:
      200:
        description: Данные профиля клиента
        content:
          application/json:
            schema:
              type: object
              properties:
                client:
                  $ref: '#/components/schemas/Client'
      404:
        description: Профиль клиента не найден
    """
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
    """
    Обновление моего профиля (все авторизованные)

    ---
    tags:
      - Clients
    summary: Обновить мой профиль
    description: Обновляет профиль клиента, связанный с текущим пользователем (только свои данные)
    security:
      - BearerAuth: 0
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              first_name:
                type: string
              last_name:
                type: string
              middle_name:
                type: string
              phone:
                type: string
              email:
                type: string
                format: email
    responses:
      200:
        description: Профиль успешно обновлён
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: Профиль обновлён
                client:
                  $ref: '#/components/schemas/Client'
      404:
        description: Профиль клиента не найден
    """
    current_user_id = get_jwt_identity()

    client = ClientService.get_client_by_user_id(current_user_id)
    if not client:
        return jsonify({'message': 'Профиль клиента не найден'}), 404

    data = request.get_json()

    client, error = ClientService.update_client(
        client_id=client.id,
        first_name=data.get('first_name'),
        last_name=data.get('last_name'),
        middle_name=data.get('middle_name'),
        phone=data.get('phone'),
        email=data.get('email')
    )

    if error:
        return jsonify(error), 404

    return jsonify({
        'message': 'Профиль обновлён',
        'client': ClientSchema().dump(client)
    }), 200
