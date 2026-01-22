from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
from starlette.middleware.sessions import SessionMiddleware
from fastapi.responses import RedirectResponse
#auth
from app.routes import auth 
#db
from app.models import init_db
from dotenv import load_dotenv
import os
#inventory
from app.routes import inventory
#live order
from app.routes import live
#summary
from app.routes.summary import router as summary_router

load_dotenv()

app = FastAPI()
#db 
init_db()
#summary
app.include_router(summary_router)
#live route
app.include_router(live.router)
#inventory
app.include_router(inventory.router)
# secret key
secret = os.getenv("SECRET_KEY")
if not secret:
    raise RuntimeError("SECRET_KEY missing: put it in .env")
app.add_middleware(SessionMiddleware, secret_key=secret)

# auth
app.include_router(auth.router)

# Template Engine
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

#Serve Static Files css/js
app.mount("/static", StaticFiles(directory="app/static"), name="static")

#test route
@app.get("/",response_class=HTMLResponse)
async def dashboard(request: Request):
    if not request.session.get("user_id"):
        return RedirectResponse("/login", status_code=302)
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "user": request.session.get("user_name")},
    )


print("\n=== ROUTES ===")
for r in app.routes:
    methods = getattr(r, "methods", None)
    print(r.path, methods)
print("==============\n")
#async def read_root(request: Request):
    #return templates.TemplateResponse("dashboard.html",{"request":request})
