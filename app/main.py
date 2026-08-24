from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.health import router as health_router
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import AppError


@asynccontextmanager
async def lifespan(_app: FastAPI):
    yield


def _app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
    headers = {"WWW-Authenticate": "Bearer"} if exc.status_code == 401 else None
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
        headers=headers,
    )


def create_app() -> FastAPI:
    application = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        lifespan=lifespan,
    )
    application.add_exception_handler(AppError, _app_error_handler)
    application.include_router(health_router)
    application.include_router(api_router, prefix=settings.api_v1_prefix)
    return application


app = create_app()
