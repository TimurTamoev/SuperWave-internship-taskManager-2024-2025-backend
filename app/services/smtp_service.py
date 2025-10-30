import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from typing import Optional, Tuple
from app.core.config import settings


class SMTPService:
    """Сервис для отправки email через SMTP"""

    def __init__(
        self,
        smtp_server: str = None,
        smtp_port: int = None,
        username: str = None,
        password: str = None,
        from_email: str = None,
        from_name: str = None,
        use_tls: bool = True
    ):
        self.smtp_server = smtp_server or settings.SMTP_SERVER
        self.smtp_port = smtp_port or settings.SMTP_PORT
        self.username = username or settings.SMTP_USERNAME
        self.password = password or settings.SMTP_PASSWORD
        self.from_email = from_email or settings.SMTP_FROM_EMAIL
        self.from_name = from_name or settings.SMTP_FROM_NAME
        self.use_tls = use_tls

    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        reply_to_subject: Optional[str] = None,
        is_html: bool = False
    ) -> Tuple[bool, str]:
        """
        Отправить email
        
        Args:
            to_email: Email получателя
            subject: Тема письма
            body: Тело письма
            reply_to_subject: Тема исходного письма (для Re:)
            is_html: Отправлять как HTML
            
        Returns:
            Tuple[success: bool, message: str]
        """
        if not self.username or not self.password or not self.from_email:
            return False, "SMTP не настроен. Проверьте SMTP_USERNAME, SMTP_PASSWORD и SMTP_FROM_EMAIL в настройках."

        try:
            # Создать сообщение
            msg = MIMEMultipart('alternative')
            
            # Если это ответ, добавить Re: к теме
            if reply_to_subject:
                if not reply_to_subject.startswith("Re:"):
                    subject = f"Re: {reply_to_subject}"
                else:
                    subject = reply_to_subject
            
            msg['Subject'] = subject
            msg['From'] = formataddr((self.from_name, self.from_email))
            msg['To'] = to_email
            
            # Добавить тело письма
            if is_html:
                part = MIMEText(body, 'html', 'utf-8')
            else:
                part = MIMEText(body, 'plain', 'utf-8')
            
            msg.attach(part)
            
            # Подключиться к SMTP серверу
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            
            if self.use_tls:
                server.starttls()
            
            # Войти
            server.login(self.username, self.password)
            
            # Отправить
            server.send_message(msg)
            server.quit()
            
            return True, f"Email успешно отправлен на {to_email}"
            
        except smtplib.SMTPAuthenticationError:
            return False, "Ошибка аутентификации SMTP. Проверьте логин и пароль."
        except smtplib.SMTPException as e:
            return False, f"Ошибка SMTP: {str(e)}"
        except Exception as e:
            return False, f"Неожиданная ошибка при отправке email: {str(e)}"

    def test_connection(self) -> Tuple[bool, str]:
        """
        Проверить подключение к SMTP серверу
        
        Returns:
            Tuple[success: bool, message: str]
        """
        if not self.username or not self.password:
            return False, "SMTP учетные данные не настроены"
        
        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            
            if self.use_tls:
                server.starttls()
            
            server.login(self.username, self.password)
            server.quit()
            
            return True, "Подключение к SMTP серверу успешно"
            
        except smtplib.SMTPAuthenticationError:
            return False, "Ошибка аутентификации SMTP"
        except Exception as e:
            return False, f"Ошибка подключения к SMTP: {str(e)}"

