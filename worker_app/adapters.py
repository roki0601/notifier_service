import asyncio
import random
import logging
from config import settings
from services import send_telegram_message, send_email_message

log = logging.getLogger(__name__)


SMS_FAIL_CHANCE = 10

async def send_telegram(telegram_id: str, text: str):
    """отправщик Telegram."""
    await send_telegram_message(chat_id=telegram_id, text=text)

    log.info(f"✅ [SUCCESS] Sent to TELEGRAM ({telegram_id}): '{text}'")
    return True

async def send_email(email: str, html: str):
    """отправщик Email."""
    subject = "Ваше уведомление от сервиса" 
    
    try:
        await send_email_message(
            smtp_host=settings.smtp_host,
            smtp_port=settings.smtp_port,
            username=settings.smtp_username,
            password=settings.smtp_password,
            sender_email=settings.smtp_sender_email,
            recipient_email=email,
            subject=subject,
            html_content=html
        )
        log.info(f"✅ [SUCCESS] Sent to EMAIL ({email}): '{html[:30]}...'")
        return True
    except ConnectionError as e:
        # если email_client выбросил ConnectionError, мы его ловим и перебрасываем,
        # чтобы логика фолбэка в worker.py перешла к SMS.
        raise e
    except Exception as e:
        log.error(f"Критическая ошибка при вызове email_client: {e}", exc_info=True)
        raise ConnectionError("Critical email adapter failure.")
    
    

async def send_sms(phone: str, text: str):
    """Фейковый отправщик SMS."""
    await asyncio.sleep(1.5) # не работал с смс, но есть сервис и библиоетка к нему smsru-api 1.2"
    if random.randint(1, 100) <= SMS_FAIL_CHANCE:
        raise ConnectionError("SmsService is Unavailable")
    
    log.info(f"✅ [SUCCESS] Sent to SMS ({phone}): '{text}'")
    return True