
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"
USERNAME = "admin"  
PASSWORD = "admin"  

def get_auth_token(username: str, password: str) -> str:
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data={
            "username": username,
            "password": password
        }
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        raise Exception(f"Login failed: {response.text}")

def test_email_connection(token: str):
    print("Проверка подключения почты")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.post(
        f"{BASE_URL}/emails/test-connection",
        headers=headers,
        json={}
    )
    
    print(f"Статус код: {response.status_code}")
    print(f"Ответ: {json.dumps(response.json(), indent=2)}")
    return response.json()

def test_custom_email_connection(token: str, email: str, email_password: str):
    print("\nПроверка подключения кастомного email")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.post(
        f"{BASE_URL}/emails/test-connection",
        headers=headers,
        json={
            "email": email,
            "email_password": email_password,
            "imap_server": "imap.mail.ru",
            "imap_port": 993
        }
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.json()

def get_email_info(token: str):
    print("\nPoluchaem informaciu o polzovatele")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{BASE_URL}/emails/me",
        headers=headers
    )
    
    print(f"Status Kod: {response.status_code}")
    print(f"Otvet: {json.dumps(response.json(), indent=2)}")
    return response.json()

def list_email_folders(token: str):
    print("\n Poluchaem papki pisem")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{BASE_URL}/emails/folders",
        headers=headers
    )
    
    print(f"Status Kod: {response.status_code}")
    print(f"Otvet: {json.dumps(response.json(), indent=2)}")
    return response.json()

def fetch_emails(token: str, limit: int = 10, folder: str = "INBOX", search_criteria: str = "ALL"):
    print(f"\nPoluchenie{limit} pisem ot{folder}")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.post(
        f"{BASE_URL}/emails/fetch",
        headers=headers,
        json={
            "folder": folder,
            "limit": limit,
            "search_criteria": search_criteria,
            "include_body": True
        }
    )
    
    print(f"Status Code: {response.status_code}")
    result = response.json()
    
    if result.get("success"):
        print(f"Vse pisma: {result.get('total_count')}")
        for idx, email in enumerate(result.get('emails', []), 1):
            print(f"\nEmail #{idx}:")
            print(f"  Subject: {email['subject']}")
            print(f"  From: {email['from_address']}")
            print(f"  Date: {email.get('date', 'N/A')}")
            print(f"  Read: {email['is_read']}")
            print(f"  Has Attachments: {email['has_attachments']}")
            if email['has_attachments']:
                print(f"  Attachments: {[a['filename'] for a in email['attachments']]}")
    else:
        print(f"Error: {result.get('message')}")
    
    return result

def fetch_unread_emails(token: str, limit: int = 5):
    print(f"\nPolushenie pisem")
    return fetch_emails(token, limit=limit, search_criteria="UNSEEN")

def main():
    print("Enpoints script - pisma")
    print(f"URL: {BASE_URL}")
    
    try:
        print("\nVhod")
        token = get_auth_token(USERNAME, PASSWORD)
        print("Vhod proshel uspeshno")
        
        get_email_info(token)
        
        test_email_connection(token)
        
        print("\nVse testi proydeni uspeshno")
        
    except Exception as e:
        print(f"\n Oshibka: {str(e)}")

if __name__ == "__main__":
    main()