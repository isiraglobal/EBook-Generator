from __future__ import annotations
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from editorial_studio.api.server import app as api_app


# Mount API
api_app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


@api_app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@api_app.get("/projects/{project_id}", response_class=HTMLResponse)
async def project_detail(request: Request, project_id: str):
    return templates.TemplateResponse("project.html", {"request": request, "project_id": project_id})


@api_app.get("/projects/{project_id}/editor", response_class=HTMLResponse)
async def project_editor(request: Request, project_id: str):
    return templates.TemplateResponse("editor.html", {"request": request, "project_id": project_id})


@api_app.get("/projects/{project_id}/preview", response_class=HTMLResponse)
async def pdf_preview(request: Request, project_id: str):
    return templates.TemplateResponse("preview.html", {"request": request, "project_id": project_id})


@api_app.get("/brands", response_class=HTMLResponse)
async def brands_page(request: Request):
    return templates.TemplateResponse("brands.html", {"request": request})


@api_app.get("/references", response_class=HTMLResponse)
async def references_page(request: Request):
    return templates.TemplateResponse("references.html", {"request": request})


def create_web_app() -> FastAPI:
    return api_app