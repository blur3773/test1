
import os
import secrets
import sys
sys.path.insert(0, '.')

from app import create_app
from app.models.user import User, UserRole
from app.extensions import db


USER_CONFIG = [
    ('ADMIN', 'admin', UserRole.ADMIN),
    ('MANAGER', 'manager', UserRole.MANAGER),
    ('CASHIER', 'cashier', UserRole.CASHIER),
    ('CLIENT', 'client_user', UserRole.CLIENT),
]


def _default_email(prefix: str) -> str:
    return f"{prefix.lower()}@bookstore.local"


def _build_test_users() -> list[dict]:
    users = []
    for env_prefix, username, role in USER_CONFIG:
        users.append({
            'email': os.environ.get(f'{env_prefix}_EMAIL', _default_email(env_prefix)),
            'username': os.environ.get(f'{env_prefix}_USERNAME', username),
            'password': os.environ.get(f'{env_prefix}_PASSWORD') or secrets.token_urlsafe(18),
            'role': role,
            'password_from_env': bool(os.environ.get(f'{env_prefix}_PASSWORD')),
        })
    return users


def init_test_users(clean_first: bool = False):

    app = create_app()
    test_users = _build_test_users()

    with app.app_context():
        if clean_first:
            print("🧹 Очистка базы данных...")
            deleted_count = User.query.delete()
            db.session.commit()
            print(f"Удалено пользователей: {deleted_count}\n")

        created_count = 0
        skipped_count = 0

        for user_data in test_users:
            existing = User.query.filter(
                (User.email == user_data['email']) |
                (User.username == user_data['username'])
            ).first()

            if existing:
                print(f"⚠️  Пользователь {user_data['username']} уже существует")
                skipped_count += 1
                continue

            user = User(
                email=user_data['email'],
                username=user_data['username'],
                role=user_data['role']
            )
            user.set_password(user_data['password'])

            db.session.add(user)
            created_count += 1
            print(f"✅ Создан пользователь: {user_data['username']} ({user_data['role'].value})")

        db.session.commit()

        print(f"\n{'='*40}")
        print(f"Создано пользователей: {created_count}")
        print(f"Пропущено: {skipped_count}")
        print(f"{'='*40}\n")

        if created_count > 0:
            print("📋 Локальные тестовые данные для входа:\n")
            for user_data in test_users:
                password_note = "из переменной окружения" if user_data['password_from_env'] else user_data['password']
                print(f"  {user_data['role'].value.upper():10} | Email: {user_data['email']:25} | Пароль: {password_note}")
            print("\nДля постоянных локальных паролей задайте *_PASSWORD в .env или окружении.")


if __name__ == '__main__':
    import sys
    clean_first = '--clean' in sys.argv or '-c' in sys.argv
    init_test_users(clean_first=clean_first)
