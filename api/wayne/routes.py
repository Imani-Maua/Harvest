from fastapi import APIRouter

from api.wayne.internal.routes.jobs_applied import jobs_applied_router
from api.wayne.internal.routes.network import network_router

wayne_router = APIRouter()
wayne_router.include_router(jobs_applied_router)
wayne_router.include_router(network_router)
