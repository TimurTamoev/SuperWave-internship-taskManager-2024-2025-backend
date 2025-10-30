from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, emails, responses

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth")
api_router.include_router(users.router, prefix="/users")
api_router.include_router(emails.router, prefix="/emails")
api_router.include_router(responses.router, prefix="/responses")
