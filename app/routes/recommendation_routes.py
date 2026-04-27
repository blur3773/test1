from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services import RecommendationService

recommendation_bp = Blueprint('recommendations', __name__, url_prefix='/api/recommendations')


@recommendation_bp.route('/cart', methods=['POST'])
def get_cart_recommendations():
    """
    Рекомендации на основе корзины.

    ---
    tags:
      - Recommendations
    summary: Рекомендации для корзины (все)
    description: Получает рекомендации книг на основе содержимого корзины
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required:
              - cart_book_ids
            properties:
              cart_book_ids:
                type: array
                items:
                  type: integer
                example: [1, 3, 5]
              limit:
                type: integer
                default: 5
                example: 5
    responses:
      200:
        description: Список рекомендованных книг
        content:
          application/json:
            schema:
              type: object
              properties:
                recommendations:
                  type: array
                  items:
                    type: object
                    properties:
                      book:
                        $ref: '#/components/schemas/Book'
                      score:
                        type: number
                      reason:
                        type: string
      400:
        description: Ошибка валидации данных
    """
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
    """
    Рекомендации на основе истории покупок.

    ---
    tags:
      - Recommendations
    summary: Рекомендации по истории (все авторизованные)
    description: Получает рекомендации на основе истории покупок клиента
    parameters:
      - in: query
        name: limit
        schema:
          type: integer
          default: 5
    responses:
      200:
        description: Список рекомендованных книг
        content:
          application/json:
            schema:
              type: object
              properties:
                recommendations:
                  type: array
                  items:
                    type: object
                    properties:
                      book:
                        $ref: '#/components/schemas/Book'
                      score:
                        type: number
                      reason:
                        type: string
      401:
        description: Токен не предоставлен или недействителен
    """
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
    """
    Рекомендации для дополнения комплектов (серий).

    ---
    tags:
      - Recommendations
    summary: Дополнить комплект (все)
    description: Находит книги для дополнения серии/комплекта
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required:
              - cart_book_ids
            properties:
              cart_book_ids:
                type: array
                items:
                  type: integer
                example: [1, 3]
    responses:
      200:
        description: Список книг для дополнения комплекта
        content:
          application/json:
            schema:
              type: object
              properties:
                recommendations:
                  type: array
                  items:
                    type: object
                    properties:
                      book:
                        $ref: '#/components/schemas/Book'
                      reason:
                        type: string
                      set_name:
                        type: string
      400:
        description: Ошибка валидации данных
    """
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
    """
    Персональные рекомендации (комбинированные).

    ---
    tags:
      - Recommendations
    summary: Персональные рекомендации (все авторизованные)
    description: Комбинированные рекомендации с учётом истории покупок, корзины и популярных книг
    parameters:
      - in: query
        name: limit
        schema:
          type: integer
          default: 5
      - in: query
        name: cart_book_ids
        schema:
          type: array
          items:
            type: integer
    responses:
      200:
        description: Список персональных рекомендаций
        content:
          application/json:
            schema:
              type: object
              properties:
                recommendations:
                  type: array
                  items:
                    type: object
                    properties:
                      book:
                        $ref: '#/components/schemas/Book'
                      score:
                        type: number
                      reason:
                        type: string
      401:
        description: Токен не предоставлен или недействителен
    """
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
    """
    Популярные книги (топ продаж).

    ---
    tags:
      - Recommendations
    summary: Популярные книги (все)
    description: Возвращает топ книг по количеству продаж
    parameters:
      - in: query
        name: limit
        schema:
          type: integer
          default: 5
    responses:
      200:
        description: Список популярных книг
        content:
          application/json:
            schema:
              type: object
              properties:
                popular_books:
                  type: array
                  items:
                    type: object
                    properties:
                      book:
                        $ref: '#/components/schemas/Book'
                      score:
                        type: integer
                      reason:
                        type: string
                        example: Популярная книга
      404:
        description: Нет данных о продажах
    """
    limit = request.args.get('limit', 5, type=int)

    recommendations = RecommendationService.get_popular_books(limit=limit)

    return jsonify({
        'popular_books': recommendations
    }), 200
