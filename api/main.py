from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from api.warren.config import Settings
from api.daisy.routes import auth_router, limiter
from api.elaine.routes import elaine_router
from api.eleanor.routes import eleanor_router
from api.wayne.routes import wayne_router

settings = Settings()

app = FastAPI(title="Harvest", version="0.1.0")

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


@app.get("/health")
def health():
    return {"status": "ok"}
