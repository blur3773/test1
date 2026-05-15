

from datetime import datetime
from typing import List, Tuple, Optional
import re
from app.models.store import (
    Book,
    BookStock,
    BookStatus,
    Sale,
    SaleItem,
    SaleStatus,
    Client,
    Order,
    OrderItem,
    OrderStatus,
    ManagerQuestion,
    QuestionStatus,
)
from app.models.user import User
from app.extensions import db
from app.services.book_cover_service import BookCoverService


_RU_PHONE_PATTERN = re.compile(r"^(?:\+7|7|8)?\d{10}$")


def _normalize_text(value: Optional[str]) -> str:
    return (value or "").strip()


def _format_ru_phone(value: Optional[str]) -> Optional[str]:
    normalized_value = _normalize_text(value)
    if not normalized_value:
        return None

    digits = re.sub(r"\D", "", normalized_value)
    if len(digits) == 10:
        return f"+7{digits}"
    if len(digits) == 11 and digits[0] in {"7", "8"}:
        return f"+7{digits[1:]}"
    return None


def _is_valid_ru_phone(value: Optional[str]) -> bool:
    normalized_value = _normalize_text(value)
    if not normalized_value:
        return True
    return bool(_RU_PHONE_PATTERN.fullmatch(re.sub(r"\s+", "", normalized_value))) or bool(_format_ru_phone(value))


class BookService:


    @staticmethod
    def get_all_books(status: Optional[BookStatus] = None) -> List[Book]:

        query = Book.query
        if status:
            query = query.filter(Book.status == status)
        return query.order_by(Book.title).all()

    @staticmethod
    def get_book_by_id(book_id: int) -> Optional[Book]:

        return Book.query.get(book_id)

    @staticmethod
    def get_book_by_isbn(isbn: str) -> Optional[Book]:

        return Book.query.filter(Book.isbn == isbn).first()

    @staticmethod
    def search_books(query: str) -> List[Book]:


        normalized_query = query.lower().replace('ё', 'е')


        books = Book.query.filter(Book.status == BookStatus.ACTIVE).all()


        results = []
        for book in books:

            normalized_title = book.title.lower().replace('ё', 'е')
            normalized_title_ru = (book.title_ru or '').lower().replace('ё', 'е')
            normalized_author = book.author.lower().replace('ё', 'е')
            normalized_isbn = book.isbn.lower().replace('ё', 'е')


            if (normalized_query in normalized_title or
                normalized_query in normalized_title_ru or
                normalized_query in normalized_author or
                normalized_query in normalized_isbn):
                results.append(book)

        return results

    @staticmethod
    def create_book(
        title: str,
        author: str,
        isbn: str,
        price: float,
        title_ru: Optional[str] = None,
        publisher: Optional[str] = None,
        year: Optional[int] = None,
        publication_place: Optional[str] = None,
        page_count: Optional[int] = None,
        weight_grams: Optional[int] = None,
        print_run: Optional[int] = None,
        genre: Optional[str] = None,
        description: Optional[str] = None,
        source_url: Optional[str] = None,
        stock_quantity: int = 0
    ) -> Tuple[Optional[Book], Optional[dict]]:

        existing_book = Book.query.filter(Book.isbn == isbn).first()
        if existing_book:
            return None, {'message': 'Книга с таким ISBN уже существует'}

        cover_url = BookCoverService.find_cover_url(
            title=title,
            author=author,
            isbn=isbn
        )

        book = Book(
            title=title,
            title_ru=title_ru,
            author=author,
            isbn=isbn,
            price=price,
            publisher=publisher,
            year=year,
            publication_place=publication_place,
            page_count=page_count,
            weight_grams=weight_grams,
            print_run=print_run,
            genre=genre,
            description=description,
            cover_url=cover_url,
            source_url=source_url,
            status=BookStatus.ACTIVE
        )

        try:
            db.session.add(book)
            db.session.flush()


            stock = BookStock(book_id=book.id, quantity=stock_quantity, reserved=0)
            db.session.add(stock)
            db.session.commit()

            return book, None
        except Exception as e:
            db.session.rollback()
            return None, {'message': f'Ошибка при создании книги: {str(e)}'}

    @staticmethod
    def update_book(
        book_id: int,
        title: Optional[str] = None,
        title_ru: Optional[str] = None,
        author: Optional[str] = None,
        isbn: Optional[str] = None,
        price: Optional[float] = None,
        publisher: Optional[str] = None,
        year: Optional[int] = None,
        publication_place: Optional[str] = None,
        page_count: Optional[int] = None,
        weight_grams: Optional[int] = None,
        print_run: Optional[int] = None,
        genre: Optional[str] = None,
        description: Optional[str] = None,
        source_url: Optional[str] = None
    ) -> Tuple[Optional[Book], Optional[dict]]:

        book = Book.query.get(book_id)
        if not book:
            return None, {'message': 'Книга не найдена'}


        if isbn and isbn != book.isbn:
            existing = Book.query.filter(Book.isbn == isbn).first()
            if existing:
                return None, {'message': 'Книга с таким ISBN уже существует'}

        try:
            effective_title = title if title else book.title
            effective_author = author if author else book.author
            effective_isbn = isbn if isbn else book.isbn

            if title:
                book.title = title
            if title_ru is not None:
                book.title_ru = title_ru
            if author:
                book.author = author
            if isbn:
                book.isbn = isbn
            if price is not None:
                book.price = price
            if publisher is not None:
                book.publisher = publisher
            if year is not None:
                book.year = year
            if publication_place is not None:
                book.publication_place = publication_place
            if page_count is not None:
                book.page_count = page_count
            if weight_grams is not None:
                book.weight_grams = weight_grams
            if print_run is not None:
                book.print_run = print_run
            if genre is not None:
                book.genre = genre
            if description is not None:
                book.description = description
            if source_url is not None:
                book.source_url = source_url

            should_refresh_cover = bool(title or author or isbn or not book.cover_url)
            if should_refresh_cover:
                resolved_cover_url = BookCoverService.find_cover_url(
                    title=effective_title,
                    author=effective_author,
                    isbn=effective_isbn
                )
                if resolved_cover_url:
                    book.cover_url = resolved_cover_url

            book.updated_at = datetime.utcnow()
            db.session.commit()

            return book, None
        except Exception as e:
            db.session.rollback()
            return None, {'message': f'Ошибка при обновлении книги: {str(e)}'}

    @staticmethod
    def archive_book(book_id: int) -> Tuple[Optional[Book], Optional[dict]]:

        book = Book.query.get(book_id)
        if not book:
            return None, {'message': 'Книга не найдена'}

        try:
            book.status = BookStatus.ARCHIVED
            book.updated_at = datetime.utcnow()
            db.session.commit()

            return book, None
        except Exception as e:
            db.session.rollback()
            return None, {'message': f'Ошибка при архивации книги: {str(e)}'}

    @staticmethod
    def restore_book(book_id: int) -> Tuple[Optional[Book], Optional[dict]]:

        book = Book.query.get(book_id)
        if not book:
            return None, {'message': 'Книга не найдена'}

        try:
            book.status = BookStatus.ACTIVE
            book.updated_at = datetime.utcnow()
            db.session.commit()

            return book, None
        except Exception as e:
            db.session.rollback()
            return None, {'message': f'Ошибка при восстановлении книги: {str(e)}'}


class StockService:


    @staticmethod
    def get_stock(book_id: int) -> Optional[BookStock]:

        return BookStock.query.filter(BookStock.book_id == book_id).first()

    @staticmethod
    def update_stock(book_id: int, quantity: int) -> Tuple[Optional[BookStock], Optional[dict]]:

        book = Book.query.get(book_id)
        if not book:
            return None, {'message': 'Книга не найдена'}

        stock = BookStock.query.filter(BookStock.book_id == book_id).first()
        if not stock:
            stock = BookStock(book_id=book_id, quantity=0, reserved=0)

        try:
            stock.quantity = quantity
            stock.updated_at = datetime.utcnow()
            db.session.commit()

            return stock, None
        except Exception as e:
            db.session.rollback()
            return None, {'message': f'Ошибка при обновлении остатков: {str(e)}'}

    @staticmethod
    def adjust_stock(book_id: int, quantity_change: int) -> Tuple[Optional[BookStock], Optional[dict]]:

        book = Book.query.get(book_id)
        if not book:
            return None, {'message': 'Книга не найдена'}

        stock = BookStock.query.filter(BookStock.book_id == book_id).first()
        if not stock:
            stock = BookStock(book_id=book_id, quantity=0, reserved=0)

        try:
            stock.quantity += quantity_change
            if stock.quantity < 0:
                stock.quantity = 0
            stock.updated_at = datetime.utcnow()
            db.session.commit()

            return stock, None
        except Exception as e:
            db.session.rollback()
            return None, {'message': f'Ошибка при корректировке остатков: {str(e)}'}

    @staticmethod
    def reserve_stock(book_id: int, quantity: int) -> Tuple[Optional[BookStock], Optional[dict]]:

        stock = BookStock.query.filter(BookStock.book_id == book_id).first()
        if not stock:
            return None, {'message': 'Остатки не найдены'}

        if stock.available < quantity:
            return None, {'message': 'Недостаточно книг на складе'}

        try:
            stock.reserved += quantity
            stock.updated_at = datetime.utcnow()
            db.session.commit()

            return stock, None
        except Exception as e:
            db.session.rollback()
            return None, {'message': f'Ошибка при резервировании: {str(e)}'}

    @staticmethod
    def release_reservation(book_id: int, quantity: int) -> Tuple[Optional[BookStock], Optional[dict]]:

        stock = BookStock.query.filter(BookStock.book_id == book_id).first()
        if not stock:
            return None, {'message': 'Остатки не найдены'}

        try:
            stock.reserved = max(0, stock.reserved - quantity)
            stock.updated_at = datetime.utcnow()
            db.session.commit()

            return stock, None
        except Exception as e:
            db.session.rollback()
            return None, {'message': f'Ошибка при снятии резерва: {str(e)}'}


class SaleService:


    @staticmethod
    def create_sale(
        cashier_id: int,
        items: List[dict],
        client_id: Optional[int] = None
    ) -> Tuple[Optional[Sale], Optional[dict]]:

        if not items:
            return None, {'message': 'Список товаров пуст'}

        try:
            sale = Sale(
                cashier_id=cashier_id,
                client_id=client_id,
                total_amount=0,
                status=SaleStatus.COMPLETED
            )
            db.session.add(sale)
            db.session.flush()

            total_amount = 0
            sale_items = []

            for item_data in items:
                book_id = item_data.get('book_id')
                quantity = item_data.get('quantity', 1)

                book = Book.query.get(book_id)
                if not book:
                    db.session.rollback()
                    return None, {'message': f'Книга с ID {book_id} не найдена'}

                if book.status != BookStatus.ACTIVE:
                    db.session.rollback()
                    return None, {'message': f'Книга "{book.title}" недоступна для продажи'}

                stock = BookStock.query.filter(BookStock.book_id == book_id).first()
                if not stock or stock.available < quantity:
                    db.session.rollback()
                    return None, {'message': f'Недостаточно книг на складе: {book.title}'}


                stock.quantity -= quantity
                stock.updated_at = datetime.utcnow()

                subtotal = float(book.price) * quantity
                total_amount += subtotal

                sale_item = SaleItem(
                    sale_id=sale.id,
                    book_id=book_id,
                    quantity=quantity,
                    price=book.price,
                    subtotal=subtotal
                )
                sale_items.append(sale_item)
                db.session.add(sale_item)

            sale.total_amount = total_amount
            db.session.commit()

            return sale, None
        except Exception as e:
            db.session.rollback()
            return None, {'message': f'Ошибка при создании продажи: {str(e)}'}

    @staticmethod
    def get_sale_by_id(sale_id: int) -> Optional[Sale]:

        return Sale.query.get(sale_id)

    @staticmethod
    def get_all_sales() -> List[Sale]:

        return Sale.query.order_by(Sale.created_at.desc()).all()

    @staticmethod
    def return_sale(sale_id: int) -> Tuple[Optional[Sale], Optional[dict]]:

        sale = Sale.query.get(sale_id)
        if not sale:
            return None, {'message': 'Продажа не найдена'}

        if sale.status == SaleStatus.RETURNED:
            return None, {'message': 'Продажа уже возвращена'}

        if sale.status == SaleStatus.CANCELLED:
            return None, {'message': 'Продажа отменена'}

        try:

            for item in sale.items:
                stock = BookStock.query.filter(BookStock.book_id == item.book_id).first()
                if stock:
                    stock.quantity += item.quantity
                    stock.updated_at = datetime.utcnow()

            sale.status = SaleStatus.RETURNED
            sale.updated_at = datetime.utcnow()
            db.session.commit()

            return sale, None
        except Exception as e:
            db.session.rollback()
            return None, {'message': f'Ошибка при возврате: {str(e)}'}

    @staticmethod
    def cancel_sale(sale_id: int) -> Tuple[Optional[Sale], Optional[dict]]:

        sale = Sale.query.get(sale_id)
        if not sale:
            return None, {'message': 'Продажа не найдена'}

        if sale.status == SaleStatus.RETURNED:
            return None, {'message': 'Продажа уже возвращена'}

        if sale.status == SaleStatus.CANCELLED:
            return None, {'message': 'Продажа уже отменена'}

        try:

            for item in sale.items:
                stock = BookStock.query.filter(BookStock.book_id == item.book_id).first()
                if stock:
                    stock.quantity += item.quantity
                    stock.updated_at = datetime.utcnow()

            sale.status = SaleStatus.CANCELLED
            sale.updated_at = datetime.utcnow()
            db.session.commit()

            return sale, None
        except Exception as e:
            db.session.rollback()
            return None, {'message': f'Ошибка при отмене: {str(e)}'}


class OrderService:


    @staticmethod
    def create_order(
        user_id: int,
        items: List[dict],
        customer_comment: Optional[str] = None
    ) -> Tuple[Optional[Order], Optional[dict]]:

        if not items:
            return None, {'message': 'Список товаров пуст'}

        client = Client.query.filter(Client.user_id == user_id).first()

        try:
            order = Order(
                user_id=user_id,
                client_id=client.id if client else None,
                status=OrderStatus.PENDING,
                customer_comment=customer_comment,
                total_amount=0
            )
            db.session.add(order)
            db.session.flush()

            total_amount = 0.0

            for item_data in items:
                book_id = item_data.get('book_id')
                quantity = int(item_data.get('quantity', 1))

                if not book_id or quantity <= 0:
                    db.session.rollback()
                    return None, {'message': 'Некорректные данные позиции заказа'}

                book = Book.query.get(book_id)
                if not book:
                    db.session.rollback()
                    return None, {'message': f'Книга с ID {book_id} не найдена'}

                if book.status != BookStatus.ACTIVE:
                    db.session.rollback()
                    return None, {'message': f'Книга "{book.title}" недоступна для заказа'}

                stock = BookStock.query.filter(BookStock.book_id == book_id).first()
                if not stock or stock.available < quantity:
                    db.session.rollback()
                    return None, {'message': f'Недостаточно книг на складе: {book.title}'}

                stock.reserved += quantity
                stock.updated_at = datetime.utcnow()

                subtotal = float(book.price) * quantity
                total_amount += subtotal

                order_item = OrderItem(
                    order_id=order.id,
                    book_id=book_id,
                    quantity=quantity,
                    price=book.price,
                    subtotal=subtotal
                )
                db.session.add(order_item)

            order.total_amount = total_amount
            db.session.commit()

            return order, None
        except Exception as e:
            db.session.rollback()
            return None, {'message': f'Ошибка при создании заказа: {str(e)}'}

    @staticmethod
    def get_orders(status: Optional[OrderStatus] = None) -> List[Order]:

        query = Order.query
        if status:
            query = query.filter(Order.status == status)
        return query.order_by(Order.created_at.desc()).all()

    @staticmethod
    def get_orders_by_user(user_id: int) -> List[Order]:

        return Order.query.filter(Order.user_id == user_id).order_by(Order.created_at.desc()).all()

    @staticmethod
    def get_order_by_id(order_id: int) -> Optional[Order]:

        return Order.query.get(order_id)

    @staticmethod
    def _release_order_reservations(order: Order) -> None:

        for item in order.items:
            stock = BookStock.query.filter(BookStock.book_id == item.book_id).first()
            if not stock:
                continue
            stock.reserved = max(0, stock.reserved - item.quantity)
            stock.updated_at = datetime.utcnow()

    @staticmethod
    def approve_order(
        order_id: int,
        manager_id: int,
        manager_comment: Optional[str] = None
    ) -> Tuple[Optional[Order], Optional[Sale], Optional[dict]]:

        order = Order.query.get(order_id)
        if not order:
            return None, None, {'message': 'Заказ не найден'}

        if order.status != OrderStatus.PENDING:
            return None, None, {'message': 'Можно подтвердить только заказ в статусе pending'}

        try:
            sale = Sale(
                cashier_id=manager_id,
                client_id=order.client_id,
                total_amount=order.total_amount,
                status=SaleStatus.COMPLETED
            )
            db.session.add(sale)
            db.session.flush()

            for item in order.items:
                stock = BookStock.query.filter(BookStock.book_id == item.book_id).first()
                if not stock:
                    db.session.rollback()
                    return None, None, {'message': f'Остатки книги ID={item.book_id} не найдены'}

                if stock.quantity < item.quantity:
                    db.session.rollback()
                    return None, None, {'message': f'Недостаточно книг на складе для ID={item.book_id}'}

                stock.reserved = max(0, stock.reserved - item.quantity)
                stock.quantity -= item.quantity
                stock.updated_at = datetime.utcnow()

                sale_item = SaleItem(
                    sale_id=sale.id,
                    book_id=item.book_id,
                    quantity=item.quantity,
                    price=item.price,
                    subtotal=item.subtotal
                )
                db.session.add(sale_item)

            order.status = OrderStatus.COMPLETED
            order.manager_id = manager_id
            if manager_comment:
                order.manager_comment = manager_comment
            order.sale_id = sale.id
            order.updated_at = datetime.utcnow()

            db.session.commit()

            return order, sale, None
        except Exception as e:
            db.session.rollback()
            return None, None, {'message': f'Ошибка при подтверждении заказа: {str(e)}'}

    @staticmethod
    def reject_order(
        order_id: int,
        manager_id: int,
        manager_comment: Optional[str] = None
    ) -> Tuple[Optional[Order], Optional[dict]]:

        order = Order.query.get(order_id)
        if not order:
            return None, {'message': 'Заказ не найден'}

        if order.status != OrderStatus.PENDING:
            return None, {'message': 'Можно отклонить только заказ в статусе pending'}

        try:
            OrderService._release_order_reservations(order)
            order.status = OrderStatus.REJECTED
            order.manager_id = manager_id
            if manager_comment:
                order.manager_comment = manager_comment
            order.updated_at = datetime.utcnow()
            db.session.commit()

            return order, None
        except Exception as e:
            db.session.rollback()
            return None, {'message': f'Ошибка при отклонении заказа: {str(e)}'}

    @staticmethod
    def cancel_order(
        order_id: int,
        actor_user_id: int,
        is_manager_action: bool = False
    ) -> Tuple[Optional[Order], Optional[dict]]:

        order = Order.query.get(order_id)
        if not order:
            return None, {'message': 'Заказ не найден'}

        if order.status != OrderStatus.PENDING:
            return None, {'message': 'Можно отменить только заказ в статусе pending'}

        if not is_manager_action and order.user_id != actor_user_id:
            return None, {'message': 'Недостаточно прав для отмены этого заказа'}

        try:
            OrderService._release_order_reservations(order)
            order.status = OrderStatus.CANCELLED
            if is_manager_action:
                order.manager_id = actor_user_id
            order.updated_at = datetime.utcnow()
            db.session.commit()

            return order, None
        except Exception as e:
            db.session.rollback()
            return None, {'message': f'Ошибка при отмене заказа: {str(e)}'}


class ClientService:


    @staticmethod
    def get_all_clients() -> List[Client]:

        return Client.query.order_by(Client.last_name).all()

    @staticmethod
    def get_client_by_id(client_id: int) -> Optional[Client]:

        return Client.query.get(client_id)

    @staticmethod
    def get_client_by_user_id(user_id: int) -> Optional[Client]:

        return Client.query.filter(Client.user_id == user_id).first()

    @staticmethod
    def create_client(
        first_name: str,
        last_name: str,
        middle_name: Optional[str] = None,
        phone: Optional[str] = None,
        email: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> Tuple[Optional[Client], Optional[dict]]:

        normalized_first_name = _normalize_text(first_name)
        normalized_last_name = _normalize_text(last_name)
        normalized_middle_name = _normalize_text(middle_name) or None
        normalized_email = _normalize_text(email) or None
        normalized_phone = _normalize_text(phone) or None

        if not normalized_first_name or not normalized_last_name:
            return None, {'message': 'Имя и фамилия обязательны'}

        if len(normalized_first_name) > 50 or len(normalized_last_name) > 50:
            return None, {'message': 'Имя и фамилия не должны превышать 50 символов'}

        if normalized_middle_name and len(normalized_middle_name) > 50:
            return None, {'message': 'Отчество не должно превышать 50 символов'}

        if normalized_email and len(normalized_email) > 120:
            return None, {'message': 'Email не должен превышать 120 символов'}

        if normalized_phone and not _is_valid_ru_phone(normalized_phone):
            return None, {'message': 'Некорректный номер телефона'}

        formatted_phone = _format_ru_phone(normalized_phone)
        if normalized_phone and not formatted_phone:
            return None, {'message': 'Некорректный номер телефона'}

        if user_id:
            existing = Client.query.filter(Client.user_id == user_id).first()
            if existing:
                return None, {'message': 'Клиент с таким пользователем уже существует'}

        client = Client(
            first_name=normalized_first_name,
            last_name=normalized_last_name,
            middle_name=normalized_middle_name,
            phone=formatted_phone,
            email=normalized_email,
            user_id=user_id
        )

        try:
            db.session.add(client)
            db.session.commit()
            return client, None
        except Exception as e:
            db.session.rollback()
            return None, {'message': f'Ошибка при создании клиента: {str(e)}'}

    @staticmethod
    def update_client(
        client_id: int,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        middle_name: Optional[str] = None,
        phone: Optional[str] = None,
        email: Optional[str] = None
    ) -> Tuple[Optional[Client], Optional[dict]]:

        client = Client.query.get(client_id)
        if not client:
            return None, {'message': 'Клиент не найден'}

        try:
            if first_name is not None:
                normalized_first_name = _normalize_text(first_name)
                if not normalized_first_name:
                    return None, {'message': 'Имя не может быть пустым'}
                if len(normalized_first_name) > 50:
                    return None, {'message': 'Имя не должно превышать 50 символов'}
                client.first_name = normalized_first_name
            if last_name is not None:
                normalized_last_name = _normalize_text(last_name)
                if not normalized_last_name:
                    return None, {'message': 'Фамилия не может быть пустой'}
                if len(normalized_last_name) > 50:
                    return None, {'message': 'Фамилия не должна превышать 50 символов'}
                client.last_name = normalized_last_name
            if middle_name is not None:
                normalized_middle_name = _normalize_text(middle_name)
                if normalized_middle_name and len(normalized_middle_name) > 50:
                    return None, {'message': 'Отчество не должно превышать 50 символов'}
                client.middle_name = normalized_middle_name or None
            if phone is not None:
                normalized_phone = _normalize_text(phone)
                if normalized_phone:
                    formatted_phone = _format_ru_phone(normalized_phone)
                    if not formatted_phone:
                        return None, {'message': 'Некорректный номер телефона'}
                    client.phone = formatted_phone
                else:
                    client.phone = None
            if email is not None:
                normalized_email = _normalize_text(email)
                if normalized_email and len(normalized_email) > 120:
                    return None, {'message': 'Email не должен превышать 120 символов'}
                client.email = normalized_email or None

            client.updated_at = datetime.utcnow()
            db.session.commit()

            return client, None
        except Exception as e:
            db.session.rollback()
            return None, {'message': f'Ошибка при обновлении клиента: {str(e)}'}

    @staticmethod
    def delete_client(client_id: int) -> Tuple[bool, Optional[dict]]:

        client = Client.query.get(client_id)
        if not client:
            return False, {'message': 'Клиент не найден'}

        try:
            db.session.delete(client)
            db.session.commit()
            return True, None
        except Exception as e:
            db.session.rollback()
            return False, {'message': f'Ошибка при удалении клиента: {str(e)}'}


class QuestionService:


    @staticmethod
    def create_question(
        message: str,
        name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        topic: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> Tuple[Optional[ManagerQuestion], Optional[dict]]:

        normalized_message = _normalize_text(message)
        if not normalized_message:
            return None, {'message': 'Поле message обязательно'}
        if len(normalized_message) > 1000:
            return None, {'message': 'Сообщение не должно превышать 1000 символов'}

        user = User.query.get(user_id) if user_id else None
        client = Client.query.filter(Client.user_id == user_id).first() if user_id else None

        normalized_name = _normalize_text(name)
        normalized_email = _normalize_text(email)
        normalized_phone = _normalize_text(phone)
        normalized_topic = _normalize_text(topic)

        if not normalized_name and user:
            normalized_name = user.username

        if not normalized_email and user:
            normalized_email = user.email

        if not normalized_phone and client and client.phone:
            normalized_phone = client.phone

        if not normalized_name:
            return None, {'message': 'Укажите имя'}
        if len(normalized_name) > 120:
            return None, {'message': 'Имя не должно превышать 120 символов'}

        if normalized_topic and len(normalized_topic) > 200:
            return None, {'message': 'Тема не должна превышать 200 символов'}

        if normalized_email and len(normalized_email) > 120:
            return None, {'message': 'Email не должен превышать 120 символов'}

        if not normalized_email and not normalized_phone:
            return None, {'message': 'Укажите email или телефон для обратной связи'}

        formatted_phone = None
        if normalized_phone:
            formatted_phone = _format_ru_phone(normalized_phone)
            if not formatted_phone:
                return None, {'message': 'Некорректный номер телефона'}

        question = ManagerQuestion(
            user_id=user_id,
            name=normalized_name,
            email=normalized_email or None,
            phone=formatted_phone,
            topic=normalized_topic or None,
            message=normalized_message,
            status=QuestionStatus.NEW
        )

        try:
            db.session.add(question)
            db.session.commit()
            return question, None
        except Exception as e:
            db.session.rollback()
            return None, {'message': f'Ошибка при отправке вопроса: {str(e)}'}

    @staticmethod
    def get_questions(status: Optional[QuestionStatus] = None) -> List[ManagerQuestion]:

        query = ManagerQuestion.query
        if status:
            query = query.filter(ManagerQuestion.status == status)
        return query.order_by(ManagerQuestion.created_at.desc()).all()
