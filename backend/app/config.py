from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ES_HOST: str = "localhost"
    ES_PORT: int = 9200
    KAFKA_BROKER: str = "localhost:9092"
    MINIO_ENDPOINT: str = "http://localhost:9000"
    AIRFLOW_URL: str = "http://localhost:8080"
    APP_NAME: str = "TFT Analytics API"
    DEBUG: bool = False
    
    class Config:
        env_file = ".env"

settings = Settings()
