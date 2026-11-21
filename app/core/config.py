from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    PROJECT_NAME: str = "B2B Document & Request Validator"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = False

    DATABASE_URL: str | None = None

    DB_DRIVER: str = "sqlite+aiosqlite"
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "postgres"
    DB_PASSWORD: str = ""
    DB_NAME: str = "b2b_validator"
    DB_ECHO: bool = False

    @computed_field
    @property
    def async_database_url(self) -> str:
        if self.DATABASE_URL:
            url = self.DATABASE_URL
            if url.startswith("postgresql://"):
                return url.replace("postgresql://", "postgresql+asyncpg://", 1)
            if url.startswith("sqlite://") and not url.startswith("sqlite+aiosqlite://"):
                return url.replace("sqlite://", "sqlite+aiosqlite://", 1)
            return url

        if "sqlite" in self.DB_DRIVER:
            return f"{self.DB_DRIVER}:///./{self.DB_NAME}.db"

        auth = f"{self.DB_USER}:{self.DB_PASSWORD}" if self.DB_PASSWORD else self.DB_USER
        return f"{self.DB_DRIVER}://{auth}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


settings = Settings()
