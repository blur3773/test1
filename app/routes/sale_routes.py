"""Роуты для управления продажами."""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import Sale, SaleStatus
from app.schemas import SaleSchema
from app.services import SaleService
from app.decorators import role_required, UserRole, cashier_or_higher_required, manager_or_admin_required

sale_bp = Blueprint('sales', __name__, url_prefix='/api/sales')


@sale_bp.route('', methods=['POST'])
@jwt_required()
@cashier_or_higher_required
def create_sale():
    """
    Оформление продажи (кассир, менеджер, администратор)

    ---
    tags:
      - Sales
    summary: Оформить продажу
    description: Создаёт новую продажу
    security:
      - BearerAuth: 0
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required:
              - items
            properties:
              items:
                type: array
                description: Список товаров
                items:
                  type: object
                  required:
                    - book_id
                    - quantity
                  properties:
                    book_id:
                      type: integer
                      example: 1
                    quantity:
                      type: integer
                      example: 2
              client_id:
                type: integer
                example: 1
                description: ID клиента (опционально)
    responses:
      201:
        description: Продажа успешно оформлена
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: Продажа успешно оформлена
                sale:
                  $ref: '#/components/schemas/Sale'
      400:
        description: Ошибка валидации данных
      403:
        description: Недостаточно прав
    """
    data = request.get_json()
    current_user_id = get_jwt_identity()

    items = data.get('items', [])
    if not items:
        return jsonify({'message': 'Список товаров пуст'}), 400

    client_id = data.get('client_id')

    sale, error = SaleService.create_sale(
        cashier_id=current_user_id,
        items=items,
        client_id=client_id
    )

    if error:
        return jsonify(error), 400

    return jsonify({
        'message': 'Продажа успешно оформлена',
        'sale': SaleSchema().dump(sale)
    }), 201


@sale_bp.route('', methods=['GET'])
@jwt_required()
@manager_or_admin_required
def get_all_sales():
    """
    Список всех продаж (менеджер, администратор)

    ---
    tags:
      - Sales
    summary: Список продаж
    description: Возвращает список всех продаж
    security:
      - BearerAuth: 0
    responses:
      200:
        description: Список продаж
        content:
          application/json:
            schema:
              type: object
              properties:
                sales:
                  type: array
                  items:
                    $ref: '#/components/schemas/Sale'
      403:
        description: Недостаточно прав
    """
    sales = SaleService.get_all_sales()
    return jsonify({
        'sales': SaleSchema(many=True).dump(sales)
    }), 200


@sale_bp.route('/<int:sale_id>', methods=['GET'])
@jwt_required()
@cashier_or_higher_required
def get_sale(sale_id: int):
    """
    Получение продажи по ID (кассир, менеджер, администратор)

    ---
    tags:
      - Sales
    summary: Данные продажи
    description: Возвращает информацию о продаже по её ID
    security:
      - BearerAuth: 0
    parameters:
      - in: path
        name: sale_id
        required: true
        schema:
          type: integer
        description: ID продажи
    responses:
      200:
        description: Данные продажи
        content:
          application/json:
            schema:
              type: object
              properties:
                sale:
                  $ref: '#/components/schemas/Sale'
      404:
        description: Продажа не найдена
    """
    sale = SaleService.get_sale_by_id(sale_id)
    if not sale:
        return jsonify({'message': 'Продажа не найдена'}), 404

    return jsonify({
        'sale': SaleSchema().dump(sale)
    }), 200


@sale_bp.route('/<int:sale_id>/return', methods=['POST'])
@jwt_required()
@cashier_or_higher_required
def return_sale(sale_id: int):
    """
    Возврат товара (кассир, менеджер, администратор)

    ---
    tags:
      - Sales
    summary: Оформить возврат
    description: Оформляет возврат продажи
    security:
      - BearerAuth: 0
    parameters:
      - in: path
        name: sale_id
        required: true
        schema:
          type: integer
        description: ID продажи
    responses:
      200:
        description: Возврат оформлен
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: Возврат успешно оформлен
                sale:
                  $ref: '#/components/schemas/Sale'
      404:
        description: Продажа не найдена
      403:
        description: Недостаточно прав
    """
    sale, error = SaleService.return_sale(sale_id)

    if error:
        return jsonify(error), 404

    return jsonify({
        'message': 'Возврат успешно оформлен',
        'sale': SaleSchema().dump(sale)
    }), 200


@sale_bp.route('/<int:sale_id>/cancel', methods=['POST'])
@jwt_required()
@manager_or_admin_required
def cancel_sale(sale_id: int):
    """
    Отмена продажи (менеджер, администратор)

    ---
    tags:
      - Sales
    summary: Отменить продажу
    description: Отменяет продажу
    security:
      - BearerAuth: 0
    parameters:
      - in: path
        name: sale_id
        required: true
        schema:
          type: integer
        description: ID продажи
    responses:
      200:
        description: Продажа отменена
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: Продажа успешно отменена
                sale:
                  $ref: '#/components/schemas/Sale'
      404:
        description: Продажа не найдена
      403:
        description: Недостаточно прав
    """
    sale, error = SaleService.cancel_sale(sale_id)

    if error:
        return jsonify(error), 404

    return jsonify({
        'message': 'Продажа успешно отменена',
        'sale': SaleSchema().dump(sale)
    }), 200
