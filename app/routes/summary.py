from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from sqlalchemy import func
from app.models import SessionLocal, Order, Product
from fastapi.responses import StreamingResponse
import csv
import io
from datetime import datetime


router = APIRouter()
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

def require_login(request: Request):
    return request.session.get("user_id")
#csv
@router.get("/summary/export.csv")
async def export_summary_csv(request: Request):
    user_id = require_login(request)
    if not user_id:
        return RedirectResponse("/login", status_code=302)

    db = SessionLocal()

    # Export all orders with product + computed line total
    rows = (
        db.query(Order, Product)
        .join(Product, Product.id == Order.product_id)
        .filter(Order.user_id == user_id)
        .order_by(Order.id.asc())
        .all()
    )

    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow(["order_id", "customer_name", "product", "qty", "unit_price", "status", "line_total", "created_at"])

    # Data
    for order, product in rows:
        line_total = float(order.qty) * float(product.price)
        writer.writerow([
            order.id,
            order.customer_name,
            product.name,
            order.qty,
            f"{product.price:.2f}",
            order.status,
            f"{line_total:.2f}",
            order.created_at.isoformat() if order.created_at else ""
        ])

    db.close()

    output.seek(0)
    filename = f"livesell_orders_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )



@router.get("/summary")
async def summary_page(request: Request):
    user_id = require_login(request)
    if not user_id:
        return RedirectResponse("/login", status_code=302)

    db = SessionLocal()

    total_orders = db.query(Order).filter(Order.user_id == user_id).count()
    paid_orders = db.query(Order).filter(Order.user_id == user_id, Order.status == "PAID").count()
    cancelled_orders = db.query(Order).filter(Order.user_id == user_id, Order.status == "CANCELLED").count()
    pending_orders = db.query(Order).filter(Order.user_id == user_id, Order.status == "PENDING").count()

    total_revenue = (
        db.query(func.sum(Order.qty * Product.price))
        .join(Product, Product.id == Order.product_id)
        .filter(Order.user_id == user_id, Order.status == "PAID")
        .scalar()
    ) or 0

    best_seller = (
        db.query(Product.name, func.sum(Order.qty).label("total_qty"))
        .join(Order, Order.product_id == Product.id)
        .filter(Order.user_id == user_id, Order.status != "CANCELLED")
        .group_by(Product.name)
        .order_by(func.sum(Order.qty).desc())
        .first()
    )

    low_stock = (
        db.query(Product)
        .filter(Product.user_id == user_id, Product.stock <= 3)
        .order_by(Product.stock.asc())
        .all()
    )

    db.close()

    return templates.TemplateResponse(
        "summary.html",
        {
            "request": request,
            "total_orders": total_orders,
            "paid_orders": paid_orders,
            "pending_orders": pending_orders,
            "cancelled_orders": cancelled_orders,
            "total_revenue": total_revenue,
            "best_seller": best_seller,
            "low_stock": low_stock,
        },
    )
