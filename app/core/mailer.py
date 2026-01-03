"""
Email Service using Resend API (HTTPS-based, not blocked by Render).
Fallback to SMTP if Resend key is not configured.
"""
import os
import requests
from app.core.logger import logger

class MailerService:
    def __init__(self):
        # Primary: Resend API (HTTPS - works on Render)
        self.resend_api_key = os.getenv("RESEND_API_KEY", "").strip()
        self.from_email = os.getenv("FROM_EMAIL", "onboarding@resend.dev").strip()
        self.admin_email = os.getenv("ADMIN_EMAIL", "").strip()
        
        # Legacy SMTP fallback
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")

    def send_daily_report(self, html_content: str) -> bool:
        """Send email via Resend API (or SMTP fallback)."""
        if self.resend_api_key:
            return self._send_via_resend(html_content)
        elif self.smtp_user and self.smtp_password:
            return self._send_via_smtp(html_content)
        else:
            logger.warning("No email credentials configured. Skipping email.")
            return False

    def _send_via_resend(self, html_content: str) -> bool:
        """Send via Resend HTTP API (Port 443 - not blocked)."""
        try:
            logger.info(f"Sending email via Resend API... FROM={self.from_email} TO={self.admin_email}")
            response = requests.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {self.resend_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "from": self.from_email,
                    "to": [self.admin_email],
                    "subject": "☀️ DevPulseAI Daily Intelligence",
                    "html": html_content
                },
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"Email sent successfully via Resend to {self.admin_email}")
                return True
            else:
                logger.error(f"Resend API error: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Resend send failed: {e}")
            return False

    def _send_via_smtp(self, html_content: str) -> bool:
        """Legacy SMTP fallback (may not work on Render Free Tier)."""
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = "☀️ DevPulseAI Daily Intelligence"
            msg["From"] = self.smtp_user
            msg["To"] = self.admin_email
            msg.attach(MIMEText(html_content, "html"))

            # Try SSL first, then TLS
            try:
                with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10) as server:
                    server.login(self.smtp_user, self.smtp_password)
                    server.sendmail(self.smtp_user, self.admin_email, msg.as_string())
                logger.info("Email sent via SMTP (SSL).")
                return True
            except Exception:
                with smtplib.SMTP("smtp.gmail.com", 587, timeout=10) as server:
                    server.starttls()
                    server.login(self.smtp_user, self.smtp_password)
                    server.sendmail(self.smtp_user, self.admin_email, msg.as_string())
                logger.info("Email sent via SMTP (TLS).")
                return True
        except Exception as e:
            logger.error(f"SMTP failed: {e}")
            return False
