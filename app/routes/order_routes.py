

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

from app.schemas import OrderSchema, SaleSchema
from app.services import OrderService
from app.decorators import role_required, UserRole, cashier_or_higher_required
from app.models import OrderStatus


order_bp = Blueprint('orders', __name__, url_prefix='/api/orders')


def _resolve_error_status(error: dict) -> int:

    message = str(error.get('message', '')).lower()
    if 'не найден' in message:
        return 404
    if 'недостаточно прав' in message:
        return 403
    return 400


@order_bp.route('/checkout', methods=['POST'])
@jwt_required()
@role_required(UserRole.CLIENT)
def checkout_order():

    data = request.get_json() or {}
    items = data.get('items', [])

    if not items:
        return jsonify({'message': 'Список товаров пуст'}), 400

    order, error = OrderService.create_order(
        user_id=get_jwt_identity(),
        items=items,
        customer_comment=data.get('customer_comment')
    )

    if error:
        return jsonify(error), _resolve_error_status(error)

    return jsonify({
        'message': 'Заказ передан менеджеру',
        'order': OrderSchema().dump(order)
    }), 201


@order_bp.route('/my', methods=['GET'])
@jwt_required()
def get_my_orders():

    orders = OrderService.get_orders_by_user(get_jwt_identity())
    return jsonify({
        'orders': OrderSchema(many=True).dump(orders)
    }), 200


@order_bp.route('', methods=['GET'])
@jwt_required()
@cashier_or_higher_required
def get_orders():

    status_param = request.args.get('status', 'pending')

    if status_param == 'all':
        status_filter = None
    else:
        status_map = {
            'pending': OrderStatus.PENDING,
            'approved': OrderStatus.APPROVED,
            'rejected': OrderStatus.REJECTED,
            'cancelled': OrderStatus.CANCELLED,
            'completed': OrderStatus.COMPLETED,
        }
        status_filter = status_map.get(status_param)
        if not status_filter:
            return jsonify({'message': 'Неверный параметр status'}), 400

    orders = OrderService.get_orders(status_filter)
    return jsonify({
        'orders': OrderSchema(many=True).dump(orders)
    }), 200


@order_bp.route('/<int:order_id>/approve', methods=['POST'])
@jwt_required()
@cashier_or_higher_required
def approve_order(order_id: int):

    data = request.get_json(silent=True) or {}
    order, sale, error = OrderService.approve_order(
        order_id=order_id,
        manager_id=get_jwt_identity(),
        manager_comment=data.get('manager_comment')
    )

    if error:
        return jsonify(error), _resolve_error_status(error)

    return jsonify({
        'message': 'Заказ подтверждён и оформлен как продажа',
        'order': OrderSchema().dump(order),
        'sale': SaleSchema().dump(sale)
    }), 200


@order_bp.route('/<int:order_id>/reject', methods=['POST'])
@jwt_required()
@cashier_or_higher_required
def reject_order(order_id: int):

    data = request.get_json(silent=True) or {}
    order, error = OrderService.reject_order(
        order_id=order_id,
        manager_id=get_jwt_identity(),
        manager_comment=data.get('manager_comment')
    )

    if error:
        return jsonify(error), _resolve_error_status(error)

    return jsonify({
        'message': 'Заказ отклонён',
        'order': OrderSchema().dump(order)
    }), 200


@order_bp.route('/<int:order_id>/cancel', methods=['POST'])
@jwt_required()
def cancel_order(order_id: int):

    jwt_claims = get_jwt()
    role = jwt_claims.get('role')
    is_manager_action = role in [UserRole.CASHIER.value, UserRole.MANAGER.value, UserRole.ADMIN.value]

    order, error = OrderService.cancel_order(
        order_id=order_id,
        actor_user_id=get_jwt_identity(),
        is_manager_action=is_manager_action
    )

    if error:
        return jsonify(error), _resolve_error_status(error)

    return jsonify({
        'message': 'Заказ отменён',
        'order': OrderSchema().dump(order)
    }), 200
