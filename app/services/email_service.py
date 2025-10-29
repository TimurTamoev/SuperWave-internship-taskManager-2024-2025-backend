import imaplib
import email
from email.header import decode_header
from typing import List, Optional, Tuple
from datetime import datetime
import re
from app.schemas.email import EmailMessage, EmailAttachment, EmailFolderInfo


class EmailService:
    def __init__(self, email_address: str, password: str, imap_server: str = "imap.mail.ru", imap_port: int = 993):
        self.email_address = email_address
        self.password = password
        self.imap_server = imap_server
        self.imap_port = imap_port
        self.connection: Optional[imaplib.IMAP4_SSL] = None

    def connect(self) -> Tuple[bool, str]:
        try:
            self.connection = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            self.connection.login(self.email_address, self.password)
            return True, "Успешно подключено к серверу email"
        except imaplib.IMAP4.error as e:
            return False, f"Ошибка IMAP аутентификации: {str(e)}"
        except Exception as e:
            return False, f"Соединение потеряно: {str(e)}"

    def disconnect(self):
        if self.connection:
            try:
                self.connection.close()
                self.connection.logout()
            except:
                pass
            self.connection = None

    def test_connection(self) -> Tuple[bool, str, Optional[str]]:
        success, message = self.connect()
        details = None
        if success:
            try:
                status, count = self.connection.select('INBOX')
                if status == 'OK':
                    message_count = int(count[0])
                    details = f"Подключено успешно. INBOX содержит {message_count} сообщений."
                else:
                    success = False
                    message = "Подключение успешно, ошибка подключения INBOX"
            except Exception as e:
                success = False
                message = f"Подключение успешно, ошибка подключения mailbox: {str(e)}"
            finally:
                self.disconnect()
        
        return success, message, details

    def list_folders(self) -> List[EmailFolderInfo]:
        folders = []
        try:
            status, folder_list = self.connection.list()
            if status == 'OK':
                for folder in folder_list:
                    folder_str = folder.decode() if isinstance(folder, bytes) else folder
                    match = re.search(r'"([^"]+)"$', folder_str)
                    if match:
                        folder_name = match.group(1)
                        folders.append(EmailFolderInfo(name=folder_name))
        except Exception as e:
            print(f"Ошибка процессинга папок: {str(e)}")
        
        return folders

    def _decode_mime_words(self, s: str) -> str:
        if not s:
            return ""
        
        decoded_fragments = decode_header(s)
        decoded_string = ""
        
        for fragment, charset in decoded_fragments:
            if isinstance(fragment, bytes):
                try:
                    if charset:
                        decoded_string += fragment.decode(charset)
                    else:
                        decoded_string += fragment.decode('utf-8', errors='ignore')
                except:
                    decoded_string += fragment.decode('utf-8', errors='ignore')
            else:
                decoded_string += fragment
        
        return decoded_string

    def _parse_email_address(self, address_header: str) -> str:
        if not address_header:
            return ""
        
        decoded = self._decode_mime_words(address_header)
        
        email_match = re.search(r'<(.+?)>', decoded)
        if email_match:
            return email_match.group(1)
        
        return decoded.strip()

    def _parse_email_addresses(self, address_header: str) -> List[str]:
        if not address_header:
            return []
        
        addresses = []
        parts = address_header.split(',')
        for part in parts:
            addr = self._parse_email_address(part.strip())
            if addr:
                addresses.append(addr)
        
        return addresses

    def _get_email_body(self, msg: email.message.Message) -> Tuple[Optional[str], Optional[str]]:
        plain_text = None
        html = None

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))

                if "attachment" in content_disposition:
                    continue

                try:
                    body = part.get_payload(decode=True)
                    if body:
                        charset = part.get_content_charset() or 'utf-8'
                        body = body.decode(charset, errors='ignore')

                        if content_type == "text/plain":
                            plain_text = body
                        elif content_type == "text/html":
                            html = body
                except Exception as e:
                    print(f"Ошибка декодирования письма часть: {str(e)}")
                    continue
        else:
            try:
                body = msg.get_payload(decode=True)
                if body:
                    charset = msg.get_content_charset() or 'utf-8'
                    body = body.decode(charset, errors='ignore')
                    
                    content_type = msg.get_content_type()
                    if content_type == "text/plain":
                        plain_text = body
                    elif content_type == "text/html":
                        html = body
                    else:
                        plain_text = body  
            except Exception as e:
                print(f"Ошибка расшифровки письма часть: {str(e)}")

        return plain_text, html

    def _get_attachments(self, msg: email.message.Message) -> List[EmailAttachment]:
        attachments = []
        
        if msg.is_multipart():
            for part in msg.walk():
                content_disposition = str(part.get("Content-Disposition", ""))
                
                if "attachment" in content_disposition:
                    filename = part.get_filename()
                    if filename:
                        filename = self._decode_mime_words(filename)
                        content_type = part.get_content_type()
                        
                        payload = part.get_payload(decode=True)
                        size = len(payload) if payload else 0
                        
                        attachments.append(EmailAttachment(
                            filename=filename,
                            content_type=content_type,
                            size=size
                        ))
        
        return attachments

    def fetch_emails(
        self, 
        folder: str = "INBOX", 
        limit: int = 50, 
        search_criteria: str = "ALL",
        include_body: bool = True
    ) -> List[EmailMessage]:

        emails = []
        
        try:
            status, count = self.connection.select(folder, readonly=True)
            if status != 'OK':
                return emails
            
            status, messages = self.connection.search(None, search_criteria)
            if status != 'OK':
                return emails
            
            email_ids = messages[0].split()
            
            email_ids = email_ids[-limit:] if len(email_ids) > limit else email_ids
            
            email_ids = list(reversed(email_ids))
            
            for email_id in email_ids:
                try:
                    if include_body:
                        status, msg_data = self.connection.fetch(email_id, '(RFC822 FLAGS)')
                    else:
                        status, msg_data = self.connection.fetch(email_id, '(BODY[HEADER] FLAGS)')
                    
                    if status != 'OK':
                        continue
                    
                    flags_part = msg_data[0] if isinstance(msg_data[0], bytes) else msg_data[0][0]
                    is_read = b'\\Seen' in flags_part
                    
                    raw_email = msg_data[0][1]
                    msg = email.message_from_bytes(raw_email)
                    
                    subject = self._decode_mime_words(msg.get('Subject', '(No Subject)'))
                    from_address = self._parse_email_address(msg.get('From', ''))
                    to_addresses = self._parse_email_addresses(msg.get('To', ''))
                    
                    date_str = msg.get('Date')
                    email_date = None
                    if date_str:
                        try:
                            email_date = email.utils.parsedate_to_datetime(date_str)
                        except:
                            pass
                    
                    plain_text = None
                    html = None
                    if include_body:
                        plain_text, html = self._get_email_body(msg)
                    
                    attachments = self._get_attachments(msg)
                    
                    email_msg = EmailMessage(
                        uid=email_id.decode(),
                        subject=subject,
                        from_address=from_address,
                        to_addresses=to_addresses,
                        date=email_date,
                        body_plain=plain_text,
                        body_html=html,
                        has_attachments=len(attachments) > 0,
                        attachments=attachments,
                        is_read=is_read
                    )
                    
                    emails.append(email_msg)
                    
                except Exception as e:
                    print(f"Ошибка процессинга писем{email_id}: {str(e)}")
                    continue
        
        except Exception as e:
            print(f"Ошибка получения писем: {str(e)}")
        
        return emails

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

