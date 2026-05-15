

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from sqlalchemy import func, desc
from app.models import Sale, SaleItem, Book, BookStock, SaleStatus, BookStatus
from app.decorators import manager_or_admin_required
from app.extensions import db
from app.utils import log_admin_action

report_bp = Blueprint('reports', __name__, url_prefix='/api/reports')


@report_bp.route('/sales', methods=['GET'])
@jwt_required()
@manager_or_admin_required
def sales_report():

    status_filter = request.args.get('status')

    query = Sale.query
    if status_filter:
        query = query.filter(Sale.status == status_filter)

    sales = query.all()

    total_sales = len(sales)
    total_revenue = sum(sale.total_amount for sale in sales if sale.status == SaleStatus.COMPLETED)
    total_items_sold = sum(
        sum(item.quantity for item in sale.items)
        for sale in sales
        if sale.status == SaleStatus.COMPLETED
    )


    sales_by_status = db.session.query(
        Sale.status,
        func.count(Sale.id).label('count'),
        func.sum(Sale.total_amount).label('total')
    ).group_by(Sale.status).all()

    sales_by_status = [
        {'status': s.status.value if hasattr(s.status, 'value') else s.status, 'count': s.count or 0, 'total': float(s.total) if s.total else 0}
        for s in sales_by_status
    ]
    log_admin_action("report_sales_view", f"status={status_filter or 'all'}")

    return jsonify({
        'total_sales': total_sales,
        'total_revenue': float(total_revenue),
        'total_items_sold': total_items_sold,
        'sales_by_status': sales_by_status
    }), 200


@report_bp.route('/sales/top-books', methods=['GET'])
@jwt_required()
@manager_or_admin_required
def top_books_report():

    limit = request.args.get('limit', 10, type=int)


    top_books = db.session.query(
        SaleItem.book_id,
        func.sum(SaleItem.quantity).label('total_quantity'),
        func.sum(SaleItem.subtotal).label('total_revenue')
    ).join(Sale).filter(
        Sale.status == SaleStatus.COMPLETED
    ).group_by(SaleItem.book_id).order_by(
        desc('total_quantity')
    ).limit(limit).all()

    result = []
    for book_stat in top_books:
        book = Book.query.get(book_stat.book_id)
        if book:
            result.append({
                'book_id': book.id,
                'title': book.title,
                'author': book.author,
                'total_quantity': book_stat.total_quantity,
                'total_revenue': float(book_stat.total_revenue) if book_stat.total_revenue else 0
            })
    log_admin_action("report_top_books_view", f"limit={limit}")

    return jsonify({
        'top_books': result
    }), 200


@report_bp.route('/stock', methods=['GET'])
@jwt_required()
@manager_or_admin_required
def stock_report():

    stocks = BookStock.query.join(Book).filter(Book.status == BookStatus.ACTIVE).all()

    total_books = sum(s.quantity for s in stocks)
    total_value = sum(
        s.quantity * float(s.book.price)
        for s in stocks
        if s.book
    )

    low_stock_books = []
    out_of_stock_books = []

    for stock in stocks:
        if stock.quantity == 0:
            out_of_stock_books.append({
                'book_id': stock.book_id,
                'title': stock.book.title if stock.book else 'Unknown',
                'author': stock.book.author if stock.book else 'Unknown',
                'quantity': 0
            })
        elif stock.quantity < 5:
            low_stock_books.append({
                'book_id': stock.book_id,
                'title': stock.book.title if stock.book else 'Unknown',
                'author': stock.book.author if stock.book else 'Unknown',
                'quantity': stock.quantity
            })
    log_admin_action("report_stock_view", f"stocks={len(stocks)}")

    return jsonify({
        'total_books': total_books,
        'total_value': float(total_value),
        'low_stock_books': low_stock_books,
        'out_of_stock_books': out_of_stock_books
    }), 200


@report_bp.route('/cashier/<int:cashier_id>', methods=['GET'])
@jwt_required()
@manager_or_admin_required
def cashier_report(cashier_id: int):

    from app.models import User
    cashier = User.query.get(cashier_id)
    if not cashier:
        return jsonify({'message': 'Кассир не найден'}), 404

    sales = Sale.query.filter(
        Sale.cashier_id == cashier_id,
        Sale.status == SaleStatus.COMPLETED
    ).all()

    total_sales = len(sales)
    total_revenue = sum(sale.total_amount for sale in sales)
    avg_sale_amount = total_revenue / total_sales if total_sales > 0 else 0
    log_admin_action("report_cashier_view", f"cashier_id={cashier_id}")

    return jsonify({
        'cashier_id': cashier_id,
        'total_sales': total_sales,
        'total_revenue': float(total_revenue),
        'avg_sale_amount': float(avg_sale_amount)
    }), 200
