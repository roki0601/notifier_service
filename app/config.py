from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/"

    notification_exchange: str = "notification_exchange"
    notification_queue: str = "notification.tasks"
    notification_routing_key: str = "notification.task.key"

settings = Settings()