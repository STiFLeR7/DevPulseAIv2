
import asyncio
import os
from dotenv import load_dotenv
load_dotenv(override=True)
from app.models.signal import Signal
from app.api.main import process_signals
from app.reports.daily import DailyReportGenerator
from app.core.mailer import MailerService
from app.persistence.client import db
from datetime import datetime

async def verify_quick():
    print("--- Starting Quick Verification (1 Item Per Source) ---")
    
    # 1. Create Dummy Signals (Source-Specific to test Colors)
    mock_signals = [
        Signal(source="github", external_id="test_gh_1", title="Test GitHub Repo", content="A test repo for coloring", url="https://github.com"),
        Signal(source="huggingface", external_id="test_hf_1", title="Test HF Model", content="A test model", url="https://huggingface.co"),
        Signal(source="medium", external_id="test_med_1", title="Test Medium Blog", content="A test blog", url="https://medium.com"),
        Signal(source="arxiv", external_id="test_arxiv_1", title="Test ArXiv Paper", content="A test paper", url="https://arxiv.org"),
        Signal(source="twitter", external_id="test_x_1", title="Test Tweet", content="A test tweet", url="https://x.com"),
    ]
    
    # 2. Store & Process
    signals_map = {}
    for sig in mock_signals:
        # Unique ID to ensure newness
        sig.external_id = f"test_{sig.source}_{datetime.utcnow().timestamp()}"
        try:
            print(f"DEBUG: Inserting {sig.external_id}")
            print(f"DEBUG: Payload keys: {sig.model_dump(mode='json').keys()}")
            record = db.insert_raw_signal(sig.source, sig.external_id, sig.model_dump(mode='json'), sig.generate_hash())
            if record:
                signals_map[record['id']] = sig
        except Exception as e:
            print(f"FAILED INSERT: {e}")
            # Try to print detailed response if available
            if hasattr(e, 'message'): print(e.message)
            if hasattr(e, 'details'): print(e.details)
            if hasattr(e, 'hint'): print(e.hint)
            raise e
            
    print(f"Stored {len(signals_map)} test signals. Running Agents...")
    
    # 3. Run Agents (Real Gemini)
    await process_signals(signals_map)
    print("Agent processing complete.")
    
    # 4. Generate & Send
    print("Generating Report...")
    gen = DailyReportGenerator()
    html = gen.generate_html_report()
    
    print("Sending Email...")
    mailer = MailerService()
    if mailer.send_daily_report(html):
        print("SUCCESS: Quick verification email sent!")
    else:
        print("FAILURE: Email sending failed.")

if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(verify_quick())
