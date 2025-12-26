import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.logger import logger
import os

class MailerService:
    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.admin_email = os.getenv("ADMIN_EMAIL", "")

    def send_daily_report(self, html_content: str):
        if not self.smtp_user or not self.smtp_password:
            logger.warning("SMTP credentials not set. Skipping email dispatch.")
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = "☀️ DevPulseAI Daily Intelligence"
            msg["From"] = self.smtp_user
            msg["To"] = self.admin_email

            part = MIMEText(html_content, "html")
            msg.attach(part)

            # Try SSL (465) by default or if specified
            if self.smtp_port == 465:
                with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port) as server:
                    server.login(self.smtp_user, self.smtp_password)
                    server.sendmail(self.smtp_user, self.admin_email, msg.as_string())
            else:
                # Fallback/Default to TLS (587)
                with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                    server.starttls()
                    server.login(self.smtp_user, self.smtp_password)
                    server.sendmail(self.smtp_user, self.admin_email, msg.as_string())
            
            logger.info(f"Daily report sent to {self.admin_email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
