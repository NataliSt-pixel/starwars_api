import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


@dataclass
class DatabaseConfig:
    """Конфигурация базы данных"""
    host: str = os.getenv("DB_HOST", "localhost")
    port: int = int(os.getenv("DB_PORT", "5432"))
    name: str = os.getenv("DB_NAME", "starwars_api")
    user: str = os.getenv("DB_USER", "postgres")
    password: str = os.getenv("DB_PASSWORD", "")

    @property
    def url(self) -> str:
        """URL для подключения к PostgreSQL"""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"

    @property
    def async_url(self) -> str:
        """Async URL для подключения к PostgreSQL"""
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


@dataclass
class APIConfig:
    """Конфигурация API"""
    title: str = "Star Wars API"
    version: str = "1.0.0"
    description: str = "Асинхронное REST API для персонажей Star Wars"
    docs_url: str = "/docs"
    openapi_url: str = "/openapi.json"

    host: str = os.getenv("API_HOST", "0.0.0.0")
    port: int = int(os.getenv("API_PORT", "8000"))
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"

    swapi_base_url: str = "https://www.swapi.tech/api"
    rate_limit: int = int(os.getenv("RATE_LIMIT", "100"))


@dataclass
class Config:
    """Основная конфигурация приложения"""
    db: DatabaseConfig = DatabaseConfig()
    api: APIConfig = APIConfig()
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")


config = Config()