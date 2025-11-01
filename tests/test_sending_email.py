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


def create_response_template(token: str, title: str, body: str, send_response: bool = False):
    print(f"\n=== Создание шаблона: {title} ===")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.post(
        f"{BASE_URL}/responses/response/create",
        headers=headers,
        json={
            "title": title,
            "body": body,
            "send_response": send_response
        }
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 201:
        data = response.json()
        print(f"✓ Создан шаблон ID: {data['id']}")
        print(f"  Заголовок: {data['title']}")
        print(f"  Текст: {data['body']}")
        return data
    else:
        print(f"✗ Ошибка: {response.text}")
        return None


def get_all_templates(token: str):
    print("\n=== Получение всех шаблонов ===")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{BASE_URL}/responses/response/all",
        headers=headers
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        templates = response.json()
        print(f"✓ Найдено шаблонов: {len(templates)}")
        for t in templates:
            print(f"  - ID {t['id']}: {t['title']}")
        return templates
    else:
        print(f"✗ Ошибка: {response.text}")
        return []


def update_template(token: str, template_id: int, **kwargs):
    print(f"\n=== Обновление шаблона ID {template_id} ===")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.put(
        f"{BASE_URL}/responses/response/{template_id}",
        headers=headers,
        json=kwargs
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Шаблон обновлен")
        print(f"  Заголовок: {data['title']}")
        print(f"  Текст: {data['body']}")
        return data
    else:
        print(f"✗ Ошибка: {response.text}")
        return None


def attach_template_to_email(token: str, email_uid: str, template_id: int, 
                              subject: str = None, from_addr: str = None, notes: str = None):
    print(f"\n=== Прикрепление шаблона {template_id} к письму {email_uid} ===")
    headers = {"Authorization": f"Bearer {token}"}
    
    data = {
        "email_uid": email_uid,
        "response_template_id": template_id,
    }
    
    if subject:
        data["email_subject"] = subject
    if from_addr:
        data["email_from"] = from_addr
    if notes:
        data["notes"] = notes
    
    response = requests.post(
        f"{BASE_URL}/responses/response/attach",
        headers=headers,
        json=data
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 201:
        data = response.json()
        print(f"✓ Прикреплено, ID связи: {data['id']}")
        return data
    else:
        print(f"✗ Ошибка: {response.text}")
        return None


def get_email_attachments(token: str, email_uid: str):
    print(f"\n=== Получение ответов для письма {email_uid} ===")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{BASE_URL}/responses/response/attachments/email/{email_uid}",
        headers=headers
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        attachments = response.json()
        print(f"✓ Найдено прикрепленных ответов: {len(attachments)}")
        for att in attachments:
            print(f"  - Шаблон ID {att['response_template_id']}")
        return attachments
    else:
        print(f"✗ Ошибка: {response.text}")
        return []


def get_template_usage(token: str, template_id: int):
    print(f"\n=== Получение писем для шаблона {template_id} ===")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{BASE_URL}/responses/response/attachments/template/{template_id}",
        headers=headers
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        emails = response.json()
        print(f"✓ Шаблон использован для {len(emails)} писем:")
        for email in emails:
            print(f"  - {email['email_from']}: {email['email_subject']}")
        return emails
    else:
        print(f"✗ Ошибка: {response.text}")
        return []


def delete_attachment(token: str, attachment_id: int):
    print(f"\n=== Удаление связи ID {attachment_id} ===")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.delete(
        f"{BASE_URL}/responses/response/attachment/{attachment_id}",
        headers=headers
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 204:
        print(f"✓ Связь удалена")
        return True
    else:
        print(f"✗ Ошибка: {response.text}")
        return False


def delete_template(token: str, template_id: int):
    print(f"\n=== Удаление шаблона ID {template_id} ===")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.delete(
        f"{BASE_URL}/responses/response/{template_id}",
        headers=headers
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 204:
        print(f"✓ Шаблон удален")
        return True
    else:
        print(f"✗ Ошибка: {response.text}")
        return False


def full_workflow_test(token: str):
    print("\n" + "="*50)
    print("ПОЛНЫЙ ТЕСТ WORKFLOW")
    print("="*50)
    
    template1 = create_response_template(
        token,
        "Благодарность",
        "Спасибо за ваше обращение! Мы свяжемся с вами в ближайшее время.",
        send_response=False
    )
    
    template2 = create_response_template(
        token,
        "Уточнение",
        "Пожалуйста, предоставьте дополнительную информацию по вашему запросу.",
        send_response=False
    )
    
    template3 = create_response_template(
        token,
        "Решение проблемы",
        "Ваша проблема решена. Если есть вопросы, напишите нам.",
        send_response=True
    )
    
    if not all([template1, template2, template3]):
        print("\n✗ Не удалось создать шаблоны")
        return
    
    templates = get_all_templates(token)
    
    if template1:
        update_template(
            token,
            template1['id'],
            body="ОБНОВЛЕНО: Спасибо! Ответим в течение 24 часов."
        )
    
    email_uid_1 = "test_email_001"
    email_uid_2 = "test_email_002"
    
    attach1 = attach_template_to_email(
        token,
        email_uid_1,
        template1['id'],
        subject="Вопрос по продукту",
        from_addr="client1@example.com",
        notes="Клиент спрашивал о цене"
    )
    
    attach2 = attach_template_to_email(
        token,
        email_uid_2,
        template1['id'],
        subject="Проблема с заказом",
        from_addr="client2@example.com",
        notes="Требуется уточнение номера заказа"
    )
    
    attach3 = attach_template_to_email(
        token,
        email_uid_2,
        template2['id'],
        subject="Проблема с заказом",
        from_addr="client2@example.com",
        notes="Дополнительный шаблон для уточнения"
    )
    
    get_email_attachments(token, email_uid_1)
    get_email_attachments(token, email_uid_2)
    
    if template1:
        get_template_usage(token, template1['id'])
    
    if attach3:
        delete_attachment(token, attach3['id'])
    
    get_email_attachments(token, email_uid_2)
    
    if template3:
        delete_template(token, template3['id'])
    
    get_all_templates(token)
    
    print("\n" + "="*50)
    print("✓ ВСЕ ТЕСТЫ ЗАВЕРШЕНЫ")
    print("="*50)


def main():
    print("=== Тест Response Templates API ===")
    print(f"URL: {BASE_URL}")
    
    try:
        print("\n--- Вход ---")
        token = get_auth_token(USERNAME, PASSWORD)
        print("✓ Успешный вход")
        
        full_workflow_test(token)
        
    except Exception as e:
        print(f"\n✗ Ошибка: {str(e)}")


if __name__ == "__main__":
    main()

