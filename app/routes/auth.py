from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from app.models import SessionLocal, User, pwd_context

router = APIRouter()
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@router.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request":request, "error":None})

@router.post("/login")
async def login(request: Request, email: str = Form(...), password: str = Form(...)):
    email = email.strip().lower()
    password = password.strip()
    if len(password.encode("utf-8")) > 72:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Password too long (max 72 bytes)."},
        )

    db = SessionLocal()
    user = db.query(User).filter(User.email == email).first()
    db.close()

    if user and pwd_context.verify(password, user.password_hash):
        request.session["user_id"] = user.id
        request.session["user_email"] = user.email
        request.session["user_name"] = user.full_name
        return RedirectResponse("/", status_code=302)

    return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials."})


@router.get("/register")
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request, "error": None})


@router.post("/register")
async def register(
    request: Request,
    full_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    business_name: str = Form(None),
    phone: str = Form(None),
):
    full_name = full_name.strip()
    email = email.strip().lower()
    password = password.strip()
    if len(password.encode("utf-8")) > 72:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Password too long (max 72 bytes)."},
        )

    db = SessionLocal()
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        db.close()
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Email is already registered."},
        )

    user = User(
        full_name=full_name,
        email=email,
        business_name=(business_name or "").strip() or None,
        phone=(phone or "").strip() or None,
        password_hash=pwd_context.hash(password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()

    request.session["user_id"] = user.id
    request.session["user_email"] = user.email
    request.session["user_name"] = user.full_name
    return RedirectResponse("/", status_code=302)
    
@router.get("/logout")    
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=302)
