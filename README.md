## 📄 README.md: Сервис Уведомлений (Notification Service)

### 🚀 Обзор проекта

Этот сервис представляет собой асинхронный микросервис, предназначенный для обработки и доставки уведомлений (событий) пользователям по различным каналам (Telegram, Email, SMS) с использованием стратегии фолбэка.

Сервис состоит из двух основных компонентов:

1.  API (Producer): Принимает HTTP-запросы от клиентских систем и ставит задачи в очередь RabbitMQ. Построен на FastAPI.
2.  Воркер (Consumer): Читает задачи из RabbitMQ, извлекает контакты пользователя, генерирует шаблон сообщения и пытается доставить его по приоритетной стратегии. Построен на aio-pika и asyncio.

### ✨ Ключевые особенности

  * Асинхронность: Использование asyncio для эффективной обработки большого числа уведомлений.
  * Надежность: Применение RabbitMQ с персистентными сообщениями (Durable/Persistent) гарантирует, что задачи не будут потеряны при падении сервиса.
  * Фолбэк-стратегия (High Reliability): Если предпочтительный канал (н-р, Telegram) не сработал, система автоматически пытается отправить сообщение через следующий канал (Email), а затем через последний (SMS).
  * Каналы доставки:
      * Telegram:  отправка через python-telegram-bot.
      * Email:  отправка через SMTP (с использованием smtplib в run_in_executor).
      * SMS: заглушка (может быть легко заменена реальным адаптером, например, для smsru-api).

### ⚙️ Стек технологий

  * Язык: Python 3.11+
  * API Framework: FastAPI
  * Очередь сообщений: RabbitMQ
  * Асинхронные библиотеки: asyncio, aio-pika
  * Библиотеки для каналов: python-telegram-bot, smtplib

### 🛠 Установка и запуск

#### 1\. Предварительные требования

Для запуска необходимы:

  * Python 3.11+
  * Docker (или локально установленный RabbitMQ)

#### 2\. Запуск RabbitMQ

Используйте Docker для быстрого запуска RabbitMQ:

docker run -d --hostname rabbit-host --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3-management

*(Порт 15672 открывает веб-интерфейс управления RabbitMQ: http://localhost:15672)*

#### 3\. Настройка окружения

Создайте файл .env в корне проекта по примеру

#### 4\. Установка зависимостей

uv sync

\*(Если нет uv, то используйте pip install -r requirements.txt) \*

#### 5\. Запуск компонентов

Терминал 1: Запуск API (Продюсер)

uvicorn app.main:app --reload

API будет доступен по адресу http://localhost:8000.

Терминал 2: Запуск Воркера (Консьюмер)

python -m app.worker

### 🎯 Использование (API Endpoint)

Основная точка входа — /api/v1/notifications/send.

Метод: POST
URL: http://localhost:8000/api/v1/notifications/send

#### Пример запроса

curl -X POST "http://localhost:8000/api/v1/notifications/send" \
-H "Content-Type: application/json" \
-d '{
  "user_id": "user-uuid-12345",
  "event_name": "order.shipped",
  "payload": {
    "order_id": "ORD-1004", 
    "customer_name": "Тест",
    "tracking_number": "ZN98765"
  }
}'

#### Пример ответа (Status 202 Accepted)

{
  "status": "queued",
  "message": "Notification task accepted and queued for processing.",
  "notification_id": "f58f4a7c-3f2e-4b7d-8c1a-2e3b4d5f6a7b"
}

### 💡 Как работает Фолбэк

Воркер использует следующую стратегию, основанную на данных из services_mock.py:
1.  Проверка контактов: Получение контактов и preferred_channel для user_id.
2.  Формирование стратегии:
      * Попытка 1: Предпочитаемый канал (например, Telegram).
      * Попытка 2: Email.
      * Попытка 3: SMS.
3.  Исполнение: Воркер пытается доставить сообщение. Если канал возвращает ошибку, унаследованную от `ConnectionError` (API-ошибка, недоступность сервера и т.д.), он переходит к следующему каналу в списке.