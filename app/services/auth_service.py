

from __future__ import annotations

from datetime import datetime, timedelta
from flask_jwt_extended import create_access_token, create_refresh_token
from app.models.user import User, UserRole
from app.extensions import db


class AuthService:


    @staticmethod
    def _create_tokens(user: User) -> dict:

        additional_claims = {'role': user.role.value}

        tokens = {
            'access_token': create_access_token(
                identity=user.id,
                additional_claims=additional_claims
            ),
            'refresh_token': create_refresh_token(
                identity=user.id,
                additional_claims=additional_claims
            )
        }
        return tokens

    @staticmethod
    def register(email: str, username: str, password: str, role: UserRole = UserRole.CLIENT) -> tuple[User | None, dict | None]:

        existing_user = User.query.filter(
            (User.email == email) | (User.username == username)
        ).first()

        if existing_user:
            if existing_user.email == email:
                return None, {'message': 'Email уже зарегистрирован'}
            if existing_user.username == username:
                return None, {'message': 'Имя пользователя уже занято'}

        user = User(email=email, username=username, role=role)
        user.set_password(password)

        try:
            db.session.add(user)
            db.session.commit()
            return user, None
        except Exception as e:
            db.session.rollback()
            return None, {'message': f'Ошибка при регистрации: {str(e)}'}

    @staticmethod
    def login(email: str, password: str) -> tuple[dict | None, dict | None]:

        user = User.query.filter_by(email=email).first()

        if not user or not user.check_password(password):
            return None, {'message': 'Неверный email или пароль'}

        if not user.is_active:
            return None, {'message': 'Аккаунт деактивирован'}

        tokens = AuthService._create_tokens(user)

        return tokens, None

    @staticmethod
    def refresh_token(refresh_token: str) -> tuple[dict | None, dict | None]:

        try:
            from flask_jwt_extended import decode_token
            from jwt.exceptions import InvalidTokenError

            decoded = decode_token(refresh_token)
            user_id = decoded.get('sub')

            user = User.query.get(user_id)
            if not user or not user.is_active:
                return None, {'message': 'Пользователь не найден или деактивирован'}

            return AuthService._create_tokens(user), None

        except InvalidTokenError:
            return None, {'message': 'Неверный refresh токен'}
        except Exception as e:
            return None, {'message': f'Ошибка при обновлении токена: {str(e)}'}

    @staticmethod
    def get_user_by_id(user_id: int) -> User | None:

        return User.query.get(user_id)

    @staticmethod
    def get_current_user(current_user_id: int) -> tuple[User | None, dict | None]:

        user = User.query.get(current_user_id)
        if not user:
            return None, {'message': 'Пользователь не найден'}
        return user, None

    @staticmethod
    def set_user_role(user_id: int, role: UserRole) -> tuple[User | None, dict | None]:

        user = User.query.get(user_id)
        if not user:
            return None, {'message': 'Пользователь не найден'}

        user.role = role
        try:
            db.session.commit()
            return user, None
        except Exception as e:
            db.session.rollback()
            return None, {'message': f'Ошибка при обновлении роли: {str(e)}'}

    @staticmethod
    def get_all_users() -> list[User]:

        return User.query.all()

    @staticmethod
    def deactivate_user(user_id: int) -> tuple[User | None, dict | None]:

        user = User.query.get(user_id)
        if not user:
            return None, {'message': 'Пользователь не найден'}

        user.is_active = False
        try:
            db.session.commit()
            return user, None
        except Exception as e:
            db.session.rollback()
            return None, {'message': f'Ошибка при деактивации: {str(e)}'}

    @staticmethod
    def activate_user(user_id: int) -> tuple[User | None, dict | None]:

        user = User.query.get(user_id)
        if not user:
            return None, {'message': 'Пользователь не найден'}

        user.is_active = True
        try:
            db.session.commit()
            return user, None
        except Exception as e:
            db.session.rollback()
            return None, {'message': f'Ошибка при активации: {str(e)}'}

    @staticmethod
    def delete_user(user_id: int) -> tuple[bool, dict | None]:

        user = User.query.get(user_id)
        if not user:
            return False, {'message': 'Пользователь не найден'}

        try:
            db.session.delete(user)
            db.session.commit()
            return True, None
        except Exception as e:
            db.session.rollback()
            return False, {'message': f'Ошибка при удалении: {str(e)}'}
