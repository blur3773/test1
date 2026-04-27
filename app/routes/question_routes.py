"""Роуты для вопросов клиентов менеджеру."""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.decorators import manager_or_admin_required
from app.models import QuestionStatus
from app.schemas import ManagerQuestionSchema
from app.services import QuestionService


question_bp = Blueprint('questions', __name__, url_prefix='/api/questions')


@question_bp.route('', methods=['POST'])
@jwt_required(optional=True)
def create_question():
    """Отправить вопрос менеджеру."""
    data = request.get_json(silent=True) or {}

    question, error = QuestionService.create_question(
        user_id=get_jwt_identity(),
        name=data.get('name'),
        email=data.get('email'),
        phone=data.get('phone'),
        topic=data.get('topic'),
        message=data.get('message')
    )

    if error:
        return jsonify(error), 400

    return jsonify({
        'message': 'Вопрос отправлен менеджеру',
        'question': ManagerQuestionSchema().dump(question)
    }), 201


@question_bp.route('', methods=['GET'])
@jwt_required()
@manager_or_admin_required
def list_questions():
    """Получить список вопросов клиентов для менеджера/админа."""
    status_param = request.args.get('status', 'new')

    if status_param == 'all':
        status_filter = None
    else:
        status_map = {
            'new': QuestionStatus.NEW,
            'resolved': QuestionStatus.RESOLVED,
        }
        status_filter = status_map.get(status_param)
        if not status_filter:
            return jsonify({'message': 'Неверный параметр status'}), 400

    questions = QuestionService.get_questions(status_filter)
    return jsonify({
        'questions': ManagerQuestionSchema(many=True).dump(questions)
    }), 200
