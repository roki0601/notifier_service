import logging

log = logging.getLogger(__name__)

async def get_user_contacts(user_id: str) -> dict:
    """
    Фейковый поход в бд.
    """
    log.info(f"Запрашиваю контакты для user_id: {user_id}")
    # фейковая база данных
    users_db = {
        "user-uuid-12345": {
            "email": "real.user@example.com",
            "phone": "+1234567890",
            "telegram": "987654321",
            "preferred_channel": "telegram"
        },
        "user-uuid-67890": {
            "email": "manager@company.com",
            "phone": "+199988877",
            "telegram": None, # У него нет телеграма
            "preferred_channel": "email"
        }
    }
    return users_db.get(user_id, {})

async def get_template(event_name: str, channel: str, payload: dict) -> str:
    """Рендерит сообщение."""  
    text = f"EVENT: {event_name}, CHANNEL: {channel}"
    
    if event_name == "order.shipped":
        order_id = payload.get("order_id", "N/A")
        if channel == "telegram":
            text = f"🚚 *Заказ №{order_id}* отправлен! Ура!"
        elif channel == "email":
            name = payload.get("customer_name", "Клиент")
            text = f"<html><body>Уважаемый {name}, Ваш заказ {order_id} отправлен.</body></html>"
        elif channel == "sms":
            text = f"ZAKAZ {order_id} otpravlen."
            
    return text