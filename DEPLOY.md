# Быстрый деплой

## Первый запуск на сервере

```bash
# 1. Скопировать проект на сервер
scp -r callerapi user@server:/opt/

# 2. Войти на сервер
ssh user@server

# 3. Перейти в директорию
cd /opt/callerapi

# 4. Настроить .env файл
cp .env.example .env
nano .env  # Заполнить реальные значения

# 5. Сделать скрипты исполняемыми
chmod +x *.sh

# 6. Запустить
./deploy.sh
```

## Управление

```bash
# Запуск
./start.sh

# Остановка
./stop.sh

# Перезапуск
./restart.sh

# Логи
./logs.sh

# Обновление и деплой
./deploy.sh
```

## Проверка работы

```bash
# Health check
curl http://localhost:8000/health

# Логи backend
./logs.sh backend

# Логи frontend
./logs.sh frontend

# Статус контейнеров
docker-compose -f docker-compose.production.yml ps
```

## Порты

- Backend: `127.0.0.1:8000`
- Frontend: `127.0.0.1:8012`

Nginx на сервере должен проксировать эти порты на публичный домен.
