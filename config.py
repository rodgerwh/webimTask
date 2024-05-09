from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Redis
    REDIS_HOST: str = "redis"
    REDIS_PORT: str = "6379"
    REDIS_URL: str = f"redis://{REDIS_HOST}:{REDIS_PORT}"

    # GitHub OAuth
    GITHUB_CLIENT_ID: str = "Iv23ligsAaz9odF6zv04"
    GITHUB_CLIENT_SECRET: str
    GITHUB_AUTHORIZE_URL: str = "https://github.com/login/oauth/authorize"
    GITHUB_TOKEN_URL: str = "https://github.com/login/oauth/access_token"
    GITHUB_USER_URL: str = "https://api.github.com/user"

    model_config = SettingsConfigDict(env_file=".env")


@lru_cache
def get_settings():
    return Settings()


settings = get_settings()
