from fastapi import APIRouter
from app.api.v1.endpoints import generator

router = APIRouter()

router.include_router(generator.app)