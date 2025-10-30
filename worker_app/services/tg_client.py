import logging
from telegram import Bot
from telegram.error import TelegramError

from config import settings

log = logging.getLogger(__name__)

bot_client = Bot(token=settings.telegram_bot_token)


async def send_telegram_message(chat_id: str, text: str):
    """
    Отправляет увед в тг
    """
    try:
        chat_id = int(chat_id)
    except ValueError:
        raise ValueError("Invalid Telegram ID format.")

    try:
        await bot_client.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode='MarkdownV2'
        )
        
        log.info(f"✅ [SUCCESS] Sent to TELEGRAM (ID: {chat_id})")
        return True
        
    except TelegramError as e:
        log.warning(f"Telegram API Error: {e.message}")
        # бросаем общую ошибку, чтобы наша логика фолбэка ее поймала
        raise ConnectionError(f"Telegram API failed: {e.message}")
    except Exception as e:
        log.error(f"Unexpected error during Telegram send: {e}", exc_info=True)
        raise ConnectionError(f"Unexpected error: {e}")