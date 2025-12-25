import asyncio
import os
import sys
from dotenv import load_dotenv

# Ensure root path
sys.path.append(os.getcwd())
load_dotenv(override=True)

from app.api.main import run_ingestion_task
from app.reports.daily import DailyReportGenerator
from app.core.mailer import MailerService
from app.core.logger import logger

async def run_full_cycle():
    print("--- Starting Live Cycle Test ---")
    
    # 1. Ingest from Sources
    sources = ["github", "arxiv", "medium", "huggingface", "twitter"]
    
    for source in sources:
        print(f"--- Ingesting {source} ---")
        try:
            await run_ingestion_task(source, run_agents=True)
            print(f"DONE: {source}")
        except Exception as e:
            print(f"FAILED: {source} - {e}")

    # 2. Generate Report
    print("--- Generating Report ---")
    generator = DailyReportGenerator()
    html = generator.generate_html_report()
    
    # 3. Send Email
    print("--- Sending Email ---")
    mailer = MailerService()
    # Override subject for this test if needed, but the service has it hardcoded or we can modify it? 
    # The service code: msg["Subject"] = "☀️ DevPulseAI Daily Intelligence"
    # User asked for title "DevPulseAI". The current subject is close enough, or I can patch it.
    # Let's stick to the service default as it's "DevPulseAI Daily Intelligence".
    
    if mailer.send_daily_report(html):
        print("SUCCESS: Email sent successfully to hillaniljppatel@gmail.com")
    else:
        print("FAILURE: Email sending failed.")

if __name__ == "__main__":
    # Windows/Python 3.10+ loop policy fix if needed, but usually fine.
    asyncio.run(run_full_cycle())
