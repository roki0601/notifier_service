import aio_pika
import asyncio
import json
import logging
from aio_pika.abc import AbstractIncomingMessage

from config import settings
from adapters import send_email, send_telegram, send_sms
from services_mock import get_template, get_user_contacts

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)


async def process_notification(task_body: dict):
    """
    Главная бизнес-логика.
    """
    event = task_body.get('event_name')
    user_id = task_body.get('user_id')
    payload = task_body.get('payload', {})
    notification_id = task_body.get('notification_id')

    log.info(f"Начинаю обработку {notification_id} (Событие: {event}, Юзер: {user_id})")


    contacts = await get_user_contacts(user_id)
    if not contacts:
        log.error(f"Не найдены контакты для user_id {user_id}. Сообщение отброшено.")
        return True

    strategy = [
        (contacts.get("preferred_channel"), contacts.get(contacts.get("preferred_channel", "_"))), # Предпочитаемый
        ("telegram", contacts.get("telegram_id")),
        ("email", contacts.get("email")),
        ("sms", contacts.get("phone")),
    ]

    processed_strategy = []
    seen_channels = set()
    for channel, contact_info in strategy:
        if channel and contact_info and channel not in seen_channels:
            processed_strategy.append((channel, contact_info))
            seen_channels.add(channel)
            
    log.info(f"Стратегия для {user_id}: {processed_strategy}")
            
    sent = False
    for channel, contact_info in processed_strategy:
        try:
            # получаем шаблон
            template = await get_template(event, channel, payload)
            
            # вызываем адаптер
            if channel == "telegram":
                await send_telegram(contact_info, template)
            elif channel == "email":
                await send_email(contact_info, template)
            elif channel == "sms":
                await send_sms(contact_info, template)
            
            sent = True
            log.info(f"УСПЕХ ({notification_id}). Отправлено через {channel}.")
            break

        except Exception as e:
            log.warning(f"Провал ({notification_id})! Канал {channel} не сработал. Ошибка: {e}")

    if not sent:
        log.error(f"Уведомление не отправлено ({notification_id}). Юзер {user_id}")
        
    return False


async def on_message(message: AbstractIncomingMessage) -> None:
    """
    Callback-функция, которая вызывается при получении нового сообщения.
    """
    async with message.process():
        
        try:
            body = message.body.decode()
            log.info(f"Получена задача из RabbitMQ: {body}")
            task_body = json.loads(body)

            if "user_id" not in task_body or "event_name" not in task_body:
                log.error("Некорректное сообщение, не хватает user_id или event_name.")
                return False

        except json.JSONDecodeError:
            log.error(f"Не удалось декодировать JSON: {message.body}")
            return False
        except Exception as e:
            log.error(f"Неизвестная ошибка парсинга: {e}")
            return False

        try:
            await process_notification(task_body)
        except Exception as e:
            log.critical(f"Критический сбой в process_notification: {e}", exc_info=True)
            raise # бросаем исключение, чтобы 'message.process()' сделал 'nack'


async def main():
    log.info("Запуск Воркера...")
    try:
        connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    except Exception as e:
        log.critical(f"Не могу подключиться к RabbitMQ, сервис не стартует: {e}")
        return

    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=10)
        
        queue = await channel.declare_queue(
            settings.notification_queue,
            durable=True
        )
        
        log.info(f"Воркер подключен. Ожидание сообщений в очереди '{settings.notification_queue}'...")
        
        await queue.consume(on_message)
        
        try:
            await asyncio.Future()
        except asyncio.CancelledError:
            log.info("Воркер останавливается...")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("Воркер остановлен (Ctrl+C).")