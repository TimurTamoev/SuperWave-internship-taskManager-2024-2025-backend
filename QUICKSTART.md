# Быстрый старт

## Минимальные шаги для запуска:

1. **Установите Python** (если не установлен): https://www.python.org/downloads/
   - ✅ Обязательно отметьте "Add Python to PATH"

2. **Откройте командную строку в папке проекта**

3. **Создайте виртуальное окружение:**
   ```cmd
   python -m venv venv
   ```

4. **Активируйте окружение:**
   ```cmd
   venv\Scripts\activate
   ```

5. **Установите зависимости:**
   ```cmd
   pip install -r requirements.txt
   ```

6. **Настройте переменные окружения:**
   ```cmd
   copy env.example .env
   ```
   Затем откройте `.env` и заполните:
   - `SECRET_KEY` - любая случайная строка 32+ символов
   - `ENCRYPTION_KEY` - любая случайная строка 32+ символов
   - `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM_EMAIL` - данные вашей почты

7. **Создайте админа (опционально):**
   ```cmd
   python create_superuser.py
   ```

8. **Запустите сервер:**
   ```cmd
   python main.py
   ```

9. **Откройте в браузере:**
   - API: http://localhost:8000
   - Документация: http://localhost:8000/api/docs

---

Подробные инструкции смотрите в [README.md](README.md)

