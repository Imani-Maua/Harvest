from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from api.logger import get_logger
from api.warren.config import Settings
from api.warren.scheduler import build_scheduler
from api.daisy.routes import auth_router, limiter
from api.elaine.routes import elaine_router
from api.eleanor.routes import eleanor_router
from api.wayne.routes import wayne_router
from api.waweru.routes import waweru_router

settings = Settings()
log = get_logger(__name__)

app = FastAPI(title="Harvest", version="0.1.0")
_scheduler = build_scheduler()


@app.on_event("startup")
def start_scheduler():
    _scheduler.start()
    log.info("scheduler_started")


@app.on_event("shutdown")
def stop_scheduler():
    _scheduler.shutdown(wait=False)
    log.info("scheduler_stopped")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(elaine_router)
app.include_router(eleanor_router)
app.include_router(wayne_router)
app.include_router(waweru_router)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    log.error(
        "unhandled_exception",
        extra={"path": request.url.path, "method": request.method, "error": str(exc)},
        exc_info=exc,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred"},
    )


@app.get("/health")
def health():
    return {"status": "ok"}
