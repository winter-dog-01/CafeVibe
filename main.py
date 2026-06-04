from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.database import Base, engine
from app.routers import auth, pages, api, profile, admin, owner
import app.models  # ensure all models are registered

Base.metadata.create_all(bind=engine)

app = FastAPI(title="CafeVibe", docs_url="/docs")

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(pages.router)
app.include_router(auth.router)
app.include_router(api.router)
app.include_router(profile.router)
app.include_router(admin.router)
app.include_router(owner.router)

templates = Jinja2Templates(directory="app/templates")


@app.exception_handler(404)
async def not_found(request: Request, exc):
    return templates.TemplateResponse("404.html", {"request": request, "current_user": None}, status_code=404)
