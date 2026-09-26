import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()

class Settings(BaseSettings):
    DB_HOST: str = os.getenv('DB_HOST')
    DB_PORT: int = int(os.getenv('DB_PORT'))
    DB_USER: str = os.getenv('DB_USER')
    DB_PASSWORD: str = os.getenv('DB_PASSWORD')
    DB_NAME: str = os.getenv('DB_NAME')
    DB_URL: str = os.getenv('DB_URL')
    SECRET_KEY: str = os.getenv('SECRET_KEY')
    ALGORITHM: str = os.getenv('ALGORITHM')
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES'))
    REFRESH_TOKEN_EXPIRE_MINUTES: int = int(os.getenv('REFRESH_TOKEN_EXPIRE_MINUTES')) * 24 * 7

    # --- Admin por defecto ---
    DEFAULT_ADMIN_EMAIL: str = os.getenv('DEFAULT_ADMIN_EMAIL')
    DEFAULT_ADMIN_PASSWORD: str = os.getenv('DEFAULT_ADMIN_PASSWORD')
    DEFAULT_ADMIN_FULL_NAME: str = os.getenv('DEFAULT_ADMIN_FULL_NAME')
    CREATE_DEFAULT_ADMIN: bool = bool(os.getenv('CREATE_DEFAULT_ADMIN'))
    
    BASE_URL: str = os.getenv('BASE_URL')
    
    class Config:
        env_file = ".env"
        
settings = Settings()