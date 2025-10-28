from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from app.core.config import settings
from app.api.v1.router import api_router
from app.core.database import engine, Base

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Backend для сервиса по организации задач ООО СуперВейв групп",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.include_router(api_router, prefix="/api/v1")


@app.get("/", summary = "Начальная страница", tags = ["Начальная страница"])
async def root():
    return {
        "сообщение": "Добро пожаловать в API системы по организации задачи ООО СуперВейв групп",
        "Версия": settings.APP_VERSION,
        "Документация": "/api/docs",
    }


@app.get("/health", summary = "Проверить состояние сервера", tags = ["Состояние сервера"])
async def health_check():
    return {"Статус": "Запущен", "Статус разработки": settings.ENVIRONMENT}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG
    )
