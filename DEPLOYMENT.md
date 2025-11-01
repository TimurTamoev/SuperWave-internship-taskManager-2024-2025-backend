# Инструкция по развертыванию на продакшен

## Быстрый старт

1. Установите Python 3.9+
2. Создайте виртуальное окружение: `python -m venv venv`
3. Активируйте: `venv\Scripts\activate`
4. Установите зависимости: `pip install -r requirements.txt`
5. Настройте `.env` файл из `env.example`
6. Создайте админа: `python create_superuser.py`
7. Запустите: `uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4`

## Критические настройки для продакшена

### 1. Безопасность

Обязательно измените в `.env`:
- `SECRET_KEY` - сгенерируйте случайную строку минимум 32 символа
- `ENCRYPTION_KEY` - сгенерируйте случайную строку минимум 32 символа
- `DEBUG=False`
- `ENVIRONMENT="Продакшен"`

Генерация ключей:
```cmd
python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"
python -c "import secrets; print('ENCRYPTION_KEY=' + secrets.token_urlsafe(32))"
```

### 2. CORS настройки

Укажите реальные домены:
```env
CORS_ORIGINS=["https://ваш-домен.com", "https://www.ваш-домен.com"]
```

### 3. База данных

Для продакшена рекомендуется PostgreSQL. Измените `DATABASE_URL`:
```env
DATABASE_URL="postgresql://user:password@localhost/dbname"
```

Для SQLite (не рекомендуется для продакшена):
```env
DATABASE_URL="sqlite:///./swtaskmanager.db"
```

### 4. SMTP настройки

Заполните реальные данные:
```env
SMTP_USERNAME="ваш_email@mail.ru"
SMTP_PASSWORD="ваш_пароль"
SMTP_FROM_EMAIL="ваш_email@mail.ru"
```

## Запуск как Windows Service

### Установка NSSM

1. Скачайте NSSM: https://nssm.cc/download
2. Распакуйте в удобную папку, например `C:\nssm`

### Создание службы

Откройте командную строку от имени администратора:

```cmd
cd C:\nssm\win64
nssm install SWTaskManagerBackend
```

В открывшемся окне укажите:

**Вкладка Application:**
- Path: `C:\путь\к\проекту\venv\Scripts\python.exe`
- Startup directory: `C:\путь\к\проекту`
- Arguments: `-m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4`

**Вкладка Details:**
- Display name: `SWTaskManager Backend`
- Description: `Backend API для Менеджера задач СуперВейв`

**Вкладка Log on:**
- Если нужен доступ к файлам - укажите учетную запись с правами

Запуск службы:
```cmd
nssm start SWTaskManagerBackend
```

Остановка:
```cmd
nssm stop SWTaskManagerBackend
```

Удаление службы:
```cmd
nssm remove SWTaskManagerBackend
```

## Использование nginx как обратный прокси

Пример конфигурации nginx:

```nginx
server {
    listen 80;
    server_name ваш-домен.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Резервное копирование

Для SQLite создайте задачу в Планировщике заданий Windows:

```cmd
copy swtaskmanager.db swtaskmanager_backup_%date:~-4,4%%date:~-10,2%%date:~-7,2%.db
```

Рекомендуется настроить автоматическое резервное копирование базы данных.

## Мониторинг

Проверка работоспособности:
```cmd
curl http://localhost:8000/health
```

Или в браузере: http://localhost:8000/health

## Логирование

Логи uvicorn будут отображаться в консоли или можно перенаправить в файл:

```cmd
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4 --log-config logging.conf
```

Создайте `logging.conf` для детальной настройки логирования.

## Производительность

Рекомендуемое количество воркеров:
- CPU cores * 2 + 1
- Например, для 4 ядер: `--workers 9`

Для высокой нагрузки рассмотрите:
- Использование gunicorn с uvicorn workers
- Кэширование (Redis)
- Балансировка нагрузки

## Проверка после развертывания

1. Проверьте доступность API: `http://ваш-домен/health`
2. Проверьте документацию: `http://ваш-домен/api/docs`
3. Проверьте аутентификацию: попробуйте войти через API
4. Проверьте отправку email: создайте тестовый шаблон с `send_response=True`

