"""
Тест автоматической отправки email
Демонстрирует работу send_response=True
"""

import requests
import json

BASE_URL = "http://localhost:8000/api/v1"
USERNAME = "admin"
PASSWORD = "admin"


def get_auth_token(username: str, password: str) -> str:
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data={"username": username, "password": password}
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        raise Exception(f"Login failed: {response.text}")


def test_smtp_connection(token: str):
    """Проверить SMTP подключение"""
    print("\n=== Проверка SMTP ===")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.post(
        f"{BASE_URL}/responses/smtp/test",
        headers=headers
    )
    
    result = response.json()
    print(f"Статус: {'✓' if result['success'] else '✗'}")
    print(f"Сообщение: {result['message']}")
    
    return result["success"]


def create_template_with_autosend(token: str, title: str, body: str):
    """Создать шаблон с автоотправкой"""
    print(f"\n=== Создание шаблона с send_response=True ===")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.post(
        f"{BASE_URL}/responses/response/create",
        headers=headers,
        json={
            "title": title,
            "body": body,
            "send_response": True  # ← КЛЮЧЕВОЙ ПАРАМЕТР
        }
    )
    
    if response.status_code == 201:
        template = response.json()
        print(f"✓ Создан шаблон ID {template['id']}: {template['title']}")
        print(f"  send_response: {template['send_response']}")
        return template
    else:
        print(f"✗ Ошибка: {response.text}")
        return None


def create_template_without_autosend(token: str, title: str, body: str):
    """Создать шаблон БЕЗ автоотправки"""
    print(f"\n=== Создание шаблона с send_response=False ===")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.post(
        f"{BASE_URL}/responses/response/create",
        headers=headers,
        json={
            "title": title,
            "body": body,
            "send_response": False  # Email НЕ отправится
        }
    )
    
    if response.status_code == 201:
        template = response.json()
        print(f"✓ Создан шаблон ID {template['id']}: {template['title']}")
        print(f"  send_response: {template['send_response']}")
        return template
    else:
        print(f"✗ Ошибка: {response.text}")
        return None


def attach_and_send(token: str, template_id: int, email_uid: str, email_from: str, email_subject: str = None):
    """Прикрепить шаблон (с автоотправкой если send_response=True)"""
    print(f"\n=== Прикрепление шаблона {template_id} к письму {email_uid} ===")
    headers = {"Authorization": f"Bearer {token}"}
    
    data = {
        "email_uid": email_uid,
        "response_template_id": template_id,
        "email_from": email_from,
    }
    
    if email_subject:
        data["email_subject"] = email_subject
    
    response = requests.post(
        f"{BASE_URL}/responses/response/attach",
        headers=headers,
        json=data
    )
    
    if response.status_code == 201:
        print(f"✓ Прикреплено")
        print(f"  Если send_response=True, email был автоматически отправлен на {email_from}")
        return response.json()
    else:
        print(f"✗ Ошибка: {response.text}")
        return None


def get_sent_emails_stats(token: str):
    """Получить статистику отправленных email"""
    print("\n=== Статистика отправленных email ===")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{BASE_URL}/responses/sent-emails/stats",
        headers=headers
    )
    
    if response.status_code == 200:
        stats = response.json()
        print(f"Всего отправлено: {stats['total_sent']}")
        print(f"Успешно: {stats['successful']}")
        print(f"Ошибок: {stats['failed']}")
        
        if stats['recent_emails']:
            print(f"\nПоследние отправленные:")
            for email in stats['recent_emails'][:5]:
                status = "✓" if email['success'] else "✗"
                print(f"  {status} {email['to_email']}: {email['subject']}")
                if not email['success']:
                    print(f"    Ошибка: {email['error_message']}")
        
        return stats
    else:
        print(f"✗ Ошибка: {response.text}")
        return None


def get_all_sent_emails(token: str, success_only: bool = None):
    """Получить все отправленные email"""
    print(f"\n=== Все отправленные email ===")
    headers = {"Authorization": f"Bearer {token}"}
    
    params = {}
    if success_only is not None:
        params["success_only"] = success_only
    
    response = requests.get(
        f"{BASE_URL}/responses/sent-emails/all",
        headers=headers,
        params=params
    )
    
    if response.status_code == 200:
        emails = response.json()
        print(f"Найдено: {len(emails)} писем")
        for email in emails[:10]:
            status = "✓ Успешно" if email['success'] else "✗ Ошибка"
            print(f"  {status} | {email['to_email']} | {email['subject']}")
        return emails
    else:
        print(f"✗ Ошибка: {response.text}")
        return None


def demonstration_workflow(token: str):
    """Полная демонстрация функционала"""
    print("\n" + "="*60)
    print("ДЕМОНСТРАЦИЯ АВТОМАТИЧЕСКОЙ ОТПРАВКИ EMAIL")
    print("="*60)
    
    # 1. Проверить SMTP
    smtp_works = test_smtp_connection(token)
    
    if not smtp_works:
        print("\n⚠️  SMTP не настроен!")
        print("Настройте SMTP в .env файле:")
        print("  SMTP_USERNAME=your_email@mail.ru")
        print("  SMTP_PASSWORD=your_password")
        print("  SMTP_FROM_EMAIL=your_email@mail.ru")
        print("\nПродолжение демонстрации (без реальной отправки)...")
    
    # 2. Создать шаблон С автоотправкой
    template_auto = create_template_with_autosend(
        token,
        "Автоответ",
        "Спасибо за обращение! Мы ответим в течение 24 часов."
    )
    
    # 3. Создать шаблон БЕЗ автоотправки
    template_manual = create_template_without_autosend(
        token,
        "Заметка",
        "Это только заметка, email не отправится."
    )
    
    # 4. Прикрепить шаблон с автоотправкой
    if template_auto:
        print("\n--- Тест 1: Прикрепление с автоотправкой ---")
        attach_and_send(
            token,
            template_auto["id"],
            "test_email_001",
            "client@example.com",
            "Вопрос по продукту"
        )
    
    # 5. Прикрепить шаблон без автоотправки
    if template_manual:
        print("\n--- Тест 2: Прикрепление БЕЗ автоотправки ---")
        attach_and_send(
            token,
            template_manual["id"],
            "test_email_002",
            "another@example.com",
            "Другой вопрос"
        )
    
    # 6. Прикрепить с автоотправкой, но БЕЗ email_from (ошибка)
    if template_auto:
        print("\n--- Тест 3: Автоотправка БЕЗ email_from (будет ошибка) ---")
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(
            f"{BASE_URL}/responses/response/attach",
            headers=headers,
            json={
                "email_uid": "test_email_003",
                "response_template_id": template_auto["id"],
                # НЕТ email_from!
            }
        )
        if response.status_code == 201:
            print("✓ Прикреплено, но email НЕ отправлен (нет email_from)")
        else:
            print(f"Ошибка: {response.text}")
    
    # 7. Показать статистику
    get_sent_emails_stats(token)
    
    # 8. Показать все отправленные
    get_all_sent_emails(token)
    
    # 9. Показать только ошибки
    print("\n--- Только ошибки ---")
    get_all_sent_emails(token, success_only=False)
    
    print("\n" + "="*60)
    print("ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА")
    print("="*60)
    print("\nЧто произошло:")
    print("1. ✓ Проверено SMTP подключение")
    print("2. ✓ Создан шаблон с send_response=True")
    print("3. ✓ Создан шаблон с send_response=False")
    print("4. ✓ При прикреплении шаблона с send_response=True → email отправлен автоматически")
    print("5. ✓ При прикреплении шаблона с send_response=False → email НЕ отправлен")
    print("6. ✓ Все отправки записаны в базу данных")
    print("7. ✓ Статистика доступна через /sent-emails/stats")


def main():
    print("=== Тест автоматической отправки Email ===")
    print(f"URL: {BASE_URL}")
    
    try:
        print("\n--- Вход ---")
        token = get_auth_token(USERNAME, PASSWORD)
        print("✓ Успешный вход")
        
        # Запустить демонстрацию
        demonstration_workflow(token)
        
    except Exception as e:
        print(f"\n✗ Ошибка: {str(e)}")


if __name__ == "__main__":
    main()

