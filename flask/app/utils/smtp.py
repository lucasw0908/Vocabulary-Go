import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from typing import Literal

from ..config import SMTP_SERVER, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, DEFAULT_SENDER


log = logging.getLogger(__name__)
smtp = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)


def send_email(to_address, subject, body, subtype: Literal["plain", "html"]="plain"):
    
    smtp.connect(SMTP_SERVER, SMTP_PORT)
    
    msg = MIMEMultipart()
    msg["From"] = Header(DEFAULT_SENDER, "utf-8")
    msg["To"] = Header(to_address, "utf-8")
    msg["Subject"] = Header(subject, "utf-8")
    msg.attach(MIMEText(body, subtype, "utf-8"))
    
    try:  
        smtp.login(SMTP_USER, SMTP_PASSWORD)
        smtp.sendmail(SMTP_USER, to_address, msg.as_string())
        
    except smtplib.SMTPException as e:
        log.error(f"Failed to send email to {to_address}: {e}")
    
    finally:
        smtp.quit()
