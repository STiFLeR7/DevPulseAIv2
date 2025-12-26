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

        msg = MIMEMultipart("alternative")
        msg["Subject"] = "☀️ DevPulseAI Daily Intelligence"
        msg["From"] = self.smtp_user
        msg["To"] = self.admin_email
        part = MIMEText(html_content, "html")
        msg.attach(part)

        # Strategy 1: Try SSL (Port 465) - Preferred for Gmail
        try:
            logger.info("Attempting using SMTP_SSL (Port 465)...")
            with smtplib.SMTP_SSL(self.smtp_host, 465, timeout=10) as server:
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.smtp_user, self.admin_email, msg.as_string())
            logger.info(f"Email sent successfully via Port 465.")
            return True
        except Exception as e:
            logger.warning(f"Port 465 failed ({e}). Retrying with TLS (Port 587)...")

        # Strategy 2: Fallback to TLS (Port 587)
        try:
            with smtplib.SMTP(self.smtp_host, 587, timeout=10) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.smtp_user, self.admin_email, msg.as_string())
            logger.info(f"Email sent successfully via Port 587.")
            return True
        except Exception as e:
            logger.error(f"All SMTP attempts failed. Last error: {e}")
            return False
