import aio_pika
import json
import logging
from .config import settings

log = logging.getLogger(__name__)

class Broker:
    """
    Класс-синглтон для управления соединением с RabbitMQ.
    """
    def __init__(self):
        self.connection = None
        self.channel = None
        self.exchange = None

    async def connect(self):
        """Подключается к RabbitMQ и объявляет exchange/queue."""
        try:
            self.connection = await aio_pika.connect_robust(settings.rabbitmq_url)
            self.channel = await self.connection.channel()
            
            self.exchange = await self.channel.declare_exchange(
                settings.notification_exchange,
                aio_pika.ExchangeType.DIRECT,
                durable=True
            )
            
            queue = await self.channel.declare_queue(
                settings.notification_queue,
                durable=True
            )
            
            await queue.bind(
                self.exchange,
                routing_key=settings.notification_routing_key
            )
            
            log.info("Успешное подключение к RabbitMQ. Exchange и Queue готовы.")
        except Exception as e:
            log.critical(f"Не удалось подключиться к RabbitMQ: {e}", exc_info=True)
            raise

    async def close(self):
        """Корректно закрывает соединения."""
        if self.channel:
            await self.channel.close()
        if self.connection:
            await self.connection.close()
        log.info("Соединение с RabbitMQ закрыто.")

    async def publish_message(self, message_body: dict, routing_key: str):
        """Публикует сообщение в наш exchange."""
        if not self.exchange:
            log.error("Exchange не инициализирован. Сообщение не отправлено.")
            raise ConnectionError("Соединение с RabbitMQ не установлено.")

        message = aio_pika.Message(
            body=json.dumps(message_body).encode(),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT 
        )
        
        await self.exchange.publish(message, routing_key=routing_key)
        log.info(f"Сообщение {message_body.get('notification_id')} опубликовано.")

broker = Broker()

async def lifespan_startup():
    await broker.connect()

async def lifespan_shutdown():
    await broker.close()

def get_broker():
    return broker