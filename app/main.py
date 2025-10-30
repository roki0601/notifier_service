from fastapi import FastAPI, Depends, HTTPException, status
from contextlib import asynccontextmanager
import uuid
import logging

from .schemas import NotificationRequest, NotificationResponse
from .broker import Broker, get_broker, lifespan_startup, lifespan_shutdown
from .config import settings

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Запуск API сервиса...")
    await lifespan_startup()
    yield
    log.info("Остановка API сервиса...")
    await lifespan_shutdown()

app = FastAPI(
    title="Notification Service API",
    description="Принимает задачи на отправку уведомлений и ставит их в очередь.",
    version="1.0.0",
    lifespan=lifespan # Подключаем наш lifespan
)

@app.get("/health", status_code=status.HTTP_200_OK, tags=["Monitoring"])
async def health_check():
    """Простой хелс-чек, что сервис жив."""
    # TODO: в идеале, проверить и живость соединения с RabbitMQ
    return {"status": "ok"}

@app.post(
    "/api/v1/notifications/send",
    response_model=NotificationResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Notifications"]
)
async def send_notification(
    request: NotificationRequest,
    broker: Broker = Depends(get_broker)
):
    """
    Принимает задачу на отправку уведомления.
    Валидирует, генерирует ID и ставит в очередь RabbitMQ.
    """
    notification_id = uuid.uuid4()
    
    queue_message = request.model_dump()
    queue_message["notification_id"] = str(notification_id)
    
    try:
        await broker.publish_message(
            message_body=queue_message,
            routing_key=settings.notification_routing_key
        )

        return NotificationResponse(
            notification_id=notification_id
        )
        
    except ConnectionError as e:
        log.critical(f"Критическая ошибка: не удалось опубликовать в RabbitMQ: {e}", exc_info=True)
        # если очередь недоступна
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Сервис очередей временно недоступен. Повторите попытку позже."
        )
    except Exception as e:
        log.error(f"Неожиданная ошибка при постановке в очередь: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренняя ошибка сервера."
        )