from fastapi import APIRouter, Request, Form, UploadFile, File
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from app.models import SessionLocal, Product
import os
import uuid

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent  # points to /app
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

def require_login(request: Request):
    return request.session.get("user_id")

@router.get("/inventory")
async def inventory_page(request: Request):
    user_id = require_login(request)
    if not user_id:
        return RedirectResponse("/login", status_code=302)

    db = SessionLocal()
    products = (
        db.query(Product)
        .filter(Product.user_id == user_id)
        .order_by(Product.id.desc())
        .all()
    )
    db.close()

    return templates.TemplateResponse("inventory.html", {"request": request, "products": products})

#upgrade product image
@router.post("/inventory/{product_id}/image")
async def update_product_image(
    request: Request,
    product_id : int,
    image: UploadFile = File(...),
):
    user_id = require_login(request)
    if not user_id:
        return RedirectResponse("/login", status_code=302)
    db = SessionLocal()
    product = (
        db.query(Product)
        .filter(Product.id == product_id, Product.user_id == user_id)
        .first()
    )

    if not product:
        db.close()
        return RedirectResponse("/inventory", status_code=302)
    #saveimage
    upload_dir = BASE_DIR/"static"/"uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)

    ext = os.path.splitext(image.filename)[1].lower()
    filename = f"{uuid.uuid4().hex}{ext}"
    save_path = upload_dir / filename

    contents = await image.read()
    with open(save_path, "wb") as f:
        f.write(contents)
    new_image_path = f"/static/uploads/{filename}"

    #delete file if exist
    if product.image_path:
        old_rel = product.image_path.lstrip("/")
        old_full = BASE_DIR / old_rel.replace("static/", "static/")
        old_full = BASE_DIR / "static" / "uploads" / Path(product.image_path).name
        if old_full.exists():
            try:
                old_full.unlink()
            except Exception:
                pass
    product.image_path = new_image_path
    db.commit()
    db.close()
    return RedirectResponse("/inventory", status_code=302)
#delete
@router.post("/inventory/{product_id}/delete")
async def delete_product(request: Request, product_id: int):
    user_id = require_login(request)
    if not user_id:
        return RedirectResponse("/login",status_code=302)
    
    db = SessionLocal()
    product = (
        db.query(Product)
        .filter(Product.id == product_id, Product.user_id == user_id)
        .first()
    )

    if product:
        db.delete(product)
        db.commit()
    db.close()
    return RedirectResponse("/inventory", status_code=302)

#update/edit
@router.post("/inventory/{product_id}/edit")
async def edit_product(
    request: Request,
    product_id :int,
    name : str = Form(...),
    price : float = Form(...),
    stock : int = Form(...),
):
    user_id = require_login(request)
    if not user_id:
        return RedirectResponse("/login", status_code=302)
    
    db = SessionLocal()
    product = (
        db.query(Product)
        .filter(Product.id == product_id, Product.user_id == user_id)
        .first()
    )

    if product:
        product.name = name.strip()
        product.price = price
        product.stock = stock
        db.commit()
    db.close()
    return RedirectResponse("/inventory", status_code=302)

@router.post("/inventory/add")
async def add_product(
    request: Request,
    name: str = Form(...),
    price: float = Form(...),
    stock: int = Form(...),
    image: UploadFile = File(None),
):
    user_id = require_login(request)
    if not user_id:
        return RedirectResponse("/login", status_code=302)

    image_path = None

    if image is not None and image.filename:
        upload_dir = BASE_DIR / "static" / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)

        ext = os.path.splitext(image.filename)[1].lower()
        filename = f"{uuid.uuid4().hex}{ext}"
        save_path = upload_dir / filename

        contents = await image.read()
        with open(save_path, "wb") as f:
            f.write(contents)

        image_path = f"/static/uploads/{filename}"

    db = SessionLocal()
    db.add(
        Product(
            name=name.strip(),
            price=price,
            stock=stock,
            image_path=image_path,
            user_id=user_id,
        )
    )
    db.commit()
    db.close()

    return RedirectResponse("/inventory", status_code=302)
