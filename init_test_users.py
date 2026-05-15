

import sys
sys.path.insert(0, '.')

from app import create_app
from app.models.user import User, UserRole
from app.extensions import db


TEST_USERS = [
    {
        'email': 'admin@bookstore.com',
        'username': 'admin',
        'password': 'Admin123!',
        'role': UserRole.ADMIN
    },
    {
        'email': 'manager@bookstore.com',
        'username': 'manager',
        'password': 'Manager123!',
        'role': UserRole.MANAGER
    },
    {
        'email': 'cashier@bookstore.com',
        'username': 'cashier',
        'password': 'Cashier123!',
        'role': UserRole.CASHIER
    },
    {
        'email': 'client@example.com',
        'username': 'client_user',
        'password': 'Client123!',
        'role': UserRole.CLIENT
    },
]


def init_test_users(clean_first: bool = False):

    app = create_app()

    with app.app_context():
        if clean_first:
            print("🧹 Очистка базы данных...")
            deleted_count = User.query.delete()
            db.session.commit()
            print(f"Удалено пользователей: {deleted_count}\n")

        created_count = 0
        skipped_count = 0

        for user_data in TEST_USERS:
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
            print("📋 Тестовые данные для входа:\n")
            for user_data in TEST_USERS:
                print(f"  {user_data['role'].value.upper():10} | Email: {user_data['email']:25} | Пароль: {user_data['password']}")


if __name__ == '__main__':
    import sys
    clean_first = '--clean' in sys.argv or '-c' in sys.argv
    init_test_users(clean_first=clean_first)
