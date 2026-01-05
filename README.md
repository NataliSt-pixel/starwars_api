#  Advertisements Async API

Асинхронное REST API для сервиса объявлений на основе aiohttp с полной аутентификацией и авторизацией.

##  Особенности

- **Асинхронная архитектура** на aiohttp
- **JWT аутентификация** с Bearer токенами
- **Полный CRUD** для пользователей и объявлений
- **Авторизация** - только автор может редактировать/удалять свои объявления
- **SQLite** для быстрого старта, **PostgreSQL** для production
- **CORS поддержка**
- **Пагинация и фильтрация**

##  Быстрый старт

### Установка и запуск (SQLite)
```bash
# Клонируйте репозиторий
git clone https://github.com/NataliSt-pixel/advertisements-api.git
cd advertisements-api

# Установите зависимости
pip install -r requirements.txt

# Запустите сервер
python run.py