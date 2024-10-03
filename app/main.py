from fastapi import FastAPI

from app.api import router

app = FastAPI()

# Подключение API роутеров
app.include_router(router)
