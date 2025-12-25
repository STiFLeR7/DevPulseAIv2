import asyncio
import os
import sys
from dotenv import load_dotenv

# Ensure root path
sys.path.append(os.getcwd())

# Load env manually to ensure we catch updates
load_dotenv(override=True)

from app.core.mailer import MailerService

def test_email():
    print("--- Testing Email Configuration ---")
    mailer = MailerService()
    print(f"SMTP User: {mailer.smtp_user}")
    
    html = """
    <h1>Test Email from DevPulseAI</h1>
    <p>If you are seeing this, the SMTP configuration is working correctly.</p>
    """
    
    print("Sending test email...")
    success = mailer.send_daily_report(html)
    
    if success:
        print("✅ Email sent successfully!")
    else:
        print("❌ Email failed to send.")

if __name__ == "__main__":
    test_email()
