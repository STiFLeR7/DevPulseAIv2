
import asyncio
import os
from app.reports.daily import DailyReportGenerator
from app.core.mailer import MailerService

async def force_report():
    print("--- Forcing Daily Report Generation ---")
    
    try:
        # 1. Generate HTML from existing DB data
        print("Generating HTML...")
        generator = DailyReportGenerator()
        html_content = generator.generate_html_report()
        
        # 2. Send Email
        print("Sending Email...")
        mailer = MailerService()
        success = mailer.send_daily_report(html_content)
        
        if success:
            print("SUCCESS: Forced report sent.")
        else:
            print("FAILURE: Email sending failed.")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(force_report())
