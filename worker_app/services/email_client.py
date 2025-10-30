import asyncio
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import logging

log = logging.getLogger(__name__)


async def send_email_message(
    smtp_host: str, 
    smtp_port: int, 
    username: str, 
    password: str, 
    sender_email: str, 
    recipient_email: str, 
    subject: str, 
    html_content: str
):
    """
    Асинхронная функция для отправки письма через SMTP.
    """
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = recipient_email
    
    msg.attach(MIMEText(html_content, 'html'))

    try:
        loop = asyncio.get_event_loop()
        
        await loop.run_in_executor(
            None,
            lambda: _sync_send_email(
                smtp_host, smtp_port, username, password, sender_email, recipient_email, msg.as_string()
            )
        )
        
        log.info(f"✅ [SUCCESS] Sent to EMAIL ({recipient_email}) with subject: {subject}")
        return True

    except smtplib.SMTPException as e:
        log.warning(f"SMTP Error: {e}")
        # перебрасываем как ConnectionError, чтобы адаптер мог обработать фолбэк
        raise ConnectionError(f"SMTP server failed to send: {e}")
    except Exception as e:
        log.error(f"Unexpected error during Email send: {e}", exc_info=True)
        raise ConnectionError(f"Unexpected error: {e}")


def _sync_send_email(
    host, port, username, password, sender_email, recipient_email, message_string
):
    """
    Синхронная часть отправки, выполняемая в отдельном потоке.
    """
    with smtplib.SMTP(host, port) as server:
        server.login(username, password)
        server.sendmail(sender_email, recipient_email, message_string)