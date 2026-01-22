from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from sqlalchemy.orm import joinedload
from datetime import datetime
from app.models import SessionLocal, Product, Order, LiveSession


router = APIRouter()
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

def require_login(request: Request):
    return request.session.get("user_id")

#LiveSession
def get_or_create_active_session(db, user_id: int):
    session = (
        db.query(LiveSession)
        .filter(LiveSession.ended_at == None, LiveSession.user_id == user_id)
        .order_by(LiveSession.id.desc())
        .first()
    )
    if session:
        return session

    session = LiveSession(title="Live Session", user_id=user_id)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session



#end
@router.post("/live/end")
async def end_live_session(request: Request):
    user_id = require_login(request)
    if not user_id:
        return RedirectResponse("/login", status_code=302)

    db = SessionLocal()
    active_session = (
        db.query(LiveSession)
        .filter(LiveSession.ended_at == None, LiveSession.user_id == user_id)
        .order_by(LiveSession.id.desc())
        .first()
    )

    if active_session:
        active_session.ended_at = datetime.utcnow()
        db.commit()

    db.close()
    return RedirectResponse("/live", status_code=302)

#liveSellingPage
@router.get("/live")
async def live_page(request: Request):
    user_id = require_login(request)
    if not user_id:
        return RedirectResponse("/login", status_code=302)

    db = SessionLocal()
    active_session = get_or_create_active_session(db, user_id)

    products = (
        db.query(Product)
        .filter(Product.user_id == user_id)
        .order_by(Product.name.asc())
        .all()
    )
    orders = (
        db.query(Order)
        .options(joinedload(Order.product))
        .filter(Order.session_id == active_session.id, Order.user_id == user_id)
        .order_by(Order.id.desc())
        .all()
    )
    db.close()

    return templates.TemplateResponse(
        "live.html",
        {"request": request, "products": products, "orders": orders, "active_session": active_session}
    )

#Mark as paid
@router.post("/live/order/{order_id}/status")
async def update_status(
    request: Request,
    order_id: int,
    status: str = Form(...)
):
    user_id = require_login(request)
    if not user_id:
        return RedirectResponse("/login", status_code=302)

    db = SessionLocal()
    order = (
        db.query(Order)
        .filter(Order.id == order_id, Order.user_id == user_id)
        .first()
    )

    if order and status in ("PENDING", "PAID", "CANCELLED"):

        # If cancelling → return stock
        if status == "CANCELLED" and order.status != "CANCELLED":
            product = (
                db.query(Product)
                .filter(Product.id == order.product_id, Product.user_id == user_id)
                .first()
            )
            if product:
                product.stock += order.qty

        order.status = status
        db.commit()

    db.close()
    return RedirectResponse("/live", status_code=302)

#Add Order
@router.post("/live/order/add")
async def add_order(
    request: Request,
    customer_name: str = Form(...),
    product_id:int = Form(...),
    qty: int = Form(...),
):
    user_id = require_login(request)
    if not user_id:
        return RedirectResponse("/login", status_code=302)
    customer_name = customer_name.strip()

    db = SessionLocal()
    active_session = get_or_create_active_session(db, user_id)
    product = (
        db.query(Product)
        .filter(Product.id == product_id, Product.user_id == user_id)
        .first()
    )

    #validations
    if not product or qty <= 0 or product.stock < qty:
        db.close()
        return RedirectResponse("/live", status_code=302)
    #create order
    db.add(
        Order(
            customer_name=customer_name,
            session_id=active_session.id,
            product_id=product_id,
            qty=qty,
            status="PENDING",
            user_id=user_id,
        )
    )

    product.stock -= qty
    db.commit()
    db.close()
    return RedirectResponse("/live", status_code=302)
