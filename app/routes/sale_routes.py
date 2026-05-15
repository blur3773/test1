

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

    sales = SaleService.get_all_sales()
    return jsonify({
        'sales': SaleSchema(many=True).dump(sales)
    }), 200


@sale_bp.route('/<int:sale_id>', methods=['GET'])
@jwt_required()
@cashier_or_higher_required
def get_sale(sale_id: int):

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

    sale, error = SaleService.cancel_sale(sale_id)

    if error:
        return jsonify(error), 404

    return jsonify({
        'message': 'Продажа успешно отменена',
        'sale': SaleSchema().dump(sale)
    }), 200
