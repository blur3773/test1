from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services import RecommendationService

recommendation_bp = Blueprint('recommendations', __name__, url_prefix='/api/recommendations')


@recommendation_bp.route('/cart', methods=['POST'])
def get_cart_recommendations():

    data = request.get_json() or {}

    cart_book_ids = data.get('cart_book_ids', [])
    if not cart_book_ids:
        return jsonify({'message': 'Необходимо указать cart_book_ids'}), 400

    limit = data.get('limit', 5)

    recommendations = RecommendationService.get_cart_recommendations(
        cart_book_ids=cart_book_ids,
        limit=limit
    )

    return jsonify({
        'recommendations': recommendations
    }), 200


@recommendation_bp.route('/history', methods=['GET'])
@jwt_required()
def get_history_recommendations():

    current_user_id = get_jwt_identity()
    limit = request.args.get('limit', 5, type=int)
    client_id = RecommendationService.get_client_id_by_user_id(current_user_id)

    recommendations = RecommendationService.get_history_recommendations(
        client_id=client_id,
        limit=limit
    )

    return jsonify({
        'recommendations': recommendations
    }), 200


@recommendation_bp.route('/sets', methods=['POST'])
def get_set_recommendations():

    data = request.get_json() or {}

    cart_book_ids = data.get('cart_book_ids', [])
    if not cart_book_ids:
        return jsonify({'message': 'Необходимо указать cart_book_ids'}), 400

    recommendations = RecommendationService.get_set_recommendations(
        cart_book_ids=cart_book_ids
    )

    return jsonify({
        'recommendations': recommendations
    }), 200


@recommendation_bp.route('/personal', methods=['GET'])
@jwt_required()
def get_personal_recommendations():

    current_user_id = get_jwt_identity()
    limit = request.args.get('limit', 5, type=int)
    client_id = RecommendationService.get_client_id_by_user_id(current_user_id)

    cart_book_ids_str = request.args.get('cart_book_ids', '')
    cart_book_ids = []
    if cart_book_ids_str:
        try:
            cart_book_ids = [int(x.strip()) for x in cart_book_ids_str.split(',') if x.strip()]
        except ValueError:
            pass

    recommendations = RecommendationService.get_personal_recommendations(
        client_id=client_id,
        cart_book_ids=cart_book_ids,
        limit=limit
    )

    return jsonify({
        'recommendations': recommendations
    }), 200


@recommendation_bp.route('/popular', methods=['GET'])
def get_popular_books():

    limit = request.args.get('limit', 5, type=int)

    recommendations = RecommendationService.get_popular_books(limit=limit)

    return jsonify({
        'popular_books': recommendations
    }), 200
